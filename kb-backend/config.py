import os
from pathlib import Path

KB_BACKEND_ROOT = Path(__file__).resolve().parent
KB_ROOT = KB_BACKEND_ROOT.parent
DB_PATH = KB_BACKEND_ROOT / "kb.db"

HOST = os.environ.get("KB_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("KB_API_PORT", 8000))

CATEGORIES = {
    "01-制度体系": {"name": "制度体系", "description": "安全管理制度文件", "sort_order": 1},
    "02-技术基线": {"name": "技术基线", "description": "各类安全技术基线与配置规范", "sort_order": 2},
    "03-合规框架": {"name": "合规框架", "description": "等保2.0 / ISO 27001 / SOC 2 / GDPR 合规映射", "sort_order": 3},
    "04-审计与整改": {"name": "审计与整改", "description": "审计记录、不符合项跟踪、整改管理", "sort_order": 4},
    "05-风险案例": {"name": "风险案例", "description": "行业安全事件、内部风险事件、风险复盘", "sort_order": 5},
    "06-应急响应": {"name": "应急响应", "description": "应急预案、响应流程、演练与复盘", "sort_order": 6},
    "07-FAQ": {"name": "FAQ", "description": "安全合规常见问题解答", "sort_order": 7},
    "08-模板中心": {"name": "模板中心", "description": "各类安全合规文档模板", "sort_order": 8},
}

COMPLIANCE_STANDARDS = {
    "等保2.0": "03-合规框架/01-等保2.0",
    "等保": "03-合规框架/01-等保2.0",
    "ISO27001": "03-合规框架/02-ISO27001",
    "ISO": "03-合规框架/02-ISO27001",
    "SOC2": "03-合规框架/03-SOC2",
    "SOC": "03-合规框架/03-SOC2",
    "GDPR": "03-合规框架/04-GDPR",
    "交叉映射": "03-合规框架/05-标准交叉映射",
}

PRIORITY_MAPPING = {
    "P0": ["02-技术基线", "01-制度体系"],
    "P1": ["03-合规框架", "06-应急响应"],
    "P2": ["04-审计与整改", "05-风险案例"],
    "P3": ["08-模板中心"],
}
