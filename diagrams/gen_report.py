#!/usr/bin/env python3
"""Generate ai-system-design-guide.html following the arvinsa-html-report conventions.
Explainer/how-to archetype: backbone + Reader's Guide only (no four-layer template)."""
import os, re, glob, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN_DATE = "2026-05-30"

# chapter dir-prefix -> (zh name, en short, icon)
CH = {
    "00": ("面試準備", "Interview Prep", "🎯"),
    "01": ("基礎原理", "Foundations", "🧱"),
    "02": ("模型版圖", "Model Landscape", "🗺️"),
    "03": ("訓練與微調", "Training & Adaptation", "🎓"),
    "04": ("推論優化", "Inference Optimization", "⚡"),
    "05": ("提示與情境工程", "Prompting & Context", "✍️"),
    "06": ("檢索系統 (RAG)", "Retrieval Systems", "🔍"),
    "07": ("代理系統", "Agentic Systems", "🤖"),
    "08": ("記憶與狀態", "Memory & State", "🧠"),
    "09": ("框架與工具", "Frameworks & Tools", "🧰"),
    "10": ("文件處理", "Document Processing", "📄"),
    "11": ("基礎設施與 MLOps", "Infrastructure & MLOps", "🏗️"),
    "12": ("安全與存取控制", "Security & Access", "🔐"),
    "13": ("可靠性與安全", "Reliability & Safety", "🛡️"),
    "14": ("評估與可觀測性", "Evaluation & Observability", "📊"),
    "15": ("AI 設計模式", "AI Design Patterns", "🧩"),
    "16": ("實戰案例", "Case Studies", "📚"),
    "17": ("工具使用與電腦代理", "Tool Use & Computer Agents", "🖥️"),
}

# lifecycle stages: (anchor, section-no, heading, [chapter prefixes], reader-guide why/focus/bottom)
STAGES = [
    ("foundations", "§4", "🧱 Foundations · 基礎", ["01", "02", "03"],
     ("先建立 LLM 與模型的底層直覺，後面所有架構決策都建立在這層理解之上。",
      ["Transformer / MoE / KV cache 的取捨", "2026 模型版圖、能力與定價", "微調 vs RAG 的界線、LoRA / 蒸餾 / 量化"],
      "看懂這三章，你就能判斷「該選哪個模型、要不要微調」。")),
    ("build", "§5", "🔨 Build · 建構", ["05", "06", "10", "07", "17"],
     ("把模型變成產品的核心——提示工程、檢索、代理與工具使用。",
      ["RAG 的檢索品質缺口與重排序", "代理的推理迴圈、MCP 與多代理協作", "工具 / 電腦使用代理的安全邊界"],
      "生產級 AI 系統大部分的工程量集中在這一層。")),
    ("operate", "§6", "⚙️ Operate · 營運", ["04", "08", "09", "11"],
     ("系統能跑起來之後，成本、延遲與狀態管理決定它能不能規模化。",
      ["推論優化：KV cache / batching / PagedAttention", "記憶分層（L1–L3）與語意快取", "框架選型與基礎設施 / MLOps"],
      "這層做不好，demo 會過、production 會垮。")),
    ("govern", "§7", "🛡️ Govern · 治理", ["12", "13", "14"],
     ("安全、可靠性與評估，是把 AI 系統交付給真實使用者的前提。",
      ["prompt injection 防禦與多租戶隔離", "guardrails、ensemble 與可靠性模式", "LLM-as-judge、RAG 評估與可觀測性"],
      "沒有評估閘（eval gate），你無法證明系統「沒有變差」。")),
    ("apply", "§8", "🚀 Apply · 應用", ["15", "16", "00"],
     ("把前面所有概念落地成設計模式、真實案例與面試答題。",
      ["設計模式與反模式（anti-patterns）", "20 個帶架構圖的端到端案例", "110+ 面試題、答題框架與白板演練"],
      "面試與實戰時，這一層就是你能直接引用的「答案庫」。")),
]

ROUTING = [
    ("我要準備 AI 工程 / Staff 面試", "§8 Apply（面試準備）＋ 附錄 A"),
    ("我要從零打造生產級 RAG", "§5 Build（檢索系統 RAG）"),
    ("我要建構 AI 代理 / 多代理系統", "§5 Build（代理系統、工具使用）"),
    ("我要選對 LLM（成本 / 延遲 / 能力）", "§4 Foundations（模型版圖）"),
    ("我要做微調 / LoRA / 知識蒸餾", "§4 Foundations（訓練與微調）"),
    ("我要降低推論成本與延遲", "§6 Operate（推論優化）"),
    ("我要評估與監控上線品質", "§7 Govern（評估與可觀測性）"),
    ("我要防 prompt injection / 多租戶隔離", "§7 Govern（安全）＋ §5"),
    ("我要看真實系統的端到端架構", "§8 Apply（20 個實戰案例）"),
    ("我只想查名詞 / 速查設計模式", "附錄 A（延伸資源）"),
]

RESOURCES = [
    ("GLOSSARY.md", "名詞表 Glossary", "本指南所有關鍵術語的定義速查。"),
    ("PATTERNS.md", "設計模式速查表", "常見 AI 設計模式的快速查找。"),
    ("COURSES.md", "推薦課程與學習路徑", "2026 年驗證過的精選課程，無過時 MOOC。"),
    ("TRANSITION_GUIDE.md", "角色轉職指南", "Backend / QA / PM / EM 轉進 AI 角色的對照地圖。"),
    ("ai_evals_comprehensive_study_guide.md", "AI Evals：Phoenix + Langfuse", "3,000+ 行的 AI 評估深入指南。"),
    ("ai_evals_complete_guide_langwatch_langfuse.md", "AI Evals：LangWatch + Langfuse", "同一套大綱，搭配 LangWatch 40+ 內建評估器。"),
    ("README.md", "README 專案總覽", "完整導覽、快速導航與常見問題。"),
]

LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
def clean_desc(text):
    text = LINK_RE.sub(r"\1", text)            # [t](url) -> t
    text = text.lstrip("> ").lstrip("*").strip()
    text = text.replace("`", "").replace("**", "")
    if len(text) > 175:
        text = text[:172].rstrip() + "…"
    return text

def parse_md(path):
    title, desc = None, ""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    for ln in lines:
        if title is None and ln.startswith("# "):
            title = ln[2:].strip()
            continue
        if title is not None and ln.strip() and not ln.startswith("#"):
            desc = clean_desc(ln.strip())
            break
    return title or os.path.basename(path), desc

def chapter_dir(prefix):
    hits = sorted(glob.glob(os.path.join(ROOT, prefix + "-*")))
    return hits[0] if hits else None

def lessons_for(prefix):
    d = chapter_dir(prefix)
    out = []
    if not d:
        return out
    for f in sorted(glob.glob(os.path.join(d, "*.md"))):
        rel = os.path.relpath(f, ROOT)
        m = re.search(r"/(\d{2})-", "/" + os.path.basename(f))
        num = m.group(1) if m else ""
        title, desc = parse_md(f)
        out.append((num, title, desc, rel))
    return out

def esc(s):
    return html.escape(s, quote=True)

# ---- counts ----
all_lessons = {p: lessons_for(p) for p in CH}
total_lessons = sum(len([x for x in v if not x[3].endswith("README.md")]) for v in all_lessons.values())
n_cases = len(all_lessons["16"])

# ---- learning-map SVG (strip fixed size so it scales) ----
with open(os.path.join(ROOT, "diagrams", "learning-map.svg"), encoding="utf-8") as f:
    svg = f.read()
svg = re.sub(r"<\?xml.*?\?>\s*", "", svg, flags=re.S)
svg = re.sub(r"<!DOCTYPE.*?>\s*", "", svg, flags=re.S)
svg = re.sub(r'(<svg\b[^>]*?)\s+width="[0-9.]+pt"\s+height="[0-9.]+pt"', r"\1", svg, count=1)

# ---------- build HTML ----------
P = []
def w(s): P.append(s)

def reader_guide(why, focus, bottom):
    foc = "".join(f"<li>{esc(x)}</li>" for x in focus)
    return (f'<div class="rg"><div class="rg-row"><span class="rg-k">為什麼看這段</span>'
            f'<span>{esc(why)}</span></div>'
            f'<div class="rg-row"><span class="rg-k">關注什麼</span><ul>{foc}</ul></div>'
            f'<div class="rg-row"><span class="rg-k">結論</span><span>{esc(bottom)}</span></div></div>')

def lesson_table(prefix):
    rows = []
    for num, title, desc, rel in all_lessons[prefix]:
        label = "概覽 README" if rel.endswith("README.md") and not num else title
        rows.append(
            f'<tr><td class="n">{esc(num)}</td>'
            f'<td><a href="{esc(rel)}">{esc(label)}</a></td>'
            f'<td class="d">{esc(desc)}</td></tr>')
    return ('<table class="lessons"><thead><tr><th>#</th><th>課程 Lesson</th><th>重點 Focus</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')

# TOC
toc = ['<li><a href="#exec">§1. 重點摘要 Executive TL;DR</a></li>',
       '<li><a href="#howto">§2. 如何閱讀本報告</a></li>',
       '<li><a href="#map">§3. 學習地圖</a></li>']
for anchor, no, head, *_ in STAGES:
    toc.append(f'<li><a href="#{anchor}">{no}. {esc(head)}</a></li>')
toc.append('<li><a href="#appendix">§9. 附錄 Appendix</a></li>')

CSS = """
:root{--ink:#16181d;--soft:#4a4f5c;--mute:#767c8a;--bd:#e3e6ee;--bd2:#eef0f5;
--accent:#5b5bd6;--accent2:#00a99d;--guide:#eef2fc;--bg:#ffffff;--soft-bg:#f7f8fb;}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang TC","Noto Sans TC","Microsoft JhengHei",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);line-height:1.7;max-width:1080px;margin:0 auto;padding:0 26px 80px;background:var(--bg);}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header.rpt{padding:34px 0 18px;border-bottom:3px solid var(--accent)}
header.rpt h1{font-size:2rem;margin:0 0 8px;letter-spacing:-.02em}
header.rpt .meta{color:var(--mute);font-size:.86rem;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
header.rpt .meta code{background:var(--soft-bg);padding:1px 6px;border-radius:5px}
h2{font-size:1.5rem;letter-spacing:-.01em;margin:2em 0 .5em;padding-bottom:.25em;border-bottom:1px solid var(--bd2);scroll-margin-top:14px}
h3{font-size:1.16rem;margin:1.5em 0 .4em;letter-spacing:-.01em}
h3 .ic{margin-right:6px}
p{color:var(--soft)}
.banner{background:linear-gradient(100deg,var(--accent),var(--accent2));color:#fff;border-radius:14px;
padding:22px 26px;margin:14px 0 16px;box-shadow:0 10px 30px rgba(91,91,214,.22)}
.banner .big{font-size:1.45rem;font-weight:850;letter-spacing:-.01em;line-height:1.3}
.banner .sub{opacity:.92;font-size:.95rem;margin-top:4px}
.stat-row{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}
.stat{background:var(--soft-bg);border:1px solid var(--bd);border-radius:11px;padding:12px 18px;flex:1;min-width:130px}
.stat b{display:block;font-size:1.7rem;color:var(--accent);letter-spacing:-.02em}
.stat span{color:var(--mute);font-size:.82rem;font-weight:600}
.rg{background:var(--guide);border:1px solid #dde3f6;border-left:4px solid var(--accent);border-radius:0 10px 10px 0;
padding:13px 18px;margin:10px 0 16px}
.rg-row{display:flex;gap:12px;align-items:flex-start;padding:3px 0;font-size:.92rem}
.rg-row+.rg-row{border-top:1px dashed #cfd6ee}
.rg-k{flex:none;width:104px;font-weight:800;color:var(--accent);font-size:.82rem;padding-top:2px}
.rg ul{margin:2px 0;padding-left:18px;color:var(--soft)}
.rg ul li{margin:1px 0}
table{border-collapse:collapse;width:100%;margin:10px 0 6px;font-size:.9rem}
th,td{border:1px solid var(--bd);padding:8px 11px;text-align:left;vertical-align:top}
th{background:var(--soft-bg);font-weight:700;font-size:.84rem;color:var(--soft)}
table.lessons td.n{width:34px;text-align:center;font-variant-numeric:tabular-nums;color:var(--accent);font-weight:800}
table.lessons td.d{color:var(--soft)}
table.route td:first-child{font-weight:600;color:var(--ink);width:46%}
.chip{display:inline-block;font-size:.74rem;font-weight:700;color:var(--accent);background:var(--guide);
border:1px solid #dde3f6;padding:2px 10px;border-radius:999px;margin-left:8px;vertical-align:middle}
nav.toc{background:var(--soft-bg);border:1px solid var(--bd);border-radius:12px;padding:14px 20px;margin:18px 0}
nav.toc h3{margin:0 0 6px;font-size:1rem}
nav.toc ol{margin:0;padding-left:20px;columns:2;column-gap:30px}
nav.toc li{margin:3px 0}
.diagram{background:var(--soft-bg);border:1px solid var(--bd);border-radius:12px;padding:20px;text-align:center;margin:10px 0}
.diagram svg{max-width:100%;height:auto}
.legend{font-size:.82rem;color:var(--mute);margin-top:8px}
details{background:var(--soft-bg);border:1px solid var(--bd);border-radius:10px;padding:6px 16px;margin:12px 0}
details summary{cursor:pointer;font-weight:700;color:var(--ink);padding:6px 0}
.back-to-top{position:fixed;bottom:22px;right:22px;background:var(--accent);color:#fff;border-radius:999px;
padding:9px 15px;font-size:.85rem;font-weight:700;box-shadow:0 6px 18px rgba(0,0,0,.2)}
.back-to-top:hover{text-decoration:none;background:#4a4ac0}
footer{margin-top:40px;padding-top:18px;border-top:1px solid var(--bd2);color:var(--mute);font-size:.85rem}
@media print{.back-to-top{display:none}body{max-width:none}nav.toc ol{columns:1}}
@media (max-width:760px){nav.toc ol{columns:1}.rg-k{width:84px}}
"""

w("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>")
w("<meta name='viewport' content='width=device-width, initial-scale=1'>")
w("<title>AI 系統設計教學指南 — 課程地圖與閱讀路徑</title>")
w(f"<style>{CSS}</style></head><body>")

# Header
w("<header class='rpt' id='top'><h1>🧠 AI 系統設計教學指南</h1>")
w(f"<div class='meta'>產生時間 generated <code>{GEN_DATE}</code> ｜ 來源 source: "
  f"<code>ai-system-design-guide/</code>（README.md + 18 個章節目錄）｜ 報告型態：Explainer / How-to</div></header>")

# TOC
w("<nav class='toc' id='toc'><h3>目錄 Contents</h3><ol>")
w("".join(toc))
w("</ol></nav>")

# §1 Exec TL;DR
w("<section id='exec'><h2>§1. 重點摘要 Executive TL;DR</h2>")
w("<div class='banner'><div class='big'>18 教學章節 · 110+ 課程單元 · 20 實戰案例</div>"
  "<div class='sub'>模型版圖、定價與協定（MCP 2.0 / A2A）更新至 2026 年 5 月</div></div>")
w("<div class='stat-row'>"
  f"<div class='stat'><b>18</b><span>教學章節 Chapters</span></div>"
  f"<div class='stat'><b>{total_lessons}+</b><span>課程單元 Lessons</span></div>"
  f"<div class='stat'><b>{n_cases}</b><span>實戰案例 Case Studies</span></div>"
  f"<div class='stat'><b>2026</b><span>最新模型版圖</span></div></div>")
w("<p>這是一份持續更新的 <b>AI 系統設計實戰教學</b>，涵蓋 LLM 原理、RAG、代理系統、MCP / A2A 協定、"
  "推論優化、評估與面試準備。內容以「生產級取捨」與「真實失敗模式」為主軸，"
  "適合準備資深 / Staff AI 工程面試，或正在把 LLM 應用推上線的工程師。</p>")
w("<p><b>建議讀法：</b>先看 <a href='#howto'>§2 路由表</a> 與 <a href='#map'>§3 學習地圖</a>，"
  "依你的目標跳讀對應章節，<b>不必從頭線性讀完</b>。每個生命週期段落（§4–§8）開頭都有一個"
  "「Reader’s Guide」，先告訴你為什麼看、看什麼、結論是什麼。</p></section>")

# §2 How to read
w("<section id='howto'><h2>§2. 如何閱讀本報告</h2>")
w("<p>對照你「現在想解決的問題」，直接跳到對應章節：</p>")
w("<table class='route'><thead><tr><th>你的問題</th><th>該讀哪一段</th></tr></thead><tbody>")
for q, where in ROUTING:
    w(f"<tr><td>{esc(q)}</td><td>{esc(where)}</td></tr>")
w("</tbody></table></section>")

# §3 Learning map
w("<section id='map'><h2>§3. 學習地圖</h2>")
w(reader_guide(
    "一張圖看懂「依目標該走哪條路」，避免從第一章線性硬讀。",
    ["找到符合你當下目標的起點", "沿箭頭走兩步即可上手該主題", "五條主路徑可任選其一切入"],
    "五條主路徑——面試 / RAG / 代理 / 選模型 / 評估——挑一條開始。"))
w(f"<div class='diagram'>{svg}<div class='legend'>圖 1 ｜ 學習路徑地圖（tier-1 靜態 SVG，由 graphviz 預先算繪並內嵌；無 CDN 相依）</div></div>")
w("</section>")

# §4-§8 lifecycle stages
for anchor, no, head, prefixes, (why, focus, bottom) in STAGES:
    w(f"<section id='{anchor}'><h2>{no}. {esc(head)}</h2>")
    w(reader_guide(why, focus, bottom))
    for p in prefixes:
        zh, en, ic = CH[p]
        cnt = len(all_lessons[p])
        w(f"<h3><span class='ic'>{ic}</span>{p} · {esc(en)} <span style='color:var(--mute);font-weight:500'>{esc(zh)}</span>"
          f"<span class='chip'>{cnt} 課</span></h3>")
        w(lesson_table(p))
    w("</section>")

# §9 Appendix
w("<section id='appendix'><h2>§9. 附錄 Appendix</h2>")
w("<h3>A. 延伸資源與深入指南</h3>")
w("<table><thead><tr><th>資源</th><th>說明</th></tr></thead><tbody>")
for rel, name, desc in RESOURCES:
    w(f"<tr><td><a href='{esc(rel)}'>{esc(name)}</a></td><td class='d'>{esc(desc)}</td></tr>")
w("</tbody></table>")
w("<h3>B. 統計與產製資訊</h3>")
w("<details open><summary>來源與數據</summary>"
  f"<ul><li>教學章節：18（00–17）</li>"
  f"<li>課程單元：{total_lessons}+（不含章節 README）</li>"
  f"<li>實戰案例：{n_cases}（章節 16）</li>"
  f"<li>產生時間：{GEN_DATE}</li>"
  "<li>內容來源：本 repo 各章節 <code>*.md</code> 的 H1 標題與首段描述，自動擷取彙整</li>"
  "<li>圖 1 產製：<code>diagrams/learning-map.dot</code> → <code>dot -Tsvg</code> → 內嵌（符合 arvinsa-html-report：tier-1 靜態 SVG、禁用 CDN、單檔自包含）</li>"
  "<li>本報告規範：依 <code>arvinsa-html-report</code> skill（Explainer / How-to 原型：backbone + Reader’s Guide）</li>"
  "</ul></details>")
w("<details><summary>C. 互動版入口</summary>"
  "<p>另有一份互動式入口頁 <a href='index.html'>index.html</a>（含即時搜尋、深色模式、頁內 Markdown 閱讀器），"
  "兩者用途不同：<b>本報告</b>適合線性 / 列印 / 離線閱讀與導覽；<b>index.html</b> 適合互動瀏覽。</p></details>")
w("</section>")

w("<footer>🧠 AI 系統設計教學指南 ｜ 內容由 <a href='https://github.com/ombharatiya'>Om Bharatiya</a> 維護（MIT License）"
  " ｜ 本教學報告依 arvinsa-html-report 規範產製。</footer>")
w("<a href='#toc' class='back-to-top'>↑ 目錄</a>")
w("</body></html>")

out = os.path.join(ROOT, "ai-system-design-guide.html")
with open(out, "w", encoding="utf-8") as f:
    f.write("".join(P))
print("WROTE", out)
print("lessons:", total_lessons, "cases:", n_cases)
