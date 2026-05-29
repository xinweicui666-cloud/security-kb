import sqlite3
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import KBFile
from config import DB_PATH, KB_ROOT, CATEGORIES


def search_files(
    db: Session,
    query: str,
    category: str | None = None,
    subcategory: str | None = None,
    fill_status: str | None = None,
    limit: int = 10,
) -> dict:
    results = []
    keywords = query.lower().split()

    q = db.query(KBFile)
    if category:
        q = q.filter(KBFile.category_code == category)
    if subcategory:
        q = q.filter(KBFile.subcategory_code == subcategory)
    if fill_status:
        q = q.filter(KBFile.fill_status == fill_status)
    files = q.all()

    for f in files:
        try:
            content = (KB_ROOT / f.relative_path).read_text(encoding="utf-8").lower()
        except (FileNotFoundError, OSError):
            continue
        if all(kw in content for kw in keywords):
            idx = content.find(keywords[0])
            start = max(0, idx - 100)
            end = min(len(content), idx + 200)
            snippet = content[start:end].replace("\n", " ").strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            results.append({
                "relative_path": f.relative_path,
                "title": f.title,
                "category_code": f.category_code,
                "fill_status": f.fill_status,
                "snippet": snippet,
                "rank": -float(len(snippet)),
            })

    results.sort(key=lambda x: x["rank"], reverse=True)
    results = results[:limit]
    return {"query": query, "total_matches": len(results), "results": results}


def reindex(db: Session) -> dict:
    start = time.time()
    files = db.query(KBFile).all()
    count = 0
    for f in files:
        p = KB_ROOT / f.relative_path
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8")
        from app.services.placeholder_detector import (
            compute_content_hash, count_substantive_lines,
            detect_fill_status, extract_source, extract_title,
        )
        new_hash = compute_content_hash(content)
        if new_hash != f.content_hash:
            f.content_hash = new_hash
            f.fill_status = detect_fill_status(content)
            f.title = extract_title(content, f.relative_path)
            f.source = extract_source(content)
            f.line_count = len(content.splitlines())
            f.content_line_count = count_substantive_lines(content)
            count += 1
    db.commit()
    elapsed = time.time() - start
    return {"reindexed_files": count, "duration_seconds": round(elapsed, 2)}
