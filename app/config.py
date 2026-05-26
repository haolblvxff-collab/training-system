"""
Semiconductor Training System — Config
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "training.db")

# Library vault paths
LIBRARY_VAULT = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Library"
)
HERMES_VAULT = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Hermes"
)

# Role-to-module mapping
ROLE_MODULES = {
    "pie": {
        "name": "工艺集成 (PIE)",
        "required": ["00-fabrication", "13-photolithography", "11-thin-film",
                      "14-dry-etch", "15-metrology", "16-CMP"],
        "elective": ["10-epitaxy", "18-IMP", "20-PKG", "41-DTCO"],
    },
    "process": {
        "name": "单点工艺",
        "required": ["15-metrology"],  # + one of litho/thin-film/etch chosen at runtime
        "elective": ["00-fabrication", "10-epitaxy", "16-CMP", "17-bonding",
                      "13-photolithography", "11-thin-film", "14-dry-etch"],
    },
    "equipment": {
        "name": "设备维护",
        "required": ["94-clean-room", "93-IE", "15-metrology"],
        "elective": ["02-Power", "11-thin-film", "14-dry-etch", "91-general"],
    },
    "quality": {
        "name": "品质管理",
        "required": ["95-Q", "15-metrology", "91-general", "93-IE"],
        "elective": ["94-clean-room", "999-industry"],
    },
    "rd": {
        "name": "研发设计",
        "required": ["13-photolithography", "40-Mask", "41-DTCO", "01-Photonics"],
        "elective": ["02-Power", "04-MEMS", "21-RF"],
    },
    "newbie": {
        "name": "通用入门",
        "required": ["00-fabrication", "91-general", "94-clean-room", "90-English"],
        "elective": [],
    },
}

# Module metadata (display names + descriptions)
MODULE_META = {
    "00-fabrication": {"name": "晶圆制造基础", "desc": "硅晶体生长、晶圆制备、基本 Fab 概念", "level": 100},
    "01-Photonics": {"name": "光子学与硅光", "desc": "激光器、调制器、波导、CPO", "level": 300},
    "02-Power": {"name": "功率半导体", "desc": "SiC、GaN、IGBT 高压电力电子", "level": 300},
    "04-MEMS": {"name": "MEMS", "desc": "微机电传感器与执行器", "level": 300},
    "05-Memory": {"name": "存储器件", "desc": "DRAM、3D NAND、新型存储器", "level": 300},
    "10-epitaxy": {"name": "外延", "desc": "MOCVD、MBE 晶体层生长", "level": 200},
    "11-thin-film": {"name": "薄膜沉积", "desc": "PVD、CVD、ALD 纳米级镀膜", "level": 200},
    "13-photolithography": {"name": "光刻", "desc": "DUV、EUV、光刻胶、OPC", "level": 200},
    "14-dry-etch": {"name": "干法刻蚀", "desc": "RIE、ICP、ALE 等离子刻蚀", "level": 200},
    "15-metrology": {"name": "计量与检测", "desc": "SEM、TEM、AFM、AOI、椭偏仪", "level": 200},
    "16-CMP": {"name": "CMP", "desc": "化学机械抛光 平坦化", "level": 200},
    "17-bonding": {"name": "晶圆键合", "desc": "熔融、粘合、共晶键合", "level": 200},
    "18-IMP": {"name": "离子注入", "desc": "掺杂 注入+退火", "level": 200},
    "20-PKG": {"name": "先进封装", "desc": "WLP、Fan-Out、2.5D/3D、Chiplet", "level": 300},
    "21-RF": {"name": "RF 器件", "desc": "GaAs、GaN HEMT、mmWave", "level": 300},
    "30-Metal": {"name": "金属化与互连", "desc": "Cu、Al、Co、Ru 互连金属", "level": 200},
    "31-Piezo": {"name": "压电器件", "desc": "PZT、AlN 压电材料", "level": 400},
    "40-Mask": {"name": "掩模设计", "desc": "光罩、OPC、ILT", "level": 300},
    "41-DTCO": {"name": "DTCO", "desc": "设计-技术协同优化", "level": 400},
    "90-English": {"name": "技术英语", "desc": "半导体工程师英语", "level": 100},
    "91-general": {"name": "半导体通识", "desc": "行业概览、供应链、基础", "level": 100},
    "92-scrum": {"name": "Scrum 敏捷", "desc": "制造业敏捷项目管理", "level": 100},
    "93-IE": {"name": "工业工程", "desc": "OEE、精益、运营优化", "level": 200},
    "94-clean-room": {"name": "洁净室与设施", "desc": "ISO 等级、HVAC、AMC、EHS", "level": 200},
    "95-Q": {"name": "品质管理", "desc": "SPC、六西格玛、FMEA、8D", "level": 200},
    "998-company": {"name": "企业档案", "desc": "AMAT、LAM、TEL、ASML 设备生态", "level": 100},
    "999-industry": {"name": "行业报告", "desc": "Yole、IC Insights、SEMI 市场报告", "level": 100},
}

DIFFICULTY_LEVELS = {"L1": "🟢 基础", "L2": "🟡 应用", "L3": "🔴 深入"}
