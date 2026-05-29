from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import search_service

router = APIRouter()


@router.get("")
def search(
    q: str = Query(..., min_length=1),
    category: str | None = Query(None),
    subcategory: str | None = Query(None),
    fill_status: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return search_service.search_files(db, q, category, subcategory, fill_status, limit)


@router.post("/reindex")
def reindex(db: Session = Depends(get_db)):
    return search_service.reindex(db)