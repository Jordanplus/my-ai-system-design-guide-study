# LangGraph Orchestration

LangGraph 是建構具狀態（stateful）、多代理（multi-agent）系統的**事實標準（de facto standard）**。它在 2025 年底達到 v1.0，並在 2026 年初因為其圖形化（graph-based）執行環境受到企業採用，GitHub star 數超越了 CrewAI。與單純的鏈（chain）不同，LangGraph 支援**循環（Cycles）**、**狀態持久化（State Persistence）**以及**人在迴路中（Human-in-the-Loop）**的介入。

## 目錄

- [圖的哲學](#philosophy)
- [循環式與非循環式工作流程](#cyclic)
- [LangGraph 中的狀態管理](#state)
- [持久化與檢查點](#persistence)
- [多代理協作模式](#multi-agent)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 圖的哲學

在 2023 年，代理（agent）是「黑盒子」。
如今，代理是**圖（Graphs）**。
一張圖由以下部分組成：
- **Nodes（節點）**：Python 函式（LLM、工具或資料處理）。
- **Edges（邊）**：節點之間的路徑。
- **Conditional Edges（條件邊）**：依據**狀態（State）**決定路徑的邏輯。

---

## 循環式與非循環式

標準的 LangChain 是**非循環的（Acyclic）**（循序執行）。
LangGraph 則是**循環的（Cyclic）**。
- **迴圈的威力**：代理可以嘗試某個工具、看到錯誤，然後**循環回到**「思考（Thinking）」節點再試一次。這正是 **ReAct** 模式的基礎。

---

## 狀態管理

**狀態結構（State Schema）**是圖的「心智（Mind）」。
```python
class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    plan: list[str]
    is_secure: bool
```
**細節（Nuance）**：搭配 `add_messages` 使用 `Annotated`，可讓圖**附加（Append）**至歷史紀錄，而非加以覆寫，從而保留完整的推理軌跡。

---

## 持久化與檢查點

目前的 LangGraph 採用**以執行緒為基礎的持久化（Thread-based Persistence）**。
- **概念**：每個工作階段（session）都有一個 `thread_id`。
- **效益**：如果使用者在 2 天後回來，代理能記住自己在多步驟工作流程中停留的確切位置。
- **時光回溯（Time-Travel）**：開發者可以從先前的某個狀態「重新執行」特定執行緒，以便除錯（debug）某次失敗。

---

## 多代理模式

| 模式 | 說明 | 案例研究 |
|---------|-------------|------------|
| **Supervisor（監督者）** | 一位「管理者」指揮多個專職工作者。 | 研究團隊 |
| **Peer-to-Peer（點對點）**| 代理彼此直接交接（hand off）任務。 | 客戶服務 |
| **Hierarchical（階層式）**| 圖中有圖（巢狀圖）。 | 企業工程 |

---

## 面試問題

### Q：為什麼要使用 LangGraph，而不是 OpenAI 的「Assistant API」？

**理想答案：**
**控制力與可攜性（Control and Portability）**。Assistant API 是一個黑盒子：你看不到確切的 prompt，也無法控制邏輯閘（logic gates）。LangGraph 則是一個**白盒框架（White Box framework）**。我可以使用任何模型（OpenAI、Claude、Llama 3.3）、精準控制工具在何時被呼叫，並在各步驟之間注入自訂的驗證邏輯。更重要的是，LangGraph 是**開源（Open Source）**的，可以在本機／地端（on-prem）執行，這對許多企業的安全需求至關重要。

### Q：在一張具有 20 個以上節點的圖中，你如何處理「狀態超載（State Overload）」？

**理想答案：**
我們採用**狀態收斂（State Narrowing）**。我們不會把整個全域狀態傳給每一個節點，而是為子圖（sub-graphs）定義專屬的子狀態。我們也會使用 **Trim Runnables** 在訊息歷史送進 LLM 之前先加以修剪，以確保不浪費 token，同時把「真相（Truth）」保存在持久化層中。

---

## 參考資料
- LangChain Team. "LangGraph: Multi-Agent Workflows at Scale" (2025)
- Anthropic. "Building Resilient Agents with State Machines" (2025)
- OpenSource AI. "Cycles and the Future of Agency" (2024 Tech Report)

---

*下一篇：[LangSmith Observability](03-langsmith-observability.md)*
