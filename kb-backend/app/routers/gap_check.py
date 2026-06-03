import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ClauseOut,
    GapCheckExportRequest,
    GapCheckHistoryDetail,
    GapCheckHistoryItem,
    GapCheckRequest,
    GapCheckResult,
    StandardClausesOut,
    StandardOut,
)
from app.services import clause_service, gap_check_service, report_service

router = APIRouter()


@router.get("/standards", response_model=dict)
def list_standards(db: Session = Depends(get_db)):
    standards = clause_service.list_standards(db)
    return {"success": True, "data": [StandardOut.model_validate(s).model_dump() for s in standards]}


@router.get("/standards/{name}/clauses", response_model=dict)
def get_clauses(name: str, db: Session = Depends(get_db)):
    data = clause_service.get_clauses_by_standard_name(db, name)
    if not data:
        return {"success": False, "error": f"未找到标准: {name}"}
    standard_out = StandardOut.model_validate(data["standard"])
    clauses_out = [ClauseOut(**c) for c in data["clauses"]]
    return {"success": True, "data": StandardClausesOut(standard=standard_out, clauses=clauses_out).model_dump()}


@router.post("/run", response_model=dict)
async def run_gap_check(req: GapCheckRequest, db: Session = Depends(get_db)):
    if not req.workContent and not req.workFile and not req.summaryCenterUrl:
        return {"success": False, "error": "缺少工作内容，请提供 workContent、workFile 或 summaryCenterUrl"}
    try:
        result = await gap_check_service.run_gap_check(db, {
            "standardName": req.standardName,
            "workContent": req.workContent,
            "workFile": req.workFile,
            "summaryCenterUrl": req.summaryCenterUrl,
            "useAI": req.useAI,
            "useKB": req.useKB,
        })
        return {"success": True, "data": result}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=dict)
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    rows = gap_check_service.get_history(db, limit)
    items = [GapCheckHistoryItem.model_validate(r).model_dump() for r in rows]
    return {"success": True, "data": items}


@router.get("/history/{history_id}", response_model=dict)
def get_history_detail(history_id: int, db: Session = Depends(get_db)):
    row = gap_check_service.get_history_detail(db, history_id)
    if not row:
        return {"success": False, "error": "未找到该记录"}
    detail = GapCheckHistoryDetail(
        id=row.id,
        standard_name=row.standard_name,
        work_content=row.work_content,
        work_source=row.work_source,
        total_clauses=row.total_clauses,
        covered_count=row.covered_count,
        gap_count=row.gap_count,
        coverage_rate=row.coverage_rate,
        ai_enhanced=row.ai_enhanced,
        kb_enhanced=row.kb_enhanced,
        kb_files_used=json.loads(row.kb_files_used) if row.kb_files_used else [],
        result_json=json.loads(row.result_json) if row.result_json else [],
        created_at=row.created_at,
    )
    return {"success": True, "data": detail.model_dump()}


@router.post("/export", response_model=dict)
async def export_report(req: GapCheckExportRequest, db: Session = Depends(get_db)):
    try:
        result = await gap_check_service.run_gap_check(db, {
            "standardName": req.standardName,
            "workContent": req.workContent,
            "workFile": req.workFile,
            "useAI": False,
        })
        fmt = req.format or "json"
        if fmt == "markdown":
            output = report_service.generate_markdown(result)
        elif fmt == "html":
            output = report_service.generate_html(result)
        else:
            output = report_service.generate_json(result)
        return {"success": True, "data": {"format": fmt, "content": output}}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
