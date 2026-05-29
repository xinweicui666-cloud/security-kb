from sqlalchemy.orm import Session

from app.models import KBFile
from app.services.file_service import read_file_content
from config import COMPLIANCE_STANDARDS, CATEGORIES


def get_compliance_standard(db: Session, standard: str) -> dict | None:
    sub_code = COMPLIANCE_STANDARDS.get(standard)
    if not sub_code:
        return None
    parts = sub_code.split("/")
    top_code = parts[0]
    sub_dir = parts[1] if len(parts) > 1 else None

    q = db.query(KBFile).filter(KBFile.category_code == top_code)
    if sub_dir:
        q = q.filter(KBFile.subcategory_code == sub_dir)
    files = q.all()

    result_files = []
    for f in files:
        try:
            content = read_file_content(f.relative_path)
        except FileNotFoundError:
            content = ""
        result_files.append({
            "relative_path": f.relative_path,
            "title": f.title,
            "fill_status": f.fill_status,
            "content": content,
            "source": f.source,
        })

    return {
        "standard": standard,
        "category_code": sub_code,
        "files": result_files,
    }


def search_compliance(db: Session, standard: str, keyword: str) -> dict | None:
    data = get_compliance_standard(db, standard)
    if not data:
        return None
    keywords = keyword.lower().split()
    results = []
    for f in data["files"]:
        lower = f["content"].lower()
        if all(kw in lower for kw in keywords):
            idx = lower.find(keywords[0])
            start = max(0, idx - 100)
            end = min(len(lower), idx + 200)
            snippet = f["content"][start:end].replace("\n", " ").strip()
            results.append({
                "relative_path": f["relative_path"],
                "title": f["title"],
                "category_code": data["category_code"].split("/")[0],
                "fill_status": f["fill_status"],
                "snippet": snippet,
                "rank": -float(len(snippet)),
            })
    return {"query": keyword, "total_matches": len(results), "results": results}


def get_matrix(db: Session) -> dict:
    summary = {}
    for std_name, sub_code in COMPLIANCE_STANDARDS.items():
        if std_name in ("等保", "ISO", "SOC"):
            continue
        parts = sub_code.split("/")
        top_code = parts[0]
        sub_dir = parts[1] if len(parts) > 1 else None
        q = db.query(KBFile).filter(KBFile.category_code == top_code)
        if sub_dir:
            q = q.filter(KBFile.subcategory_code == sub_dir)
        total = q.count()
        filled = q.filter(KBFile.fill_status == "filled").count()
        summary[std_name] = {
            "total_files": total,
            "filled_files": filled,
            "fill_percentage": round(filled / total * 100, 1) if total else 0,
        }

    cross_file = db.query(KBFile).filter(
        KBFile.relative_path.like("03-合规框架/05-标准交叉映射/%"),
    ).first()
    cross_info = None
    if cross_file:
        cross_info = {
            "relative_path": cross_file.relative_path,
            "title": cross_file.title,
            "fill_status": cross_file.fill_status,
        }

    return {
        "standards": [s for s in COMPLIANCE_STANDARDS if s not in ("等保", "ISO", "SOC")],
        "cross_mapping_file": cross_info,
        "summary": summary,
    }
