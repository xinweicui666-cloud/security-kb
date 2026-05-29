from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import KBFile
from app.services.placeholder_detector import (
    compute_content_hash,
    count_substantive_lines,
    detect_fill_status,
    extract_source,
    extract_title,
)
from config import KB_ROOT


def _resolve_path(relative_path: str) -> Path:
    p = (KB_ROOT / relative_path).resolve()
    if not str(p).startswith(str(KB_ROOT)):
        raise ValueError("路径越界")
    return p


def read_file_content(relative_path: str) -> str:
    p = _resolve_path(relative_path)
    if not p.exists():
        raise FileNotFoundError(p)
    return p.read_text(encoding="utf-8")


def write_file_content(relative_path: str, content: str) -> None:
    p = _resolve_path(relative_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def delete_file(relative_path: str) -> None:
    p = _resolve_path(relative_path)
    if p.exists():
        p.unlink()


def analyze_content(content: str, fallback_name: str = "") -> dict:
    return {
        "fill_status": detect_fill_status(content),
        "title": extract_title(content, fallback_name),
        "source": extract_source(content),
        "content_hash": compute_content_hash(content),
        "line_count": len(content.splitlines()),
        "content_line_count": count_substantive_lines(content),
    }


def get_file_detail(db: Session, file_id: int) -> dict | None:
    f = db.query(KBFile).filter(KBFile.id == file_id).first()
    if not f:
        return None
    try:
        content = read_file_content(f.relative_path)
    except FileNotFoundError:
        content = ""
    return {
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
    }


def list_files(
    db: Session,
    category: str | None = None,
    subcategory: str | None = None,
    fill_status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    q = db.query(KBFile)
    if category:
        q = q.filter(KBFile.category_code == category)
    if subcategory:
        q = q.filter(KBFile.subcategory_code == subcategory)
    if fill_status:
        q = q.filter(KBFile.fill_status == fill_status)
    total = q.count()
    items = q.order_by(KBFile.relative_path).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def create_file(db: Session, data: dict) -> KBFile:
    existing = db.query(KBFile).filter(KBFile.relative_path == data["relative_path"]).first()
    if existing:
        raise ValueError(f"文件已存在: {data['relative_path']}")

    write_file_content(data["relative_path"], data["content"])
    info = analyze_content(data["content"], data["relative_path"])

    f = KBFile(
        relative_path=data["relative_path"],
        category_code=data["category_code"],
        subcategory_code=data.get("subcategory_code"),
        title=info["title"],
        fill_status=info["fill_status"],
        content_hash=info["content_hash"],
        line_count=info["line_count"],
        content_line_count=info["content_line_count"],
        source=data.get("source") or info["source"],
        last_modified=datetime.utcnow(),
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def update_file(db: Session, file_id: int, data: dict) -> KBFile | None:
    f = db.query(KBFile).filter(KBFile.id == file_id).first()
    if not f:
        return None

    write_file_content(f.relative_path, data["content"])
    info = analyze_content(data["content"], f.relative_path)

    f.title = info["title"]
    f.fill_status = info["fill_status"]
    f.content_hash = info["content_hash"]
    f.line_count = info["line_count"]
    f.content_line_count = info["content_line_count"]
    f.source = data.get("source") or info["source"]
    f.last_modified = datetime.utcnow()
    db.commit()
    db.refresh(f)
    return f


def delete_file_record(db: Session, file_id: int) -> KBFile | None:
    f = db.query(KBFile).filter(KBFile.id == file_id).first()
    if not f:
        return None
    delete_file(f.relative_path)
    db.delete(f)
    db.commit()
    return f
