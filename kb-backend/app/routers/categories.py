from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CategoryCreate, CategoryUpdate
from app.services import category_service

router = APIRouter()


@router.get("")
def list_categories(
    flat: bool = Query(False),
    db: Session = Depends(get_db),
):
    return {"categories": category_service.list_categories(db, flat)}


@router.get("/{code}")
def get_category(code: str, db: Session = Depends(get_db)):
    result = category_service.get_category(db, code)
    if not result:
        raise HTTPException(404, "分类不存在")
    return result


@router.post("")
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    try:
        c = category_service.create_category(db, data.model_dump())
    except ValueError as e:
        raise HTTPException(409, str(e))
    return c


@router.put("/{code}")
def update_category(code: str, data: CategoryUpdate, db: Session = Depends(get_db)):
    from app.models import Category
    c = db.query(Category).filter(Category.code == code).first()
    if not c:
        raise HTTPException(404, "分类不存在")
    if data.name is not None:
        c.name = data.name
    if data.description is not None:
        c.description = data.description
    if data.compliance_standard is not None:
        c.compliance_standard = data.compliance_standard
    if data.sort_order is not None:
        c.sort_order = data.sort_order
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{code}")
def delete_category(code: str, db: Session = Depends(get_db)):
    try:
        c = category_service.delete_category(db, code)
    except ValueError as e:
        raise HTTPException(409, str(e))
    if not c:
        raise HTTPException(404, "分类不存在")
    return {"deleted": c.code}