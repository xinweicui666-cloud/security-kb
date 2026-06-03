import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import GapCheckHistory
from app.services import ai_service, clause_service, kb_source_service, work_source_service
from config import GAP_CHECK

logger = logging.getLogger(__name__)


def keyword_match(clause: dict, work_content: str) -> float:
    text = work_content.lower()
    keywords = clause.get("keywords", [])
    if not keywords:
        return 0.0
    matched = sum(1 for kw in keywords if kw.lower() in text)
    return matched / len(keywords)


async def run_gap_check(db: Session, options: dict) -> dict:
    standard_name = options["standardName"]
    use_ai = options.get("useAI", True)
    use_kb = options.get("useKB", True)

    # 1. 加载条款
    data = clause_service.get_clauses_by_standard_name(db, standard_name)
    if not data:
        raise ValueError(f"未找到标准: {standard_name}")
    standard = data["standard"]
    clauses = data["clauses"]

    # 2. 获取工作内容
    work_content, work_source = await work_source_service.get_work_content(options)

    # 3. 获取知识库内容（直接 DB 查询）
    kb_content = ""
    kb_context = ""
    kb_source_info = ""
    kb_files_used = []
    if use_kb:
        try:
            kb_result = kb_source_service.get_kb_content(db, standard_name)
            kb_content = kb_result["evidence_content"]
            kb_context = kb_result["context_content"]
            kb_source_info = kb_result["kb_source"]
            kb_files_used = kb_result["kb_files_used"]
        except Exception as e:
            logger.warning(f"[gap-check] 知识库增强失败: {e}")

    # 4. 合并工作内容与 KB 证据
    merged_content = f"{work_content}\n\n## 知识库合规证据\n{kb_content}" if kb_content else work_content
    merged_source = f"{work_source}+{kb_source_info}" if kb_content else work_source

    # 5. 关键词匹配
    min_confidence = GAP_CHECK["keyword_min_confidence"]
    results = []
    for clause in clauses:
        confidence = keyword_match(clause, merged_content)
        confidence = round(confidence, 2)
        covered = confidence >= min_confidence
        results.append({
            "clause_id": clause["clause_id"],
            "section": clause["section"],
            "clause_text": clause["clause_text"],
            "keywords": clause["keywords"],
            "confidence": confidence,
            "covered": covered,
            "reason": "",
        })

    covered_count = sum(1 for r in results if r["covered"])
    gap_clauses = [r for r in results if not r["covered"]]
    ai_result = None

    # 6. AI 增强
    if use_ai and gap_clauses:
        try:
            prompt = ai_service.build_gap_check_prompt(gap_clauses, merged_content, kb_context)
            ai_text = await ai_service.call_ai(prompt)
            ai_result = ai_service.parse_ai_response(ai_text)

            if ai_result and ai_result.get("reassessed"):
                ai_min_confidence = GAP_CHECK["ai_min_confidence"]
                for ra in ai_result["reassessed"]:
                    idx = next((i for i, r in enumerate(results) if r["clause_id"] == ra["clause_id"]), -1)
                    if idx != -1 and ra.get("covered") and ra.get("confidence", 0) >= ai_min_confidence:
                        results[idx]["covered"] = True
                        results[idx]["confidence"] = round(ra["confidence"], 2)
                        results[idx]["reason"] = ra.get("reason", "AI判断隐含覆盖")
                covered_count = sum(1 for r in results if r["covered"])
                gap_clauses = [r for r in results if not r["covered"]]
        except Exception as e:
            logger.warning(f"[gap-check] AI增强失败: {e}")

    # 7. 计算覆盖率
    total_clauses = len(results)
    gap_count = total_clauses - covered_count
    coverage_rate = round((covered_count / total_clauses) * 10000) / 100 if total_clauses > 0 else 0

    summary = _build_summary(standard_name, total_clauses, covered_count, gap_count, coverage_rate)

    # 8. 整改建议
    suggestions = ai_result.get("suggestions") if ai_result else None
    if not suggestions:
        suggestions = [
            {
                "clause_id": c["clause_id"],
                "section": c["section"],
                "clause": c["clause_text"],
                "suggestion": f"建议补充 {c['section']} 相关工作以覆盖该条款",
                "priority": "中",
            }
            for c in gap_clauses
        ]

    # 9. 保存历史
    history_id = _save_history(
        db, standard_name, work_content, merged_source,
        total_clauses, covered_count, gap_count, coverage_rate,
        bool(ai_result), bool(kb_content), kb_files_used, results,
    )

    return {
        "id": history_id,
        "standard": standard_name,
        "standardCode": standard.code,
        "workSource": merged_source,
        "kbEnhanced": bool(kb_content),
        "kbFilesUsed": kb_files_used,
        "totalClauses": total_clauses,
        "coveredCount": covered_count,
        "gapCount": gap_count,
        "coverageRate": coverage_rate,
        "aiEnhanced": bool(ai_result),
        "summary": summary,
        "results": results,
        "gapClauses": [r for r in results if not r["covered"]],
        "coveredClauses": [r for r in results if r["covered"]],
        "suggestions": suggestions,
    }


def _build_summary(standard_name: str, total: int, covered: int, gap: int, rate: float) -> str:
    if rate >= 80:
        level = "良好"
    elif rate >= 60:
        level = "一般"
    elif rate >= 40:
        level = "较差"
    else:
        level = "严重不足"
    return f"{standard_name}合规覆盖率为{rate}%（{covered}/{total}），合规水平{level}。存在{gap}条未覆盖条款需要整改。"


def _save_history(db: Session, standard_name, work_content, work_source,
                  total_clauses, covered_count, gap_count, coverage_rate,
                  ai_enhanced, kb_enhanced, kb_files_used, results) -> int:
    row = GapCheckHistory(
        standard_name=standard_name,
        work_content=work_content,
        work_source=work_source,
        total_clauses=total_clauses,
        covered_count=covered_count,
        gap_count=gap_count,
        coverage_rate=coverage_rate,
        ai_enhanced=1 if ai_enhanced else 0,
        kb_enhanced=1 if kb_enhanced else 0,
        kb_files_used=json.dumps(kb_files_used or [], ensure_ascii=False),
        result_json=json.dumps(results, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.id


def get_history(db: Session, limit: int = 20) -> list[GapCheckHistory]:
    return db.query(GapCheckHistory).order_by(GapCheckHistory.id.desc()).limit(limit).all()


def get_history_detail(db: Session, history_id: int) -> GapCheckHistory | None:
    return db.query(GapCheckHistory).filter(GapCheckHistory.id == history_id).first()
