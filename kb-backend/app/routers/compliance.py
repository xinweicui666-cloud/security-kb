from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import compliance_service
from config import COMPLIANCE_STANDARDS

router = APIRouter()


@router.get("/matrix")
def get_matrix(db: Session = Depends(get_db)):
    return compliance_service.get_matrix(db)


@router.get("/{standard}")
def get_standard(standard: str, db: Session = Depends(get_db)):
    result = compliance_service.get_compliance_standard(db, standard)
    if not result:
        available = ", ".join(COMPLIANCE_STANDARDS.keys())
        raise HTTPException(400, f"不支持的标准: {standard}。可选: {available}")
    return result


@router.get("/{standard}/search")
def search_standard(
    standard: str,
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    result = compliance_service.search_compliance(db, standard, q)
    if not result:
        raise HTTPException(400, f"不支持的标准: {standard}")
    return result