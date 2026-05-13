#!/usr/bin/env python3
# FastAPI 接口：包装 bazi.py 的 compute_bazi，便于浏览器/前端调用。

from pathlib import Path
import re
import threading
from typing import List

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from bazi import compute_bazi

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

app = FastAPI(title="bazi API", version="0.1.0")

ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
_bazi_lock = threading.Lock()


def _build_args(
    year: int,
    month: int,
    day: int,
    hour: int,
    *,
    calendar: str,
    is_leap: bool,
    female: bool,
) -> List[str]:
    args = [str(year), str(month), str(day), str(hour)]
    if calendar == "公历":
        args.append("-g")
    else:
        if is_leap:
            args.append("-r")
    if female:
        args.append("-n")
    return args


def _split_sections(text: str):
    parts = re.split(r"\n?-{20,}\n?", text)
    cleaned = []
    for part in parts:
        p = part.strip()
        if not p:
            continue
        title_line = p.splitlines()[0][:60]
        cleaned.append({"title": title_line, "content": p})
    return cleaned


@app.get('/', response_class=HTMLResponse)
def index():
    if WEB_DIR.exists():
        index_file = WEB_DIR / "index.html"
        if index_file.exists():
            return index_file.read_text(encoding="utf-8")
    return HTMLResponse("UI 文件缺失，请确认 web/index.html 是否存在。", status_code=500)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/bazi")
def bazi(
    year: int = Query(..., ge=1850, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23, description="24 小时制"),
    calendar: str = Query("公历", pattern="^(公历|农历)$"),
    is_leap: bool = Query(False, description="仅农历有效"),
    female: bool = Query(False, description="女性请设为 true"),
    strip_ansi: bool = Query(True, description="是否去除 ANSI 颜色码"),
    split: bool = Query(True, description="是否按分隔线拆分 sections"),
):
    args = _build_args(year, month, day, hour, calendar=calendar, is_leap=is_leap, female=female)
    with _bazi_lock:
        raw = compute_bazi(args)
    if strip_ansi:
        raw = ANSI_RE.sub("", raw)
    sections = _split_sections(raw) if split else []
    return {
        "args": args,
        "calendar": calendar,
        "is_leap": is_leap,
        "female": female,
        "raw": raw,
        "sections": sections,
    }


# 运行示例： uvicorn api:app --reload --port 8000
