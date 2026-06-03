from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# --- Category schemas ---

class CategoryBase(BaseModel):
    code: str
    name: str
    parent_code: Optional[str] = None
    description: Optional[str] = None
    compliance_standard: Optional[str] = None
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    compliance_standard: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryOut(CategoryBase):
    id: int
    created_at: Optional[datetime] = None
    file_count: int = 0
    filled_count: int = 0

    model_config = {"from_attributes": True}


class CategoryTreeOut(CategoryOut):
    subcategories: list["CategoryOut"] = []
    fill_percentage: float = 0.0


# --- KBFile schemas ---

class KBFileBase(BaseModel):
    relative_path: str
    category_code: str
    subcategory_code: Optional[str] = None


class KBFileCreate(KBFileBase):
    content: str
    source: Optional[str] = None


class KBFileUpdate(BaseModel):
    content: str
    source: Optional[str] = None


class KBFileStatusUpdate(BaseModel):
    fill_status: str


class KBFileOut(KBFileBase):
    id: int
    title: str
    fill_status: str
    content_hash: Optional[str] = None
    line_count: int = 0
    content_line_count: int = 0
    source: Optional[str] = None
    last_modified: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KBFileDetailOut(KBFileOut):
    content: str = ""


class KBFileListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[KBFileOut]


# --- Status schemas ---

class ModuleStatus(BaseModel):
    category_code: str
    category_name: str
    total_files: int
    filled_files: int
    partial_files: int
    placeholder_files: int
    fill_percentage: float


class StatusSummary(BaseModel):
    total_files: int
    filled_files: int
    partial_files: int
    placeholder_files: int
    fill_percentage: float
    modules: list[ModuleStatus]


class GapFile(BaseModel):
    relative_path: str
    title: str
    category_code: str


class GapGroup(BaseModel):
    priority: str
    description: str
    files: list[GapFile]


class GapsOut(BaseModel):
    gaps: list[GapGroup]


# --- Search schemas ---

class SearchResult(BaseModel):
    relative_path: str
    title: str
    category_code: str
    fill_status: str
    snippet: str
    rank: float


class SearchOut(BaseModel):
    query: str
    total_matches: int
    results: list[SearchResult]


class ReindexOut(BaseModel):
    reindexed_files: int
    duration_seconds: float


# --- Compliance schemas ---

class ComplianceFile(BaseModel):
    relative_path: str
    title: str
    fill_status: str
    content: str = ""
    source: Optional[str] = None


class ComplianceOut(BaseModel):
    standard: str
    category_code: str
    files: list[ComplianceFile]


class ComplianceSummary(BaseModel):
    total_files: int
    filled_files: int
    fill_percentage: float


class ComplianceMatrixOut(BaseModel):
    standards: list[str]
    cross_mapping_file: Optional[dict] = None
    summary: dict[str, ComplianceSummary]


# --- Import/Export schemas ---

class ImportRequest(BaseModel):
    mode: str = "scan"  # scan, paths, content
    paths: list[str] = []
    items: list[dict] = []


class ImportDetail(BaseModel):
    relative_path: str
    action: str
    fill_status: str


class ImportOut(BaseModel):
    imported: int
    updated: int
    skipped: int
    errors: list[str] = []
    details: list[ImportDetail] = []


class ExportOut(BaseModel):
    exported_at: str
    total_files: int
    files: list[KBFileDetailOut]


# --- Gap Check schemas ---


class StandardOut(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    clause_count: int = 0
    loaded_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ClauseOut(BaseModel):
    clause_id: str
    section: str
    clause_text: str
    keywords: list[str]


class StandardClausesOut(BaseModel):
    standard: StandardOut
    clauses: list[ClauseOut]


class GapCheckRequest(BaseModel):
    standardName: str
    workContent: Optional[str] = None
    workFile: Optional[str] = None
    summaryCenterUrl: Optional[str] = None
    useAI: bool = True
    useKB: bool = True


class ClauseResult(BaseModel):
    clause_id: str
    section: str
    clause_text: str
    keywords: list[str]
    confidence: float
    covered: bool
    reason: str = ""


class Suggestion(BaseModel):
    clause_id: str
    suggestion: str
    priority: str = "中"
    section: Optional[str] = None
    clause: Optional[str] = None


class KBFileUsed(BaseModel):
    relative_path: str
    title: str
    fill_status: str
    source: str = ""


class GapCheckResult(BaseModel):
    id: int
    standard: str
    standardCode: Optional[str] = None
    workSource: str
    kbEnhanced: bool
    kbFilesUsed: list[KBFileUsed]
    totalClauses: int
    coveredCount: int
    gapCount: int
    coverageRate: float
    aiEnhanced: bool
    summary: str
    results: list[ClauseResult]
    gapClauses: list[ClauseResult]
    coveredClauses: list[ClauseResult]
    suggestions: list[Suggestion]


class GapCheckHistoryItem(BaseModel):
    id: int
    standard_name: str
    work_source: str
    total_clauses: int
    covered_count: int
    gap_count: int
    coverage_rate: float
    ai_enhanced: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GapCheckHistoryDetail(BaseModel):
    id: int
    standard_name: str
    work_content: str
    work_source: str
    total_clauses: int
    covered_count: int
    gap_count: int
    coverage_rate: float
    ai_enhanced: int
    kb_enhanced: int
    kb_files_used: list[dict]
    result_json: list[dict]
    created_at: Optional[datetime] = None


class GapCheckExportRequest(BaseModel):
    standardName: str
    workContent: Optional[str] = None
    workFile: Optional[str] = None
    format: str = "json"
