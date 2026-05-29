from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import KBFile
from app.services.file_service import (
    analyze_content, write_file_content,
)
from config import KB_ROOT, CATEGORIES


def import_files(db: Session, data: dict) -> dict:
    mode = data.get("mode", "scan")
    imported = updated = skipped = 0
    errors = []
    details = []

    if mode == "scan":
        category_codes = list(CATEGORIES.keys())
        md_files = sorted(KB_ROOT.rglob("*.md"))
        for f in md_files:
            try:
                rel = str(f.relative_to(KB_ROOT))
            except ValueError:
                continue
            top = rel.split("/")[0].split("\\")[0]
            if top not in category_codes:
                continue
            existing = db.query(KBFile).filter(KBFile.relative_path == rel).first()
            if existing:
                skipped += 1
                continue
            content = f.read_text(encoding="utf-8")
            info = analyze_content(content, rel)
            parts = Path(rel).parts
            sub_code = parts[1] if len(parts) > 2 else None
            kb_file = KBFile(
                relative_path=rel,
                category_code=parts[0],
                subcategory_code=sub_code,
                title=info["title"],
                fill_status=info["fill_status"],
                content_hash=info["content_hash"],
                line_count=info["line_count"],
                content_line_count=info["content_line_count"],
                source=info["source"],
                last_modified=datetime.utcnow(),
            )
            db.add(kb_file)
            imported += 1
            details.append({"relative_path": rel, "action": "created", "fill_status": info["fill_status"]})
        db.commit()

    elif mode == "paths":
        for rel in data.get("paths", []):
            p = KB_ROOT / rel
            if not p.exists():
                errors.append(f"文件不存在: {rel}")
                continue
            content = p.read_text(encoding="utf-8")
            info = analyze_content(content, rel)
            existing = db.query(KBFile).filter(KBFile.relative_path == rel).first()
            if existing:
                existing.fill_status = info["fill_status"]
                existing.title = info["title"]
                existing.content_hash = info["content_hash"]
                existing.line_count = info["line_count"]
                existing.content_line_count = info["content_line_count"]
                existing.source = info["source"]
                updated += 1
                details.append({"relative_path": rel, "action": "updated", "fill_status": info["fill_status"]})
            else:
                parts = Path(rel).parts
                sub_code = parts[1] if len(parts) > 2 else None
                kb_file = KBFile(
                    relative_path=rel, category_code=parts[0],
                    subcategory_code=sub_code,
                    title=info["title"], fill_status=info["fill_status"],
                    content_hash=info["content_hash"],
                    line_count=info["line_count"],
                    content_line_count=info["content_line_count"],
                    source=info["source"],
                    last_modified=datetime.utcnow(),
                )
                db.add(kb_file)
                imported += 1
                details.append({"relative_path": rel, "action": "created", "fill_status": info["fill_status"]})
        db.commit()

    elif mode == "content":
        for item in data.get("items", []):
            rel = item.get("relative_path", "")
            content = item.get("content", "")
            if not rel:
                errors.append("缺少 relative_path")
                continue
            write_file_content(rel, content)
            info = analyze_content(content, rel)
            existing = db.query(KBFile).filter(KBFile.relative_path == rel).first()
            if existing:
                existing.fill_status = info["fill_status"]
                existing.title = info["title"]
                existing.content_hash = info["content_hash"]
                existing.line_count = info["line_count"]
                existing.content_line_count = info["content_line_count"]
                existing.source = info["source"]
                updated += 1
                details.append({"relative_path": rel, "action": "updated", "fill_status": info["fill_status"]})
            else:
                parts = Path(rel).parts
                sub_code = parts[1] if len(parts) > 2 else None
                kb_file = KBFile(
                    relative_path=rel, category_code=parts[0],
                    subcategory_code=sub_code,
                    title=info["title"], fill_status=info["fill_status"],
                    content_hash=info["content_hash"],
                    line_count=info["line_count"],
                    content_line_count=info["content_line_count"],
                    source=info["source"],
                    last_modified=datetime.utcnow(),
                )
                db.add(kb_file)
                imported += 1
                details.append({"relative_path": rel, "action": "created", "fill_status": info["fill_status"]})
        db.commit()

    return {
        "imported": imported, "updated": updated, "skipped": skipped,
        "errors": errors, "details": details,
    }


def export_files(
    db: Session,
    category: str | None = None,
    fill_status: str | None = None,
) -> dict:
    q = db.query(KBFile)
    if category:
        q = q.filter(KBFile.category_code == category)
    if fill_status:
        q = q.filter(KBFile.fill_status == fill_status)
    files = q.all()

    result = []
    for f in files:
        try:
            content = (KB_ROOT / f.relative_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            content = ""
        result.append({
            "id": f.id,
            "relative_path": f.relative_path,
            "category_code": f.category_code,
            "subcategory_code": f.subcategory_code,
            "title": f.title,
            "fill_status": f.fill_status,
            "content_hash": f.content_hash,
            "line_count": f.line_count,
            "content_line_count": f.content_line_count,
            "source": f.source,
            "last_modified": f.last_modified,
            "created_at": f.created_at,
            "updated_at": f.updated_at,
            "content": content,
        })

    return {
        "exported_at": datetime.utcnow().isoformat(),
        "total_files": len(result),
        "files": result,
    }
