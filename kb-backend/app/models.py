from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    parent_code = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    compliance_standard = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KBFile(Base):
    __tablename__ = "kb_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    relative_path = Column(Text, unique=True, nullable=False)
    category_code = Column(Text, nullable=False)
    subcategory_code = Column(Text, nullable=True)
    title = Column(Text, nullable=False)
    fill_status = Column(Text, nullable=False, default="placeholder")
    content_hash = Column(Text, nullable=True)
    line_count = Column(Integer, default=0)
    content_line_count = Column(Integer, default=0)
    source = Column(Text, nullable=True)
    last_modified = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
