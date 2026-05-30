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
    "01-Photonics": {
        "objectives": ["理解硅基光子学基本原理与优势","掌握波导/调制器/探测器等核心器件工作原理","了解CPO共封装光学架构","了解激光器与光放大器基本类型"],
        "topics": [{"name":"光波导基础","subs":["SOI脊形波导","有效折射率","单模条件","传播损耗"]},{"name":"光调制器","subs":["MZ干涉仪","载流子色散效应","PN/PN结调制器","微环谐振器"]},{"name":"光电探测器","subs":["Ge-on-Si探测器","PIN/APD结构","响应度与带宽"]},{"name":"激光器与集成","subs":["III-V/Si异质集成","微盘激光器","DFB激光器","CPO共封装"]}]
    },
    "02-Power": {
        "objectives": ["了解功率半导体的分类与应用场景","掌握SiC与GaN宽禁带材料优势","理解MOSFET/IGBT器件结构与工作原理","了解功率模块封装与散热设计"],
        "topics": [{"name":"宽禁带材料","subs":["SiC 4H/6H多型","GaN HEMT异质结","Baliga优值","临界电场"]},{"name":"功率MOSFET","subs":["VDMOS结构","Trench栅","SiC MOSFET","导通电阻Ron"]},{"name":"IGBT","subs":["PT/NPT结构","场截止FS-IGBT","闩锁效应","开关损耗"]},{"name":"封装与可靠性","subs":["功率模块DBC基板","银烧结","热阻Rth","短路耐受"]}]
    },
    "04-MEMS": {
        "objectives": ["理解MEMS微机电系统基本原理","掌握体微加工与表面微加工工艺","了解常见MEMS传感器工作原理","了解MEMS与CMOS集成的技术路线"],
        "topics": [{"name":"微加工工艺","subs":["体硅刻蚀KOH/TMAH","DRIE深硅刻蚀","牺牲层释放","晶圆键合"]},{"name":"惯性传感器","subs":["加速度计","陀螺仪Coriolis","梳齿驱动","IMU六轴集成"]},{"name":"压力与声学","subs":["压阻式压力传感器","电容式麦克风","PMUT超声换能器"]},{"name":"光学MEMS","subs":["DMD数字微镜","MOEMS扫描镜","微bolometer红外"]}]
    },
    "05-Memory": {
        "objectives": ["掌握DRAM/3D NAND基本结构与工作原理","了解SRAM与新型非易失存储器","理解存储层级与性能指标","了解先进存储技术趋势"],
        "topics": [{"name":"DRAM","subs":["1T1C单元","电容结构演进","刷新机制","DDR/LPDDR/HBM"]},{"name":"3D NAND","subs":["浮动栅vs电荷陷阱","3D堆叠工艺","QLC/PLC多比特","CMOS under Array"]},{"name":"SRAM","subs":["6T单元","读写Margin","漏电功耗","高速缓存"]},{"name":"新型存储器","subs":["MRAM STT/SOT","PCRAM相变","FeRAM铁电","ReRAM忆阻"]}]
    },
    "10-epitaxy": {
        "objectives": ["理解外延生长基本原理与应用","掌握MOCVD/MBE两种主流外延技术","了解外延层质量控制与表征方法","了解异质外延与应变工程"],
        "topics": [{"name":"外延基础","subs":["同质/异质外延","晶格匹配与失配","临界厚度","应变与弛豫"]},{"name":"MOCVD","subs":["前驱体化学","III-V生长","反应腔设计","原位监测"]},{"name":"MBE","subs":["超高真空","RHEED振荡","原子层精度","掺杂控制"]},{"name":"Si外延","subs":["选择性外延SEG","SiGe应变层","Si:C外延","外延缺陷"]}]
    },
    "17-bonding": {
        "objectives": ["理解晶圆键合基本原理与分类","掌握熔融键合/粘合键合/金属键合特点","了解混合键合在3D集成中的应用","了解键合质量检测方法"],
        "topics": [{"name":"键合类型","subs":["直接键合/熔融键合","阳极键合","共晶键合","粘合键合"]},{"name":"Hybrid Bonding","subs":["Cu-Cu直接键合","介电质-介电质键合","CMP平坦化要求","热预算控制"]},{"name":"键合工艺","subs":["表面处理/等离子活化","对准精度","热压参数","界面空洞"]},{"name":"检测与缺陷","subs":["SAM扫描声学","IR红外透视","界面强度测试","void检测"]}]
    },
    "18-IMP": {
        "objectives": ["理解离子注入基本原理与剂量/能量概念","掌握注入损伤与退火修复机制","了解注入机主要部件与工艺参数","了解先进注入技术(低温/等离子掺杂)"],
        "topics": [{"name":"注入物理","subs":["离子射程Rp/ΔRp","沟道效应","损伤与缺陷","非晶化阈值"]},{"name":"退火技术","subs":["RTA快速热退火","尖峰退火Spike","毫秒退火MSA","固相外延SPER"]},{"name":"工艺应用","subs":["阱注入Well","源漏延伸SDE","晕注入Halo","超浅结USJ"]},{"name":"先进注入","subs":["等离子浸没PLAD","低温注入","共注入","团簇注入"]}]
    },
    "20-PKG": {
        "objectives": ["掌握先进封装技术全景","理解WLP/Fan-Out/2.5D/3D封装区别","了解Chiplet与异构集成趋势","了解封装可靠性与热管理"],
        "topics": [{"name":"WLP晶圆级封装","subs":["Fan-In WLP","Fan-Out (eWLB)","RDL再分布层","UBM凸点下金属"]},{"name":"2.5D/3D集成","subs":["硅中介层Interposer","TSV通孔工艺","μBump微凸点","HBM堆叠"]},{"name":"Chiplet生态","subs":["UCIe标准","Die-to-Die互联","异构集成","Chiplet分区设计"]},{"name":"封装可靠性","subs":["热膨胀CTE失配","底填Underfill","热界面材料TIM","温度循环TCT"]}]
    },
    "21-RF": {
        "objectives": ["了解RF/微波器件基本概念","掌握GaAs/GaN HEMT工作原理","理解RF开关/功放/滤波器类型","了解mmWave与6G通信射频挑战"],
        "topics": [{"name":"RF器件物理","subs":["截止频率fT/fmax","MAG最大可用增益","噪声系数NF","线性度IP3"]},{"name":"GaAs/GaN HEMT","subs":["AlGaAs/GaAs异质结","AlGaN/GaN 2DEG","场板Field Plate","电流崩塌"]},{"name":"RF前端模块","subs":["功率放大器PA","低噪声放大器LNA","RF SOI开关","BAW/SAW滤波器"]},{"name":"mmWave与封装","subs":["Antenna-in-Package","LTCC基板","电磁仿真","天线阵列"]}]
    },
    "30-Metal": {
        "objectives": ["理解互连金属化演进路线","掌握Cu damascene工艺流程","了解扩散阻挡层与种子层","了解先进互连材料(Co/Ru/Mo)"],
        "topics": [{"name":"互连基础","subs":["RC延迟","趋肤效应","电迁移EM","应力迁移SM"]},{"name":"Cu Damascene","subs":["沟槽刻蚀","TaN/Ta阻挡层","Cu种子层","ECP电镀+退火"]},{"name":"low-k集成","subs":["SiCOH低k介质","k值演进","等离子损伤","多孔low-k挑战"]},{"name":"先进互连","subs":["Co帽层","Ru半damascene","Mo互连","气隙Air Gap"]}]
    },
    "31-Piezo": {
        "objectives": ["理解压电效应基本原理与材料体系","掌握PZT/AlN/ScAlN材料特性","了解BAW/SAW滤波器工作原理","了解压电MEMS器件与应用"],
        "topics": [{"name":"压电材料","subs":["PZT铁电特性","AlN压电系数","Sc掺杂AlN增强","压电常数d33/d31"]},{"name":"声学滤波器","subs":["SAW叉指换能器","BAW体声波","FBAR薄膜结构","SMR固态装配"]},{"name":"压电MEMS","subs":["PMUT超声","压电微镜","能量收集","压电传感器"]},{"name":"表征与测试","subs":["e31/f压电系数","谐振频率","机电耦合k²","品质因数Q"]}]
    },
    "40-Mask": {
        "objectives": ["理解光掩模在光刻中的关键作用","掌握OPC光学邻近修正原理","了解PSM相移掩模技术","了解ILT逆向光刻与EUV掩模挑战"],
        "topics": [{"name":"掩模基础","subs":["二元掩模BIM","掩模材料(Cr/MoSi)","掩模制造流程","掩模误差因子MEF"]},{"name":"OPC","subs":["基于规则OPC","基于模型OPC","亚分辨率辅助SRAF","OPC验证"]},{"name":"相移掩模","subs":["交替型AltPSM","衰减型AttPSM","无铬CPL","工艺窗口增强"]},{"name":"先进掩模","subs":["ILT逆向光刻","多光束掩模写入","EUV掩模缺陷","掩模检测AIMS"]}]
    },
    "41-DTCO": {
        "objectives": ["理解DTCO/STCO设计技术协同优化概念","掌握标准单元设计与工艺约束","了解PPA功率性能面积权衡","了解路径查找Pathfinding方法"],
        "topics": [{"name":"DTCO基础","subs":["PPAC指标","设计规则DRC","标准单元库","工艺设计套件PDK"]},{"name":"标准单元优化","subs":["FinFET单元","GAA单元","接触孔Placement","单元高度Track"]},{"name":"互连尺度","subs":["金属间距MP","Via电阻","IR Drop","信号完整性"]},{"name":"STCO系统级","subs":["背面供电BSPDN","3D堆叠逻辑","DTCO流程闭环","TCAD仿真链路"]}]
    },
    "90-English": {
        "objectives": ["掌握半导体技术英语核心术语","能阅读英文datasheet与论文","能撰写英文工艺报告与邮件","能进行英文技术汇报"],
        "topics": [{"name":"核心术语","subs":["工艺术语300词","缩写全称对照","设备部件命名","Fab日常用语"]},{"name":"文献阅读","subs":["论文结构(Abstract/Method)","图表解读","关键数据定位","速读技巧"]},{"name":"技术写作","subs":["工艺变更通知PCN","良率报告YMR","设备异常报告","邮件规范"]},{"name":"口头交流","subs":["工艺review汇报","跨部门会议","供应商沟通","发音精练"]}]
    },
    "91-general": {
        "objectives": ["建立半导体产业全局认知","了解半导体历史与关键里程碑","掌握芯片从设计到制造的完整流程","了解主要企业与产业链分工"],
        "topics": [{"name":"产业概览","subs":["摩尔定律演进","半导体产业规模","IDM/Fabless/Foundry","产业链分工"]},{"name":"芯片制造流程","subs":["设计(RTL/Synthesis)","制造(FEOL/BEOL)","封装与测试","产品认证"]},{"name":"关键里程碑","subs":["晶体管发明1947","集成电路1958","微处理器1971","FinFET 2011"]},{"name":"主要企业","subs":["台积电TSMC","三星/Intel","ASML/AMAT/LAM","Qualcomm/NVIDIA/AMD"]}]
    },
    "92-scrum": {
        "objectives": ["理解Scrum敏捷框架在制造业的应用","掌握Sprint规划与Daily Standup","学会用户故事拆分与估算","理解持续改进与回顾机制"],
        "topics": [{"name":"Scrum框架","subs":["Scrum角色(Scrum Master/PO)","Sprint周期","产品待办列表","完成的定义DoD"]},{"name":"制造Scrum","subs":["设备维护Sprint","良率改善增量","Kanban+Scrum混合","跨职能团队"]},{"name":"估算与规划","subs":["故事点估算","Planning Poker","速度Velocity","燃尽图Burndown"]},{"name":"回顾与改进","subs":["Sprint回顾会","根因分析5Why","改善Kaizen","A3报告"]}]
    },
    "93-IE": {
        "objectives": ["掌握工业工程核心指标(OEE/UPH/WIP)","理解精益生产与价值流分析","了解工厂仿真与排程","了解约束理论与瓶颈分析"],
        "topics": [{"name":"OEE设备综合效率","subs":["可用率Availability","性能率Performance","良率Quality","六大损失"]},{"name":"精益生产","subs":["价值流图VSM","七大浪费","拉动生产Pull","5S管理"]},{"name":"产能与排程","subs":["产能模型","TOC约束理论","Little定律","瓶颈漂移"]},{"name":"IE工具","subs":["时间研究","动作分析","人机工程","仿真建模"]}]
    },
    "94-clean-room": {
        "objectives": ["理解洁净室ISO等级标准","掌握洁净室气流组织与过滤","了解AMC气态污染物控制","了解EHS安全与ESD防护"],
        "topics": [{"name":"洁净室设计","subs":["ISO 1-9等级","FFU风机过滤单元","层流/湍流","正压/负压"]},{"name":"环境控制","subs":["温湿度控制","AMC气态污染物","化学过滤器","VOC/酸/碱"]},{"name":"设施系统","subs":["纯水UPW","特气Bulk/Specialty","化学品供应CDS","排风Exhaust"]},{"name":"安全与ESD","subs":["静电放电ESD","接地规范","消防与应急","化学品安全"]}]
    },
    "95-Q": {
        "objectives": ["掌握SPC统计过程控制原理","理解FMEA失效模式分析","了解8D问题解决法","了解六西格玛DMAIC方法"],
        "topics": [{"name":"SPC统计控制","subs":["控制图Xbar-R","过程能力Cpk/Ppk","Western Electric规则","非正态数据"]},{"name":"FMEA","subs":["设计DFMEA","过程PFMEA","RPN风险优先级","探测度预防"]},{"name":"8D问题解决","subs":["D1团队→D8庆祝","5Why根因","防错Poka-Yoke","永久纠正措施"]},{"name":"六西格玛","subs":["DMAIC框架","MSA测量系统","DOE实验设计","假设检验"]}]
    },
    "998-company": {
        "objectives": ["了解主要半导体设备厂商与产品线","掌握各工艺环节主流设备品牌","了解设备选型考量因素","了解设备市场格局与竞争动态"],
        "topics": [{"name":"光刻设备","subs":["ASML DUV/EUV","Nikon/Canon","涂布显影Track","量测设备"]},{"name":"沉积与刻蚀","subs":["AMAT Endura/Producer","LAM Kiyo/Flex","TEL Tactras","中微/北方华创"]},{"name":"检测与量测","subs":["KLA量测","AMAT PROVision","日立CD-SEM","Onto Innovation"]},{"name":"后段与测试","subs":["Teradyne/Advantest","ASM/KE","Disco划片","Besi贴片"]}]
    },
    "999-industry": {
        "objectives": ["了解半导体行业周期性规律","掌握主要市场研究机构与报告","了解技术路线图与趋势","了解地缘政治对产业影响"],
        "topics": [{"name":"市场格局","subs":["全球半导体产值","晶圆代工份额","设备市场WFE","EDA/IP格局"]},{"name":"技术路线图","subs":["IRDS路线图","台积电路线图","IMEC roadmap","晶体管演进"]},{"name":"研究机构","subs":["Yole Intelligence","TechInsights/IC Insights","SEMI","Counterpoint"]},{"name":"产业趋势","subs":["Chiplet时代","AI芯片热潮","地缘与供应链","绿色制造"]}]
    },
    "50-RF Generator & Match": {
        "objectives": ["理解RF电源基本原理与关键参数","掌握阻抗匹配原理与自动匹配器","了解不同工艺对RF电源需求差异","了解主要厂商与选型考量"],
        "topics": [{"name":"RF电源基础","subs":["13.56MHz标准","功率范围100W-10kW","固态vs电子管","正向/反射功率"]},{"name":"阻抗匹配网络","subs":["L型/π型匹配","自动匹配器VVC","匹配速度<500ms","脉冲等离子体"]},{"name":"工艺应用","subs":["刻蚀双频2MHz+60MHz","PECVD 400kHz","PVD DC+RF","脉冲RF"]},{"name":"厂商与选型","subs":["AE Navio/Cesar","MKS SurePower","Daihen","冷却方式选型"]}]
    },
    "50-Pumps-Cryo": {
        "objectives": ["理解低温泵工作原理与G-M制冷循环","掌握两级冷头80K+15K结构","了解半导体工艺应用场景","掌握再生流程与最佳实践"],
        "topics": [{"name":"G-M制冷循环","subs":["闭循环氦气制冷","一级80K大冷量","二级10-12K","压缩机组"]},{"name":"气体捕获机制","subs":["80K挡板冷凝H2O","15K低温板冷凝N2/O2/Ar","活性炭吸附H2/He/Ne","三种捕获方式"]},{"name":"半导体应用","subs":["PVD溅射10^-8Pa","离子注入大量H2","刻蚀配合分子泵","CVD频繁再生"]},{"name":"再生操作","subs":["自然升温1-2h","稀释排气Dilution Phase","加热烘烤30-40°C","粗抽+降温投用"]}]
    },
    "50-Pumps-Turbo": {
        "objectives": ["理解涡轮分子泵工作原理","了解动叶轮/静叶轮交错结构","掌握磁悬浮轴承优势","了解工艺应用与选型"],
        "topics": [{"name":"原理与结构","subs":["动叶轮/静叶轮交错","转速3-9万RPM","每级压缩比10-100","磁悬浮无油"]},{"name":"抽气特性","subs":["N2抽速300-3000L/s","压缩比N2>10^9","极限<10^-8Pa","H2压缩比仅10^3"]},{"name":"工艺应用","subs":["刻蚀耐腐蚀型","PVD大抽速","量测SEM","配合干泵前级"]},{"name":"厂商与维护","subs":["Pfeiffer HiPace","Edwards nEXT","轴承寿命3-5年","过滤网清洗"]}]
    },
    "50-Pumps-Dry": {
        "objectives": ["了解干泵类型与工作原理","理解罗茨/爪式/螺杆泵区别","掌握半导体工艺兼容性要求","了解维护与故障排除"],
        "topics": [{"name":"泵类型","subs":["罗茨泵高抽速","爪式多级","螺杆耐腐蚀","涡旋小型"]},{"name":"多级组合","subs":["罗茨+螺杆组合","抽速30-600m³/h","极限<0.5Pa","N2吹扫5-20SLM"]},{"name":"工艺兼容","subs":["PECVD粉末多","刻蚀耐腐蚀","ALD快速循环","防凝结N2稀释"]},{"name":"厂商与维护","subs":["Edwards iXH/iXM","Ebara A系列","半年保养","转子卡死预防"]}]
    },
    "50-Pumps-Ion": {
        "objectives": ["理解Penning放电与溅射吸附原理","了解离子泵优缺点与适用场景","了解NEG与离子泵组合技术"],
        "topics": [{"name":"工作原理","subs":["Penning放电","Ti溅射化学吸附","惰性气体掩埋","电流正比压力"]},{"name":"特点","subs":["无油无振动>50000h","对惰性气体抽速低","高压下发热","H脆化阴极"]},{"name":"应用","subs":["SEM/TEM/SIMS","同步辐射","MBE","不适合大流量工艺"]},{"name":"厂商","subs":["Gamma Vacuum","Agilent VacIon","ULVAC PST","SAES NEG组合"]}]
    },
    "50-Pumps-Scroll": {
        "objectives": ["理解涡旋泵工作原理","了解双涡旋盘无油设计","掌握半导体行业中的应用场景"],
        "topics": [{"name":"原理","subs":["固定+动涡旋偏心","新月形气腔压缩","单级10Pa双级1Pa","无接触间隙0.1mm"]},{"name":"特点","subs":["完全无油","低噪<55dBA","免维护","抽速<30m³/h"]},{"name":"应用","subs":["Load Lock粗抽","氦检漏仪标配","SEM/XPS前级","R&D小型腔体"]},{"name":"厂商","subs":["Edwards nXDS","Agilent TriScroll","Anest Iwata ISP","中科科仪"]}]
    },
    "50-Pumps-Diaphragm": {
        "objectives": ["理解隔膜泵膜片往复原理","掌握耐腐蚀材料选择","了解半导体辅助应用"],
        "topics": [{"name":"原理","subs":["膜片往复运动","进排气单向阀","多级串联压缩","极限50-200Pa"]},{"name":"特点","subs":["完全无油","PTFE耐腐蚀","极其可靠","抽速<10m³/h"]},{"name":"应用","subs":["气体采样RGA前级","密封腔保压","化学品输送","实验室通用"]},{"name":"厂商","subs":["KNF德国","Vacuubrand ME","Welch","Edwards"]}]
    },
    "50-Pumps-Diffusion": {
        "objectives": ["理解油扩散泵蒸汽射流原理","了解其历史地位与衰退原因","知道仍在使用的大型场景"],
        "topics": [{"name":"原理","subs":["油加热蒸汽射流","多级喷嘴超音速","水冷回流","前级泵配合"]},{"name":"特点","subs":["高抽速低成本","对所有气体均匀","油返流污染","需冷阱挡板"]},{"name":"应用","subs":["大型PVD光伏/玻璃","真空热处理","空间模拟舱","已淘汰于精密半导体制程"]},{"name":"厂商","subs":["Agilent HS/NHS","Edwards Diffstak","Leybold DIP","硅油/聚苯醚"]}]
    },
    "54-MFC": {
        "objectives": ["理解MFC热式测量原理","掌握PID闭环控制","了解关键性能指标","了解半导体工艺对MFC的特殊要求"],
        "topics": [{"name":"工作原理","subs":["热式测量分流管","毛细管加热测温","PID电磁比例阀","1SCCM-200SLM"]},{"name":"关键指标","subs":["响应时间<1s","精度±1% S.P.","重复性±0.2%","压差0.1-3.0MPa"]},{"name":"工艺需求","subs":["刻蚀耐腐蚀","CVD加热防冷凝","ALD快速响应","量测高精度"]},{"name":"厂商与校准","subs":["MKS全球最大","Horiba高精度","七星华创国产","6-12月校准周期"]}]
    },
    "55-Gauge & Sensor": {
        "objectives": ["了解真空计类型与适用量程","掌握全量程覆盖策略","理解不同工艺对真空计的特殊需求"],
        "topics": [{"name":"真空计类型","subs":["Pirani热传导1atm-10^-1Pa","CDG电容薄膜最高精度","冷阴极高真空","热阴极超高真空"]},{"name":"全量程覆盖","subs":["大气-粗真空Pirani+CDG","中-高真空冷阴极","组合式Pirani+冷阴极","MKS/Inficon主流"]},{"name":"工艺需求","subs":["刻蚀耐腐蚀全Ni","CVD防沉积","PVD抗电磁干扰","CDG定期调零"]},{"name":"常见问题","subs":["CDG零漂","冷阴极打火","信号干扰","屏蔽与接地"]}]
    },
    "56-Chiller & Temperature": {
        "objectives": ["理解温控系统架构","掌握多通道PID温控","了解各工艺温控需求","了解维护要点"],
        "topics": [{"name":"系统架构","subs":["压缩机制冷/电加热","循环泵导热液","PID±0.1°C","管路快插接头"]},{"name":"工艺温控","subs":["刻蚀腔壁60-80°C","ESC -20-60°C","PVD靶材水冷","光刻22±0.1°C"]},{"name":"多通道控制","subs":["4-8通道独立","区域PID","改善均匀性","Galden导热液"]},{"name":"厂商与维护","subs":["SMC行业龙头","AE Atonarp","导热液6-12月更换","管路堵塞清洗"]}]
    },
    "57-Robot & Wafer Handling": {
        "objectives": ["了解机械手类型与特点","理解ATM/VAC机械手区别","掌握关键性能指标","了解末端执行器设计"],
        "topics": [{"name":"机械手类型","subs":["SCARA水平多关节","蛙腿型径向伸缩","直线导轨重载","半导体主流SCARA"]},{"name":"ATM与VAC","subs":["大气机械手EFEM","真空机械手VAC","特殊润滑MoS2","真空散热设计"]},{"name":"关键指标","subs":["定位精度<±0.1mm","搬运<5s/片","MTBF>50000h","ISO Class1洁净"]},{"name":"厂商与末端","subs":["Brooks Magnet系列","Rorze日本","边缘夹持/真空吸附","陶瓷Al2O3低颗粒"]}]
    },
    "58-Chamber & Components": {
        "objectives": ["理解腔体设计原则","掌握ESC静电卡盘原理","了解喷淋头与陶瓷窗设计"],
        "topics": [{"name":"腔体设计","subs":["铝合金6061+阳极氧化","O-ring/Kalrez密封","水冷/加热通道","对称性气流RF"]},{"name":"静电卡盘ESC","subs":["J-R力/Coulomb力","双极多区温控","背面He冷却2-10Torr","去chuck电压反转"]},{"name":"喷淋头Showerhead","subs":["均匀分布工艺气体","兼作上电极CCP","Si/SiC材质","孔径0.5-1.0mm"]},{"name":"其他关键件","subs":["ICP陶瓷窗Al2O3/石英","观察窗蓝宝石","RF/DC电馈通","OES光纤"]}]
    },
    "59-Power Supply & Electrical": {
        "objectives": ["了解设备配电系统","理解DC电源类型与应用","掌握安全互锁与SEMI标准"],
        "topics": [{"name":"配电系统","subs":["380V三相五线","AC配电盘ACDB","UPS不间断供电","隔离变压器"]},{"name":"DC电源","subs":["24V传感器/电磁阀","±15V模拟电路","高压DC ESC kV级","TDK-Lambda/Cosel"]},{"name":"安全互锁","subs":["紧急停机EMO","门锁联锁","接地故障GFCI","SEMI S2/S8标准"]},{"name":"电气规范","subs":["SEMI S2/S8/F47","NFPA 79工业机械","EMC电磁兼容","Siemens/Schneider配电"]}]
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
        new_role = st.selectbox("工种", ["newbie", "process", "equipment", "quality", "rd"],
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
                if st.button("📐 可视化实验室", use_container_width=True):
                    st.session_state.page = "viz_lab"; st.rerun()
            st.divider()
            st.markdown("[📊 YMS 良率管理系统](http://zi23899nt64.vicp.fun:38362)", unsafe_allow_html=True)
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
    from app.course_content import get_course_content
    
    topics = framework.get("topics", [])
    for topic in topics:
        with st.expander(f"📂 {topic['name']}", expanded=False):
            # Try to load detailed content
            content_html = get_course_content(module_code, topic["name"])
            if content_html:
                st.markdown(f"""<div style="background:#1c2128;border:1px solid #30363d;border-radius:8px;padding:16px;margin:8px 0;color:#c9d1d9;font-size:14px;line-height:1.8;">{content_html}</div>""", unsafe_allow_html=True)
            else:
                for sub in topic.get("subs", []):
                    st.markdown(f"• **{sub}** — `📝 详细内容开发中`")
    
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
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 班级概况", "👤 学员管理", "✏️ 题库管理", "📈 班级成绩"])
    
    with tab1:
        st.subheader("班级概况")
        overview = api("/teacher/overview")
        if overview:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: st.metric("学员总数", overview.get("total_users", 0))
            with c2: st.metric("答题总量", f"{overview.get('total_answers', 0):,}")
            with c3: st.metric("班级正确率", f"{overview.get('accuracy', 0)}%")
            with c4: st.metric("题库总量", overview.get("total_questions", 0))
            with c5: st.metric("待复习错题", overview.get("pending_mistakes", 0))
            
            st.divider()
            st.subheader("📊 各模块答题覆盖")
            mp = overview.get("module_progress", {})
            if mp:
                for mc, data in sorted(mp.items()):
                    if data["active_users"] > 0:
                        cols = st.columns([3, 1, 1])
                        with cols[0]:
                            st.markdown(f"**{data['name']}**")
                            st.progress(min(1.0, data.get("coverage_pct", 0) / 100))
                        with cols[1]:
                            st.caption(f"{data['active_users']} 名学员")
                        with cols[2]:
                            st.caption(f"{data['questions_attempted']}/{data['total_questions']} 题")
    
    with tab2:
        st.subheader("学员管理")
        users_data = api("/teacher/users")
        if users_data and users_data.get("users"):
            role_map = {"pie":"PIE","process":"单点工艺","equipment":"设备","quality":"品质","rd":"研发","newbie":"入门"}
            
            # Header
            hcols = st.columns([2, 2, 1.5, 1, 1, 1, 0.8])
            with hcols[0]: st.markdown("**用户名**")
            with hcols[1]: st.markdown("**角色**")
            with hcols[2]: st.markdown("**答题/正确率**")
            with hcols[3]: st.markdown("**错题**")
            with hcols[4]: st.markdown("**最近活跃**")
            
            for u in users_data["users"]:
                cols = st.columns([2, 2, 1.5, 1, 1, 1, 0.8])
                with cols[0]: st.markdown(f"**{u.get('display_name', u['username'])}**")
                with cols[1]: st.caption(role_map.get(u.get('role',''), '未知'))
                with cols[2]: st.caption(f"{u.get('answered',0)}题 / {u.get('accuracy',0)}%")
                with cols[3]: st.caption(str(u.get('mistakes',0)))
                with cols[4]: st.caption((u.get('last_active','') or '')[:10])
                with cols[5]:
                    if u.get('role') not in ('pie', 'rd'):
                        if st.button("🗑️", key=f"del_{u['id']}", help=f"删除 {u['username']}"):
                            api("/teacher/users/delete", "POST", {"user_id": u['id']})
                            st.rerun()
    
    with tab3:
        st.subheader("添加题目")
        with st.form("add_question_form"):
            c1, c2 = st.columns(2)
            with c1:
                from app.config import MODULE_META
                mod_names = [f"{code} - {meta['name']}" for code, meta in MODULE_META.items()]
                selected_mod = st.selectbox("模块", mod_names)
                difficulty = st.selectbox("难度", ["L1", "L2", "L3"], index=1)
            with c2:
                qtype = st.selectbox("题型", ["single", "judge"], format_func=lambda x: "单选题" if x == "single" else "判断题")
            
            question_text = st.text_area("题目", placeholder="输入题目内容...", height=80)
            
            if qtype == "single":
                opt_str = st.text_area("选项（每行一个，如 A. 选项内容）", placeholder="A. 光刻\nB. 刻蚀\nC. 沉积\nD. CMP", height=100)
            answer = st.text_input("正确答案", placeholder="A / B / C / D 或 正确/错误")
            explanation = st.text_area("解析（可选）", placeholder="解释为什么这个答案是正确的...", height=60)
            
            if st.form_submit_button("✅ 提交题目"):
                if not question_text or not answer:
                    st.error("题目和答案不能为空")
                else:
                    mod_code = selected_mod.split(" - ")[0] if " - " in selected_mod else selected_mod
                    opts = [o.strip() for o in opt_str.split("\n") if o.strip()] if qtype == "single" else []
                    result = api("/teacher/questions/add", "POST", {
                        "module_code": mod_code,
                        "question": question_text,
                        "answer": answer,
                        "options": opts,
                        "difficulty": difficulty,
                        "qtype": qtype,
                        "explanation": explanation,
                        "tags": mod_code
                    })
                    if result and result.get("status") == "ok":
                        st.success(f"题目添加成功！ID: {result.get('id')}")
                        st.info("💡 重启后端服务使题目生效，或调用 /api/knowledge/refresh")
                    else:
                        st.error(f"添加失败：{result.get('message', '未知错误')}")
    
    with tab4:
        st.subheader("班级成绩看板")
        users_data = api("/teacher/users")
        if users_data and users_data.get("users"):
            # Sort by answered count desc
            sorted_users = sorted(users_data["users"], key=lambda x: x.get("answered", 0), reverse=True)
            
            st.markdown("| 排名 | 学员 | 角色 | 答题数 | 正确率 | 错题 |")
            st.markdown("|------|------|------|--------|--------|------|")
            for i, u in enumerate(sorted_users, 1):
                if u.get("answered", 0) > 0:
                    medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}"))
                    st.markdown(f"| {medal} | {u.get('display_name', u['username'])} | {role_map.get(u.get('role', ''), '')} | {u.get('answered', 0)} | {u.get('accuracy', 0)}% | {u.get('mistakes', 0)} |")
        
        # Module stats
        st.divider()
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
        ql = query.lower()
        found_any = False
        
        # 1. Search module index
        index = api("/knowledge/index")
        if index:
            mod_results = []
            for code, mod in index.items():
                if ql in mod["name"].lower() or ql in mod["desc"].lower():
                    mod_results.append((mod, code))
                for pdf in mod.get("pdfs", []):
                    if ql in pdf["name"].lower():
                        mod_results.append((mod, code))
                        break
            
            if mod_results:
                found_any = True
                st.success(f"🔍 找到 {len(mod_results)} 个相关模块")
                for mod, code in mod_results:
                    with st.expander(f"📂 {mod['name']} ({mod['total_pdfs']} 篇文献)"):
                        st.write(mod["desc"])
                        for pdf in mod.get("pdfs", [])[:5]:
                            st.caption(f"📄 {pdf['name'][:80]}")
        
        # 2. Search course content
        from app.course_content import COURSE_CONTENT
        content_results = []
        for mc, topics in COURSE_CONTENT.items():
            from app.config import MODULE_META
            mod_name = MODULE_META.get(mc, {}).get("name", mc)
            for topic_name, html_content in topics.items():
                if ql in html_content.lower():
                    # Extract a relevant snippet
                    idx = html_content.lower().find(ql)
                    start = max(0, idx - 40)
                    end = min(len(html_content), idx + len(ql) + 80)
                    snippet = html_content[start:end].replace("<h4>","").replace("</h4>","").replace("<p>","").replace("</p>","")
                    content_results.append({
                        "module": mod_name,
                        "topic": topic_name,
                        "snippet": snippet + ("..." if end < len(html_content) else "")
                    })
        
        if content_results:
            if not found_any:
                st.success(f"📚 课程内容匹配 {len(content_results)} 条")
                found_any = True
            else:
                st.markdown(f"---\n📚 **课程内容** 匹配 {len(content_results)} 条")
            for cr in content_results[:10]:
                st.markdown(f"**{cr['module']}** → _{cr['topic']}_  ")
                st.caption(cr['snippet'][:200].strip())
        
        # 3. Search questions
        import sqlite3, os
        from app.config import DATA_DIR
        db_path = os.path.join(DATA_DIR, "training.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            qrows = conn.execute(
                "SELECT q.question, q.explanation, q.module_code, q.difficulty FROM questions q WHERE q.question LIKE ? OR q.explanation LIKE ? OR q.tags LIKE ? LIMIT 15",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            ).fetchall()
            conn.close()
            if qrows:
                if not found_any:
                    st.success(f"✏️ 匹配到 {len(qrows)} 道相关题目")
                    found_any = True
                else:
                    st.markdown(f"---\n✏️ **题目匹配** {len(qrows)} 条")
                from app.config import MODULE_META as mm
                for r in qrows:
                    mod_name = mm.get(r["module_code"], {}).get("name", r["module_code"])
                    st.markdown(f"**{mod_name}** · {r['difficulty']}")
                    st.caption(r["question"][:150])
        
        if not found_any:
            st.info("未找到相关结果，请尝试其他关键词")

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

def library_page():
    """Browse and search the Library Obsidian vault"""
    st.title("📚 文献资料库")
    
    mode = st.radio("", ["📂 浏览模块文献", "🔍 全文检索"], horizontal=True, label_visibility="collapsed")
    
    if mode == "📂 浏览模块文献":
        # Module selector
        from app.config import MODULE_META
        mod_list = [(code, f"{meta['name']}") for code, meta in sorted(MODULE_META.items())]
        selected = st.selectbox("选择模块", mod_list, format_func=lambda x: f"{x[0]} - {x[1]}")
        
        if selected:
            mod_code = selected[0]
            st.caption(f"📂 {selected[1]}")
            
            # Browse state
            if "lib_view_file" not in st.session_state:
                st.session_state.lib_view_file = None
            if "lib_view_content" not in st.session_state:
                st.session_state.lib_view_content = None
            
            # Reading view
            if st.session_state.lib_view_file:
                if st.button("← 返回文件列表", use_container_width=True):
                    st.session_state.lib_view_file = None
                    st.session_state.lib_view_content = None
                    st.rerun()
                
                st.subheader(f"📄 {st.session_state.lib_view_file}")
                content = st.session_state.lib_view_content or ""
                # Render markdown with simple formatting
                st.markdown(f"""<div style="background:#1c2128;border:1px solid #30363d;border-radius:8px;padding:20px;max-height:70vh;overflow-y:auto;color:#c9d1d9;font-size:14px;line-height:1.8;"><pre style="white-space:pre-wrap;word-wrap:break-word;font-family:inherit;color:#c9d1d9;">{content}</pre></div>""", unsafe_allow_html=True)
                return
            
            # File listing
            files_data = api(f"/library/files?module_code={mod_code}")
            if files_data and files_data.get("files"):
                pdfs = [f for f in files_data["files"] if f["type"] == "pdf"]
                notes = [f for f in files_data["files"] if f["type"] == "note"]
                
                st.markdown(f"📄 **{len(pdfs)}** 篇 PDF · 📝 **{len(notes)}** 篇笔记")
                st.divider()
                
                if notes:
                    st.subheader("📝 Obsidian 笔记")
                    for note in notes:
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            subdir_tag = f" `{note['subdir']}/`" if note.get('subdir') and note['subdir'] != '.' else ""
                            st.markdown(f"📝 **{note['name']}**{subdir_tag}")
                        with col2:
                            if st.button("📖 阅读", key=f"read_lib_{note['path'][:50]}"):
                                data = api(f"/library/read?path={note['path']}")
                                if data and data.get("content"):
                                    st.session_state.lib_view_file = note['name']
                                    st.session_state.lib_view_content = data["content"]
                                    st.rerun()
                                else:
                                    st.error("无法读取文件")
                
                if pdfs:
                    st.subheader("📄 PDF 文献")
                    for pdf in pdfs[:50]:
                        subdir_tag = f" `{pdf['subdir']}/`" if pdf.get('subdir') and pdf['subdir'] != '.' else ""
                        size_kb = pdf.get("size", 0) / 1024
                        size_str = f"{size_kb:.0f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"
                        pdf_key = pdf['path'].replace('/', '_').replace('.', '_')[:60]

                        with st.expander(f"📄 {pdf['name']}{subdir_tag} — {size_str}"):
                            pdf_url = f"https://zi23899nt64.vicp.fun/lib-pdf?path={pdf['path']}"
                            st.markdown(f"""
                            <div style="background:#1c2128;border:1px solid #30363d;border-radius:8px;overflow:hidden;margin-bottom:8px;">
                                <embed src="{pdf_url}" width="100%" height="600px" type="application/pdf"
                                    style="border:none;">
                            </div>
                            <div style="text-align:center;">
                                <a href="{pdf_url}" target="_blank"
                                    style="display:inline-block;padding:8px 24px;background:rgba(35,134,54,0.2);color:#3fb950;border:1px solid #30363d;border-radius:6px;text-decoration:none;font-size:14px;font-weight:600;">
                                    🔗 新窗口打开 PDF
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("该模块暂无文献")
    
    else:  # Full-text search
        query = st.text_input("搜索 Library 笔记", placeholder="如: EUV, ALD, TSV, 良率...")
        if query:
            with st.spinner("搜索中..."):
                results = api(f"/library/search?q={query}")
            if results and results.get("results"):
                st.success(f"找到 {results['count']} 个匹配文件")
                for r in results["results"]:
                    name_icon = "⭐ " if r["name_match"] else ""
                    with st.expander(f"{name_icon}{r['name']} — {r['matches']} 处匹配"):
                        st.caption(f"📁 {r['path']}")
                        for snip in r.get("snippets", [])[:5]:
                            st.markdown(f"`L{snip['line_num']}` {snip['text'][:200]}")
                        if st.button("📖 打开全文", key=f"srch_{r['path'][:50]}"):
                            data = api(f"/library/read?path={r['path']}")
                            if data and data.get("content"):
                                st.session_state.lib_view_file = r['name']
                                st.session_state.lib_view_content = data["content"]
                                st.rerun()
            else:
                st.info("未找到匹配结果")

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

    user = st.session_state.user
    is_admin = user.get("role") == "pie"
    
    if is_admin:
        student_tab, library_tab, teacher_tab = st.tabs([
            "学生端", "📚 文献资料", "教师端"
        ])
    else:
        student_tab, teacher_tab = st.tabs([
            "学生端", "教师端"
        ])

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
            "viz_lab": viz_lab_page,
        }
        page_func = pages.get(st.session_state.page, home_page)
        page_func()

    if is_admin:
        with library_tab:
            library_page()

    with teacher_tab:
        if st.session_state.user.get("role") in ("pie", "rd"):
            teacher_page()
        else:
            st.warning("仅 PIE / 研发 角色可访问教师端")

if __name__ == "__main__":
    main()
