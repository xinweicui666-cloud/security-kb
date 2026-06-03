import json
import re
from datetime import datetime


def generate_json(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


def generate_markdown(result: dict) -> str:
    lines = []
    lines.append(f"# {result['standard']} 合规差距排查报告")
    lines.append("")
    lines.append(f"**标准编号**: {result.get('standardCode', '')}")
    lines.append(f"**工作来源**: {result['workSource']}")
    lines.append(f"**排查时间**: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
    lines.append(f"**AI增强**: {'是' if result.get('aiEnhanced') else '否'}")
    kb_files = result.get("kbFilesUsed") or []
    lines.append(f"**知识库增强**: {'是 (' + str(len(kb_files)) + '个文件)' if result.get('kbEnhanced') else '否'}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 总体情况")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| 总条款数 | {result['totalClauses']} |")
    lines.append(f"| 已覆盖 | {result['coveredCount']} |")
    lines.append(f"| 未覆盖(Gap) | {result['gapCount']} |")
    lines.append(f"| 覆盖率 | {result['coverageRate']}% |")
    lines.append("")
    lines.append(f"> {result['summary']}")
    lines.append("")

    covered_clauses = result.get("coveredClauses") or []
    if covered_clauses:
        lines.append("## 已覆盖条款")
        lines.append("")
        lines.append("| 条款ID | 类别 | 条款内容 | 置信度 |")
        lines.append("|--------|------|----------|--------|")
        for c in covered_clauses:
            lines.append(f"| {c['clause_id']} | {c['section']} | {c['clause_text']} | {c['confidence']} |")
        lines.append("")

    gap_clauses = result.get("gapClauses") or []
    if gap_clauses:
        lines.append("## 未覆盖条款(Gap)")
        lines.append("")
        lines.append("| 条款ID | 类别 | 条款内容 | 置信度 |")
        lines.append("|--------|------|----------|--------|")
        for c in gap_clauses:
            lines.append(f"| {c['clause_id']} | {c['section']} | {c['clause_text']} | {c['confidence']} |")
        lines.append("")

    suggestions = result.get("suggestions") or []
    if suggestions:
        lines.append("## 整改建议")
        lines.append("")
        lines.append("| 条款ID | 建议 | 优先级 |")
        lines.append("|--------|------|--------|")
        for s in suggestions:
            lines.append(f"| {s['clause_id']} | {s['suggestion']} | {s.get('priority', '中')} |")
        lines.append("")

    if kb_files:
        lines.append("## 知识库证据来源")
        lines.append("")
        lines.append("| 文件路径 | 标题 | 填充状态 | 来源 |")
        lines.append("|---------|------|---------|------|")
        for f in kb_files:
            lines.append(f"| {f['relative_path']} | {f['title']} | {f['fill_status']} | {f.get('source', '-')} |")
        lines.append("")

    return "\n".join(lines)


def generate_html(result: dict) -> str:
    md = generate_markdown(result)
    html = md
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)
    html = re.sub(r"^---$", "<hr>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

    def _table_row(match):
        cells = [c.strip() for c in match.group(0).split("|") if c.strip()]
        tag = "th" if any(c.startswith("-") for c in cells) else "td"
        return "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"

    html = re.sub(r"^\|(.+)\|$", _table_row, html, flags=re.MULTILINE)
    html = re.sub(
        r"((<tr>.*?</tr>\n?)+)",
        r'<table border="1" cellpadding="6" cellspacing="0">\1</table>',
        html,
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{result['standard']} 合规差距排查报告</title>
<style>body{{font-family:sans-serif;max-width:960px;margin:2em auto;padding:0 1em}}table{{border-collapse:collapse;margin:1em 0}}th,td{{border:1px solid #ddd;padding:6px 10px}}th{{background:#f5f5f5}}blockquote{{border-left:3px solid #4a9eff;padding-left:12px;color:#555}}</style></head>
<body>{html}</body></html>"""
