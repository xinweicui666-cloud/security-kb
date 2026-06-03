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

# --- 合规差距排查 (gap-check) 配置 ---
CLAUSES_DIR = KB_BACKEND_ROOT / "data" / "clauses"

GAP_CHECK = {
    "keyword_min_confidence": float(os.environ.get("GC_KEYWORD_MIN_CONFIDENCE", "0.15")),
    "ai_min_confidence": float(os.environ.get("GC_AI_MIN_CONFIDENCE", "0.5")),
}

# AI 配置 (可选，不配置则仅使用关键词匹配)
AI_CONFIG = {
    "provider": os.environ.get("GC_AI_PROVIDER", ""),   # claude | glm | minimax | '' (空=不启用)
    "api_key": os.environ.get("GC_AI_API_KEY", ""),
    "model": os.environ.get("GC_AI_MODEL", ""),
    "base_url": os.environ.get("GC_AI_BASE_URL", ""),
}

# gap-check 标准名 → 知识库合规框架子目录映射
GAP_CHECK_STANDARD_MAP = {
    "等保2.0": "等保2.0",
    "ISO27001": "ISO27001",
    "SOC2": "SOC2",
    "GDPR": "GDPR",
}

# 无直接映射的标准 → 关键词搜索兜底
GAP_CHECK_STANDARD_KEYWORDS = {
    "网络安全法": ["网络安全", "安全管理制度", "网络防护", "安全监测"],
    "数据安全法": ["数据安全", "数据管理", "数据分级", "数据保护", "数据分类"],
    "个人信息保护法": ["个人信息", "隐私保护", "数据脱敏", "用户数据", "知情同意"],
}

# 知识库证据通道类目 (合并到工作内容，参与关键词匹配)
EVIDENCE_CATEGORIES = ["01-制度体系", "02-技术基线", "06-应急响应"]

# 知识库上下文通道类目 (仅注入AI Prompt)
CONTEXT_CATEGORIES = ["03-合规框架", "04-审计与整改"]

# KB 内容最大字符数 (防 prompt 溢出)
KB_MAX_CONTENT_LENGTH = int(os.environ.get("GC_KB_MAX_CONTENT", "50000"))

# Summary Center API (工作内容来源之一)
SUMMARY_CENTER_URL = os.environ.get("GC_SUMMARY_CENTER_URL", "")

# KB 搜索每次最大返回数
KB_MAX_SEARCH_RESULTS = int(os.environ.get("GC_KB_MAX_SEARCH_RESULTS", "10"))
