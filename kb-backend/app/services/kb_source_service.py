import logging

from sqlalchemy.orm import Session

from app.models import KBFile
from app.services.file_service import read_file_content
from config import (
    COMPLIANCE_STANDARDS,
    CONTEXT_CATEGORIES,
    EVIDENCE_CATEGORIES,
    GAP_CHECK_STANDARD_KEYWORDS,
    GAP_CHECK_STANDARD_MAP,
    KB_MAX_CONTENT_LENGTH,
    KB_MAX_SEARCH_RESULTS,
)

logger = logging.getLogger(__name__)


def _format_kb_file(f: KBFile, content: str) -> str:
    header = f.title or f.relative_path or "未知文件"
    source = f" (来源: {f.source})" if f.source else ""
    return f"### {header}{source}\n{content}"


def get_kb_content(db: Session, standard_name: str) -> dict:
    """直接 DB 查询获取知识库证据和上下文，取代原 kb-source.js 的 HTTP 调用。"""
    evidence_parts = []
    context_parts = []
    files_used = []
    seen_paths = set()

    # Strategy 1: 合规标准映射 — 查该标准子目录下的 filled 文件
    kb_standard = GAP_CHECK_STANDARD_MAP.get(standard_name)
    if kb_standard and kb_standard in COMPLIANCE_STANDARDS:
        sub_dir = COMPLIANCE_STANDARDS[kb_standard]
        matched = (
            db.query(KBFile)
            .filter(KBFile.relative_path.startswith(sub_dir))
            .filter(KBFile.fill_status == "filled")
            .all()
        )
        for f in matched:
            if f.relative_path in seen_paths:
                continue
            seen_paths.add(f.relative_path)
            try:
                content = read_file_content(f.relative_path)
            except FileNotFoundError:
                continue
            rel_path = f.relative_path
            is_evidence = any(rel_path.startswith(cat) for cat in EVIDENCE_CATEGORIES)
            is_context = any(rel_path.startswith(cat) for cat in CONTEXT_CATEGORIES) or rel_path.startswith("03-合规框架")
            formatted = _format_kb_file(f, content)
            if is_evidence:
                evidence_parts.append(formatted)
            elif is_context:
                context_parts.append(formatted)
            files_used.append({
                "relative_path": rel_path,
                "title": f.title or rel_path,
                "fill_status": f.fill_status,
                "source": f.source or "",
            })

    # Strategy 2: 关键词搜索兜底（对无直接映射的标准）
    keywords = GAP_CHECK_STANDARD_KEYWORDS.get(standard_name, [standard_name] if standard_name not in GAP_CHECK_STANDARD_MAP else [])
    for kw in keywords:
        matched = (
            db.query(KBFile)
            .filter(KBFile.fill_status == "filled")
            .filter(KBFile.content.contains(kw))
            .limit(KB_MAX_SEARCH_RESULTS)
            .all()
        )
        for f in matched:
            if f.relative_path in seen_paths:
                continue
            seen_paths.add(f.relative_path)
            try:
                content = read_file_content(f.relative_path)
            except FileNotFoundError:
                continue
            rel_path = f.relative_path
            is_evidence = any(rel_path.startswith(cat) for cat in EVIDENCE_CATEGORIES)
            is_context = any(rel_path.startswith(cat) for cat in CONTEXT_CATEGORIES) or rel_path.startswith("03-合规框架")
            if is_evidence or is_context:
                formatted = _format_kb_file(f, content)
                if is_evidence:
                    evidence_parts.append(formatted)
                elif is_context:
                    context_parts.append(formatted)
                files_used.append({
                    "relative_path": rel_path,
                    "title": f.title or rel_path,
                    "fill_status": f.fill_status,
                    "source": "",
                })

    # Strategy 3: 直接获取证据类目的 filled 文件
    for cat in EVIDENCE_CATEGORIES:
        matched = (
            db.query(KBFile)
            .filter(KBFile.category_code == cat)
            .filter(KBFile.fill_status == "filled")
            .limit(20)
            .all()
        )
        for f in matched:
            if f.relative_path in seen_paths:
                continue
            seen_paths.add(f.relative_path)
            try:
                content = read_file_content(f.relative_path)
            except FileNotFoundError:
                continue
            formatted = _format_kb_file(f, content)
            evidence_parts.append(formatted)
            files_used.append({
                "relative_path": f.relative_path,
                "title": f.title or f.relative_path,
                "fill_status": f.fill_status,
                "source": f.source or "",
            })

    # 截断
    evidence_content = "\n\n".join(evidence_parts)
    context_content = "\n\n".join(context_parts)

    if len(evidence_content) > KB_MAX_CONTENT_LENGTH:
        evidence_content = evidence_content[:KB_MAX_CONTENT_LENGTH] + "\n...(知识库证据内容已截断)"
    context_max = KB_MAX_CONTENT_LENGTH // 4
    if len(context_content) > context_max:
        context_content = context_content[:context_max] + "\n...(知识库上下文已截断)"

    kb_source = "knowledge-base" if evidence_content or context_content else ""
    return {
        "evidence_content": evidence_content,
        "context_content": context_content,
        "kb_source": kb_source,
        "kb_files_used": files_used,
    }
