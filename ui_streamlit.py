#!/usr/bin/env python3
# Streamlit UI for bazi.py. 输入年月日时，调用原脚本进行排盘。

import datetime
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


today = datetime.datetime.now()
st.subheader("输入参数")
with st.form("bazi-form"):
    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("年", min_value=1850, max_value=2100, value=today.year, step=1)
        month = st.number_input("月", min_value=1, max_value=12, value=today.month, step=1)
        day = st.number_input("日", min_value=1, max_value=31, value=today.day, step=1)
    with col2:
        hour = st.number_input("时 (0-23)", min_value=0, max_value=23, value=today.hour, step=1, help="按24小时制")
        calendar = st.radio("日期类型", ["公历", "农历"], index=0, horizontal=True)
        is_leap = st.checkbox("闰月（仅农历有效）", value=False)
        is_female = st.checkbox("女性（-n）", value=False)

    submitted = st.form_submit_button("开始排盘")

if submitted:
    args = [str(year), str(month), str(day), str(hour)]
    if calendar == "公历":
        args.append("-g")
    else:
        if is_leap:
            args.append("-r")
    if is_female:
        args.append("-n")

    st.info("执行命令：" + " ".join(args))
    code, stdout, stderr, cmd = run_bazi(args)

    st.code(" ".join(cmd), language="bash")

    if stdout:
        sections = split_sections(stdout)
        if sections:
            st.subheader("排盘结果（分段）")
            for idx, (title, content) in enumerate(sections, start=1):
                with st.expander(f"部分 {idx}: {title}"):
                    st.code(content, language="text")
        st.subheader("原始输出")
        st.code(stdout, language="text")
    if stderr:
        st.warning("stderr：\n" + stderr)
    if code != 0:
        st.error(f"进程返回码：{code}")
else:
    st.write("填写参数后点击“开始排盘”即可在本地运行原有 bazi.py。")
