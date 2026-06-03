from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, ForeignKey, UniqueConstraint,
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


# --- 合规差距排查 (gap-check) 模型 ---


class Standard(Base):
    __tablename__ = "standards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)
    code = Column(Text, nullable=True)
    version = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    clause_count = Column(Integer, default=0)
    loaded_at = Column(DateTime, default=datetime.utcnow)

    clauses = relationship("Clause", back_populates="standard", cascade="all, delete-orphan")


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    clause_id = Column(Text, nullable=False)
    section = Column(Text, nullable=False)
    clause_text = Column(Text, nullable=False)
    keywords = Column(Text, nullable=False, default="[]")

    standard = relationship("Standard", back_populates="clauses")

    __table_args__ = (UniqueConstraint("standard_id", "clause_id"),)


class GapCheckHistory(Base):
    __tablename__ = "gap_check_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    standard_name = Column(Text, nullable=False)
    work_content = Column(Text, nullable=False)
    work_source = Column(Text, default="direct")
    total_clauses = Column(Integer, default=0)
    covered_count = Column(Integer, default=0)
    gap_count = Column(Integer, default=0)
    coverage_rate = Column(Float, default=0)
    ai_enhanced = Column(Integer, default=0)
    kb_enhanced = Column(Integer, default=0)
    kb_files_used = Column(Text, default="[]")
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
