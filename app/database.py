"""
SQLite database — users, questions, answers, progress
"""
import sqlite3, os, hashlib, secrets
from .config import DB_PATH, DATA_DIR

os.makedirs(DATA_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'newbie',
            display_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            module_code TEXT NOT NULL,
            domain TEXT,
            difficulty TEXT NOT NULL DEFAULT 'L2',
            qtype TEXT NOT NULL DEFAULT 'single',
            question TEXT NOT NULL,
            options_json TEXT,
            answer TEXT NOT NULL,
            explanation TEXT,
            tags TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            user_answer TEXT,
            is_correct INTEGER NOT NULL DEFAULT 0,
            spent_seconds REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );
        
        CREATE TABLE IF NOT EXISTS mistakes (
            user_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            wrong_count INTEGER DEFAULT 1,
            last_wrong_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mastered INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, question_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );
        
        CREATE TABLE IF NOT EXISTS reading_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            module_code TEXT NOT NULL,
            entry_title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS progress (
            user_id INTEGER NOT NULL,
            module_code TEXT NOT NULL,
            questions_done INTEGER DEFAULT 0,
            questions_correct INTEGER DEFAULT 0,
            reading_count INTEGER DEFAULT 0,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, module_code),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_answers_user ON answers(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_answers_question ON answers(question_id);
        CREATE INDEX IF NOT EXISTS idx_mistakes_user ON mistakes(user_id);
        CREATE INDEX IF NOT EXISTS idx_progress_user ON progress(user_id);
    """)
    conn.commit()
    conn.close()

def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((password + salt).encode()).hexdigest()
    return h, salt

def create_user(username: str, password: str, role: str = "newbie", display_name: str = None):
    conn = get_db()
    pw_hash, salt = hash_password(password)
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, role, display_name) VALUES (?,?,?,?,?)",
            (username, pw_hash, salt, role, display_name or username)
        )
        conn.commit()
        return conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def verify_user(username: str, password: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    if not row:
        return None
    pw_hash, _ = hash_password(password, row["salt"])
    if pw_hash == row["password_hash"]:
        # Update last_active
        conn = get_db()
        conn.execute("UPDATE users SET last_active=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
        conn.commit()
        conn.close()
        user = dict(row)
        user.pop("password_hash", None)
        user.pop("salt", None)
        return user
    return None

def get_user(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return None
    user = dict(row)
    user.pop("password_hash", None)
    user.pop("salt", None)
    return user

def seed_default_users():
    """Create default test users if not exist"""
    defaults = [
        ("erwinbo", "erwinbo669570", "pie", "Erwinbo"),
    ]
    for username, password, role, display in defaults:
        conn = get_db()
        exists = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if not exists:
            create_user(username, password, role, display)
