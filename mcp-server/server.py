import os
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

KB_PATH = os.environ.get(
    "SECURITY_KB_PATH",
    str(Path(__file__).resolve().parent.parent),
)

CATEGORIES = {
    "制度体系": "01-制度体系",
    "技术基线": "02-技术基线",
    "合规框架": "03-合规框架",
    "审计与整改": "04-审计与整改",
    "风险案例": "05-风险案例",
    "应急响应": "06-应急响应",
    "FAQ": "07-FAQ",
    "模板中心": "08-模板中心",
}

COMPLIANCE_STANDARDS = {
    "等保": "03-合规框架/01-等保2.0",
    "等保2.0": "03-合规框架/01-等保2.0",
    "ISO27001": "03-合规框架/02-ISO27001",
    "ISO": "03-合规框架/02-ISO27001",
    "SOC2": "03-合规框架/03-SOC2",
    "SOC": "03-合规框架/03-SOC2",
    "GDPR": "03-合规框架/04-GDPR",
    "交叉映射": "03-合规框架/05-标准交叉映射",
}

mcp = FastMCP("security-kb")


def _find_md_files(base: str | None = None) -> list[Path]:
    root = Path(KB_PATH)
    if base:
        root = root / base
    return sorted(root.rglob("*.md"))


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[读取失败: {e}]"


def _extract_summary(content: str, max_chars: int = 200) -> str:
    lines = content.strip().splitlines()
    non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    summary = " ".join(non_empty[:5])
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "..."
    return summary or "(空文件)"


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(KB_PATH))
    except ValueError:
        return str(path)


@mcp.tool()
def search_kb(query: str, category: str = "", limit: int = 5) -> str:
    """在安全合规知识库中全文搜索关键词，返回匹配文件的路径和摘要。
示例：
        search_kb("个人信息保护影响评估")
        search_kb("SSH配置", category="技术基线")
    """
    Args:
        query: 搜索关键词，如"个人信息保护影响评估"、"SSH配置"、"等保定级"
        category: 可选的分类过滤，可选值：制度体系、技术基线、合规框架、审计与整改、风险案例、应急响应、FAQ、模板中心
        limit: 返回结果数量上限，默认5
    """
    base_dir = CATEGORIES.get(category) if category else None
    md_files = _find_md_files(base_dir)

    if not md_files:
        return f"未找到知识库文件。KB_PATH={KB_PATH}"

    keywords = query.lower().split()
    results = []

    for f in md_files:
        content = _read_file(f)
        lower = content.lower()
        if all(kw in lower for kw in keywords):
            rel = _relative_path(f)
            summary = _extract_summary(content, 300)
            results.append(f"**{rel}**\n{summary}")

    if not results:
        return f"未找到与 '{query}' 相关的内容。试试换个关键词或去掉分类过滤。"

    results = results[:limit]
    header = f"搜索 '{query}' 找到 {len(results)} 个匹配文件：\n\n"
    return header + "\n---\n".join(results)


@mcp.tool()
def read_kb_file(file_path: str) -> str:
    """读取知识库中指定文件的完整内容。

    Args:
        file_path: 知识库中文件的相对路径，如 "03-合规框架/04-GDPR/DPIA评估模板.md" 或 "07-FAQ/02-数据安全FAQ.md"
    """
    full_path = Path(KB_PATH) / file_path
    if not full_path.exists():
        return f"文件不存在: {file_path}\n可用文件请使用 list_kb_categories 查看。"
    if not str(full_path).startswith(KB_PATH):
        return "只能读取知识库目录内的文件。"
    return _read_file(full_path)


@mcp.tool()
def list_kb_categories() -> str:
    """列出安全合规知识库的所有模块及文件清单。"""
    lines = ["# 安全合规知识库文件清单\n"]
    for name, dir_key in CATEGORIES.items():
        md_files = _find_md_files(dir_key)
        lines.append(f"\n## {name} ({dir_key})")
        for f in md_files:
            lines.append(f"- {_relative_path(f)}")
    return "\n".join(lines)


@mcp.tool()
def ask_compliance(standard: str, keyword: str) -> str:
    """在指定合规标准下搜索控制项和要求。

    Args:
        standard: 合规标准名称，可选值：等保、等保2.0、ISO27001、ISO、SOC2、SOC、GDPR、交叉映射
        keyword: 搜索关键词，如"访问控制"、"加密"、"权限审计"
    """
    subdir = COMPLIANCE_STANDARDS.get(standard)
    if not subdir:
        available = ", ".join(COMPLIANCE_STANDARDS.keys())
        return f"不支持的标准: '{standard}'\n可选值: {available}"

    md_files = _find_md_files(subdir)
    keywords = keyword.lower().split()
    results = []

    for f in md_files:
        content = _read_file(f)
        lower = content.lower()
        if all(kw in lower for kw in keywords):
            rel = _relative_path(f)
            results.append(f"**{rel}**\n{_extract_summary(content, 300)}")

    if not results:
        return f"在 '{standard}' 标准下未找到与 '{keyword}' 相关的控制项。"

    header = f"在 {standard} 标准下搜索 '{keyword}' 找到 {len(results)} 个匹配：\n\n"
    return header + "\n---\n".join(results)


if __name__ == "__main__":
    print(f"Security KB MCP Server starting, KB_PATH={KB_PATH}", file=sys.stderr)
    mcp.run(transport="stdio")