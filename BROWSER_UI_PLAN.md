# 浏览器化与可调用化方案

## 本次改动
- `bazi.py` 抽象出 `_main(argv=None)`，原 CLI 行为不变（`python bazi.py ...` 仍可直接使用）。
- 新增 `run_bazi(argv=None, capture_output=False)`：可在代码内调用，`capture_output=True` 时返回 stdout 字符串。
- 新增别名 `compute_bazi(argv=None)`：等同 `run_bazi(argv, capture_output=True)`，便于外部直接获取排盘文本。

## Python 内部调用示例
```python
from bazi import compute_bazi

text = compute_bazi(['1977', '9', '23', '19', '-g', '-n'])
print(text[:400])  # 截断查看
```
说明：`argv` 传入的参数与命令行一致；若要在脚本里打印而不捕获，可用 `run_bazi(argv)`。

## 浏览器化推荐方案
1. **短期（低侵入）**
   - 沿用现有 `compute_bazi`，在服务层用 `capture_output=True` 获取文本。
   - 用轻量 Web 框架（如 FastAPI）暴露 `/bazi` 接口，接受 year/month/day/hour/flags，返回原始文本，并可增加 `sections` 字段（按分隔线拆段）。
   - 前端可先直接显示文本/分段卡片，后续再逐步结构化。

2. **中期（可结构化）**
   - 在服务层对文本做解析：
     - 按长横线拆段；
     - 正则提取：干支、五行分数、强弱标记、大运表（行级切分）、缺失五行提示；
     - 返回 JSON：`{"summary": {...}, "sections": [...], "raw": "..."}`。
   - 前端（React/Vue/Tauri/Electron 任意）据此渲染：
     - 卡片化分段；
     - 关键指标高亮（五行计分、缺失元素）；
     - 搜索/折叠/导出 TXT/PDF。

3. **长期（彻底组件化）**
   - 将核心计算重构为纯函数，减少对全局变量的依赖，使其线程安全、便于并发服务。
   - 输出结构直接由计算层生成（而非从文本逆解析），Web/UI 层直接消费结构化数据。
   - 可考虑封装成 pip 包供其他项目复用。

## 行动清单（可选优先级）
1) 在新建的 `api.py`（FastAPI/Flask 等）中调用 `compute_bazi`，先做简单 HTTP 包装，弃用 Streamlit。 
2) 实现一版文本分段/关键字段提取的解析器，返回 JSON；补充一组固定日期的快照测试，防回归。 
3) 前端直接调用 API，选任意框架（React/Vue/Tauri/Electron），只做纯 Web/桌面 UI，不再使用 Streamlit。 
4) 若需要高并发，再把核心计算改为纯函数，移除全局状态，避免多线程共享问题。

## 已知注意点
- 目前仍依赖全局变量（`me/gans/zhis`），`compute_bazi` 每次调用会覆盖这些全局，单进程串行可用；高并发时需进一步纯函数化。
- 输出包含 ANSI 颜色码（`compute_bazi` 原样返回），若在其他前端展示请先去色。 
- Windows 管道下可能出现控制台编码提示，服务端用 `PYTHONUTF8=1` 可减轻。
