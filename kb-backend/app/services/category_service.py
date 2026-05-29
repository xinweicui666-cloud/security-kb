from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Category, KBFile
from config import KB_ROOT, CATEGORIES


def list_categories(db: Session, flat: bool = False) -> list:
    cats = db.query(Category).order_by(Category.sort_order).all()
    if flat:
        result = []
        for c in cats:
            fc = db.query(KBFile).filter(KBFile.category_code == c.code).count()
            fi = db.query(KBFile).filter(
                KBFile.category_code == c.code,
                KBFile.fill_status == "filled",
            ).count()
            result.append({
                "id": c.id, "code": c.code, "name": c.name,
                "parent_code": c.parent_code, "description": c.description,
                "compliance_standard": c.compliance_standard,
                "sort_order": c.sort_order,
                "file_count": fc, "filled_count": fi,
                "created_at": c.created_at,
            })
        return result

    top_cats = [c for c in cats if c.parent_code is None]
    sub_cats = [c for c in cats if c.parent_code is not None]
    result = []
    for tc in top_cats:
        fc = db.query(KBFile).filter(KBFile.category_code == tc.code).count()
        fi = db.query(KBFile).filter(
            KBFile.category_code == tc.code,
            KBFile.fill_status == "filled",
        ).count()
        subs = []
        for sc in sub_cats:
            if sc.parent_code == tc.code:
                sfc = db.query(KBFile).filter(
                    KBFile.category_code == tc.code,
                    KBFile.subcategory_code == sc.code.split("/")[-1] if "/" in sc.code else None,
                ).count()
                sfi = db.query(KBFile).filter(
                    KBFile.category_code == tc.code,
                    KBFile.fill_status == "filled",
                ).count()
                subs.append({
                    "id": sc.id, "code": sc.code, "name": sc.name,
                    "parent_code": sc.parent_code,
                    "description": sc.description,
                    "compliance_standard": sc.compliance_standard,
                    "sort_order": sc.sort_order,
                    "file_count": sfc, "filled_count": sfi,
                    "created_at": sc.created_at,
                })
        pct = fi / fc * 100 if fc else 0
        result.append({
            "id": tc.id, "code": tc.code, "name": tc.name,
            "parent_code": None, "description": tc.description,
            "compliance_standard": None, "sort_order": tc.sort_order,
            "file_count": fc, "filled_count": fi,
            "fill_percentage": pct,
            "subcategories": subs,
            "created_at": tc.created_at,
        })
    return result


def get_category(db: Session, code: str) -> dict | None:
    c = db.query(Category).filter(Category.code == code).first()
    if not c:
        return None
    fc = db.query(KBFile).filter(KBFile.category_code == c.code).count()
    fi = db.query(KBFile).filter(
        KBFile.category_code == c.code,
        KBFile.fill_status == "filled",
    ).count()
    return {
        "id": c.id, "code": c.code, "name": c.name,
        "parent_code": c.parent_code, "description": c.description,
        "compliance_standard": c.compliance_standard,
        "sort_order": c.sort_order,
        "file_count": fc, "filled_count": fi,
        "created_at": c.created_at,
    }


def create_category(db: Session, data: dict) -> Category:
    existing = db.query(Category).filter(Category.code == data["code"]).first()
    if existing:
        raise ValueError(f"分类已存在: {data['code']}")
    dir_path = KB_ROOT / data["code"]
    dir_path.mkdir(parents=True, exist_ok=True)
    c = Category(
        code=data["code"],
        name=data["name"],
        parent_code=data.get("parent_code"),
        description=data.get("description"),
        compliance_standard=data.get("compliance_standard"),
        sort_order=data.get("sort_order", 0),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def delete_category(db: Session, code: str) -> Category | None:
    c = db.query(Category).filter(Category.code == code).first()
    if not c:
        return None
    has_files = db.query(KBFile).filter(KBFile.category_code == code).count()
    if has_files > 0:
        raise ValueError(f"分类下还有 {has_files} 个文件，无法删除")
    dir_path = KB_ROOT / code
    if dir_path.exists() and dir_path.is_dir():
        try:
            dir_path.rmdir()
        except OSError:
            pass
    db.delete(c)
    db.commit()
    return c