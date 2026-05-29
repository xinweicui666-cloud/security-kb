import hashlib
import re
from pathlib import Path


def detect_fill_status(content: str) -> str:
    placeholder_lines = 0
    substantive_lines = 0

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<!--") or "-->" in stripped:
            placeholder_lines += 1
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(">") and len(stripped) > 2:
            substantive_lines += 1
            continue
        if len(stripped) > 10:
            substantive_lines += 1

    if substantive_lines == 0:
        return "placeholder"
    if placeholder_lines > substantive_lines:
        return "partial"
    return "filled"


def extract_title(content: str, fallback: str = "") -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            return stripped[3:].strip()
    name = Path(fallback).stem if fallback else "Untitled"
    name = re.sub(r"^\d+-", "", name)
    return name


def extract_source(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("> 来源") or stripped.startswith(">来源"):
            source = stripped.lstrip(">").lstrip()
            if source.startswith("来源") or source.startswith("来源"):
                source = source[2:].lstrip("：: ")
            return source
    return None


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def count_substantive_lines(content: str) -> int:
    count = 0
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<!--") or "-->" in stripped:
            continue
        if stripped.startswith("#"):
            continue
        if len(stripped) > 5:
            count += 1
    return count
