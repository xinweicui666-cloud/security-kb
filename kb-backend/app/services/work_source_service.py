import logging
from pathlib import Path

import httpx

from config import SUMMARY_CENTER_URL

logger = logging.getLogger(__name__)


async def get_work_content(options: dict) -> tuple[str, str]:
    """获取工作内容，返回 (content, source)。优先级：直接输入 > 文件 > Summary Center API。"""
    if options.get("workContent"):
        return options["workContent"], "direct"

    if options.get("workFile"):
        filepath = Path(options["workFile"])
        suffix = filepath.suffix.lower()
        if suffix == ".docx":
            content = _read_docx(filepath)
        elif suffix == ".pdf":
            content = _read_pdf(filepath)
        else:
            content = filepath.read_text(encoding="utf-8")
        return content, f"file:{options['workFile']}"

    summary_url = options.get("summaryCenterUrl") or SUMMARY_CENTER_URL
    if summary_url:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(f"{summary_url}/reports/draft")
                data = res.json()
                if data.get("success") and data.get("data"):
                    content = _format_summary_center_data(data["data"])
                    return content, "summary-center"
        except Exception as e:
            logger.warning(f"[work-source] 无法从Summary Center获取数据: {e}")

    raise ValueError("未提供工作内容。请通过 workContent 参数直接输入，或通过 workFile 指定文件，或配置 summaryCenterUrl")


def _format_summary_center_data(data: dict) -> str:
    lines = []
    daily_tasks = data.get("daily_tasks", [])
    if daily_tasks:
        lines.append("## 日常工作")
        for t in daily_tasks:
            lines.append(f"- {t.get('content') or t.get('task', '')}")

    projects = data.get("projects", [])
    if projects:
        lines.append("## 项目推进")
        for p in projects:
            lines.append(f"- {p.get('name', '')}: {p.get('progress') or p.get('status', '')}")

    achievements = data.get("achievements", [])
    if achievements:
        lines.append("## 工作成果")
        for a in achievements:
            lines.append(f"- {a.get('content') or a.get('title', '')}")

    return "\n".join(lines)


def _read_docx(filepath: Path) -> str:
    """从 .docx 文件提取纯文本。"""
    from docx import Document
    doc = Document(str(filepath))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _read_pdf(filepath: Path) -> str:
    """从 .pdf 文件提取纯文本。"""
    from PyPDF2 import PdfReader
    reader = PdfReader(str(filepath))
    texts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            texts.append(t)
    return "\n".join(texts)
