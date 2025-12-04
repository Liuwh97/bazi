#!/usr/bin/env python3
# Streamlit UI for bazi.py. 输入年月日时，调用原脚本进行排盘。

import datetime
import html
import os
import re
import subprocess
import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
BAZI_SCRIPT = BASE_DIR / "bazi.py"
ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

# Streamlit 1.52 参数为 page_title（旧版是 title）
st.set_page_config(page_title="八字排盘 (Streamlit)", page_icon="🧮", layout="wide")

# 简单配色与排版微调
st.markdown(
    """
    <style>
    body {background-color: #f6f8fb;}
    .note-box {
        padding: 0.5rem 0.75rem;
        background: #f5f7fa;
        border: 1px solid #e3e7ee;
        border-radius: 6px;
    }
    .small-mono {font-family: SFMono-Regular,Consolas,Menlo,monospace; font-size: 12px;}
    .section-card {
        margin: 0.35rem 0;
        padding: 0.5rem 0.75rem;
        background: #ffffff;
        border: 1px solid #e6e9ef;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .section-header {
        font-weight: 700;
        font-size: 14px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .section-title {
        font-weight: 600;
        margin-top: 2px;
        color: #334155;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        background: #eef2ff;
        color: #4338ca;
        border: 1px solid #c7d2fe;
    }
    .section-body {
        background: #0f172a;
        color: #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        font-family: SFMono-Regular,Consolas,Menlo,monospace;
        font-size: 13px;
        line-height: 1.45;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-word;
    }
    .section-body code {background: transparent;}
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("八字排盘（Streamlit UI）")
st.caption("基于 bazi.py，所有计算在本地完成，方便保持与上游代码同步。")


def run_bazi(args: list[str]):
    """调用 bazi.py，返回 (returncode, stdout, stderr, cmd)。"""
    cmd = [sys.executable, str(BAZI_SCRIPT)] + args
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    stdout = ANSI_RE.sub("", result.stdout)
    stderr = ANSI_RE.sub("", result.stderr)
    return result.returncode, stdout, stderr, cmd


def split_sections(text: str):
    """按长横线分段，便于在 UI 中展开查看。"""
    parts = re.split(r"\n?-{20,}\n?", text)
    cleaned = []
    for part in parts:
        p = part.strip()
        if not p:
            continue
        title_line = p.splitlines()[0][:60]
        cleaned.append((title_line, p))
    return cleaned


def render_section_cards(sections):
    """带色条的章节式展示。"""
    palette = ["#2563eb", "#db2777", "#059669", "#f59e0b", "#7c3aed", "#0ea5e9"]
    for idx, (title, content) in enumerate(sections, start=1):
        color = palette[(idx - 1) % len(palette)]
        safe_content = html.escape(content)
        st.markdown(
            f"""
            <div class="section-card" style="border-left: 6px solid {color};">
                <div class="section-header" style="color:{color};">部分 {idx}</div>
                <div class="section-title">{title}</div>
                <pre class="section-body">{safe_content}</pre>
            </div>
            """,
            unsafe_allow_html=True,
        )


today = datetime.datetime.now()
st.title("八字排盘（Streamlit UI）")
st.caption("表单在左侧侧栏，右侧显示排盘结果。保持与上游 bazi.py 兼容，不改动核心逻辑。")

# 预设示例，便于快速体验
presets = {
    "自定义": None,
    "示例：1977-09-23 19 女 公历": {"year": 1977, "month": 9, "day": 23, "hour": 19, "calendar": "公历", "is_leap": False, "is_female": True},
    "今天当前时刻（公历）": {"year": today.year, "month": today.month, "day": today.day, "hour": today.hour, "calendar": "公历", "is_leap": False, "is_female": False},
}

st.sidebar.header("输入参数")
with st.sidebar.form("bazi-form"):
    preset_name = st.selectbox("快速填充", list(presets.keys()), index=0)
    defaults = presets[preset_name] or {
        "year": today.year,
        "month": today.month,
        "day": today.day,
        "hour": today.hour,
        "calendar": "公历",
        "is_leap": False,
        "is_female": False,
    }
    year = st.number_input("年", min_value=1850, max_value=2100, value=defaults["year"], step=1)
    month = st.number_input("月", min_value=1, max_value=12, value=defaults["month"], step=1)
    day = st.number_input("日", min_value=1, max_value=31, value=defaults["day"], step=1)
    hour = st.number_input("时 (0-23)", min_value=0, max_value=23, value=defaults["hour"], step=1, help="按24小时制")
    calendar = st.radio("日期类型", ["公历", "农历"], index=0 if defaults["calendar"] == "公历" else 1, horizontal=True)
    is_leap = st.checkbox("闰月（仅农历有效）", value=defaults["is_leap"])
    is_female = st.checkbox("女性（-n）", value=defaults["is_female"])
    submitted = st.form_submit_button("开始排盘", type="primary")

if submitted:
    args = [str(year), str(month), str(day), str(hour)]
    if calendar == "公历":
        args.append("-g")
    else:
        if is_leap:
            args.append("-r")
    if is_female:
        args.append("-n")

    st.markdown(f"**当前参数：** `{year}-{month:02d}-{day:02d} {hour:02d}点` · 历法：{calendar} · 闰月：{is_leap} · 女性：{is_female}")
    st.caption("执行命令（等价命令行）")
    st.code(" ".join([str(x) for x in cmd]) if (cmd := [sys.executable, str(BAZI_SCRIPT)] + args) else "", language="bash")

    code, stdout, stderr, _ = run_bazi(args)

    if stdout:
        tabs = st.tabs(["分段视图", "原始输出"])
        sections = split_sections(stdout)
        with tabs[0]:
            if sections:
                st.subheader("分段查看")
                render_section_cards(sections)
            else:
                st.code(stdout, language="text")
        with tabs[1]:
            st.code(stdout, language="text")

    if stderr:
        st.warning("stderr：\n" + stderr)
    if code != 0:
        st.error(f"进程返回码：{code}")
else:
    st.markdown(
        '<div class="note-box">填写侧栏参数后点击“开始排盘”即可在本地调用原有 bazi.py 完成排盘。</div>',
        unsafe_allow_html=True,
    )
