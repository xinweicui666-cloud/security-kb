import uvicorn
from fastapi import FastAPI

from app.database import init_db, SessionLocal
from app.routers import files, categories, status, search, compliance, import_export, gap_check
from app.services import clause_service
from config import HOST, PORT

app = FastAPI(title="安全合规知识库管理 API", version="1.0.0")

app.include_router(files.router, prefix="/api/v1/files", tags=["文件管理"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["分类管理"])
app.include_router(status.router, prefix="/api/v1/status", tags=["填充状态"])
app.include_router(search.router, prefix="/api/v1/search", tags=["搜索"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["合规查询"])
app.include_router(import_export.router, prefix="/api/v1/io", tags=["导入导出"])
app.include_router(gap_check.router, prefix="/api/v1/gap-check", tags=["合规差距排查"])


@app.on_event("startup")
async def startup():
    init_db()
    db = SessionLocal()
    try:
        clause_service.seed_clauses(db)
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)