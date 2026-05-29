from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import status_service

router = APIRouter()


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return status_service.get_summary(db)


@router.get("/gaps")
def get_gaps(
    category: str | None = Query(None),
    priority: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return status_service.get_gaps(db, category, priority)


@router.get("/changes")
def get_changes(since: str = Query(...), db: Session = Depends(get_db)):
    return {"changes": status_service.get_changes(db, since)}