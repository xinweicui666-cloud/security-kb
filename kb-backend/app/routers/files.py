from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    KBFileCreate, KBFileUpdate, KBFileStatusUpdate,
    KBFileOut, KBFileDetailOut, KBFileListOut,
)
from app.services import file_service

router = APIRouter()


@router.get("", response_model=KBFileListOut)
def list_files(
    category: str | None = Query(None),
    subcategory: str | None = Query(None),
    fill_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = file_service.list_files(db, category, subcategory, fill_status, page, page_size)
    return result


@router.get("/{file_id}")
def get_file(file_id: int, db: Session = Depends(get_db)):
    result = file_service.get_file_detail(db, file_id)
    if not result:
        raise HTTPException(404, "文件不存在")
    return result


@router.post("", response_model=KBFileOut)
def create_file(data: KBFileCreate, db: Session = Depends(get_db)):
    try:
        f = file_service.create_file(db, data.model_dump())
    except ValueError as e:
        raise HTTPException(409, str(e))
    return f


@router.put("/{file_id}", response_model=KBFileOut)
def update_file(file_id: int, data: KBFileUpdate, db: Session = Depends(get_db)):
    f = file_service.update_file(db, file_id, data.model_dump())
    if not f:
        raise HTTPException(404, "文件不存在")
    return f


@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    f = file_service.delete_file_record(db, file_id)
    if not f:
        raise HTTPException(404, "文件不存在")
    return {"deleted": f.relative_path}


@router.patch("/{file_id}/status", response_model=KBFileOut)
def update_status(file_id: int, data: KBFileStatusUpdate, db: Session = Depends(get_db)):
    from app.models import KBFile
    f = db.query(KBFile).filter(KBFile.id == file_id).first()
    if not f:
        raise HTTPException(404, "文件不存在")
    if data.fill_status not in ("placeholder", "partial", "filled"):
        raise HTTPException(400, "fill_status 必须为 placeholder/partial/filled")
    f.fill_status = data.fill_status
    db.commit()
    db.refresh(f)
    return f