# 狀態管理模式

AI 系統中的狀態管理已經從單純的「sessions」演進為 **Stateful Agent Graphs（具狀態的代理圖）**。管理一個代理「思維」的流動與持久化，其重要性不亞於 LLM 本身：這也是 LangGraph 成為 LangChain 建構代理的預設控制流程 runtime 的主因之一。

## 目錄

- [狀態物件](#state-object)
- [狀態機 vs. DAG 編排](#orchestration)
- [檢查點與續行（Checkpointing and Resume）](#checkpointing)
- [平行狀態與 Fork/Join](#parallel)
- [時光回溯（狀態改寫）](#time-travel)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 狀態物件

「State（狀態）」是一個代理 session 的 **Single Source of Truth（唯一真實來源）**。
```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    plan: list[str]
    current_task: str
    tool_results: dict[str, Any]
    user_context: dict[str, Any]
    iteration_count: int
```
**最佳實務**：狀態應盡可能採用 **Strictly Typed（嚴格型別）** 並維持 **Append-Only（僅追加）**，以避免在長時間執行的迴圈中發生資料遺失。

---

## 狀態機（LangGraph）

業界已收斂到 **Cyclic Graphs（循環圖，即狀態機）**。
- **Nodes（節點）**：接收狀態並回傳一份更新的函式。
- **Edges（邊）**：根據狀態值決定下一個節點的條件邏輯（例如 `if state['error'] -> goto 'recovery_node'`）。

---

## 檢查點與續行

在生產環境中，代理可能執行數分鐘甚至數小時。
- **Persistence Layer（持久化層）**：每一次狀態更新都會儲存到資料庫（Postgres/Redis）。
- **Resiliancy（韌性）**：若伺服器當機，編排器會取回最後一個 `checkpoint_id`，並從上次中斷的確切位置恢復執行。
- **UX（使用者體驗）**：這讓 **Asynchronous Agents（非同步代理）** 成為可能——使用者會先收到一則「我正在處理中」的訊息，並在 10 分鐘後當狀態變為「Complete（完成）」時收到通知。

---

## 平行狀態（Fork/Join）

對於複雜的任務，我們會 **Fork（分支）** 狀態。
1. **Fan-out（扇出）**：將狀態送往 3 個子代理（例如 Researcher A、B 與 C）。
2. **Fan-in（扇入，即 Join）**：一個「Manager」代理接收這三者的輸出，並將它們合併回主狀態物件。

---

## 時光回溯（狀態改寫）

如同 HITL 章節所述，狀態管理讓 **Human Intervention（人為介入）** 成為可能。
- 開發者可以瀏覽 session 歷史、找出某個「壞掉的回合（bad turn）」、在該特定時間戳記編輯狀態物件，並從該點 **Re-run（重新執行）** 整張圖。

---

## 面試題

### Q：為什麼代理要使用「基於圖（Graph-based）」的狀態機（LangGraph），而不是單純的「While 迴圈」？

**強而有力的回答：**
While 迴圈是 **Opaque and Brittle（不透明且脆弱的）**。你無法輕易地將邏輯視覺化，而錯誤處理會淪為一團巢狀的 if 判斷式。基於圖的做法則是 **Observable and Modular（可觀測且模組化的）**。你可以將整個流程視覺化（以 Mermaid 圖呈現）、對個別節點進行單元測試，並且只需新增邊就能實作出像「Backtracking（回溯）」或「Parallel execution（平行執行）」這類複雜功能。它也讓 **State Persistence（狀態持久化）** 變得輕而易舉，因為框架會處理節點之間的儲存／載入。

### Q：在長時間執行的代理 session 中，你如何避免「State Bloat（狀態膨脹）」？

**強而有力的回答：**
我們會使用 **State Pruning（狀態修剪）** 與 **Message Summarization（訊息摘要）**。與其把整份 `tool_results` 字典帶著走遍整張圖，我們會在某個子任務完成後就立即修剪它。對於 `messages` 清單，我們則使用一個專門的「Summarizer Node（摘要節點）」，每 10 個回合執行一次，把歷史壓縮成一段精煉的 context 區塊，確保我們在維持狀態物件靈活反應的同時，不會撞到 token 上限。

---

## 參考資料
- LangChain. "LangGraph: Multi-Agent Workflows" (2024/2025)
- Temporal.io. "Stateful AI Agents at Scale" (2025)
- AWS Bedrock. "Managing Long-Running Agent Sessions" (2025)

---

*下一篇：[第 09 節：框架與工具](../09-frameworks-and-tools/01-langchain-deep-dive.md)*
