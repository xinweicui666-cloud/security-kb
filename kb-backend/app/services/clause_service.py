import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Standard, Clause
from config import CLAUSES_DIR

logger = logging.getLogger(__name__)

SEED_FILES = [
    "clauses-dengbao2.json",
    "clauses-wanganfa.json",
    "clauses-shujuanquan.json",
    "clauses-gerenxinxi.json",
    "clauses-iso27001.json",
    "clauses-soc2.json",
    "clauses-gdpr.json",
]


def seed_clauses(db: Session) -> None:
    for filename in SEED_FILES:
        filepath = CLAUSES_DIR / filename
        if not filepath.exists():
            logger.warning(f"[clauses] 种子文件不存在: {filepath}")
            continue

        data = json.loads(filepath.read_text(encoding="utf-8"))
        standard_name = data["standardName"]
        standard_code = data.get("standardCode", "")
        version = data.get("version", "")
        description = data.get("description", "")
        clauses_data = data.get("clauses", [])

        existing = db.query(Standard).filter(Standard.name == standard_name).first()
        if existing:
            continue

        standard = Standard(
            name=standard_name,
            code=standard_code,
            version=version,
            description=description,
            clause_count=len(clauses_data),
        )
        db.add(standard)
        db.flush()

        for c in clauses_data:
            clause = Clause(
                standard_id=standard.id,
                clause_id=c["id"],
                section=c["section"],
                clause_text=c["clause"],
                keywords=json.dumps(c.get("keywords", []), ensure_ascii=False),
            )
            db.add(clause)

        db.commit()
        logger.info(f"[clauses] 已加载: {standard_name} ({len(clauses_data)}条)")


def list_standards(db: Session) -> list[Standard]:
    return db.query(Standard).order_by(Standard.id).all()


def get_standard_by_name(db: Session, name: str) -> Standard | None:
    return db.query(Standard).filter(Standard.name == name).first()


def get_clauses_by_standard_name(db: Session, name: str) -> dict | None:
    standard = get_standard_by_name(db, name)
    if not standard:
        return None
    clauses = (
        db.query(Clause)
        .filter(Clause.standard_id == standard.id)
        .order_by(Clause.clause_id)
        .all()
    )
    return {
        "standard": standard,
        "clauses": [
            {
                "clause_id": c.clause_id,
                "section": c.section,
                "clause_text": c.clause_text,
                "keywords": json.loads(c.keywords),
            }
            for c in clauses
        ],
    }
