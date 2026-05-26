"""
Quiz Engine — question management, quiz generation, scoring
"""
import json, random, os
from .database import get_db
from .config import MODULE_META, DIFFICULTY_LEVELS, DATA_DIR

def load_seed_questions():
    """Load seed questions from JSON file"""
    seed_path = os.path.join(DATA_DIR, "questions_seed.json")
    if not os.path.exists(seed_path):
        return []
    with open(seed_path) as f:
        return json.load(f)

def seed_questions_to_db():
    """Import seed questions into SQLite (idempotent)"""
    conn = get_db()
    questions = load_seed_questions()
    inserted = 0
    for q in questions:
        try:
            cur = conn.execute("""
                INSERT OR IGNORE INTO questions (id, module_code, domain, difficulty, qtype, question, options_json, answer, explanation, tags, source)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                q["id"], q["module_code"], q.get("domain", ""), q.get("difficulty", "L2"),
                q.get("qtype", "single"), q["question"],
                json.dumps(q.get("options", []), ensure_ascii=False),
                q["answer"], q.get("explanation", ""),
                q.get("tags", ""), q.get("source", "")
            ))
            inserted += 1 if cur.rowcount and cur.rowcount > 0 else 0
        except:
            pass
    conn.commit()
    total = conn.execute("SELECT COUNT(*) as c FROM questions").fetchone()["c"]
    conn.close()
    return {"inserted": inserted, "total": total}

def _row_to_public_question(row: dict):
    q = dict(row)
    try:
        q["options"] = json.loads(q.get("options_json", "[]"))
    except:
        q["options"] = []
    q.pop("answer", None)
    return q

def generate_mistake_quiz(user_id: int, module_code: str = "", count: int = 10, difficulty: str = None):
    """Generate a quiz from unmastered mistakes"""
    conn = get_db()
    conditions = ["m.user_id=? AND m.mastered=0"]
    params = [user_id]
    if module_code:
        conditions.append("q.module_code=?")
        params.append(module_code)
    if difficulty:
        conditions.append("q.difficulty=?")
        params.append(difficulty)

    rows = conn.execute(
        f"""
        SELECT q.*, m.wrong_count, m.last_wrong_at
        FROM mistakes m JOIN questions q ON m.question_id = q.id
        WHERE {' AND '.join(conditions)}
        ORDER BY m.wrong_count DESC, m.last_wrong_at DESC
        LIMIT ?
        """,
        (*params, count),
    ).fetchall()
    conn.close()
    return [_row_to_public_question(dict(r)) for r in rows]

def get_progress_summary(user_id: int):
    """Progress summary by module (completion %)"""
    conn = get_db()

    totals = {
        row["module_code"]: row["total"]
        for row in conn.execute(
            "SELECT module_code, COUNT(*) as total FROM questions GROUP BY module_code"
        ).fetchall()
    }

    progress_rows = {
        row["module_code"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM progress WHERE user_id=?", (user_id,)
        ).fetchall()
    }

    items = []
    for mc, total in sorted(totals.items()):
        p = progress_rows.get(mc, {})
        done = int(p.get("questions_done", 0) or 0)
        correct = int(p.get("questions_correct", 0) or 0)
        reading_count = int(p.get("reading_count", 0) or 0)
        completion = round(min(1.0, (done / total) if total else 0.0) * 100, 1) if total else 0.0
        accuracy = round((correct / done) * 100, 1) if done > 0 else 0.0
        meta = MODULE_META.get(mc, {"name": mc, "desc": ""})
        items.append(
            {
                "module_code": mc,
                "name": meta.get("name", mc),
                "desc": meta.get("desc", ""),
                "total_questions": total,
                "questions_done": done,
                "questions_correct": correct,
                "accuracy": accuracy,
                "completion_pct": completion,
                "reading_count": reading_count,
            }
        )

    conn.close()
    return {"user_id": user_id, "modules": items}

def generate_daily_recommendation(user_id: int, count: int = 10):
    """
    Daily recommendation based on progress:
    - Prefer modules with low completion
    - Prefer unanswered questions
    """
    conn = get_db()

    totals = {
        row["module_code"]: row["total"]
        for row in conn.execute(
            "SELECT module_code, COUNT(*) as total FROM questions GROUP BY module_code"
        ).fetchall()
    }
    if not totals:
        conn.close()
        return []

    progress = {
        row["module_code"]: dict(row)
        for row in conn.execute(
            "SELECT module_code, questions_done FROM progress WHERE user_id=?", (user_id,)
        ).fetchall()
    }

    answered_ids = {
        row["question_id"]
        for row in conn.execute(
            "SELECT DISTINCT question_id FROM answers WHERE user_id=?", (user_id,)
        ).fetchall()
    }

    module_rank = []
    for mc, total in totals.items():
        done = int(progress.get(mc, {}).get("questions_done", 0) or 0)
        completion = (done / total) if total else 0.0
        module_rank.append((completion, mc))
    module_rank.sort(key=lambda x: x[0])

    picked = []
    picked_ids = set()
    for _, mc in module_rank:
        if len(picked) >= count:
            break
        rows = conn.execute(
            """
            SELECT * FROM questions
            WHERE module_code=?
            ORDER BY CASE difficulty WHEN 'L1' THEN 1 WHEN 'L2' THEN 2 ELSE 3 END, RANDOM()
            """,
            (mc,),
        ).fetchall()
        for r in rows:
            if len(picked) >= count:
                break
            qid = r["id"]
            if qid in picked_ids:
                continue
            if qid in answered_ids:
                continue
            picked_ids.add(qid)
            picked.append(_row_to_public_question(dict(r)))

    if len(picked) < count:
        remaining = count - len(picked)
        rows = conn.execute(
            """
            SELECT * FROM questions
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (remaining * 3,),
        ).fetchall()
        for r in rows:
            if len(picked) >= count:
                break
            qid = r["id"]
            if qid in picked_ids:
                continue
            picked_ids.add(qid)
            picked.append(_row_to_public_question(dict(r)))

    conn.close()
    return picked[:count]

def generate_quiz(user_id: int, module_code: str, count: int = 10, difficulty: str = None):
    """
    Generate a quiz for a user.
    Strategy: 30% mistakes + 70% new/unanswered, difficulty ascending
    """
    conn = get_db()
    
    # Get mistake question IDs
    mistake_ids = set()
    for row in conn.execute(
        "SELECT question_id FROM mistakes WHERE user_id=? AND mastered=0", (user_id,)
    ).fetchall():
        mistake_ids.add(row["question_id"])
    
    # Get answered question IDs
    answered_ids = set()
    for row in conn.execute(
        "SELECT DISTINCT question_id FROM answers WHERE user_id=?", (user_id,)
    ).fetchall():
        answered_ids.add(row["question_id"])
    
    # Build query
    conditions = ["module_code=?"]
    params = [module_code]
    if difficulty:
        conditions.append("difficulty=?")
        params.append(difficulty)
    
    all_questions = conn.execute(
        f"SELECT * FROM questions WHERE {' AND '.join(f'({c})' for c in conditions)}",
        params
    ).fetchall()
    
    conn.close()
    
    if not all_questions:
        return []
    
    # Separate into mistakes, unanswered, and answered
    mistake_pool = [dict(q) for q in all_questions if q["id"] in mistake_ids]
    unanswered_pool = [dict(q) for q in all_questions if q["id"] not in answered_ids]
    answered_pool = [dict(q) for q in all_questions if q["id"] in answered_ids and q["id"] not in mistake_ids]
    
    # Shuffle each pool
    random.shuffle(mistake_pool)
    random.shuffle(unanswered_pool)
    random.shuffle(answered_pool)
    
    # Sort by difficulty within each pool
    for pool in [mistake_pool, unanswered_pool, answered_pool]:
        pool.sort(key=lambda x: x.get("difficulty", "L2"))
    
    # Build quiz: mistakes first, then unanswered, fill with answered
    quiz = []
    mistake_count = min(len(mistake_pool), max(3, count // 3))  # ~30% mistakes
    quiz.extend(mistake_pool[:mistake_count])
    
    remaining = count - len(quiz)
    quiz.extend(unanswered_pool[:remaining])
    
    remaining = count - len(quiz)
    if remaining > 0:
        quiz.extend(answered_pool[:remaining])
    
    # Final shuffle and parse options
    random.shuffle(quiz)
    for q in quiz:
        try:
            q["options"] = json.loads(q.get("options_json", "[]"))
        except:
            q["options"] = []
        # Don't send answer to client
        q.pop("answer", None)
    
    return quiz[:count]

def submit_answer(user_id: int, question_id: str, user_answer: str, spent_seconds: float = 0):
    """Record an answer and update stats"""
    conn = get_db()
    
    # Get correct answer
    q = conn.execute("SELECT answer, module_code FROM questions WHERE id=?", (question_id,)).fetchone()
    if not q:
        conn.close()
        return None
    
    is_correct = (user_answer.strip().upper() == q["answer"].strip().upper())
    
    # Record answer
    conn.execute("""
        INSERT INTO answers (user_id, question_id, user_answer, is_correct, spent_seconds)
        VALUES (?,?,?,?,?)
    """, (user_id, question_id, user_answer, 1 if is_correct else 0, spent_seconds))
    
    # Update mistakes
    if is_correct:
        conn.execute("""
            UPDATE mistakes SET mastered=1 WHERE user_id=? AND question_id=?
        """, (user_id, question_id))
    else:
        conn.execute("""
            INSERT INTO mistakes (user_id, question_id, wrong_count, last_wrong_at)
            VALUES (?,?,1,CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, question_id) DO UPDATE SET
                wrong_count = wrong_count + 1,
                last_wrong_at = CURRENT_TIMESTAMP,
                mastered = 0
        """, (user_id, question_id))
    
    # Update progress
    conn.execute("""
        INSERT INTO progress (user_id, module_code, questions_done, questions_correct)
        VALUES (?,?,1,?)
        ON CONFLICT(user_id, module_code) DO UPDATE SET
            questions_done = questions_done + 1,
            questions_correct = questions_correct + ?,
            last_activity = CURRENT_TIMESTAMP
    """, (user_id, q["module_code"], 1 if is_correct else 0, 1 if is_correct else 0))
    
    conn.commit()
    conn.close()
    
    return {"is_correct": is_correct, "correct_answer": q["answer"]}

def get_user_stats(user_id: int):
    """Get user's overall statistics"""
    conn = get_db()
    stats = {}
    
    # Overall
    row = conn.execute("""
        SELECT COUNT(*) as total, SUM(is_correct) as correct
        FROM answers WHERE user_id=?
    """, (user_id,)).fetchone()
    stats["total_questions"] = row["total"] or 0
    stats["total_correct"] = row["correct"] or 0
    stats["accuracy"] = round(stats["total_correct"] / stats["total_questions"] * 100, 1) if stats["total_questions"] > 0 else 0
    
    # Mistake count
    row = conn.execute("""
        SELECT COUNT(*) as c FROM mistakes WHERE user_id=? AND mastered=0
    """, (user_id,)).fetchone()
    stats["pending_mistakes"] = row["c"]
    
    # Module breakdown
    module_stats = {}
    for row in conn.execute("""
        SELECT q.module_code, COUNT(*) as total, SUM(a.is_correct) as correct
        FROM answers a JOIN questions q ON a.question_id = q.id
        WHERE a.user_id=?
        GROUP BY q.module_code
    """, (user_id,)).fetchall():
        mc = row["module_code"]
        meta = MODULE_META.get(mc, {"name": mc})
        module_stats[mc] = {
            "name": meta["name"],
            "total": row["total"],
            "correct": row["correct"] or 0,
            "accuracy": round((row["correct"] or 0) / row["total"] * 100, 1) if row["total"] > 0 else 0
        }
    stats["modules"] = module_stats
    
    # Difficulty breakdown
    diff_stats = {}
    for row in conn.execute("""
        SELECT q.difficulty, COUNT(*) as total, SUM(a.is_correct) as correct
        FROM answers a JOIN questions q ON a.question_id = q.id
        WHERE a.user_id=?
        GROUP BY q.difficulty
    """, (user_id,)).fetchall():
        diff_stats[row["difficulty"]] = {
            "name": DIFFICULTY_LEVELS.get(row["difficulty"], row["difficulty"]),
            "total": row["total"],
            "correct": row["correct"] or 0,
            "accuracy": round((row["correct"] or 0) / row["total"] * 100, 1) if row["total"] > 0 else 0
        }
    stats["by_difficulty"] = diff_stats
    
    # Top mistakes
    top_mistakes = []
    for row in conn.execute("""
        SELECT m.question_id, q.question, q.module_code, m.wrong_count
        FROM mistakes m JOIN questions q ON m.question_id = q.id
        WHERE m.user_id=? AND m.mastered=0
        ORDER BY m.wrong_count DESC LIMIT 10
    """, (user_id,)).fetchall():
        top_mistakes.append({
            "question_id": row["question_id"],
            "question": row["question"][:80],
            "module": MODULE_META.get(row["module_code"], {}).get("name", row["module_code"]),
            "wrong_count": row["wrong_count"],
        })
    stats["top_mistakes"] = top_mistakes
    
    conn.close()
    return stats

def log_reading(user_id: int, module_code: str, entry_title: str = ""):
    """Log a reading event"""
    conn = get_db()
    conn.execute("INSERT INTO reading_logs (user_id, module_code, entry_title) VALUES (?,?,?)",
                 (user_id, module_code, entry_title))
    conn.execute("""
        INSERT INTO progress (user_id, module_code, reading_count)
        VALUES (?,?,1)
        ON CONFLICT(user_id, module_code) DO UPDATE SET
            reading_count = reading_count + 1,
            last_activity = CURRENT_TIMESTAMP
    """, (user_id, module_code))
    conn.commit()
    conn.close()
