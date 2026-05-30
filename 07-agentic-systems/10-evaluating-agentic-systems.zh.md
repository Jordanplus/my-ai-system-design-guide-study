# 評估 Agentic 系統

評估 agent 與評估 RAG 本質上截然不同。RAG 關注的是「準確度（Accuracy）」，而 agent 關注的則是**「可靠性（Reliability）」、「效率（Efficiency）」與「安全性（Safety）」**。在生產環境中，agent 評估仰賴 **Trajectory Benchmarks（軌跡基準測試）**與 **LLM-as-Judge** 來處理多步驟推理，並搭配 Langfuse、LangWatch、Braintrust 與 Arize Phoenix 等工具，這些工具皆原生支援 trace 層級的評分。

> [!NOTE]
> 關於標準 RAG 評估（Retrieval 對比 Generation 指標），請參閱 [06-retrieval-systems/09-advanced-retrieval-patterns.md](../06-retrieval-systems/09-advanced-retrieval-patterns.md) 與第 14 節。本章專門聚焦於 agent 的*執行路徑（Execution Path）*。

## 目錄

- [評估的典範轉移](#shift)
- [Trajectory Benchmarks（黃金標準）](#benchmarks)
- [關鍵指標：成功率、成本與耗時](#metrics)
- [以 LLM-as-Judge 評估步驟品質](#judge)
- [生產環境評估（對 Agent 進行 A/B 測試）](#production)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 評估的典範轉移

| 指標 | RAG 應用 | Agentic 應用 |
|--------|---------|-------------|
| **評估單位** | 單一回應 | **Trajectory（軌跡）**（所有步驟） |
| **成功標準**| Groundedness／Faithfulness | 任務完成度／邏輯健全性 |
| **複雜度** | 低（文字相似度） | 高（工具狀態驗證） |

---

## Trajectory Benchmarks

現代評估會針對**「通往結果的路徑」**進行評分。
1. **Optimal Path（最佳路徑）**：解決任務所需最短的工具呼叫序列。
2. **Agent Path（Agent 路徑）**：實際採取的步驟。
3. **The Score（評分）**：`Efficiency = (Optimal Steps / Agent Steps)`。分數為 `0.2` 代表 agent 走了冤枉路或過度迴圈。

**常見基準測試**：
- **SWE-bench**：修復 GitHub issue（程式碼能動性，Code Agency）。
- **WebArena**：操作選單與表單（瀏覽器能動性，Browser Agency）。
- **GAIA**：通用工具使用任務（助理能動性，Assistant Agency）。

---

## 關鍵指標

### 1. Task Success Rate（任務成功率，TSR）
最終狀態正確的任務所佔的百分比。
> [!IMPORTANT]
> 在資深的生產環境中，透過「錯誤路徑」得到「正確答案」的分數為 0。

### 2. Action Success Rate（動作成功率，ASR）
回傳有效資料（而非錯誤或幻覺）的個別工具呼叫所佔的百分比。

### 3. Unit Cost per Task（每項任務的單位成本）
每完成一個目標所耗用的總 token 數加上基礎設施成本（Sandbox、API 呼叫）。

---

## 以 LLM-as-Judge 評估步驟品質

我們使用更強大的模型（Claude Opus 4.7、GPT-5.5 reasoning）來審查較小型 agent 的 **Reasoning Log（推理紀錄）**。
- **Thought Quality（思考品質）**：agent 使用工具 X 的邏輯是否確實是從觀察結果 Y 推導而來？
- **Redundancy Check（冗餘檢查）**：agent 是否重複執行了剛剛才做過的搜尋？
- **Feedback Loop（回饋迴路）**：這個「Judge」的輸出接著會被用於 **DPO（Direct Preference Optimization，直接偏好最佳化）**，以校準 agent 未來的行為。

---

## 生產環境評估

生產團隊會採用 **Shadow Execution（影子執行）**。
1. **V1 Agent** 對使用者做出回應。
2. **V2（實驗版）Agent** 在「隱藏 Sandbox」中執行相同的查詢。
3. **The Comparison（比較）**：我們比較這兩條軌跡。若 V2 能持續以更少的步驟解決任務且不違反安全規範，我們便將其晉升至生產環境。

---

## 面試問題

### Q：當環境是非確定性（non-deterministic）時（例如網頁），你會如何評估 agent？

**理想答案：**
我們會使用 **Mock Environments（模擬環境）**或 **Snapshotted States（快照狀態）**。為了進行高擬真度的測試，我們會使用容器化的瀏覽器，並在每次測試執行時將其重置為乾淨的狀態。接著我們會將 agent 的軌跡與 **Reference Trace（參考軌跡）**進行比對。若環境確實是即時的（live），我們則採用 **State-Based Verification（以狀態為基礎的驗證）**——不去比對文字，而是檢查外部世界的狀態（例如：「資料庫中是否新增了一筆數值正確的資料列？」）。

### Q：在 Staff 等級的 Agent 設計中，為何「Meandering（繞路、步驟過多）」是一項關鍵失敗？

**理想答案：**
繞路會導致三種失敗：1）**成本（Cost）**：每一個步驟都是一次 LLM 呼叫；2）**延遲（Latency）**：每一個步驟都會增加 2-5 秒；3）**熵（Entropy）**：軌跡越長，agent 遭遇詭異邊界案例並觸發幻覺的機率就越高。標準的解法是 **Step Budgets（步驟預算）**：若 agent 在 10 個步驟內無法解決任務，我們便終止它並升級交由人工處理，以避免「Token Leak（Token 洩漏）」。

---

## 參考資料
- Jimenez et al. "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?" (2024/2025 update)
- Microsoft Research. "AgentBench: A Comprehensive Benchmark for AI Agents" (2024)
- RAGAS. "Agentic Evaluation Module" (2025)

---

*下一篇：[記憶體架構](../08-memory-and-state/01-memory-architectures.md)*
