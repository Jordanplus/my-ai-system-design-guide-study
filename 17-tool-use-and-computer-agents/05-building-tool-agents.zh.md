# 建構 Tool-Use Agent

本章探討 tool-use agent 的實務工程：設計 LLM 能可靠呼叫的 tool schema、建構 MCP server 來託管這些 tool、將 tool 組合成工作流程，以及測試整個系統。這些就是區分一個 demo 與正式環境部署的關鍵模式。

## 目錄

- [為 LLM 設計 Tool Schema](#designing-tool-schemas-for-llms)
- [建立 MCP Server](#mcp-server-creation)
- [Tool 註冊與探索](#tool-registration-and-discovery)
- [輸入驗證與輸出格式化](#input-validation-and-output-formatting)
- [Tool 組合：串接 Tool](#tool-composition-chaining-tools)
- [建構自訂 Agent Skill](#building-custom-agent-skills)
- [建立 Function-Calling 端點](#creating-function-calling-endpoints)
- [測試 Tool-Use Agent](#testing-tool-use-agents)
- [Tool Use 的可觀測性](#observability-for-tool-use)
- [常見錯誤與反模式](#common-mistakes-and-anti-patterns)
- [Tool 版本控管與向後相容](#tool-versioning-and-backwards-compatibility)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 為 LLM 設計 Tool Schema

tool schema 是 LLM 與你的系統之間的合約。設計良好的 schema 能減少幻覺出來的引數、防止誤用，並讓模型的 tool 選擇更可靠。

### 一個好的 Tool 定義的結構

```json
{
  "name": "search_customers",
  "description": "Search for customers by name, email, or account ID. Returns up to 10 matching customer records. Use this when the user asks about a specific customer. Do NOT use this for aggregate queries like 'how many customers do we have'.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search term: customer name, email address, or account ID (e.g., 'john@acme.com' or 'ACC-12345')"
      },
      "limit": {
        "type": "integer",
        "description": "Max results to return (1-10). Default: 5",
        "default": 5,
        "minimum": 1,
        "maximum": 10
      }
    },
    "required": ["query"]
  }
}
```

### Schema 設計規則

**1. 精準命名**：使用 `verb_noun` 格式。用 `search_customers`，而不是 `search` 或 `customer_tool`。

**2. 描述何時「不該」使用**：模型需要負面範例。「Do NOT use for aggregate queries」比只列出有效用途更能防止誤用。

**3. 提供引數範例**：在 description 字串中包含範例值。模型會用這些來校準它的輸出。

**4. 限制範圍**：使用 `minimum`、`maximum`、`enum` 與 `pattern`，在 schema 層級而非你的 handler 中防止無效引數。

**5. 讓 tool 保持原子性**：一個 tool 只做一件事。避免用一個 `manage_customer` tool 來建立、讀取、更新、刪除 —— 拆成四個 tool。

**6. 使用 `strict: true`**：Anthropic 的 strict 模式保證模型輸出完全符合 schema。在正式環境中務必啟用它。

```
Good Tool Design:                    Bad Tool Design:

+-------------------+                +-------------------+
| search_customers  |                | customer_tool     |
| - query (string)  |                | - action (string) |
| - limit (int 1-10)|                | - data (object)   |
+-------------------+                | - options (any)   |
| create_customer   |                +-------------------+
| - name (string)   |                "action" can be
| - email (string)  |                "search", "create",
+-------------------+                "update", "delete"
| update_customer   |                => model confused,
| - id (string)     |                   schema too loose,
| - fields (object) |                   hard to validate
+-------------------+
```

---

## 建立 MCP Server

MCP server 是一個獨立的行程（process），向任何相容 MCP 的客戶端（Claude、GPT、基於 Llama 的 agent）公開 tool、resource 與 prompt。你只需撰寫一次 server，任何 LLM 都能使用它。

### MCP 架構

```
+------------------+          JSON-RPC           +------------------+
|                  |  ========================>  |                  |
|   MCP Client     |                             |   MCP Server     |
|   (AI App)       |  <========================  |   (Your Code)    |
|                  |                             |                  |
|  - Claude Code   |  Transport:                 |  Exposes:        |
|  - Custom Agent  |  - stdio (local)            |  - Tools         |
|  - IDE Plugin    |  - Streamable HTTP (remote)  |  - Resources     |
|                  |                             |  - Prompts       |
+------------------+                             +------------------+
```

### TypeScript MCP Server

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "customer-service", version: "1.0.0" });

server.tool(
  "search_customers",
  "Search customers by name, email, or ID. Returns up to 10 matches.",
  {
    query: z.string().describe("Search term: name, email, or account ID"),
    limit: z.number().min(1).max(10).default(5).describe("Max results"),
  },
  async ({ query, limit }) => ({
    content: [{ type: "text",
      text: JSON.stringify(await db.customers.search(query, limit), null, 2) }],
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Python MCP Server (FastMCP)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("customer-service")

@mcp.tool()
async def search_customers(query: str, limit: int = 5) -> str:
    """Search customers by name, email, or ID. Returns up to 10 matches.
    Args:
        query: Search term - customer name, email, or account ID
        limit: Max results to return (1-10, default 5)
    """
    return json.dumps(await db.customers.search(query, limit), indent=2)
```

兩個 SDK 都遵循相同的模式：建立一個 server、用具型別的 schema 註冊 tool、連接一個 transport。TypeScript SDK 使用 Zod 來驗證；Python 則使用型別提示（type hints）與 docstring。

### 部署模式

| 模式 | Transport | 使用情境 |
|------|-----------|----------|
| Local (stdio) | stdin/stdout pipe | 桌面工具、IDE 外掛 |
| Remote (Streamable HTTP) | HTTP + SSE | 雲端服務、共享 server |
| Hybrid | 兩者皆是 | 本地開發、遠端部署 |

---

## Tool 註冊與探索

在正式環境中，agent 需要動態探索可用的 tool，而不是把它們寫死。

### 靜態註冊

在設定檔（例如 `claude_desktop_config.json`）中宣告 MCP server。每個項目將一個 server 名稱對應到一個命令、引數，以及選擇性的環境變數。簡單但缺乏彈性 —— 不論是否相關，每個 server 都會在啟動時載入。

### 動態探索（Tool Search）

Anthropic 的 Tool Search（2025）解決了 schema 過載問題。agent 不是把 200 個 tool schema 載入 context（這會降低推理能力），而是送出一個輕量的搜尋查詢，只接收 3-5 個相關的 tool schema。這讓 context window 聚焦於推理，而非剖析未使用的 schema。

### MCP 探索協定

MCP 客戶端透過標準的 JSON-RPC 方法來探索能力：`tools/list` 回傳可用的 tool、`resources/list` 回傳資料 resource、`prompts/list` 回傳 prompt 範本。這讓執行期探索成為可能，無須寫死。

---

## 輸入驗證與輸出格式化

### 輸入驗證的各層

```
+---------------------+
|  Schema Validation   |  <-- JSON Schema / Zod / Pydantic
|  (type, range, enum) |      Catches: wrong types, out-of-range
+----------+----------+
           |
           v
+---------------------+
|  Business Validation |  <-- Your handler code
|  (exists, permitted) |      Catches: invalid IDs, unauthorized
+----------+----------+
           |
           v
+---------------------+
|  Execution           |  <-- Actual operation
+---------------------+
```

務必在兩層都進行驗證。schema 驗證捕捉格式錯誤的輸入。business 驗證捕捉語意上無效的輸入。

```python
@mcp.tool()
async def transfer_funds(
    from_account: str,
    to_account: str,
    amount: float
) -> str:
    """Transfer funds between accounts."""
    # Schema already enforced types via type hints

    # Business validation
    if amount <= 0:
        return "Error: Amount must be positive."
    if amount > 10000:
        return "Error: Transfers over $10,000 require manual approval."
    if from_account == to_account:
        return "Error: Cannot transfer to the same account."

    from_acct = await db.accounts.get(from_account)
    if not from_acct:
        return f"Error: Account {from_account} not found."

    # Execute
    result = await db.transfers.execute(from_account, to_account, amount)
    return f"Transferred ${amount:.2f}. Confirmation: {result.id}"
```

### 輸出格式化

當模型需要對結果進行推理時，回傳結構化資料。當結果是最終結論時，回傳人類可讀的文字。

```python
# Good: structured for further reasoning
return json.dumps({
    "customers": [
        {"id": "ACC-123", "name": "Jane Smith", "email": "jane@acme.com"},
        {"id": "ACC-456", "name": "John Doe", "email": "john@acme.com"}
    ],
    "total_matches": 2,
    "has_more": False
})

# Bad: unstructured blob
return "Found Jane Smith (ACC-123, jane@acme.com) and John Doe (ACC-456, john@acme.com)"
```

---

## Tool 組合：串接 Tool

真實任務需要依序呼叫多個 tool。有兩種組合模式：

### 模式 1：LLM 編排的串接

LLM 根據先前的結果決定接下來要呼叫哪個 tool：

```
User: "Find customer Jane Smith and create a high-priority ticket for her billing issue"

Turn 1:  LLM -> search_customers("Jane Smith")
         Result: {"id": "ACC-123", "name": "Jane Smith", ...}

Turn 2:  LLM -> create_ticket("ACC-123", "Billing issue", "...", "high")
         Result: "Ticket TK-789 created."

Turn 3:  LLM -> "I found Jane Smith (ACC-123) and created ticket TK-789."
```

每一次 tool 呼叫都是一次獨立的 API 往返。模型在各次呼叫之間針對結果進行推理。

### 模式 2：Programmatic Tool Calling

Anthropic 的 programmatic tool calling（2025）讓模型撰寫程式碼來串接 tool，而無須往返：

```
LLM generates code:
  customer = search_customers("Jane Smith")
  if customer.results:
    ticket = create_ticket(customer.results[0].id, ...)
    return f"Created {ticket.id} for {customer.results[0].name}"
  else:
    return "Customer not found"
```

這會以單一一次 API 呼叫執行，將延遲從 3 次往返降到 1 次。

### 模式 3：Server 端組合

在 MCP server 本身內部組合 tool —— 單一個 `resolve_customer_issue` tool 在內部呼叫 search 與 create_ticket，將多步驟邏輯對 LLM 隱藏起來。對於固定、定義明確、LLM 不需要在步驟之間進行推理的工作流程，使用這種方式。

### 何時使用各模式

| 模式 | 延遲 | 彈性 | 最適用於 |
|---------|---------|-------------|----------|
| LLM 編排 | 高（N 次往返） | 非常高 | 複雜、有分支的邏輯 |
| Programmatic | 低（1 次往返） | 高 | 線性串接、批次處理 |
| Server 端 | 最低 | 低 | 固定、常見的工作流程 |

---

## 建構自訂 Agent Skill

Agent Skill（Anthropic，2025）是 agent 動態載入的一組打包好的指令、tool 與 resource。一個 skill 是一個資料夾：

```
my-skill/
  SKILL.md          # Instructions the agent loads into system prompt
  tools/            # MCP tool implementations
  resources/        # Data files, templates, schemas
  tests/            # Evaluation cases
```

在執行期，SkillManager 註冊可用的 skill 並依需求啟用它們 —— 將該 skill 的指令注入 system prompt，並將其 tool 加入可用的 tool 集合。這讓基礎 agent 保持輕量，同時實現深度的專業化。

---

## 建立 Function-Calling 端點

要讓任何 LLM 都能呼叫你的 API，請透過搭配 Pydantic model 的 FastAPI 來公開它。自動產生的 OpenAPI 規格（`/openapi.json`）同時也可作為 function calling 的 tool schema。或者，你也可以將相同的邏輯包裝在一個 MCP server 中，以便與 Claude、GPT 或其他相容 MCP 的客戶端直接整合。

---

## 測試 Tool-Use Agent

### 三個測試層級

```
+---------------------------+
|   Eval Suites             |  End-to-end: does the agent
|   (Agent + LLM + Tools)  |  complete the task?
+-------------+-------------+
              |
+-------------v-------------+
|   Integration Tests       |  Does tool X work correctly
|   (Tool + Dependencies)   |  with real DB / API?
+-------------+-------------+
              |
+-------------v-------------+
|   Unit Tests              |  Does validation logic
|   (Tool Logic Only)       |  handle edge cases?
+---------------------------+
```

### Tool 的單元測試

在隔離環境中，以 mock 的相依物件來測試每個 tool handler。涵蓋：輸入驗證的邊界情況（超出範圍的值、缺漏的欄位）、錯誤訊息品質（它是否引導模型復原？），以及輸出格式（有效的 JSON、正確的 schema）。

### 針對 Agent 行為的 Eval Suite

建立一個包含 100 個以上真實查詢與預期結果的資料集：

```python
eval_cases = [
    {
        "input": "Find Jane Smith's account and check her last payment",
        "expected_tools": ["search_customers", "get_payment_history"],
        "max_tool_calls": 5,
    },
    {
        "input": "What is the meaning of life?",
        "expected_tools": [],  # Should NOT call any tools
        "max_tool_calls": 0,
    },
]
```

對每個案例，衡量：tool 選擇準確率（對的 tool 嗎？）、引數品質（引數正確嗎？）、任務完成率，以及效率（tool 呼叫次數）。在每次模型版本變更與每次 tool schema 變更時執行 eval。

---

## Tool Use 的可觀測性

每一次 tool 呼叫都應記錄：trace/span ID、時間戳記、tool 名稱、輸入引數、輸出大小、延遲、狀態、使用的模型、token 使用量，以及 session ID。

### 關鍵指標

| 指標 | 衡量內容 | 警示門檻 |
|--------|-----------------|-----------------|
| Tool 呼叫成功率 | 回傳有效結果的呼叫百分比 | < 95% |
| Tool 選擇準確率 | 是否選對了 tool？ | < 90% |
| 每任務平均 tool 呼叫數 | tool use 的效率 | > 2x baseline |
| 每次 tool 呼叫的延遲 | tool handler 的回應時間 | > 5s (p99) |
| 幻覺出來的引數 | 儘管有 schema 仍出現無效引數 | > 2% |
| 每任務成本 | LLM 加 tool 執行的總成本 | > budget |

### 追蹤架構

```
+-------------+     +----------------+     +--------------+
|  Agent      |---->|  Tool Handler  |---->|  Backend     |
|  (LLM call) |     |  (MCP Server)  |     |  (DB/API)    |
+------+------+     +--------+-------+     +------+-------+
       |                     |                     |
       v                     v                     v
+------+---------------------+---------------------+------+
|                    Trace Collector                       |
|              (OpenTelemetry / Langfuse)                  |
+---------------------------+------------------------------+
                            |
                            v
                   +--------+--------+
                   |   Dashboard     |
                   |   - Success %   |
                   |   - Latency     |
                   |   - Cost        |
                   +-----------------+
```

---

## 常見錯誤與反模式

| 反模式 | 問題 | 修正 |
|-------------|---------|-----|
| Tool 過載 | 50 個以上的 tool 會降低選擇準確率 | 動態探索，每回合載入 5-10 個 |
| 模糊的描述 | 「Handles customer operations」—— 太模糊 | 包含何時使用、何時「不該」使用、範例 |
| 萬能 tool | 一個帶 `action` 參數的 tool 包辦一切 | 拆成原子化的 tool，每個只做一個操作 |
| 缺少錯誤情境 | tool 回傳「Error」卻無細節 | 提供可付諸行動的訊息：「ACC-999 not found. Use search_customers...」 |
| 非結構化輸出 | tool 回傳模型必須剖析的散文 | 回傳 JSON 以利結構化推理 |
| 沒有冪等性 | `create_ticket` 被呼叫兩次就建立重複資料 | 接受冪等性金鑰（idempotency key），在建立前先檢查 |
| 暴露內部 ID | tool 要求模型無從得知的資料庫 UUID | 接受人類可讀的識別碼，在內部解析 |
| 忽略速率限制 | agent 迴圈跑了 100 次 API 呼叫，遭到節流 | 在 handler 中採用退避（backoff），回傳「retry in X seconds」 |

---

## Tool 版本控管與向後相容

隨著 tool 演進，你必須與依賴它們的 agent 維持相容性。

**規則：**
1. **增添式變更**（新增選擇性參數）：無須提升版本。舊的呼叫仍然有效。
2. **破壞性變更**（更名、移除參數、改變語意）：以新的 schema 建立一個新的 tool 名稱。讓舊的 tool 繼續運作，並在其 description 中加上「DEPRECATED: Use new_tool instead」。記錄每一次已棄用的呼叫以供監控。
3. **永遠不要移除一個 tool**，直到你確認沒有任何活躍的 agent 依賴它為止。

---

## 面試問題

### Q：你需要讓一個 LLM agent 存取 200 個內部 tool。你會如何處理 schema 過載？

**有力的回答：**
我不會把全部 200 個 tool schema 載入 context。相反地，我會採用兩階段做法。第一，一個 tool 探索階段，agent 描述它需要做什麼，由一個輕量搜尋（embedding 相似度或關鍵字比對）回傳 5-10 個最相關的 tool schema。第二，一個 tool 執行階段，只有被選出的 tool 才會被納入實際 LLM 呼叫的 context 中。

這呼應了 Anthropic 的 Tool Search 模式。探索步驟可以是一次獨立、較便宜的 LLM 呼叫，甚至是一次非 LLM 的搜尋。關鍵洞見在於：被不相關的 tool schema 佔用的 context window 空間，會直接降低模型的推理品質。我會把 tool 選擇準確率當作關鍵指標來衡量 —— 如果 agent 在應該呼叫 `get_customer_by_id` 時卻呼叫了 `search_customers`，探索階段就需要調校。

至於 MCP 的實作，我會把 tool 分組到特定領域的 server（customer-service、billing、analytics），並只連接與當前對話相關的 server。

### Q：為一個處理客戶支援的 tool-use agent 設計一套測試策略。

**有力的回答：**
我會在三個層級進行測試。第一，針對每個 tool handler 的單元測試：驗證輸入的邊界情況、錯誤訊息與輸出格式。這些測試在每次 commit 時於 CI 中以 mock 的相依物件執行。

第二，整合測試，驗證 tool 針對真實的（staging）資料庫能正常運作。例如，`create_ticket` 確實建立一筆記錄，而 `search_customers` 能把它找回來。這些測試能捕捉 tool 與後端之間的 schema 漂移（schema drift）。

第三，eval suite，測試完整的 agent —— LLM 加上 tool。我會建立一個包含 100 個以上真實客戶查詢的資料集，附帶預期的 tool 呼叫序列與輸出標準。這套 eval 衡量 tool 選擇準確率（它選對 tool 了嗎？）、引數品質（引數正確嗎？）、任務完成率（它解決了問題嗎？），以及效率（它用了幾次 tool 呼叫？）。

我會在每次模型版本變更與每次 tool schema 變更時執行 eval。如果在某次 schema 變更後 tool 選擇準確率掉了 2%，那代表需要修改的是描述，而非模型。

---

## 參考資料

- Anthropic. "Tool Use with Claude" API Documentation (2025)
- Model Context Protocol. "Build an MCP Server" (2025)
- MCP TypeScript SDK: github.com/modelcontextprotocol/typescript-sdk
- MCP Python SDK: github.com/modelcontextprotocol/python-sdk
- Anthropic. "Introducing Advanced Tool Use" (2025)
- Anthropic. "Agent Skills" Beta Documentation (2025)

---

*上一篇：[Computer-Use Agents](04-computer-use-agents.md)*
