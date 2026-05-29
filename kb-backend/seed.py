"""导入现有知识库文件到数据库。"""

import sys
from datetime import datetime
from pathlib import Path

from config import KB_ROOT, DB_PATH, CATEGORIES, COMPLIANCE_STANDARDS
from app.database import engine, SessionLocal, Base
from app.models import Category, KBFile
from app.services.placeholder_detector import (
    compute_content_hash,
    count_substantive_lines,
    detect_fill_status,
    extract_source,
    extract_title,
)


def seed_categories(session):
    for code, info in CATEGORIES.items():
        cat = Category(
            code=code, name=info["name"],
            description=info["description"],
            sort_order=info["sort_order"],
        )
        session.merge(cat)

    for code in CATEGORIES:
        cat_dir = KB_ROOT / code
        if not cat_dir.exists():
            continue
        for sub_dir in sorted(cat_dir.iterdir()):
            if not sub_dir.is_dir() or sub_dir.name.startswith("."):
                continue
            sub_code = f"{code}/{sub_dir.name}"
            standard = None
            for std_name, std_sub in COMPLIANCE_STANDARDS.items():
                if std_sub == sub_code:
                    standard = std_name
            name = sub_dir.name.split("-")[-1] if "-" in sub_dir.name else sub_dir.name
            sub_cat = Category(
                code=sub_code, name=name,
                parent_code=code,
                compliance_standard=standard,
            )
            session.merge(sub_cat)
    session.commit()


def seed_files(session):
    category_codes = list(CATEGORIES.keys())
    md_files = sorted(KB_ROOT.rglob("*.md"))

    imported = updated = 0
    for f in md_files:
        try:
            rel = str(f.relative_to(KB_ROOT))
        except ValueError:
            continue
        top = rel.split("/")[0].split("\\")[0]
        if top not in category_codes:
            continue

        content = f.read_text(encoding="utf-8")
        parts = Path(rel).parts
        category_code = parts[0]
        subcategory_code = parts[1] if len(parts) > 2 else None

        info = {
            "fill_status": detect_fill_status(content),
            "title": extract_title(content, rel),
            "source": extract_source(content),
            "content_hash": compute_content_hash(content),
            "line_count": len(content.splitlines()),
            "content_line_count": count_substantive_lines(content),
        }

        existing = session.query(KBFile).filter(KBFile.relative_path == rel).first()
        if existing:
            existing.fill_status = info["fill_status"]
            existing.title = info["title"]
            existing.source = info["source"]
            existing.content_hash = info["content_hash"]
            existing.line_count = info["line_count"]
            existing.content_line_count = info["content_line_count"]
            existing.last_modified = datetime.utcnow()
            updated += 1
        else:
            kb_file = KBFile(
                relative_path=rel,
                category_code=category_code,
                subcategory_code=subcategory_code,
                title=info["title"],
                fill_status=info["fill_status"],
                content_hash=info["content_hash"],
                line_count=info["line_count"],
                content_line_count=info["content_line_count"],
                source=info["source"],
                last_modified=datetime.utcnow(),
            )
            session.add(kb_file)
            imported += 1

    session.commit()
    return imported, updated


def main():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    if "--force" in sys.argv:
        session.query(KBFile).delete()
        session.query(Category).delete()
        session.commit()

    seed_categories(session)
    imported, updated = seed_files(session)

    total = session.query(KBFile).count()
    filled = session.query(KBFile).filter(KBFile.fill_status == "filled").count()
    partial = session.query(KBFile).filter(KBFile.fill_status == "partial").count()
    placeholder = session.query(KBFile).filter(KBFile.fill_status == "placeholder").count()

    print(f"导入完成: {imported} 新增, {updated} 更新")
    print(f"总计 {total} 个文件: {filled} 已填充, {partial} 部分填充, {placeholder} 占位符")
    print(f"填充率: {filled/total*100:.1f}%")

    session.close()


if __name__ == "__main__":
    main()