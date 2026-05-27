"""
半导体培训系统 — Streamlit Frontend
Student + Teacher portals
"""
import streamlit as st
import requests, json, time
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

API = "http://127.0.0.1:8001/api"

st.set_page_config(
    page_title="半导体培训系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────── Dark theme CSS ──────
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    .main .block-container { padding-top: 1rem; }
    h1, h2, h3, h4 { color: #c9d1d9 !important; }
    p, li, td, th, span { color: #c9d1d9; }
    .stButton > button { background-color: #238636; color: white; border: 1px solid #30363d; border-radius: 6px; }
    .stButton > button:hover { background-color: #2ea043; }
    .stTextInput > div > div > input { background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d; }
    .stSelectbox > div > div { background-color: #161b22; color: #c9d1d9; }
    div[data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; }
    div[data-testid="stMetric"] label { color: #8b949e !important; }
    div[data-testid="stMetric"] div { color: #58a6ff !important; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 16px; margin: 8px 0; }
    .card h4 { color: #58a6ff; margin: 0 0 8px 0; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .badge-l1 { background: #3fb95033; color: #3fb950; }
    .badge-l2 { background: #d2991d33; color: #d2991d; }
    .badge-l3 { background: #f8514933; color: #f85149; }
    .module-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 14px; margin: 6px 0; cursor: pointer; }
    .module-card:hover { border-color: #58a6ff; }
    .question-box { background: #1c2128; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin: 10px 0; }
    .correct-flash { border-left: 4px solid #3fb950; }
    .wrong-flash { border-left: 4px solid #f85149; }
</style>
""", unsafe_allow_html=True)

# ────── Session State ──────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "quiz" not in st.session_state:
    st.session_state.quiz = []
if "quiz_idx" not in st.session_state:
    st.session_state.quiz_idx = 0
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "quiz_module" not in st.session_state:
    st.session_state.quiz_module = ""
if "answer_result" not in st.session_state:
    st.session_state.answer_result = None  # None | {"is_correct": bool, "correct_answer": str}
if "course_module" not in st.session_state:
    st.session_state.course_module = None  # 当前查看的模块代码

# ────── Module Learning Frameworks ──────
MODULE_FRAMEWORK = {
    "00-fabrication": {
        "objectives": ["理解硅晶体生长(CZ/FZ)与晶圆制备流程","掌握Fab基本术语与洁净室概念","了解CMOS工艺全流程概览","理解半导体产业链分工"],
        "topics": [{"name":"半导体物理基础","subs":["能带理论","掺杂原理","载流子输运"]},{"name":"硅材料与晶圆","subs":["CZ法单晶生长","FZ法","晶圆规格参数","SOI衬底"]},{"name":"CMOS工艺流程","subs":["前段FEOL","后段BEOL","工艺流程概览"]},{"name":"Fab运营基础","subs":["洁净室ISO等级","WIP与Little定律","设备利用率OEE"]}]
    },
    "13-photolithography": {
        "objectives": ["掌握光刻基本原理与衍射极限公式","理解DUV/EUV光刻光源系统差异","了解光刻胶化学与涂布显影工艺","理解OPC/RET分辨率增强技术","掌握关键光刻参数(CD/Overlay/DOF)"],
        "topics": [{"name":"光刻基本原理","subs":["衍射极限 R=k1·λ/NA","曝光系统光学","焦深DOF"]},{"name":"光源系统","subs":["DUV 193nm ArF","EUV 13.5nm","浸没式光刻"]},{"name":"光刻胶","subs":["正胶/负胶","化学放大胶CAR","涂布与软烘","显影工艺"]},{"name":"分辨率增强","subs":["OPC光学邻近修正","相移掩模PSM","离轴照明OAI","多重曝光"]},{"name":"先进光刻","subs":["EUV掩模","High-NA EUV","DSA导向自组装","纳米压印NIL"]}]
    },
    "11-thin-film": {
        "objectives": ["区分PVD/CVD/ALD三种沉积技术原理","掌握溅射与蒸发的基本工艺参数","理解ALD自限制反应机制","了解薄膜应力控制与附着力"],
        "topics": [{"name":"PVD物理气相沉积","subs":["磁控溅射","电子束蒸发","离子束沉积","台阶覆盖率"]},{"name":"CVD化学气相沉积","subs":["LPCVD","PECVD","MOCVD","前驱体化学"]},{"name":"ALD原子层沉积","subs":["自限制反应","TMA/H2O Al2O3","PEALD","前驱体选择"]},{"name":"薄膜表征","subs":["椭偏仪测厚","XRR","应力测量","附着力测试"]}]
    },
    "14-dry-etch": {
        "objectives": ["理解等离子体刻蚀基本原理","区分各向同性/各向异性刻蚀","掌握RIE/ICP/DRIE工艺特点","了解刻蚀选择比与终点检测"],
        "topics": [{"name":"等离子体基础","subs":["DC/RF辉光放电","离子轰击效应","电子温度与离子能量"]},{"name":"RIE反应离子刻蚀","subs":["CCP电容耦合","RIE滞后效应","侧壁钝化"]},{"name":"ICP deep etch","subs":["Bosch工艺","深硅刻蚀","ARDE宽高比相关刻蚀"]},{"name":"刻蚀表征","subs":["刻蚀速率","选择比","均匀性","终点检测OES"]}]
    },
    "15-metrology": {
        "objectives": ["掌握半导体量测基本方法","理解CD-SEM与光学CD测量原理","了解薄膜厚度测量技术","了解缺陷检测与分类"],
        "topics": [{"name":"CD量测","subs":["CD-SEM","光学CD OCD","散射测量"]},{"name":"薄膜量测","subs":["椭偏仪","反射仪","XRR"]},{"name":"Overlay测量","subs":["IBO成像法","DBO衍射法"]},{"name":"缺陷检测","subs":["明场/暗场检测","电子束检测","缺陷分类ADC"]}]
    },
    "16-CMP": {
        "objectives": ["理解CMP基本原理与Preston方程","掌握CMP工艺参数(压力/转速/浆料)","了解CMP后清洗与缺陷控制","了解STI/铜互联CMP特点"],
        "topics": [{"name":"CMP机理","subs":["Preston方程","机械与化学协同","材料去除率"]},{"name":"工艺参数","subs":["下压力","转速","浆料化学","抛光垫"]},{"name":"CMP应用","subs":["STI CMP","W CMP","Cu CMP","ILD CMP"]},{"name":"CMP缺陷","subs":["划痕Scratch","碟形Dishing","腐蚀Erosion","后清洗"]}]
    },
}

def api(path, method="GET", data=None):
    url = f"{API}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=10)
        elif method == "POST":
            r = requests.post(url, json=data, timeout=10)
        return r.json() if r.ok else None
    except:
        return None

def _interp(xs, ys, x):
    if not xs:
        return None
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            if x1 == x0:
                return y0
            t = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return ys[-1]

def _nk_data():
    return {
        "Si": [(200, 0.92, 2.90), (400, 5.57, 0.38), (632.8, 3.88, 0.02), (1000, 3.55, 0.00)],
        "SiO2": [(200, 1.55, 0.00), (400, 1.47, 0.00), (632.8, 1.46, 0.00), (1000, 1.45, 0.00)],
        "Si3N4": [(200, 2.05, 0.02), (400, 2.02, 0.00), (632.8, 2.00, 0.00), (1000, 1.98, 0.00)],
        "TiN": [(200, 2.20, 2.80), (400, 2.00, 3.50), (632.8, 1.80, 3.20), (1000, 2.00, 4.00)],
        "Cu": [(200, 0.95, 2.70), (400, 0.65, 2.60), (632.8, 0.28, 3.40), (1000, 0.32, 6.50)],
        "Al": [(200, 0.55, 4.90), (400, 0.95, 6.30), (632.8, 1.44, 7.30), (1000, 1.55, 10.0)],
        "photoresist": [(200, 1.70, 0.20), (365, 1.69, 0.04), (405, 1.68, 0.02), (633, 1.65, 0.00), (1000, 1.62, 0.00)],
    }

def _rho_irvin(conc_cm3: float, dop_type: str):
    n_table = [
        (14.0, 45.0),
        (15.0, 9.0),
        (16.0, 1.2),
        (17.0, 0.18),
        (18.0, 0.028),
        (19.0, 0.008),
        (20.0, 0.003),
    ]
    p_table = [
        (14.0, 110.0),
        (15.0, 22.0),
        (16.0, 3.0),
        (17.0, 0.45),
        (18.0, 0.07),
        (19.0, 0.02),
        (20.0, 0.008),
    ]
    if conc_cm3 <= 0:
        return None
    logn = math.log10(conc_cm3)
    table = n_table if dop_type == "N" else p_table
    xs = [x for x, _ in table]
    ys = [math.log10(y) for _, y in table]
    logrho = _interp(xs, ys, logn)
    return 10 ** logrho if logrho is not None else None

def viz_lithography():
    st.subheader("模块1：光刻衍射极限模拟器")
    c1, c2, c3 = st.columns(3)
    with c1:
        na = st.slider("NA", 0.30, 1.40, 1.35, 0.01)
    with c2:
        lam = st.selectbox("波长 λ (nm)", [13.5, 193.0, 248.0, 365.0], index=1)
    with c3:
        k1 = st.slider("k1 因子", 0.25, 0.80, 0.35, 0.01)

    r_nm = k1 * float(lam) / na
    st.metric("最小半周期分辨率 R", f"{r_nm:.2f} nm", help="R = k1 * λ / NA")

    na_grid = [0.30 + i * (1.40 - 0.30) / 110 for i in range(111)]
    lam_grid = [13.5, 193.0, 248.0, 365.0]
    z = []
    for l in lam_grid:
        row = []
        for n in na_grid:
            row.append(k1 * l / n)
        z.append(row)

    fig, ax = plt.subplots(figsize=(8, 3.6))
    im = ax.imshow(z, aspect="auto", origin="lower", extent=[min(na_grid), max(na_grid), 0, len(lam_grid) - 1])
    ax.set_xlabel("NA")
    ax.set_ylabel("λ")
    ax.set_yticks(list(range(len(lam_grid))))
    ax.set_yticklabels([f"{l:g}nm" for l in lam_grid])
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("R (nm)")

    nodes = [
        ("28nm", 193.0, 1.35, 0.20),
        ("14nm", 193.0, 1.35, 0.10),
        ("7nm", 13.5, 0.33, 0.17),
        ("3nm", 13.5, 0.55, 0.12),
    ]
    lam_to_y = {13.5: 0, 193.0: 1, 248.0: 2, 365.0: 3}
    for label, l, n, k in nodes:
        y = lam_to_y.get(float(l))
        if y is None:
            continue
        ax.scatter([n], [y], s=36, edgecolor="white", facecolor="none")
        ax.text(n + 0.02, y + 0.05, label, fontsize=9)

    st.pyplot(fig, clear_figure=True)

def viz_cmp():
    st.subheader("模块2：CMP Preston 方程计算器")
    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.slider("压力 P (psi)", 0.5, 8.0, 3.0, 0.1)
    with c2:
        v = st.slider("相对速度 V (m/s)", 0.1, 2.0, 0.8, 0.05)
    with c3:
        kp = st.slider("Preston 系数 Kp", 1e-7, 5e-5, 8e-6, format="%.1e")

    rr = kp * p * v
    st.metric("移除速率 RR", f"{rr:.3e} (相对单位)", help="RR = Kp * P * V")

    a = 0.35
    densities = [i / 100 for i in range(101)]
    rr_local = [rr * (1.0 - a * (d - 0.5)) for d in densities]

    fig, ax = plt.subplots(figsize=(7.5, 3.0))
    ax.plot(densities, rr_local, linewidth=2)
    ax.set_xlabel("图案密度 (0~1)")
    ax.set_ylabel("局部 RR")
    ax.grid(True, alpha=0.25)
    st.pyplot(fig, clear_figure=True)

def viz_nk():
    st.subheader("模块3：薄膜光学常数 (n, k) 浏览器")
    data = _nk_data()
    material = st.selectbox("材料", list(data.keys()))
    lam_min, lam_max = st.slider("波长范围 (nm)", 200, 1000, (300, 900), 10)
    lam_pick = st.slider("选定波长 (nm)", lam_min, lam_max, int((lam_min + lam_max) / 2), 5)

    pts = sorted(data[material], key=lambda x: x[0])
    xs = [p[0] for p in pts]
    ns = [p[1] for p in pts]
    ks = [p[2] for p in pts]

    xs_plot = [x for x in range(lam_min, lam_max + 1, 5)]
    n_plot = [_interp(xs, ns, x) for x in xs_plot]
    k_plot = [_interp(xs, ks, x) for x in xs_plot]

    n0 = _interp(xs, ns, lam_pick)
    k0 = _interp(xs, ks, lam_pick)
    if n0 is not None and k0 is not None:
        r = ((n0 - 1) ** 2 + k0 ** 2) / ((n0 + 1) ** 2 + k0 ** 2)
        c1, c2, c3 = st.columns(3)
        c1.metric("n(λ)", f"{n0:.3f}")
        c2.metric("k(λ)", f"{k0:.3f}")
        c3.metric("反射率 R", f"{r*100:.2f}%")

    fig, ax1 = plt.subplots(figsize=(7.5, 3.2))
    ax2 = ax1.twinx()
    ax1.plot(xs_plot, n_plot, color="#58a6ff", linewidth=2, label="n")
    ax2.plot(xs_plot, k_plot, color="#f85149", linewidth=2, label="k")
    ax1.set_xlabel("λ (nm)")
    ax1.set_ylabel("n")
    ax2.set_ylabel("k")
    ax1.grid(True, alpha=0.25)
    st.pyplot(fig, clear_figure=True)

def viz_doping():
    st.subheader("模块4：掺杂浓度-电阻率换算器")
    dop = st.selectbox("掺杂类型", ["N型 (P/As/Sb)", "P型 (B)"])
    dop_type = "N" if dop.startswith("N") else "P"
    logn = st.slider("掺杂浓度 log10(N/cm³)", 14.0, 20.0, 17.0, 0.1)
    conc = 10 ** logn
    t_um = st.slider("结深 t (μm)", 0.05, 2.0, 0.30, 0.01)

    rho = _rho_irvin(conc, dop_type)
    if rho is None:
        st.warning("无法计算")
        return

    rs = rho / (t_um * 1e-4)
    c1, c2, c3 = st.columns(3)
    c1.metric("ρ (Ω·cm)", f"{rho:.4g}")
    c2.metric("R_sheet (Ω/□)", f"{rs:.4g}")
    c3.metric("N (cm⁻³)", f"{conc:.2e}")

    xs = [14.0 + i * 0.05 for i in range(int((20.0 - 14.0) / 0.05) + 1)]
    ys = [_rho_irvin(10 ** x, dop_type) for x in xs]

    fig, ax = plt.subplots(figsize=(7.5, 3.0))
    ax.plot(xs, ys, linewidth=2)
    ax.set_yscale("log")
    ax.set_xlabel("log10(N/cm³)")
    ax.set_ylabel("ρ (Ω·cm)")
    ax.grid(True, which="both", alpha=0.25)
    ax.scatter([logn], [rho])
    st.pyplot(fig, clear_figure=True)

def viz_rc():
    st.subheader("模块5：互连 RC 延迟模型")
    c1, c2, c3 = st.columns(3)
    with c1:
        w_nm = st.number_input("线宽 W (nm)", min_value=5.0, max_value=200.0, value=28.0, step=1.0)
        s_nm = st.number_input("线间距 S (nm)", min_value=5.0, max_value=300.0, value=28.0, step=1.0)
    with c2:
        h_nm = st.number_input("线高 H (nm)", min_value=10.0, max_value=400.0, value=60.0, step=5.0)
        k = st.number_input("介电常数 k", min_value=1.5, max_value=4.2, value=2.7, step=0.1)
    with c3:
        rho_uohm_cm = st.number_input("金属电阻率 ρ (μΩ·cm)", min_value=1.0, max_value=10.0, value=2.0, step=0.1)
        length_um = st.number_input("互连长度 L (μm)", min_value=10.0, max_value=20000.0, value=1000.0, step=50.0)

    w_m = w_nm * 1e-9
    h_m = h_nm * 1e-9
    s_m = s_nm * 1e-9
    l_m = length_um * 1e-6
    rho = rho_uohm_cm * 1e-8

    a = max(1e-18, w_m * h_m)
    r_per_m = rho / a

    eps0 = 8.854e-12
    c_per_m = eps0 * k * (h_m / max(1e-18, s_m))

    r = r_per_m * l_m
    c = c_per_m * l_m
    rc = r * c

    c1, c2, c3 = st.columns(3)
    c1.metric("R (Ω)", f"{r:.3g}")
    c2.metric("C (F)", f"{c:.3g}")
    c3.metric("RC 延迟 (s)", f"{rc:.3g}")

    cases = [
        ("Cu / low-k", 1.7e-8, 2.5),
        ("Al / SiO2", 2.65e-8, 3.9),
    ]
    vals = []
    for name, rho_case, k_case in cases:
        r_case = (rho_case / a) * l_m
        c_case = (eps0 * k_case * (h_m / max(1e-18, s_m))) * l_m
        vals.append((name, r_case * c_case))

    fig, ax = plt.subplots(figsize=(6.8, 3.0))
    ax.bar([v[0] for v in vals], [v[1] for v in vals], color=["#58a6ff", "#d2991d"])
    ax.set_ylabel("RC (s)")
    ax.grid(True, axis="y", alpha=0.25)
    st.pyplot(fig, clear_figure=True)

# ────── Auth ──────
def login_page():
    st.title("📚 半导体培训系统")
    
    # ── Intro Dashboard for visitors ──
    with st.expander("📋 系统介绍 — 面向学校/培训教师", expanded=False):
        col_a, col_b, col_c, col_d, col_e = st.columns(5)
        with col_a: st.metric("知识模块", "27")
        with col_b: st.metric("题库总量", "541")
        with col_c: st.metric("行业文献", "834")
        with col_d: st.metric("工种路径", "6")
        with col_e: st.metric("可视化实验", "5")
        
        st.markdown("""
        ### 平台定位
        
        基于本地 **834 篇半导体行业文献** 的知识引擎，融合 AI 驱动的自适应学习、互动物理可视化与多维数据分析，为半导体工程师打造从入门到精通的系统化培训平台。
        
        ### 核心特色
        
        | 特色 | 说明 |
        |------|------|
        | 📖 **工种定制路径** | 6 大工种（PIE·单点工艺·设备·品质·研发·入门），必修+选修双轨 |
        | ✏️ **自适应练习** | 541 题 L1→L3 逐级递进，即时反馈 + 错题自动收集 |
        | 📐 **可视化实验室** | 5 个交互物理模拟器：光刻衍射·CMP·薄膜 n/k·掺杂换算·RC 延迟 |
        | 📈 **进度追踪** | 个人 Dashboard：答题数·正确率·模块完成度·难度分析 |
        | 📕 **智能错题本** | 自动归集错误次数，一键重练，按模块过滤 |
        | 🎯 **每日推荐** | AI 基于历史薄弱点动态生成个性化练习 |
        """)
    
    st.divider()
    st.subheader("🔐 登录")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("登录")
        username = st.text_input("用户名", key="login_user")
        password = st.text_input("密码", type="password", key="login_pass")
        if st.button("登录", use_container_width=True):
            result = api("/auth/login", "POST", {"username": username, "password": password})
            if result:
                st.session_state.user = result
                st.rerun()
            else:
                st.error("用户名或密码错误")
    
    with col2:
        st.subheader("注册")
        new_user = st.text_input("用户名", key="reg_user")
        new_pass = st.text_input("密码", type="password", key="reg_pass")
        new_name = st.text_input("显示名称", key="reg_name")
        new_role = st.selectbox("工种", ["newbie", "pie", "process", "equipment", "quality", "rd"],
                                format_func=lambda x: {"newbie":"通用入门","pie":"工艺集成","process":"单点工艺","equipment":"设备维护","quality":"品质管理","rd":"研发设计"}.get(x,x))
        if st.button("注册", use_container_width=True):
            result = api("/auth/register", "POST", {"username": new_user, "password": new_pass, "role": new_role, "display_name": new_name})
            if result:
                st.success(f"注册成功！用户ID: {result['user_id']}")
            else:
                st.error("注册失败，用户名可能已存在")

# ────── Sidebar ──────
def sidebar():
    with st.sidebar:
        st.markdown(f"### 📚 半导体培训")
        if st.session_state.user:
            st.markdown(f"👤 **{st.session_state.user['display_name']}**")
            role_map = {"pie":"PIE","process":"单点工艺","equipment":"设备","quality":"品质","rd":"研发","newbie":"入门"}
            st.caption(f"工种: {role_map.get(st.session_state.user['role'], '未知')}")
            st.divider()
            
            # 在模块详情页时只显示返回按钮
            if st.session_state.page == "module_detail":
                if st.button("← 返回课程中心", use_container_width=True):
                    st.session_state.course_module = None
                    st.session_state.page = "courses"
                    st.rerun()
            else:
                if st.button("🏠 首页", use_container_width=True):
                    st.session_state.page = "home"; st.rerun()
                if st.button("📖 课程中心", use_container_width=True):
                    st.session_state.page = "courses"; st.rerun()
                if st.button("✏️ 练习答题", use_container_width=True):
                    st.session_state.page = "quiz_select"; st.rerun()
                if st.button("📈 我的进度", use_container_width=True):
                    st.session_state.page = "progress"; st.rerun()
                if st.button("📕 错题本", use_container_width=True):
                    st.session_state.page = "mistakes"; st.rerun()
                if st.button("📊 我的成绩", use_container_width=True):
                    st.session_state.page = "stats"; st.rerun()
                if st.button("🔍 知识搜索", use_container_width=True):
                    st.session_state.page = "search"; st.rerun()
            st.divider()
            if st.button("🚪 退出", use_container_width=True):
                st.session_state.user = None; st.rerun()

# ────── Home ──────
def home_page():
    st.title(f"👋 欢迎, {st.session_state.user['display_name']}")
    stats = api(f"/quiz/stats/{st.session_state.user['user_id']}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("答题总数", stats.get("total_questions", 0) if stats else 0)
    with col2:
        st.metric("正确率", f"{stats.get('accuracy', 0)}%")
    with col3:
        st.metric("待复习错题", stats.get("pending_mistakes", 0) if stats else 0)
    with col4:
        modules_data = api(f"/knowledge/role/{st.session_state.user['role']}")
        mod_count = len(modules_data["required"]) + len(modules_data["elective"]) if modules_data else 0
        st.metric("学习模块", mod_count)
    
    st.divider()
    st.subheader("⚡ 快速入口")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("📖 进入课程中心", use_container_width=True):
            st.session_state.page = "courses"; st.rerun()
    with c2:
        if st.button("✏️ 开始答题练习", use_container_width=True):
            st.session_state.page = "quiz_select"; st.rerun()
    with c3:
        if st.button("📊 查看成绩报告", use_container_width=True):
            st.session_state.page = "stats"; st.rerun()
    with c4:
        if st.button("🎯 每日推荐", use_container_width=True):
            rec = api(f"/quiz/daily-recommendation/{st.session_state.user['user_id']}?count=10")
            if rec and rec.get("questions"):
                st.session_state.quiz = rec["questions"]
                st.session_state.quiz_idx = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_module = "daily"
                st.session_state.page = "quiz_active"
                st.rerun()
            else:
                st.warning("暂无可推荐题目")
    
    # Top mistakes
    if stats and stats.get("top_mistakes"):
        st.divider()
        st.subheader("🔴 待复习错题 TOP 5")
        for m in stats["top_mistakes"][:5]:
            st.markdown(f"• **{m['module']}** — {m['question'][:60]}... (错{m['wrong_count']}次)")

# ────── Courses ──────
def courses_page():
    st.title("📖 课程中心")
    modules_data = api(f"/knowledge/role/{st.session_state.user['role']}")
    if not modules_data:
        st.warning("无法加载课程数据")
        return
    
    tab1, tab2 = st.tabs(["🔴 必修模块", "🟡 选修模块"])
    
    with tab1:
        for m in modules_data["required"]:
            level_badge = {100: "badge-l1", 200: "badge-l2", 300: "badge-l3", 400: "badge-l3"}
            badge_cls = level_badge.get(m["level"], "badge-l2")
            with st.container():
                st.markdown(f"""
                <div class="module-card">
                    <h4>{m['name']} <span class="badge {badge_cls}">L{m['level']//100}</span></h4>
                    <p style="color:#8b949e;font-size:14px;">{m['desc']}</p>
                    <p style="font-size:12px;color:#8b949e;">📄 {m['total_pdfs']} 篇文献 · 📝 {len(m.get('notes',[]))} 篇笔记</p>
                </div>
                """, unsafe_allow_html=True)
                col1, col2, col3 = st.columns([5, 2, 2])
                with col2:
                    if st.button("📖 进入模块", key=f"enter_{m.get('code','')}", use_container_width=True):
                        st.session_state.course_module = m.get("code", "")
                        st.session_state.page = "module_detail"
                        st.rerun()
                with col3:
                    if m.get("notes"):
                        for note in m["notes"][:1]:
                            if st.button("阅读", key=f"read_{m.get('code','')}_{note['name'][:10]}", use_container_width=True):
                                log_reading(st.session_state.user['user_id'], m.get('code', ''), note['name'])
                                st.toast("已记录阅读")
    
    with tab2:
        for m in modules_data["elective"]:
            level_badge = {100: "badge-l1", 200: "badge-l2", 300: "badge-l3", 400: "badge-l3"}
            badge_cls = level_badge.get(m["level"], "badge-l2")
            st.markdown(f"""
            <div class="module-card" style="opacity:0.85;">
                <h4>{m['name']} <span class="badge {badge_cls}">L{m['level']//100}</span></h4>
                <p style="color:#8b949e;font-size:14px;">{m['desc']}</p>
                <p style="font-size:12px;color:#8b949e;">📄 {m['total_pdfs']} 篇文献</p>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([6, 3])
            with col2:
                if st.button("📖 进入模块", key=f"enter_e_{m.get('code','')}", use_container_width=True):
                    st.session_state.course_module = m.get("code", "")
                    st.session_state.page = "module_detail"
                    st.rerun()

def log_reading(user_id, module_code, title):
    api("/reading/log", "POST", {"user_id": user_id, "module_code": module_code, "entry_title": title})

def module_detail_page():
    from app.config import MODULE_META
    module_code = st.session_state.course_module
    if not module_code:
        st.session_state.page = "courses"
        st.rerun()
    
    meta = MODULE_META.get(module_code, {"name": module_code, "desc": "", "level": 200})
    framework = MODULE_FRAMEWORK.get(module_code, {
        "objectives": ["掌握本模块核心知识", "理解关键概念与应用", "能够独立分析相关问题"],
        "topics": [{"name": "核心内容", "subs": ["待细化"]}]
    })
    
    # 返回按钮
    if st.button("← 返回课程中心", use_container_width=True):
        st.session_state.course_module = None
        st.session_state.page = "courses"
        st.rerun()
    
    st.title(f"📖 {meta['name']}")
    level_badge = {100: "🟢 L1 基础", 200: "🟡 L2 应用", 300: "🟠 L3 深入", 400: "🔴 L4 专家"}
    st.caption(f"{level_badge.get(meta['level'], 'L2')} | {meta['desc']}")
    
    # 学习目标
    st.subheader("🎯 学习目标")
    objectives = framework.get("objectives", ["掌握本模块核心知识"])
    for i, obj in enumerate(objectives, 1):
        st.markdown(f"{i}. {obj}")
    
    st.divider()
    
    # 核心知识点
    st.subheader("📚 知识框架")
    topics = framework.get("topics", [])
    for topic in topics:
        with st.expander(f"📂 {topic['name']}", expanded=False):
            for sub in topic.get("subs", []):
                st.markdown(f"• {sub}  `📝 详细内容开发中`")
    
    st.divider()
    
    # 相关资源
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 文献资源")
        index = api("/knowledge/index")
        if index and module_code in index:
            mod_data = index[module_code]
            for pdf in mod_data.get("pdfs", [])[:10]:
                st.caption(f"📄 {pdf['name'][:70]}")
            if len(mod_data.get("pdfs", [])) > 10:
                st.caption(f"... 共 {len(mod_data['pdfs'])} 篇")
    with col2:
        st.subheader("✏️ 相关练习")
        if st.button("🚀 开始练习", key=f"quiz_{module_code}", use_container_width=True):
            quiz = api("/quiz/generate", "POST", {
                "user_id": st.session_state.user["user_id"],
                "module_code": module_code,
                "count": 10,
                "difficulty": None
            })
            if quiz and quiz.get("questions"):
                st.session_state.quiz = quiz["questions"]
                st.session_state.quiz_idx = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_module = module_code
                st.session_state.answer_result = None
                st.session_state.page = "quiz_active"
                st.rerun()

# ────── Quiz ──────
def quiz_select_page():
    st.title("✏️ 练习答题")
    modules_data = api(f"/knowledge/role/{st.session_state.user['role']}")
    if not modules_data:
        st.warning("无法加载模块")
        return
    
    all_mods = modules_data["required"] + modules_data["elective"]
    mod_names = [f"{m['name']}" for m in all_mods]
    
    col1, col2 = st.columns(2)
    with col1:
        selected_name = st.selectbox("选择模块", mod_names)
        question_count = st.slider("题目数量", 5, 30, 10, 5)
    with col2:
        difficulty = st.selectbox("难度", ["全部", "L1 基础", "L2 应用", "L3 深入"])
        mistake_only = st.checkbox("只练错题")
    
    # Find module code
    selected_mod = None
    for m in all_mods:
        if m["name"] == selected_name:
            selected_mod = m
            break
    
    if selected_mod and st.button("🚀 开始答题", use_container_width=True, type="primary"):
        # Find the module code (reverse lookup from MODULE_META)
        from app.config import MODULE_META
        mod_code = None
        for code, meta in MODULE_META.items():
            if meta["name"] == selected_name:
                mod_code = code
                break
        if not mod_code:
            mod_code = selected_name
        
        diff_param = None
        if difficulty != "全部":
            diff_param = difficulty[:2]

        if mistake_only:
            quiz = api("/quiz/retry-mistakes", "POST", {
                "user_id": st.session_state.user["user_id"],
                "module_code": mod_code,
                "count": question_count,
                "difficulty": diff_param
            })
        else:
            quiz = api("/quiz/generate", "POST", {
                "user_id": st.session_state.user["user_id"],
                "module_code": mod_code,
                "count": question_count,
                "difficulty": diff_param
            })
        
        if quiz and quiz.get("questions"):
            st.session_state.quiz = quiz["questions"]
            st.session_state.quiz_idx = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_module = mod_code
            st.session_state.page = "quiz_active"
            st.rerun()
        else:
            st.error("暂无可用题目（可能该模块暂无题库，或错题已清空）")

def progress_page():
    st.title("📈 我的进度")
    summary = api(f"/progress/summary/{st.session_state.user['user_id']}")
    modules_data = api(f"/knowledge/role/{st.session_state.user['role']}")
    if not summary or not modules_data:
        st.warning("无法加载进度数据")
        return

    wanted = {m.get("code") for m in (modules_data.get("required", []) + modules_data.get("elective", []))}
    rows = [m for m in summary.get("modules", []) if m.get("module_code") in wanted]
    required_codes = [m.get("code") for m in modules_data.get("required", [])]
    elective_codes = [m.get("code") for m in modules_data.get("elective", [])]

    tab1, tab2 = st.tabs(["🔴 必修模块", "🟡 选修模块"])
    with tab1:
        for code in required_codes:
            r = next((x for x in rows if x.get("module_code") == code), None)
            if not r:
                continue
            st.markdown(f"**{r['name']}**")
            st.progress(min(1.0, (r.get('completion_pct', 0.0) or 0.0) / 100.0))
            st.caption(f"完成 {r.get('questions_done', 0)}/{r.get('total_questions', 0)} · 正确率 {r.get('accuracy', 0)}% · 阅读 {r.get('reading_count', 0)} 次")
    with tab2:
        for code in elective_codes:
            r = next((x for x in rows if x.get("module_code") == code), None)
            if not r:
                continue
            st.markdown(f"**{r['name']}**")
            st.progress(min(1.0, (r.get('completion_pct', 0.0) or 0.0) / 100.0))
            st.caption(f"完成 {r.get('questions_done', 0)}/{r.get('total_questions', 0)} · 正确率 {r.get('accuracy', 0)}% · 阅读 {r.get('reading_count', 0)} 次")

def mistakes_page():
    st.title("📕 错题本")
    stats = api(f"/quiz/stats/{st.session_state.user['user_id']}")
    pending = stats.get("pending_mistakes", 0) if stats else 0
    st.metric("待复习错题", pending)

    col1, col2 = st.columns([2, 1])
    with col1:
        count = st.slider("抽取数量", 5, 50, 20, 5)
    with col2:
        if st.button("🔄 开始重练", use_container_width=True, type="primary"):
            quiz = api("/quiz/retry-mistakes", "POST", {
                "user_id": st.session_state.user["user_id"],
                "module_code": "",
                "count": count,
                "difficulty": None
            })
            if quiz and quiz.get("questions"):
                st.session_state.quiz = quiz["questions"]
                st.session_state.quiz_idx = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_module = "mistakes"
                st.session_state.page = "quiz_active"
                st.rerun()
            else:
                st.info("暂无需要重练的错题")

def quiz_active_page():
    st.title("✏️ 答题中")
    if not st.session_state.quiz or st.session_state.quiz_idx >= len(st.session_state.quiz):
        st.session_state.answer_result = None  # 重置状态
        st.session_state.page = "quiz_result"
        st.rerun()
    
    q = st.session_state.quiz[st.session_state.quiz_idx]
    progress = f"{st.session_state.quiz_idx + 1}/{len(st.session_state.quiz)}"
    st.progress(st.session_state.quiz_idx / len(st.session_state.quiz))
    st.caption(f"📝 {progress} · 模块: {st.session_state.quiz_module}")
    
    diff_map = {"L1": "🟢 基础", "L2": "🟡 应用", "L3": "🔴 深入"}
    diff_label = diff_map.get(q.get("difficulty", "L2"), q.get("difficulty", ""))
    
    st.markdown(f"""
    <div class="question-box">
        <span style="color:#8b949e;font-size:12px;">{diff_label}</span>
        <h3 style="margin:10px 0;">{q['question']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # ── 模式 1: 未提交答案 → 显示题目 + 提交按钮 ──
    if st.session_state.answer_result is None:
        answer = None
        if q.get("qtype") == "judge":
            answer = st.radio("选择答案", ["正确", "错误"], key=f"q_{st.session_state.quiz_idx}", index=None)
        else:
            opts = q.get("options", [])
            if opts:
                answer = st.radio("选择答案", opts, key=f"q_{st.session_state.quiz_idx}", index=None)
        
        if st.button("✅ 提交答案", use_container_width=True) and answer:
            result = api("/quiz/submit", "POST", {
                "user_id": st.session_state.user["user_id"],
                "question_id": q["id"],
                "user_answer": answer[0] if answer[0] in "ABCDEFG" else ("正确" if answer == "正确" else "错误"),
            })
            if result:
                if result["is_correct"]:
                    st.session_state.quiz_score += 1
                st.session_state.answer_result = result
                st.rerun()
    
    # ── 模式 2: 已提交答案 → 显示结果 + 下一题按钮 ──
    else:
        result = st.session_state.answer_result
        # 重新显示题目和选项（disabled）
        if q.get("qtype") == "judge":
            st.radio("选择答案", ["正确", "错误"], key=f"q_{st.session_state.quiz_idx}",
                     index=0 if result.get("correct_answer") == "正确" else 1, disabled=True)
        else:
            opts = q.get("options", [])
            if opts:
                # 找到正确答案的索引
                correct_letter = result.get("correct_answer", "A")
                idx = ord(correct_letter) - ord("A") if correct_letter in "ABCDEFG" else 0
                idx = max(0, min(idx, len(opts)-1))
                st.radio("选择答案", opts, key=f"q_{st.session_state.quiz_idx}", index=idx, disabled=True)
        
        if result["is_correct"]:
            st.success("✅ 正确！")
        else:
            st.error(f"❌ 错误！正确答案是: {result['correct_answer']}")
            if result.get("explanation"):
                st.info(f"💡 {result['explanation']}")
        
        # ★ 关键修复：下一题按钮独立渲染，不嵌套在任何条件内
        if st.button("下一题 ➡️", use_container_width=True):
            st.session_state.quiz_idx += 1
            st.session_state.answer_result = None  # 重置为未提交状态
            st.rerun()

def quiz_result_page():
    st.title("📊 答题结果")
    total = len(st.session_state.quiz) if st.session_state.quiz else st.session_state.quiz_idx
    score = st.session_state.quiz_score
    accuracy = round(score / total * 100, 1) if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总分", f"{score}/{total}")
    with col2:
        st.metric("正确率", f"{accuracy}%")
    with col3:
        st.metric("模块", st.session_state.quiz_module)
    
    if accuracy >= 80:
        st.success("🎉 表现优秀！继续保持！")
    elif accuracy >= 60:
        st.info("👍 不错，还有提升空间")
    else:
        st.warning("📚 需要加强学习，建议复习课程内容")
    
    if st.button("🔄 再来一轮", use_container_width=True):
        st.session_state.page = "quiz_select"
        st.rerun()

# ────── Stats ──────
def stats_page():
    st.title("📊 我的成绩")
    stats = api(f"/quiz/stats/{st.session_state.user['user_id']}")
    if not stats:
        st.warning("暂无数据")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总答题数", stats["total_questions"])
    with col2:
        st.metric("总正确率", f"{stats['accuracy']}%")
    with col3:
        st.metric("待复习错题", stats["pending_mistakes"])
    
    # Module breakdown
    st.divider()
    st.subheader("📊 各模块正确率")
    if stats.get("modules"):
        for mc, ms in stats["modules"].items():
            acc = ms["accuracy"]
            bar = "█" * int(acc/5) + "░" * (20 - int(acc/5))
            st.markdown(f"**{ms['name']}** ({ms['total']}题)")
            st.markdown(f"`{bar}` {acc}%")
    
    # Difficulty breakdown
    st.divider()
    st.subheader("📈 难度分析")
    if stats.get("by_difficulty"):
        for diff, ds in stats["by_difficulty"].items():
            st.markdown(f"**{ds['name']}** — {ds['total']}题 — 正确率 {ds['accuracy']}%")

# ────── Teacher ──────
def teacher_page():
    st.title("👥 教师后台")
    st.info("🏗️ 教师管理功能将在 Phase 3 实现")
    
    # Module stats overview
    index = api("/knowledge/index")
    if index:
        st.subheader("📊 知识库模块统计")
        for code, mod in sorted(index.items()):
            if mod.get("total_pdfs", 0) > 0:
                st.markdown(f"• **{mod['name']}** — {mod['total_pdfs']} 篇文献")

# ────── Search ──────
def search_page():
    st.title("🔍 知识搜索")
    query = st.text_input("搜索关键词", placeholder="如: EUV 光刻, ALD, 刻蚀...")
    if query:
        index = api("/knowledge/index")
        if index:
            results = []
            for code, mod in index.items():
                if query.lower() in mod["name"].lower() or query.lower() in mod["desc"].lower():
                    results.append((mod, code))
                # Search in PDF names
                for pdf in mod.get("pdfs", []):
                    if query.lower() in pdf["name"].lower():
                        results.append((mod, code))
                        break
            
            if results:
                st.success(f"找到 {len(results)} 个相关模块")
                for mod, code in results:
                    with st.expander(f"📂 {mod['name']} ({mod['total_pdfs']} 篇文献)"):
                        st.write(mod["desc"])
                        for pdf in mod.get("pdfs", [])[:5]:
                            st.caption(f"📄 {pdf['name'][:80]}")
            else:
                st.info("未找到相关结果")

def viz_lab_page():
    st.title("📐 可视化实验室")
    with st.expander("模块1：光刻衍射极限模拟器", expanded=True):
        viz_lithography()
    with st.expander("模块2：CMP Preston 方程计算器", expanded=False):
        viz_cmp()
    with st.expander("模块3：薄膜光学常数 (n, k) 浏览器", expanded=False):
        viz_nk()
    with st.expander("模块4：掺杂浓度-电阻率换算器", expanded=False):
        viz_doping()
    with st.expander("模块5：互连 RC 延迟模型", expanded=False):
        viz_rc()

def intro_page():
    """Landing intro page with Streamlit-native rendering."""
    # Hero
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 style='text-align:center;font-size:2.4em;color:#fff;'>📚 半导体培训系统</h1>", unsafe_allow_html=True)
        st.markdown("""
        <p style='text-align:center;font-size:1.15em;color:#8b949e;max-width:600px;margin:0 auto 24px;'>
        基于本地 834 篇行业文献的知识引擎，融合 AI 驱动的自适应学习、互动物理可视化与多维数据分析，
        为半导体工程师打造从入门到精通的系统化培训平台。
        </p>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            if st.button("🚀 进入培训系统", type="primary", use_container_width=True):
                st.session_state.show_login = True
                st.rerun()

    st.markdown("---")

    # Stats
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("知识模块", "27")
    with c2:
        st.metric("题库总量", "541")
    with c3:
        st.metric("行业文献", "834")
    with c4:
        st.metric("工种路径", "6")
    with c5:
        st.metric("可视化实验室", "5")

    # Difficulty
    st.markdown("### 📊 题库难度分布")
    c1, c2, c3 = st.columns([11, 31, 58])
    with c1:
        st.markdown("<div style='background:#3fb950;height:8px;border-radius:4px 0 0 4px;'></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='background:#d2991d;height:8px;'></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='background:#f85149;height:8px;border-radius:0 4px 4px 0;'></div>", unsafe_allow_html=True)
    st.caption("🟢 L1 基础 59 题 (11%) 🟡 L2 应用 169 题 (31%) 🔴 L3 深入 313 题 (58%)")

    st.markdown("---")

    # Features
    st.markdown("### ⚡ 核心功能")
    cols = st.columns(3)
    features = [
        ("📖 课程中心", "基于 6 大工种定制学习路径，必修/选修模块自动匹配文献库。", "必修模块 · 选修模块 · 文献阅读"),
        ("✏️ 自适应练习", "541 道原创题，按模块/难度筛选，L1→L3 递进，自动记录错题。", "按模块筛选 · L1-L3 · 错题收集"),
        ("📈 进度追踪", "个人 Dashboard：答题数、正确率、模块完成度、难度分布分析。", "个人统计 · 模块完成度 · 难度分析"),
        ("📕 智能错题本", "自动归集错题，标注错误次数与所属模块，一键重练薄弱点。", "按模块过滤 · 错误统计 · 一键重练"),
        ("🎯 每日推荐", "AI 驱动个性化练习推荐，高频薄弱题优先复现。", "AI 驱动 · 个性化 · 薄弱点优先"),
        ("🔍 知识搜索", "全库关键词检索，秒级返回相关模块与文献索引。", "全库搜索 · 秒级响应"),
    ]
    for i, (title, desc, tags) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;margin:8px 0;'>
                <h4 style='color:#58a6ff;margin:0 0 8px;'>{title}</h4>
                <p style='font-size:14px;color:#8b949e;line-height:1.7;'>{desc}</p>
                <p style='font-size:11px;color:#8b949e;margin-top:8px;'>{tags}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Viz Lab
    st.markdown("### 📐 互动物理可视化实验室")
    st.caption("实时可调参数的物理模拟器，直观理解半导体工艺背后的物理原理。")
    viz_cols = st.columns(5)
    viz_items = [
        ("🔬", "光刻衍射极限", "NA/λ/k1 热力图"),
        ("⚙️", "CMP Preston", "移除速率计算"),
        ("🌈", "薄膜 n/k 浏览", "7 种材料曲线"),
        ("💎", "掺杂换算器", "Irvin 实时查表"),
        ("⚡", "RC 延迟模型", "Cu/low-k vs Al/SiO₂"),
    ]
    for i, (emoji, title, desc) in enumerate(viz_items):
        with viz_cols[i]:
            st.markdown(f"""
            <div style='background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;text-align:center;'>
                <div style='font-size:2em;'>{emoji}</div>
                <h4 style='color:#fff;font-size:0.95em;margin:8px 0 4px;'>{title}</h4>
                <p style='font-size:12px;color:#8b949e;'>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Module table
    st.markdown("### 📚 27 大知识模块")
    modules_data = [
        ("00 半导体物理基础", "基础", "L1"),
        ("01 CMOS 器件物理", "器件", "L1-L2"),
        ("02 FinFET / GAA", "器件", "L2-L3"),
        ("03 内存技术", "器件", "L2-L3"),
        ("04 功率器件 (GaN/SiC)", "器件", "L2-L3"),
        ("10 光刻技术", "前段", "L1-L3"),
        ("11 刻蚀技术", "前段", "L1-L3"),
        ("12 薄膜沉积", "前段", "L1-L3"),
        ("13 CMP 平坦化", "前段", "L1-L2"),
        ("14 扩散与注入", "前段", "L1-L2"),
        ("15 量测与检测", "量测", "L1-L3"),
        ("20 互连与 BEOL", "后段", "L2-L3"),
        ("21 先进封装", "后段", "L2-L3"),
        ("22 Hybrid Bonding", "后段", "L3"),
        ("30 材料科学", "材料", "L2-L3"),
        ("40 Mask/OPC/RET", "设计", "L2-L3"),
        ("41 DTCO/STCO", "设计", "L3"),
        ("50 良率与缺陷", "品质", "L1-L3"),
        ("51 SPC 统计控制", "品质", "L1-L2"),
        ("60 设备工程", "设备", "L1-L2"),
        ("90 训练体系", "管理", "L1"),
        ("99 产业分析", "产业", "L1-L2"),
    ]
    md_html = "<table style='width:100%;font-size:13px;'><tr><th style='color:#8b949e'>模块</th><th style='color:#8b949e'>领域</th><th style='color:#8b949e'>难度</th></tr>"
    for name, field, diff in modules_data:
        md_html += f"<tr><td style='padding:6px 12px;border-bottom:1px solid #30363d;'>{name}</td><td style='padding:6px 12px;border-bottom:1px solid #30363d;'>{field}</td><td style='padding:6px 12px;border-bottom:1px solid #30363d;'>{diff}</td></tr>"
    md_html += "</table>"
    st.markdown(md_html, unsafe_allow_html=True)

    st.markdown("---")

    # Tech stack
    st.markdown("### 🏗️ 技术架构")
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        st.markdown("""<div style='background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;'>
            <h4 style='color:#58a6ff;'>⚡ FastAPI 后端</h4>
            <p style='font-size:14px;color:#8b949e;'>异步 REST API · SQLite 持久化 · 热重载</p>
        </div>""", unsafe_allow_html=True)
    with tc2:
        st.markdown("""<div style='background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;'>
            <h4 style='color:#58a6ff;'>🎨 Streamlit 前端</h4>
            <p style='font-size:14px;color:#8b949e;'>深色主题 · Matplotlib 图表 · 零前端依赖</p>
        </div>""", unsafe_allow_html=True)
    with tc3:
        st.markdown("""<div style='background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;'>
            <h4 style='color:#58a6ff;'>📖 Library 知识引擎</h4>
            <p style='font-size:14px;color:#8b949e;'>Obsidian · 834 篇 PDF · 27 模块索引</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Test accounts
    st.markdown("### 👤 测试账号")
    st.code("admin / admin123 | newbie_user / newbie123 | equip_user / equip123", language=None)

    st.markdown("---")
    st.caption("半导体培训系统 v2.0 · Built with FastAPI + Streamlit")


# ────── Main Router ──────
def main():
    if not st.session_state.user:
        show_login = st.session_state.get("show_login", False)
        if show_login:
            login_tab, intro_tab = st.tabs(["🔑 登录", "📖 系统介绍"])
        else:
            intro_tab, login_tab = st.tabs(["📖 系统介绍", "🔑 登录"])
        with intro_tab:
            intro_page()
        with login_tab:
            login_page()
        return

    intro_tab, student_tab, viz_tab, teacher_tab = st.tabs([
        "📖 系统介绍", "学生端", "📐 可视化实验室", "教师端"
    ])

    with intro_tab:
        intro_page()

    with student_tab:
        sidebar()
        pages = {
            "home": home_page,
            "courses": courses_page,
            "quiz_select": quiz_select_page,
            "quiz_active": quiz_active_page,
            "quiz_result": quiz_result_page,
            "progress": progress_page,
            "mistakes": mistakes_page,
            "stats": stats_page,
            "search": search_page,
            "module_detail": module_detail_page,
        }
        page_func = pages.get(st.session_state.page, home_page)
        page_func()

    with viz_tab:
        viz_lab_page()

    with teacher_tab:
        if st.session_state.user.get("role") in ("pie", "rd"):
            teacher_page()
        else:
            st.warning("仅 PIE / 研发 角色可访问教师端")

if __name__ == "__main__":
    main()
