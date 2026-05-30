# 2026 年的工具使用與電腦代理（Computer Agent）全景

AI 代理與外部世界互動的方式已經歷劇烈轉變。在 2024 年，「工具使用」指的是模型發出一個 JSON function call，再由你的後端去執行。如今我們已經有了完整的自主代理（autonomous agent），它們會 clone 程式碼倉庫、執行 shell 指令、透過截圖控制桌面，甚至在 WhatsApp 上傳訊息給你，這一切都透過像 MCP 這樣的標準化協定來協調。本章將描繪這些工具的全景、它們的架構，以及讓它們彼此區別的設計決策。

## 目錄

- [生態系概觀](#ecosystem-overview)
- [類別分類法](#category-taxonomy)
- [OpenClaw：爆紅的個人 AI 代理](#openclaw)
- [OpenHands：自主開發者代理](#openhands)
- [Open Interpreter：本地程式碼執行](#open-interpreter)
- [Claude Computer Use：以視覺為基礎的自動化](#claude-computer-use)
- [Claude Code：終端機代理](#claude-code)
- [IDE 代理：Cursor、Windsurf、Cline](#ide-agents)
- [比較矩陣](#comparison-matrix)
- [市場趨勢與採用情況（2026）](#market-trends)
- [系統設計面試切入點](#interview-angle)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 生態系概觀

2026 年的工具使用生態系已收斂為四種架構模式，各自針對不同程度的自主性、安全性與整合深度進行最佳化：

```
+-----------------------------------------------------------------------+
|                     2026 Tool-Use Ecosystem                           |
+-----------------------------------------------------------------------+
|                                                                       |
|  +-------------------+  +-------------------+  +-------------------+  |
|  |  LOCAL AGENTS     |  |  CLOUD AGENTS     |  |  IDE AGENTS       |  |
|  |                   |  |                   |  |                   |  |
|  |  OpenClaw         |  |  Claude Code      |  |  Cursor           |  |
|  |  Open Interpreter |  |  OpenAI Codex     |  |  Windsurf         |  |
|  |  OpenHands (local)|  |  OpenHands Cloud  |  |  Cline            |  |
|  |  LM Studio Agent  |  |  Google Jules     |  |  GitHub Copilot   |  |
|  +-------------------+  +-------------------+  +-------------------+  |
|                                                                       |
|  +-------------------+  +-------------------+  +-------------------+  |
|  |  COMPUTER-USE     |  |  MCP SERVERS      |  |  MESSAGING AGENTS |  |
|  |                   |  |                   |  |                   |  |
|  |  Claude Computer  |  |  10,000+ servers  |  |  OpenClaw (multi) |  |
|  |  Use API          |  |  97M monthly SDK  |  |  Custom bots      |  |
|  |  Open Interpreter |  |  downloads        |  |  via MCP bridges  |  |
|  |  (Computer API)   |  |                   |  |                   |  |
|  +-------------------+  +-------------------+  +-------------------+  |
+-----------------------------------------------------------------------+
```

2026 年的關鍵洞見是：這些類別正在彼此收斂。Claude Code 是一個在本地端執行的雲端代理。OpenClaw 是一個連接到雲端 LLM 的本地代理。Cursor 是一個帶有雲端側 Background Agent 的 IDE 代理。界線正在模糊化，而真正重要的是底層的**架構模式**（下一章會涵蓋）。

---

## 類別分類法

### 1. 本地代理（自架、由使用者掌控）

在使用者自有硬體上執行的代理。LLM 呼叫可能送往雲端，但代理行程、記憶與工具執行都在本地端。

**關鍵特性：**
- 對使用者機器擁有完整的檔案系統存取權
- 持久化記憶儲存在本地（SQLite、JSON、Markdown）
- 使用者擁有所有資料；不會被供應商鎖定（vendor lock-in）
- 安全責任完全落在運營者身上

**範例：** OpenClaw、Open Interpreter、本地部署的 OpenHands

### 2. 雲端代理（供應商代管、由 API 驅動）

在供應商管理的雲端環境中執行的代理。程式碼執行發生在沙箱化的 VM 或容器中。

**關鍵特性：**
- 沙箱化執行（Docker、Firecracker VM、E2B）
- 沒有本地檔案系統存取權（在 clone 下來的倉庫上運作）
- 由供應商處理擴展、安全與基礎設施
- 採用按用量計費或訂閱制定價

**範例：** Claude Code（雲端模式）、OpenAI Codex、Google Jules、OpenHands Cloud

### 3. IDE 代理（與編輯器整合、具上下文感知）

直接內嵌在程式碼編輯器中的代理。它們對專案結構、開啟中的檔案以及編輯器狀態有深入的理解。

**關鍵特性：**
- 與編輯器 UI 緊密整合（行內 diff、tab 補全）
- 透過 embedding 或 AST 解析建立程式碼庫索引
- 在分支上非同步運作的 background agent
- 針對開發者工作流程最佳化，而非一般性自動化

**範例：** Cursor（Agent Mode + Background Agents）、Windsurf（Cascade）、Cline、GitHub Copilot

### 4. 電腦使用代理（以視覺為基礎、由 GUI 驅動）

以人類的方式與軟體互動的代理——透過觀看截圖並點擊。

**關鍵特性：**
- 模型看截圖，決定滑鼠／鍵盤動作
- 可與任何應用程式協作（不需要 API）
- 延遲較高（截圖—動作迴圈每一步約 1-3 秒）
- 為了安全需要沙箱化環境（VM + VNC）

**範例：** Claude Computer Use API、Open Interpreter Computer API

---

## OpenClaw：爆紅的個人 AI 代理

### 它是什麼

OpenClaw 是一個自架、開源的個人 AI 助理，由奧地利開發者 Peter Steinberger 所創。它最初於 2025 年 11 月以「Clawdbot」之名發布，並於 2026 年 1 月更名為 OpenClaw。它在不到五個月內從 0 暴增到 346,000 個 GitHub star，並於 2026 年 3 月 3 日超越 React，成為 GitHub 上 star 數最多的軟體專案。

**數字一覽（2026 年 5 月）：**
- 346,000+ 個 GitHub star
- 320 萬名活躍使用者
- 500,000+ 個運行中的執行個體
- ClawHub 上 44,000+ 個社群技能（skill）
- 專案網站每月 3,800 萬名訪客
- 24+ 個訊息平台整合

### 它如何運作

OpenClaw 的架構有六個核心元件：

```
+-------------------------------------------------------------------+
|                      OpenClaw Architecture                        |
+-------------------------------------------------------------------+
|                                                                   |
|  +-----------+     +-----------+     +----------+                 |
|  |  Gateway  |---->|  LLM      |---->| PI Agent |                 |
|  |           |     |  (Brain)  |     | (Exec)   |                 |
|  +-----------+     +-----------+     +----------+                 |
|       ^                  |                |                       |
|       |                  v                v                       |
|  +-----------+     +-----------+     +----------+                 |
|  | Channels  |     | SOUL.md   |     | Skills   |                 |
|  | (24+)     |     | (Identity)|     | (44K+)   |                 |
|  +-----------+     +-----------+     +----------+                 |
|                          |                                        |
|                          v                                        |
|                    +-----------+                                  |
|                    | Memories  |                                  |
|                    | (Persist) |                                  |
|                    +-----------+                                  |
+-------------------------------------------------------------------+
```

**1. Gateway**：訊息進出層。連接到 WhatsApp（透過 Baileys）、Telegram、Discord、Slack、Signal、iMessage、Microsoft Teams、Matrix 以及 16+ 個其他平台。同時支援私訊（DM）與群組對話，並以提及（mention）為基礎觸發啟用。

**2. LLM（大腦）**：在設計上與模型無關（model-agnostic）。支援 GPT-4o、Claude、Gemini、DeepSeek，或透過 Ollama 使用本地模型。由使用者挑選模型；架構本身並不在意是哪一個。

**3. PI Agent（Process Interactor，行程互動器）**：一個小型執行階段（runtime），讓 LLM 能在主機系統上建立、編輯、執行與刪除檔案。LLM 產生程式碼，PI Agent 將其儲存，接著執行。這是代理的「雙手」。

**4. SOUL.md（身分層）**：一個純 Markdown 檔案，定義代理的個性、溝通風格、價值觀與行為護欄（guardrail）。在工作階段開始時載入並注入到 system prompt。每個代理執行個體都會先讀取 SOUL.md——它「把自己讀進存在之中」。

**5. Skills（外掛系統）**：賦予代理新能力的擴充功能。ClawHub 上已存在超過 44,000 個社群技能。技能遵循 AgentSkills 規範，可被打包、限定於工作區（workspace-local），或全域安裝。

**6. Memories（持久化上下文）**：儲存在本地的長期記憶。代理會跨多次對話累積關於使用者的上下文。結合 SOUL.md，這讓每個代理在所有訊息平台上都擁有一致的個性。

### 工作區檔案

| 檔案 | 用途 |
|------|------|
| `SOUL.md` | 代理的個性、語氣、價值觀、護欄 |
| `AGENTS.md` | 操作指令、工具配置 |
| `HEARTBEAT.md` | 排程的自主動作（類似 cron） |
| `Memories/` | 跨多次對話的持久化上下文 |

### 安全疑慮

OpenClaw 的急速成長已超出其安全實務的腳步。截至 2026 年 5 月，已有超過 135,000 個執行個體暴露在公開網際網路上，其中許多仍使用預設配置。ClawHub 技能市集的安全監管極為薄弱：技能是帶有選擇性 TypeScript 的 Markdown，容易建立與安裝，也容易遭到濫用。對於任何要將 OpenClaw 部署到正式環境的人來說，這是一項關鍵的設計考量。

---

## OpenHands：自主開發者代理

### 它是什麼

OpenHands（前身為 OpenDevin）是一個開源的自主 AI 軟體工程師。採用 MIT 授權，它能修改程式碼、執行指令、瀏覽網頁，並與 API 互動。不同於那些只會建議程式碼片段的工具，OpenHands 會 clone 倉庫、執行終端機指令、跑測試，並在沙箱化的 Docker 容器內除錯。

### 架構：事件串流（Event-Stream）+ 沙箱化執行階段

```
+-------------------------------------------------------------------+
|                     OpenHands Architecture                        |
+-------------------------------------------------------------------+
|                                                                   |
|  +------------------+                                             |
|  |   User / API     |                                             |
|  +--------+---------+                                             |
|           |                                                       |
|           v                                                       |
|  +--------+---------+     +------------------+                    |
|  |  Agent Controller |<--->|  Event Stream    |                   |
|  |  (CodeAct 1.0)   |     |  Hub             |                   |
|  +--------+---------+     +--------+---------+                    |
|           |                        |                              |
|           v                        v                              |
|  +--------+---------+     +--------+---------+                    |
|  |  Action Dispatch  |     |  Observation     |                   |
|  |                   |     |  Collector       |                   |
|  |  - CmdRunAction   |     |                  |                   |
|  |  - FileWriteAction|     |  - CmdOutput     |                   |
|  |  - BrowseURLAction|     |  - FileContent   |                   |
|  |  - CodeAction     |     |  - BrowserState  |                   |
|  +--------+---------+     +------------------+                    |
|           |                                                       |
|           v                                                       |
|  +--------+--------------------------------------------------+    |
|  |              Docker Sandbox (Per Session)                 |    |
|  |                                                           |    |
|  |  +----------+  +----------+  +----------+                |    |
|  |  | Terminal  |  |  Python  |  | Browser  |                |    |
|  |  | (bash)   |  | (stateful)|  | (BrowserGym)             |    |
|  |  +----------+  +----------+  +----------+                |    |
|  +-----------------------------------------------------------+    |
+-------------------------------------------------------------------+
```

**關鍵架構決策：**
- **事件串流架構**：所有代理—環境的互動都以具型別的事件（typed event）形式流經一個中央 hub。代理分析對話狀態並產生 Action；沙箱則產生 Observation。
- **每個工作階段一個 Docker 容器**：每個工作階段都會取得自己獨立的容器，具備完整的 OS 能力。容器與主機相互隔離。
- **CodeAct 1.0**：預設的代理範本。將 LLM 推理嵌入一個統一的編碼控制平面（control plane），並維持工作階段層級的專案上下文。
- **BrowserGym 整合**：代理能透過宣告式基礎操作（DOM 操作、導覽）進行瀏覽器自動化。
- **SDK 可組合性**：OpenHands SDK 是一個 Python 函式庫。你可以用程式碼定義代理、在本地端執行，或在雲端擴展到數千個。

**近期更新（v1.6.0，2026 年 3 月）：**
- 支援 Kubernetes 以編排代理工作階段
- Planning Mode beta，用於多步驟任務拆解
- 來自 188+ 位貢獻者的 2,100+ 筆貢獻

---

## Open Interpreter：本地程式碼執行

### 它是什麼

Open Interpreter 是一個本地程式碼執行代理，提供類似 ChatGPT 的終端機介面。它不會把程式碼秀出來再請你執行，而是先徵求許可，接著直接在你的機器上執行，並對你的本地檔案擁有完整存取權。

### 架構

```
+-------------------------------------------------------------------+
|                  Open Interpreter Architecture                    |
+-------------------------------------------------------------------+
|                                                                   |
|  +------------------+                                             |
|  |  Terminal UI      |                                            |
|  |  (ChatGPT-like)  |                                            |
|  +--------+---------+                                             |
|           |                                                       |
|           v                                                       |
|  +--------+---------+     +------------------+                    |
|  |  Core Engine      |<--->|  LLM Provider   |                   |
|  |                   |     |  (100+ models)  |                    |
|  |  - NL to Code     |     |  GPT, Claude,   |                   |
|  |  - Permission     |     |  Ollama, LM     |                   |
|  |    Gate            |     |  Studio, etc.   |                   |
|  +--------+---------+     +------------------+                    |
|           |                                                       |
|           v                                                       |
|  +--------+---------+                                             |
|  |  Code Executor    |                                            |
|  |                   |                                            |
|  |  - Python         |                                            |
|  |  - JavaScript     |                                            |
|  |  - Shell/Bash     |                                            |
|  |  - AppleScript    |                                            |
|  +--------+---------+                                             |
|           |                                                       |
|           v                                                       |
|  +--------+---------+                                             |
|  |  Computer API     |                                            |
|  |  (GUI Control)    |                                            |
|  |                   |                                            |
|  |  - Screen capture |                                            |
|  |  - Mouse/Keyboard |                                            |
|  |  - Icon detection |                                            |
|  +-------------------+                                            |
+-------------------------------------------------------------------+
```

**關鍵特性：**
- **模型彈性**：可與 100+ 個 LLM 協作。使用 GPT-4o 或 Claude 以獲得最大能力，或為了隱私完全離線地以 Ollama 與 LM Studio 執行。
- **許可閘門（permission gate）**：每一次程式碼執行都需要使用者核准（對於受信任的工作流程可停用）。
- **Computer API**：除了程式碼執行之外，Open Interpreter 還能看見你的螢幕、辨識 UI 元素，並控制你的滑鼠與鍵盤——將它從一個程式碼直譯器提升為一個電腦自動化代理。
- **預設不沙箱化**：直接在主機上執行。這是為了追求最大能力而刻意做出的設計選擇，但也意味著一段糟糕的 LLM 輸出可能損壞你的系統。Docker 沙箱化是選擇性的。

### 何時該使用 Open Interpreter

最適合用於資料分析、檔案操作，以及你想為本地機器配上對話式介面的系統管理任務。並不適合正式環境部署或不受信任的環境。

---

## Claude Computer Use：以視覺為基礎的自動化

### 它是什麼

Claude Computer Use 是 Anthropic 的一項 API 功能，讓 Claude 能透過截圖、滑鼠移動、鍵盤輸入與應用程式互動來控制桌面。它於 2024 年 10 月以 beta 形式推出，此後已大幅演進。截至 2026 年 5 月，Sonnet 4.6 在 OSWorld-Verified 上達到 72.5%，相較推出時的 14.9% 大幅提升，而 Opus 4.7 則在代理式編碼基準（agentic coding benchmark）上更進一步（SWE-bench Pro 達 64.3%）。

### 視覺—動作迴圈（Vision-Action Loop）

```
+-------------------------------------------------------------------+
|              Claude Computer Use: Vision-Action Loop               |
+-------------------------------------------------------------------+
|                                                                   |
|  Step 1: OBSERVE          Step 2: REASON          Step 3: ACT    |
|  +----------------+       +----------------+      +------------+ |
|  |  Take          |       |  Analyze       |      |  Execute   | |
|  |  Screenshot    |------>|  Screenshot    |----->|  Action    | |
|  |  (base64 PNG)  |       |  + Task Goal   |      |  (click,   | |
|  |                |       |  + History      |      |  type,     | |
|  +----------------+       +----------------+      |  scroll)   | |
|                                                    +------+-----+ |
|                                                           |       |
|          +------------------------------------------------+       |
|          |                                                        |
|          v                                                        |
|  +-------+--------+                                               |
|  |  Wait + Take   |                                               |
|  |  New Screenshot|-------> (Loop back to Step 1)                 |
|  +----------------+                                               |
|                                                                   |
+-------------------------------------------------------------------+
```

### 可用工具

| 工具 | 能力 | 備註 |
|------|------------|-------|
| `computer` | 滑鼠、鍵盤、截圖 | 完整的桌面 GUI 控制 |
| `bash` | 執行 shell 指令 | 跨多輪維持的持久化工作階段 |
| `text_editor` | 讀取／寫入／編輯檔案 | 支援 view、create、str_replace |

### 2026 年的強化

- **Zoom Action（縮放動作）**：在點擊之前以高解析度檢視小型 UI 元素。降低在密集介面上的誤點率。
- **可於 Claude Cowork 與 Claude Code 中使用**：對 Pro 與 Max 使用者開放的研究預覽（research preview），在執行破壞性動作之前需要人工確認。
- **沙箱化最佳實務**：永遠在沙箱化的 VM 中執行（Docker + VNC，或 E2B 雲端）。絕不要把電腦使用的存取權交給未沙箱化的主機。

### 效能軌跡

| 日期 | OSWorld 分數 | 關鍵里程碑 |
|------|---------------|---------------|
| Oct 2024 | 14.9% | Beta 推出（Claude 3.5 Sonnet） |
| Mid 2025 | ~40% | Claude 3.7 改進 |
| Q1 2026 | 72.5% | Sonnet 4.6、Zoom Action |

---

## Claude Code：終端機代理

### 它是什麼

Claude Code 是 Anthropic 那個常駐於終端機的代理式編碼工具。它會讀取你的程式碼庫、編輯檔案、執行指令，並與開發工具整合。它於 2025 年 5 月公開推出，並在 2026 年 2 月前突破 25 億美元 ARR。

### 架構

Claude Code 是一個 TypeScript 終端機代理，它循環經過三個階段：

```
+-------------------------------------------------------------------+
|                   Claude Code Agent Loop                          |
+-------------------------------------------------------------------+
|                                                                   |
|  +------------------+                                             |
|  |  1. GATHER       |  Read files, grep codebase, glob search,   |
|  |     CONTEXT      |  check git status, analyze structure        |
|  +--------+---------+                                             |
|           |                                                       |
|           v                                                       |
|  +--------+---------+                                             |
|  |  2. TAKE         |  Edit files, run bash, write new files,     |
|  |     ACTION       |  create commits, spawn subagents            |
|  +--------+---------+                                             |
|           |                                                       |
|           v                                                       |
|  +--------+---------+                                             |
|  |  3. VERIFY       |  Run tests, check build, review diffs,     |
|  |     RESULTS      |  validate output                            |
|  +--------+---------+                                             |
|           |                                                       |
|           +--------> (Loop back to Step 1 if not done)            |
|                                                                   |
+-------------------------------------------------------------------+

Built-in Tools: bash, read, write, edit, glob, grep, browser,
                subagent, notebook, web_search, web_fetch
```

**關鍵架構特性：**
- 一個帶有豐富工具調色盤（tool palette）的代理迴圈
- 透過 slash command 與 CLAUDE.md 進行的隨選技能載入（on-demand skill loading）
- 針對長工作階段的上下文壓縮（1M+ token 上下文）
- 為了平行工作流而生成子代理（subagent）
- 為了平行分支執行而做的 worktree 隔離
- 權限治理（針對工具的 allow/deny 規則）
- 帶有依賴圖（dependency graph）的任務系統
- 用於自訂自動化的 hook（commit 前／後、檔案變更）

---

## IDE 代理：Cursor、Windsurf、Cline

### Cursor

Cursor 是一個帶有深度 AI 整合的 VS Code 分支（fork）。2.0 版（2026 年初）引入了：
- **Agent Mode**：採用 20 倍規模化的強化學習（reinforcement learning）進行多檔案編輯
- **Background Agents**：在雲端 VM 中 clone 你的倉庫、自主運作，並在完成時開啟 PR
- **Mission Control**：用於管理平行代理工作流的儀表板
- **市場**：20 億美元年化營收、200 萬+ 使用者、100 萬+ 付費客戶，半數的《財星》500 大企業（Fortune 500）採用

### Windsurf

Windsurf（前身為 Codeium，於 2025 年 7 月被 Cognition 以 2.5 億美元收購）具備：
- **Cascade**：一個多步驟 AI 代理，能分析專案結構、協調跨檔案變更，並從錯誤中自我復原
- **專有模型**：SWE-1.5（比 Sonnet 4.5 快 13 倍）與 Fast Context
- **Codemaps**：由 AI 驅動的視覺化程式碼導覽
- **跨 IDE 外掛**：適用於 40+ 個 IDE（JetBrains、Vim、NeoVim、XCode）

### Cline

Cline 是一個 VS Code 擴充功能，以一個完整的代理而非自動補全工具的形式運作。它會採取一連串步驟、評估結果、修正自身的錯誤，然後繼續。比 Cursor 或 Windsurf 更自主，但打磨程度較低。

### IDE 代理架構比較

```
+-------------------------------------------------------------------+
|                 IDE Agent Architecture Patterns                   |
+-------------------------------------------------------------------+
|                                                                   |
|  Cursor:                                                          |
|  [Editor] --> [Agent Mode] --> [Multi-file RL] --> [Apply Diffs]  |
|                    |                                               |
|                    +--> [Background Agent] --> [Cloud VM] --> [PR] |
|                                                                   |
|  Windsurf:                                                        |
|  [Editor] --> [Cascade Agent] --> [RAG Codebase] --> [Apply Edits]|
|                    |                                               |
|                    +--> [SWE-1.5 Model] --> [Fast Context]        |
|                                                                   |
|  Cline:                                                           |
|  [Editor] --> [Agent Loop] --> [Evaluate] --> [Self-Fix] --> [Act]|
|                    |                                               |
|                    +--> [Any LLM Provider] --> [Tool Calls]       |
+-------------------------------------------------------------------+
```

---

## 比較矩陣

| 特性 | OpenClaw | OpenHands | Open Interpreter | Claude Computer Use | Claude Code | Cursor |
|---------|----------|-----------|-----------------|-------------------|-------------|--------|
| **類型** | 本地代理 | 開發代理 | 本地程式碼執行 | 視覺自動化 | 終端機代理 | IDE 代理 |
| **授權** | AGPL-3.0 | MIT | AGPL-3.0 | 專有 API | 專有 | 專有 |
| **GitHub Star** | 346K | 51K+ | 58K+ | N/A（API） | 42K+ | N/A |
| **沙箱化** | 否（主機） | 是（Docker） | 否（主機） | 需要 VM | 可配置 | 是（BG agent） |
| **LLM 支援** | 任意（與模型無關） | 任意 | 100+ 個模型 | 僅限 Claude | 僅限 Claude | 多模型 |
| **GUI 控制** | 否 | 是（BrowserGym） | 是（Computer API） | 是（原生） | 透過 computer-use | 否 |
| **程式碼執行** | 是（PI Agent） | 是（容器） | 是（本地） | 是（bash 工具） | 是（bash） | 是（終端機） |
| **訊息傳遞** | 24+ 個平台 | Web UI／API | 終端機 | API | 終端機／IDE | 編輯器 |
| **記憶** | 持久化（本地） | 以工作階段為基礎 | 以工作階段為基礎 | 每次對話 | 工作階段 + CLAUDE.md | 限定於專案 |
| **MCP 支援** | 社群技能 | 有限 | 否 | 透過 Claude | 原生 | 持續增長中 |
| **最適合** | 個人助理 | 自主開發 | 資料分析 | GUI 自動化 | 專業開發 | IDE 工作流 |
| **風險等級** | 高（未沙箱化） | 低（已沙箱化） | 高（未沙箱化） | 中（需要 VM） | 中 | 低 |

---

## 市場趨勢與採用情況（2026）

### 數字

- **MCP 生態系**：10,000+ 個活躍 server、每月 9,700 萬次 SDK 下載
- **Gartner 預測**：到 2026 年底，40% 的企業應用將整合 AI 代理（相較於 2025 年初的不到 5%）
- **OpenClaw**：史上最快達到 30 萬個 GitHub star 的專案（不到 5 個月）
- **Claude Code**：到 2026 年 2 月達到 25 億美元 ARR——史上最快達到 10 億美元的企業軟體產品
- **Cursor**：20 億美元年化營收，半數的《財星》500 大企業

### 關鍵趨勢

**1. 代理類型的收斂**：本地、雲端與 IDE 代理之間的界線正在消解。Claude Code 在本地端執行但使用雲端模型。Cursor 的 Background Agents 在雲端執行。OpenClaw 可連接到任何 LLM。整體趨勢正朝向一種能在任何環境中運作的通用代理架構演進。

**2. MCP 作為通用工具層**：MCP 已成為工具整合的標準，獲得 Anthropic、OpenAI、Google 以及數百家工具供應商採用。2026 年的藍圖聚焦於企業就緒度：身分傳遞（identity propagation）、工具預算（tool budgeting）、結構化錯誤語意（structured error semantics），以及稽核軌跡（audit trail）。

**3. 沙箱化成為不可妥協的事項**：OpenClaw 的安全危機（135,000 個暴露的執行個體）已推動整個產業走向「預設沙箱化」的架構。新的代理被期望要開箱即提供隔離。

**4. 成本最佳化成為第一級關注事項**：Plan-and-Execute 模式（一個能力強的模型負責規劃，較便宜的模型負責執行）可將成本降低 90%。這是代理式版本的雲端成本最佳化。

**5. 背景與非同步代理**：Cursor 的 Background Agents 與 Claude Code 的子代理生成，代表著從同步、互動式的代理，轉向自主、非同步、完成時通知你的工作者（worker）的一種轉變。

---

## 系統設計面試切入點

在系統設計面試中被問到工具使用代理時，請聚焦於這些面向：

**1. 安全模型**：執行有沙箱化嗎？憑證（credential）如何管理？如果 LLM 產生惡意程式碼會發生什麼事？（OpenClaw 的 AGPL 授權與未沙箱化執行，對比 OpenHands 的 Docker 隔離，是一個絕佳的比較點。）

**2. 狀態管理**：代理如何跨多次工具呼叫維持上下文？以工作階段為基礎（OpenHands）、持久化記憶（OpenClaw），還是以檔案為基礎（Claude Code 的 CLAUDE.md）？

**3. 工具探索（Tool Discovery）**：靜態 manifest（舊作法）、透過 MCP 的動態探索，還是技能市集（OpenClaw ClawHub）？

**4. 延遲預算**：function calling（每次工具呼叫 50-200ms），對比以視覺為基礎的自動化（每次截圖—動作迴圈 1-3 秒）。這對 UX 有何影響？

**5. 失敗處理**：當一次工具呼叫失敗時會發生什麼事？重試？退回備援（fallback）？還是 human-in-the-loop？在放棄之前要重試幾次？

---

## 面試題

### Q：你的團隊想打造一個內部 AI 助理。你應該以 OpenClaw、OpenHands 為基礎來打造，還是用 Claude Code + MCP 客製化自建？

**有力的回答：**
這取決於使用情境與安全需求。OpenClaw 針對帶有訊息整合的個人助理做了最佳化——如果目標是一個具備持久化個性的 Slack/Teams 機器人，它會是理想選擇。但它未沙箱化的執行與 AGPL 授權會帶來企業層面的疑慮。OpenHands 較適合自主開發任務——它的 Docker 沙箱化與 MIT 授權對企業很友善。對於一個客製化的內部工具，搭配 MCP server 的 Claude Code 能給你最大的掌控權：你可以精確定義有哪些工具可用、在你自己的基礎設施中執行它們，並從 MCP 的標準化探索與認證（auth）中受益。決策樹是：以訊息為先？選 OpenClaw。開發自動化？選 OpenHands。客製化企業工具？選 MCP + 你自己的代理迴圈。

### Q：你會如何設計一個讓非技術使用者能用 AI 自動化桌面任務的系統？

**有力的回答：**
我會採用以視覺為基礎的電腦使用模式（Claude Computer Use 或類似工具）。關鍵設計決策：(1) 永遠在沙箱化的 VM 中執行，讓代理無法損壞使用者實際的機器。(2) 在任何破壞性動作之前——刪除檔案、提交表單、購買——實作一個 human-in-the-loop 確認步驟。(3) 使用 Zoom Action 模式以降低在密集 UI 上的誤點。(4) 設定 token／成本上限以防止失控的迴圈。(5) 把所有動作記錄為稽核軌跡。主要的取捨在於延遲——每個截圖—動作步驟需要 1-3 秒——但這種作法可與任何應用程式協作，而不需要 API。對於更高速的工作流程，可將電腦使用與 function calling 結合，用於那些有 API 的應用程式。

### Q：為什麼 OpenClaw 的成長速度比史上任何開源專案都快？這告訴了你關於市場的什麼事？

**有力的回答：**
有三項因素。(1) **零摩擦上手**：OpenClaw 連接到人們本來就在用的訊息平台（WhatsApp、Telegram）。使用者不需要學習一個新介面。(2) **SOUL.md 個人化**：能賦予你的代理一個自訂個性，這創造了情感依附與病毒式傳播——人們會分享他們的代理。(3) **與模型無關的架構**：使用者不會被鎖定在單一 LLM 供應商，這降低了成本並提高了彈性。市場訊號在於，代理的「介面」比底層模型更重要。人們想要的是會在他們所在之處與他們相遇的代理（訊息應用程式，而非 Web UI）。另一面則是：在沒有安全投資下的急速成長會導致像 135,000 個暴露執行個體這樣的危機，對任何開源代理專案而言這都是一則警世故事。

### Q：比較 AI 代理的沙箱化與未沙箱化執行。你會在什麼時候選擇哪一種？

**有力的回答：**
沙箱化（Docker/VM）：用於不受信任的程式碼執行、多租戶（multi-tenant）系統，或任何正式環境部署。OpenHands 在這方面做得很好——每個工作階段都有自己的 Docker 容器。取捨在於設定的複雜度與效能負擔。未沙箱化（主機存取）：僅用於單一使用者、受信任且使用者正在旁觀的環境。Open Interpreter 與 OpenClaw 採取這種作法以追求最大能力。風險在於一段糟糕的 LLM 輸出可能損壞主機系統。2026 年的共識是「預設沙箱化」，並為進階使用者保留逃生口（escape hatch）。在面試中，永遠要提到沙箱邊界是一項安全決策，而不只是一項便利性決策。

---

## 參考資料

- OpenClaw GitHub Repository and Documentation (2025-2026)
- OpenHands Documentation and SDK Reference (2025-2026)
- Open Interpreter GitHub Repository (2024-2026)
- Anthropic. "Computer Use Tool Documentation" (2024-2026)
- Anthropic. "Claude Code Overview" (2025-2026)
- MCP Specification 2025-11-25 and 2026 Roadmap
- Gartner. "AI Agent Adoption Projections" (2025-2026)
- Cursor, Windsurf, and Cline official documentation (2025-2026)

---

*下一篇：[工具使用代理的架構模式](02-architecture-patterns.md)*
