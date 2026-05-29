from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ImportRequest
from app.services import import_export_service

router = APIRouter()


@router.post("/import")
def import_files(data: ImportRequest, db: Session = Depends(get_db)):
    return import_export_service.import_files(db, data.model_dump())


@router.get("/export")
def export_files(
    category: str | None = Query(None),
    fill_status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return import_export_service.export_files(db, category, fill_status)