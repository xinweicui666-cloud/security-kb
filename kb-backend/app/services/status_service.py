from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import KBFile, Category
from config import CATEGORIES, PRIORITY_MAPPING


def get_summary(db: Session) -> dict:
    total = db.query(KBFile).count()
    filled = db.query(KBFile).filter(KBFile.fill_status == "filled").count()
    partial = db.query(KBFile).filter(KBFile.fill_status == "partial").count()
    placeholder = db.query(KBFile).filter(KBFile.fill_status == "placeholder").count()

    modules = []
    for code, info in CATEGORIES.items():
        t = db.query(KBFile).filter(KBFile.category_code == code).count()
        f = db.query(KBFile).filter(
            KBFile.category_code == code, KBFile.fill_status == "filled",
        ).count()
        p = db.query(KBFile).filter(
            KBFile.category_code == code, KBFile.fill_status == "partial",
        ).count()
        ph = db.query(KBFile).filter(
            KBFile.category_code == code, KBFile.fill_status == "placeholder",
        ).count()
        pct = f / t * 100 if t else 0
        modules.append({
            "category_code": code,
            "category_name": info["name"],
            "total_files": t,
            "filled_files": f,
            "partial_files": p,
            "placeholder_files": ph,
            "fill_percentage": round(pct, 1),
        })

    return {
        "total_files": total,
        "filled_files": filled,
        "partial_files": partial,
        "placeholder_files": placeholder,
        "fill_percentage": round(filled / total * 100, 1) if total else 0,
        "modules": modules,
    }


def get_gaps(db: Session, category: str | None = None, priority: str | None = None) -> dict:
    gaps = []
    priorities = [priority] if priority else ["P0", "P1", "P2", "P3"]
    for p in priorities:
        codes = PRIORITY_MAPPING.get(p, [])
        if category and category not in codes:
            continue
        files = db.query(KBFile).filter(
            KBFile.fill_status == "placeholder",
            KBFile.category_code.in_(codes),
        ).all()
        if not files:
            continue
        gap_files = [
            {"relative_path": f.relative_path, "title": f.title, "category_code": f.category_code}
            for f in files
        ]
        descriptions = {
            "P0": "技术基线 + 制度体系 — 直接支撑等保/ISO合规",
            "P1": "合规框架 + 应急响应 — 合规覆盖与应急能力",
            "P2": "审计与整改 + 风险案例 — 审计闭环与知识沉淀",
            "P3": "模板中心 — 模板可用性",
        }
        gaps.append({
            "priority": p,
            "description": descriptions.get(p, ""),
            "files": gap_files,
        })
    return {"gaps": gaps}


def get_changes(db: Session, since: str) -> list:
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(since)
    except ValueError:
        dt = datetime.utcnow()
    files = db.query(KBFile).filter(KBFile.updated_at > dt).all()
    return [
        {
            "id": f.id,
            "relative_path": f.relative_path,
            "title": f.title,
            "fill_status": f.fill_status,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        }
        for f in files
    ]
