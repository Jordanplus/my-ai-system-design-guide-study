# 工具使用代理的架構模式

2026 年的每一個工具使用代理 -- 從 OpenClaw 到 Claude Code 再到 Cursor 的 Background Agents -- 都建立在少數幾種核心架構模式之上。理解這些模式能讓你從第一性原理出發來設計代理，而不是直接複製特定工具。本章將逐一拆解每種模式，搭配詳細的圖解、程式碼範例、權衡取捨，以及何時該採用哪一種的指引。

## 目錄

- [模式 1：函式／工具呼叫](#pattern-1-functiontool-calling)
- [模式 2：以視覺為基礎的自動化](#pattern-2-vision-based-automation)
- [模式 3：本地程式碼執行](#pattern-3-local-code-execution)
- [模式 4：多代理工具編排](#pattern-4-multi-agent-tool-orchestration)
- [沙箱化 vs. 非沙箱化執行](#sandboxed-vs-unsandboxed-execution)
- [跨工具呼叫的狀態管理](#state-management-across-tool-calls)
- [錯誤處理與重試模式](#error-handling-and-retry-patterns)
- [MCP 整合模式](#mcp-integration-patterns)
- [架構決策樹](#architecture-decision-tree)
- [系統設計面試切入角度](#system-design-interview-angle)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 模式 1：函式／工具呼叫

在生產環境中部署最廣泛的模式。LLM 決定要呼叫哪個工具以及帶入什麼引數；由框架執行該呼叫；結果再被回饋到對話中，供下一個推理步驟使用。

### 架構

```
+-------------------------------------------------------------------+
|              Function/Tool Calling Pattern                        |
+-------------------------------------------------------------------+
|                                                                   |
|  +------------------+                                             |
|  |  User Message     |                                            |
|  +--------+---------+                                             |
|           |                                                       |
|           v                                                       |
|  +--------+---------+     +------------------+                    |
|  |  LLM Reasoning   |---->|  Tool Selection  |                   |
|  |                   |     |                  |                    |
|  |  "I need to look  |     |  tool: search_db |                   |
|  |   up the order"  |     |  args: {id: 42}  |                    |
|  +-------------------+     +--------+---------+                   |
|                                     |                             |
|                                     v                             |
|                            +--------+---------+                   |
|                            |  Tool Executor   |                   |
|                            |  (Framework)     |                   |
|                            |                  |                   |
|                            |  Validates args  |                   |
|                            |  Calls function  |                   |
|                            |  Returns result  |                   |
|                            +--------+---------+                   |
|                                     |                             |
|                                     v                             |
|                            +--------+---------+                   |
|                            |  Result Injected |                   |
|                            |  into Context    |                   |
|                            |                  |                   |
|                            |  {status: "shipped",                 |
|                            |   tracking: "1Z..."} |               |
|                            +--------+---------+                   |
|                                     |                             |
|                                     v                             |
|                            +--------+---------+                   |
|                            |  LLM Generates   |                   |
|                            |  Final Response  |                   |
|                            +------------------+                   |
+-------------------------------------------------------------------+
```

### 三個步驟的細節

**步驟 1 -- 結構描述呈現（Schema Presentation）**：模型會收到一份描述可用工具的 JSON schema。在 2026 年，最佳實務是使用 Dynamic Manifests，根據使用者的意圖只擷取相關的工具，而不是一開始就載入所有工具的 schema。

**步驟 2 -- 意圖與擷取（Intent and Extraction）**：模型輸出一個結構化的工具呼叫。這不是自由格式的文字；而是一個帶有 `tool_name` 與 `arguments` 的 JSON 物件，框架可以對其進行確定性的解析。

**步驟 3 -- 執行與情境化（Execution and Contextualization）**：框架驗證引數（使用 Pydantic、Zod 或類似工具），呼叫該函式，並將結果以角色為 `tool` 的新訊息形式回注到對話中。

### 程式碼範例：MCP Server + Client

```python
# MCP Server: defines a tool with strict schema
from mcp.server import Server
from pydantic import BaseModel, Field

server = Server("order-service")

class OrderLookup(BaseModel):
    """Look up an order by ID. DO NOT use for cancelled orders."""
    order_id: str = Field(..., description="The order UUID")

@server.tool()
async def lookup_order(args: OrderLookup) -> dict:
    order = await db.orders.find_one({"id": args.order_id})
    if not order:
        return {"error": "Order not found", "suggestion": "Check order ID format"}
    return {"status": order["status"], "tracking": order.get("tracking_number")}
```

```python
# MCP Client: agent discovers tools dynamically, calls them, feeds results back
tools = await mcp_client.list_tools()
response = client.messages.create(model="claude-sonnet-4-6", tools=tools,
    messages=[{"role": "user", "content": "Where is my order ORD-12345?"}])

if response.stop_reason == "tool_use":
    tool_call = response.content[0]
    result = await mcp_client.call_tool(tool_call.name, tool_call.input)
    # Feed result back as a tool_result message for the next LLM turn
```

### 何時採用此模式

- API 整合（資料庫、SaaS 工具、內部服務）
- 結構化資料的擷取與變更
- 任何你能事先定義工具介面的工作流程
- 需要稽核軌跡與輸入驗證的生產系統

### 權衡取捨

| 優點 | 缺點 |
|-----------|--------------|
| 確定性的執行 | 需要事先準備工具 schema |
| 易於稽核與記錄 | 無法與任意 UI 互動 |
| 速度快（每次工具呼叫 50-200ms） | 模型可能產生幻覺的工具名稱／引數 |
| 適用於任何支援工具使用的 LLM | 工具過多時 schema 會過載 |

---

## 模式 2：以視覺為基礎的自動化

模型看到螢幕的截圖，推理該做什麼，並發出一個低階動作（點擊、輸入、捲動）。環境執行該動作，擷取新的截圖，然後迴圈重複。這就是 Claude Computer Use 與 Open Interpreter 的 Computer API 的運作方式。

### 架構

```
+-------------------------------------------------------------------+
|              Vision-Based Automation Pattern                      |
+-------------------------------------------------------------------+
|                                                                   |
|  +------------------+                                             |
|  |  Task Goal        |  "Fill out the expense form with           |
|  |  (NL instruction) |   last week's receipts"                    |
|  +--------+---------+                                             |
|           |                                                       |
|           v                                                       |
|  +--------+--------------------------------------------------+    |
|  |                    VISION-ACTION LOOP                      |    |
|  |                                                            |    |
|  |   +------------+    +-------------+    +------------+     |    |
|  |   |  OBSERVE   |    |  REASON     |    |  ACT       |     |    |
|  |   |            |    |             |    |            |     |    |
|  |   | Screenshot |--->| Analyze     |--->| Emit action|     |    |
|  |   | (base64)   |    | screenshot  |    | {type:     |     |    |
|  |   |            |    | + goal      |    |  "click",  |     |    |
|  |   |            |    | + history   |    |  x: 450,   |     |    |
|  |   |            |    | + prev acts |    |  y: 320}   |     |    |
|  |   +-----^------+    +-------------+    +------+-----+     |    |
|  |         |                                      |          |    |
|  |         +--------------------------------------+          |    |
|  |                    (Loop until done)                       |    |
|  +-----------------------------------------------------------+    |
|                            |                                      |
|                            v                                      |
|  +-------------------------+------------------------------+       |
|  |         Sandboxed Environment (VM / Docker + VNC)      |       |
|  |                                                        |       |
|  |   +----------+  +----------+  +----------+            |       |
|  |   | Desktop  |  | Browser  |  | Apps     |            |       |
|  |   | (Xfce)   |  | (Chrome) |  | (any)    |            |       |
|  |   +----------+  +----------+  +----------+            |       |
|  +--------------------------------------------------------+       |
+-------------------------------------------------------------------+
```

### Observe-Reason-Act 循環

**Observe（觀察）**：擷取目前螢幕狀態的截圖。在 Claude Computer Use 中，這是一張以 base64 編碼的 PNG，作為 image content block 傳送。Zoom Action（2026 年新增）允許針對密集的 UI 擷取特定區域的高解析度裁切。

**Reason（推理）**：多模態 LLM 會同時分析截圖、任務目標與動作歷史。它決定下一個動作應該是什麼。此步驟消耗的 token 最多。

**Act（行動）**：模型發出一個結構化動作：
- `left_click(x, y)` -- 在座標處點擊
- `type(text)` -- 輸入一段字串
- `key(key_combo)` -- 按下鍵盤快捷鍵
- `scroll(direction, amount)` -- 捲動頁面
- `screenshot()` -- 不執行動作，擷取一張新截圖
- `zoom(x0, y0, x1, y1)` -- 以高解析度檢視某個區域

### 程式碼範例：Computer Use 迴圈

```python
tools = [
    {"type": "computer_20250124", "name": "computer",
     "display_width_px": 1280, "display_height_px": 800},
    {"type": "bash_20250124", "name": "bash"},
    {"type": "text_editor_20250124", "name": "str_replace_based_edit_tool"}
]
messages = [{"role": "user", "content": "Open the browser and go to GitHub."}]

while True:  # The vision-action loop
    response = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=4096, tools=tools, messages=messages)
    if response.stop_reason == "end_turn":
        break
    for block in response.content:
        if block.type == "tool_use":
            result = sandbox.execute_action(block.name, block.input)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": block.id, "content": result}]})
```

### 何時採用此模式

- 自動化沒有 API 的舊版應用程式
- 圖形介面的端到端測試
- 需要與多個應用程式互動的任務
- 以自然語言描述任務的非開發者使用者

### 權衡取捨

| 優點 | 缺點 |
|-----------|--------------|
| 適用於任何 GUI 應用程式 | 速度慢（每個動作步驟 1-3 秒） |
| 不需要 API 或整合 | token 成本高（截圖體積大） |
| 能處理動態 UI | 在密集介面上有誤點風險 |
| 非技術使用者也能上手 | 為了安全需要沙箱化 VM |

---

## 模式 3：本地程式碼執行

使用者以自然語言描述任務。LLM 產生程式碼。程式碼在本地機器（或在沙箱中）執行。觀察其輸出，接著 LLM 要麼產生更多程式碼，要麼提供最終答案。這就是 Open Interpreter 以及 Claude Code 部分功能的運作方式。

### 架構

```
User (NL): "Analyze the CSV and plot the top 10 products"
  |
  v
[LLM Generates Code] --> Python/Bash/JS
  |
  v
[Permission Gate] --> "Run this code? [y/N]" (auto-approve, always-ask, or rules-based)
  |
  v
[Code Executor] --> Execute, capture stdout/stderr/return value
  |
  v
[Output Observer] --> Error? Feed back to LLM for fix. Success? Present to user.
  |
  v
[LLM Decides] --> Done? Return result. Need more? Generate next code block. (Loop)
```

### NL-Code-Execute-Observe 循環

**1. 自然語言轉程式碼**：LLM 將使用者的意圖轉譯成可執行的程式碼。程式碼語言取決於任務 -- 資料分析用 Python，系統操作用 bash，網頁任務用 JavaScript。

**2. 權限關卡（Permission Gate）**：在執行之前，會詢問使用者是否核准。這是非沙箱化環境中關鍵的安全機制。各種實作方式不盡相同：
- **總是詢問**（Open Interpreter 預設）：每個程式碼區塊都需要明確核准
- **自動核准**（信任模式）：危險但快速
- **以規則為基礎**（Claude Code 模式）：在組態中設定允許／拒絕的樣式。例如：允許 `git` 指令，拒絕 `rm -rf`

**3. 執行與擷取**：程式碼在具有完整（或受限）系統存取權的執行環境中運行。Stdout、stderr、回傳值以及任何產生的檔案都會被擷取。

**4. 觀察與迭代**：LLM 看到執行輸出。如果有錯誤，它會產生修正。如果輸出不完整，它會產生下一個步驟。這形成了一個自我修正的迴圈。

### 程式碼範例：程式碼執行代理

```python
class CodeExecutionAgent:
    def __init__(self, llm_client, sandbox=None):
        self.llm = llm_client
        self.sandbox = sandbox  # None = unsandboxed (host)
        self.history = []

    async def run(self, task: str) -> str:
        self.history.append({"role": "user", "content": task})
        for iteration in range(10):  # Max 10 code-execute cycles
            response = await self.llm.generate(messages=self.history)
            code = extract_code_block(response)
            if not code:
                return response  # No code = final answer
            if not self.sandbox and not await user_approves(code):
                return "Execution cancelled by user."
            result = await (self.sandbox or LocalExecutor()).run(code, timeout=30)
            self.history.append({"role": "assistant", "content": response})
            self.history.append({"role": "user",
                "content": f"stdout: {result.stdout}\nstderr: {result.stderr}"})
        return "Max iterations reached."
```

### 何時採用此模式

- 資料分析與視覺化任務
- 系統管理與 DevOps 自動化
- 檔案處理與轉換
- 任何由使用者描述「做什麼」而由代理找出「怎麼做」的任務

### 權衡取捨

| 優點 | 缺點 |
|-----------|--------------|
| 極為靈活 | 若未沙箱化則有安全風險 |
| 透過觀察迴圈自我修正 | 模型可能產生危險的程式碼 |
| 搭配本地模型可離線運作 | 需要使用者評估程式碼（或選擇信任） |
| 必要時可完整存取系統 | 非確定性（相同 prompt 會產生不同程式碼） |

---

## 模式 4：多代理工具編排

與其讓一個代理擁有許多工具，不如擁有多個各自掌管一部分工具的專門代理。一個編排器（orchestrator）將任務路由到正確的代理。這就是代理界的「微服務革命」。

### 架構

```
  [User Request]
       |
       v
  [ORCHESTRATOR] (Frontier model: Claude Opus, GPT-4o)
  Analyzes task, selects agent, routes and waits
       |
  +----+----+----+
  |         |         |
  v         v         v
[Code Agent]  [Data Agent]  [Web Agent]
 bash, edit,   SQL, plot,    fetch, scrape,
 git           csv            browse
  |         |         |
  v         v         v
[Sandbox]  [Sandbox]  [Sandbox]
(Docker)   (Docker)   (Docker)
```

### 編排策略

**1. 以路由為基礎（Router-Based，最簡單）**：編排器是一個分類器。它檢視使用者的訊息，挑選正確的專門代理，並轉發整個任務。代理之間沒有互相通訊。

**2. 規劃並執行（Plan-and-Execute）**：一個規劃模型（frontier 等級）將任務拆解成子任務，並把每個子任務指派給適當的專門代理。子任務的結果由規劃器彙總。基準測試顯示，相較於循序的 ReAct，其任務完成率達 92%，速度提升 3.6 倍。

**3. 階層式（Hierarchical）**：高階代理將工作指派給低階代理，後者可能進一步委派。這反映了組織結構，對複雜的專案運作良好。

**4. 協作式（Collaborative，點對點）**：代理之間可以直接互相通訊，分享觀察並請求協助。這是最複雜的模式，但能妥善處理突發性的任務。

### 成本最佳化：Plan-and-Execute 的優勢

```
Traditional: [Frontier Model] handles all steps       Cost: $1.00/task

Plan-and-Execute:
  [Frontier Model] plans (1 call)                     Cost: $0.05
  [Small Model] executes steps 1-3                    Cost: $0.03
  [Frontier Model] aggregates (1 call)                Cost: $0.05
                                                      Total: $0.13/task
                                                      Savings: ~87%
```

2026 年的趨勢是將代理的成本最佳化視為頭等重要的考量，就如同雲端成本最佳化在微服務時代成為必備一樣。

---

## 沙箱化 vs. 非沙箱化執行

這是任何工具使用代理最具影響力的架構決策。

### 比較

```
  UNSANDBOXED (Host Access)              SANDBOXED (Isolated)
  +------------------------+             +------------------------+
  | LLM output executes    |             | LLM output executes    |
  | directly on host OS    |             | inside Docker/VM/E2B   |
  |                        |             |                        |
  | Risk: rm -rf /         |             | Isolated filesystem,   |
  | Risk: data exfiltration|             | network, processes     |
  |                        |             |                        |
  | Used by: OpenClaw,     |             | Used by: OpenHands,    |
  | Open Interpreter,      |             | OpenAI Codex, Jules,   |
  | Claude Code (default)  |             | Cursor Background Agents|
  +------------------------+             +------------------------+
```

### 沙箱實作選項

| 技術 | 隔離層級 | 啟動時間 | 使用情境 |
|------------|----------------|-------------|----------|
| Docker | 行程 + 檔案系統 | 1-5 秒 | 多數代理沙箱（OpenHands） |
| Firecracker | 完整 VM（microVM） | ~125ms | 高安全性、多租戶 |
| gVisor | 核心層級 | ~200ms | Google Cloud Run |
| E2B | 雲端沙箱 | 2-3 秒 | 遠端代理執行 |
| WebAssembly | 語言層級 | <50ms | 以瀏覽器為基礎的執行 |

### 2026 年的共識

預設沙箱化，並保留逃生出口（escape hatches）。OpenClaw 的安全危機（公開網路上有 135,000 個暴露的實例）已讓業界正視這件事。新的生產代理被期望要預設沙箱化。非沙箱化執行則保留給單一使用者、有人監督的環境。

---

## 跨工具呼叫的狀態管理

代理需要在工具呼叫之間維持狀態。其策略取決於代理的生命週期與使用情境。

### 狀態管理模式

| 模式 | 生命週期 | 儲存方式 | 使用者 |
|---------|-----------|---------|---------|
| **對話狀態（Conversation State）** | 短暫（單一對話） | 訊息陣列 | 多數以 API 為基礎的代理 |
| **工作階段狀態（Session State）** | 每個工作階段（工作目錄、開啟的檔案） | Docker 容器／暫存目錄 | OpenHands、Claude Code |
| **持久狀態（Persistent State）** | 跨工作階段（數天、數週） | DB、檔案、Markdown | OpenClaw（Memories/）、CLAUDE.md |
| **環境狀態（Environment State）** | 外部（真實來源 / source of truth） | Git repo、資料庫、檔案系統 | Claude Code（git status）、CI/CD |

### 實作：工作階段狀態

```python
class AgentSession:
    """Manages state across tool calls within a single session."""
    def __init__(self):
        self.conversation: list[dict] = []
        self.working_dir: str = tempfile.mkdtemp()
        self.open_files: dict[str, str] = {}  # path -> content cache
        self.tool_call_count: int = 0

    def add_tool_result(self, tool_name: str, args: dict, result: dict):
        self.tool_call_count += 1
        self.conversation.append({"role": "tool", "tool_name": tool_name,
            "args": args, "result": result, "timestamp": time.time()})
        # Update derived state from side effects
        if tool_name == "write_file":
            self.open_files[args["path"]] = args["content"]

    def get_context_for_llm(self, max_tokens: int = 100_000) -> list[dict]:
        """Return conversation history, compressed if over budget."""
        if estimate_tokens(self.conversation) < max_tokens:
            return self.conversation
        return self._compress_history(max_tokens)  # Summarize old results
```

---

## 錯誤處理與重試模式

工具呼叫會失敗。網路會逾時。API 會回傳錯誤。程式碼會拋出例外。一個生產級的代理需要系統化的錯誤處理。

### 錯誤分類

| 錯誤類型 | 範例 | 策略 |
|-----------|----------|----------|
| **暫時性（Transient）** | 網路逾時、速率限制、503 | 指數退避重試（最多 3 次） |
| **輸入（Input）** | 引數無效、格式錯誤 | 將錯誤回饋給 LLM，讓它修正引數 |
| **權限（Permission）** | 驗證失敗、存取遭拒 | 回報給使用者，不要重試 |
| **邏輯（Logic）** | 工具錯誤、不可能的操作 | 將錯誤回饋給 LLM，讓它重新規劃 |
| **災難性（Catastrophic）** | OOM、沙箱當機、無限迴圈 | 中止、回報、清理資源 |

### 重試模式實作

```python
class ToolExecutor:
    MAX_RETRIES = 3

    async def execute_with_retry(self, tool_name: str, args: dict) -> dict:
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self.call_tool(tool_name, args)
                if not result.get("error"):
                    return result  # Success
                error_type = classify_error(result["error"])
                if error_type == "transient":
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                elif error_type == "input":
                    return {"error": result["error"], "fix_hint": "Adjust args"}
                elif error_type == "permission":
                    return {"error": result["error"], "action": "Report to user"}
                else:  # catastrophic
                    await self.cleanup_sandbox()
                    return {"error": "Fatal error. Task aborted."}
            except TimeoutError:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        return {"error": f"Failed after {self.MAX_RETRIES} retries"}
```

### 自我修正迴圈

2026 年最強大的錯誤處理模式。代理觀察自己的失敗，並自主地修正它們：

```
LLM generates code/tool call
  --> Execute --> Success? -- YES --> Return result
                     |
                     NO
                     |
                     v
              Feed error + stderr to LLM --> LLM generates fix --> Execute again
              (max 5 corrections to prevent infinite loops)
```

這就是 Claude Code、OpenHands 與 Cline 處理測試失敗的方式：執行測試、看到失敗、編輯程式碼、重新執行測試，反覆進行直到全部通過為止。

---

## MCP 整合模式

在 2026 年，MCP 已成為工具整合的標準協定。以下是將 MCP 整合進代理架構的關鍵模式。

### 模式 A：直接 MCP 連線

```
[Agent (Client)] <-- stdio / HTTP --> [MCP Server]
```
最簡單的模式。一個代理，一個 server。用於單一用途的工具（資料庫、檔案系統）。

### 模式 B：多 Server 扇出（Fan-Out）

```
                  +--> [GitHub MCP]
[Agent (Client)]--+--> [Postgres MCP]
                  +--> [Slack MCP]
```
代理同時連線到多個 MCP server。各工具的 schema 會被合併成一份 manifest。Claude Code 與多工具助理會使用此模式。

### 模式 C：MCP 閘道（Gateway，企業級）

```
[Agent 1] --+                          +--> [GitHub MCP]
[Agent 2] --+--> [MCP Gateway]  --+--> [Postgres MCP]
[Agent 3] --+    (Auth, Rate Limit,    +--> [Slack MCP]
                  Audit, Route)
```
中央閘道負責處理驗證、速率限制與稽核記錄。代理只需向閘道進行驗證。用於企業與多租戶部署。

### MCP 藍圖（Roadmap）的缺口

目前的 MCP 規範（截至 2026 年 5 月）缺少三個關鍵的生產原語（primitives）：

1. **身分傳播（Identity Propagation）**：沒有標準化的方式能將使用者身分從 client 一路傳遞到 server。閘道模式是一種變通做法。
2. **自適應工具預算（Adaptive Tool Budgeting）**：在協定層級沒有支援限制每次工具呼叫的 token／成本消耗。
3. **結構化錯誤語意（Structured Error Semantics）**：沒有標準的錯誤碼或錯誤類別。每個 server 都自行定義其錯誤格式。

這些都在 2026 年的藍圖中，但尚未正式定案。

---

## 架構決策樹

使用這棵決策樹來為你的使用情境挑選正確的模式：

```
Does the target system have an API?
 +-- YES --> Pattern 1 (Tool Calling). Wrap as MCP server. Fastest, most reliable.
 +-- NO  --> Does the task require GUI interaction?
              +-- YES --> Pattern 2 (Vision-Based). Sandbox in VM. Accept latency.
              +-- NO  --> Is the task primarily code/data work?
                           +-- YES --> Pattern 3 (Code Exec). Sandbox if multi-tenant.
                           +-- NO  --> Complex enough for multiple specialists?
                                        +-- YES --> Pattern 4 (Multi-Agent Orch.)
                                        +-- NO  --> Pattern 1 with custom tool.
```

### 混合架構

在實務上，生產系統會結合多種模式。Claude Code 採用：
- 模式 1（工具呼叫）用於檔案操作與 git
- 模式 2（以視覺為基礎）用於 computer use 功能
- 模式 3（程式碼執行）用於 bash 與執行測試
- 模式 4（多代理）用於衍生子代理（subagent spawning）

關鍵在於預設採用最簡單的模式（函式呼叫），只有在使用情境有需求時才增添複雜度。

---

## 系統設計面試切入角度

在面試中討論工具使用架構時，圍繞以下五個面向來組織你的答案：

### 1. 模式選擇

先從辨識哪種模式合適開始：「目標系統有一個 REST API，所以我會採用函式／工具呼叫模式，搭配一個包裝該 API 的 MCP server。」這顯示你理解這棵決策樹。

### 2. 沙箱邊界

務必處理安全議題：「對於多租戶部署，我會把每位使用者的代理工作階段沙箱化在一個 Docker 容器中，且不開放對內部服務的網路存取。MCP server 在沙箱之外運行，並中介所有對外的呼叫。」

### 3. 狀態策略

說明狀態如何管理：「我會在 Docker 容器內使用工作階段狀態來存放工作檔案，並以環境狀態（git repo）作為真實來源（source of truth）。此使用情境不需要持久的代理記憶。」

### 4. 錯誤預算

討論失敗模式：「工具呼叫可能因暫時性錯誤（以退避方式重試）、輸入錯誤（讓 LLM 自我修正）或權限錯誤（呈報給使用者）而失敗。我會設定最多 5 次自我修正嘗試，超過後就升級處理。」

### 5. 成本模型

談談經濟面：「對於編排器，我會採用 Plan-and-Execute 模式：由 Opus 規劃任務，由 Haiku 執行每個步驟。相較於凡事都用 Opus，這能將成本降低約 87%。」

---

## 面試問題

### Q：設計一個系統，讓客戶支援專員能運用來自 Zendesk、Salesforce 與內部知識庫的資料來回答問題。

**強力答案：**
採用模式 1（函式／工具呼叫），搭配三個 MCP server，每個資料來源各一個。使用多 Server 扇出模式並搭配 dynamic manifests，讓每個查詢只載入相關的工具。對於生產環境，再加上一個 MCP Gateway 來處理各資料來源的 OAuth、速率限制（對 Salesforce API 限制至關重要）以及稽核記錄。狀態是短暫的 -- 客戶支援不需要跨工作階段的記憶。

### Q：你會如何防止 AI 代理透過工具呼叫造成損害？

**強力答案：**
跨五個層面的縱深防禦（defense in depth）：（1）帶有拒絕樣式的 schema 約束（以 regex 拒絕 `DROP TABLE` 等）。（2）針對破壞性操作的權限關卡 -- Claude Code 的允許／拒絕規則是個好範本。（3）沙箱隔離（Docker 搭配唯讀掛載、無對外網路）。（4）token 與成本上限以防止失控的迴圈。（5）透過 MCP Gateway 模式建立稽核軌跡。沒有任何單一層面足夠 -- 模型可能產生通過驗證的幻覺引數（需要沙箱），而沙箱也無法防止透過被允許的路徑進行資料外洩（需要稽核記錄）。

### Q：解釋以視覺為基礎的 computer use 與以 API 為基礎的工具呼叫之間的權衡。

**強力答案：**
以 API 為基礎的方式較快（每步 50-200ms vs. 1-3s）、較便宜（文字 token vs. 影像 token）、較可靠（確定性 vs. 座標點擊），也較容易測試。只要有 API 存在，總是優先採用它。以視覺為基礎的方式則是針對沒有 API 的應用程式、舊版系統或多應用程式工作流程的後備方案。2026 年的 Zoom Action 緩解了在密集 UI 上的誤點問題。最佳實務：對於 80% 有 API 支援的任務使用 API 呼叫，對於其餘 20% 使用以視覺為基礎的方式。

---

## 參考資料

- Anthropic. "Computer Use Tool Documentation" (2024-2026)
- Anthropic. "Model Context Protocol Specification" (2025-2026)
- MCP 2026 Roadmap. "Transport Evolution, Agent Communication, Governance" (2026)
- IBM Developer. "MCP Architecture Patterns for Multi-Agent AI Systems" (2026)
- Google Cloud. "Choose a Design Pattern for Your Agentic AI System" (2025-2026)
- Microsoft Azure. "AI Agent Orchestration Patterns" (2025-2026)
- OpenHands Documentation. "Runtime Architecture" (2025-2026)
- OpenClaw Documentation. "Architecture and SOUL.md Guide" (2025-2026)
- Open Interpreter GitHub Repository (2024-2026)
- ArXiv 2603.13417. "Design Patterns for Deploying AI Agents with MCP" (2026)

---

*上一篇：[工具使用與電腦代理全景](01-tool-use-landscape.md)*
*下一章：[案例研究](../16-case-studies/)*
