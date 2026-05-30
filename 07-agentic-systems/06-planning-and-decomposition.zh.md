# 規劃與任務拆解

規劃是讓代理人能夠解決多階段問題而不會「漫無目的遊蕩」的「System 2」元件。生產級代理人已經從單純的「Chain-of-Thought」演進到 **遞迴拆解（Recursive Decomposition）** 與 **樹搜尋（Tree Search）**，並由具備原生推理能力的模型（Claude Opus 4.7、GPT-5.5 extended thinking、DeepSeek-R2）在內部完成繁重的規劃工作。

## 目錄

- [規劃的光譜](#spectrum)
- [靜態規劃 vs. 動態規劃](#static-vs-dynamic)
- [Chain-of-Thought (CoT) 與 o1 推理](#cot)
- [遞迴式任務拆解](#decomposition)
- [代理人路徑的樹搜尋（MCTS）](#mcts)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 規劃的光譜

| 方法 | 策略 | 複雜度 | 最適合的場景 |
|--------|----------|------------|----------|
| **線性（Linear）** | 一次一步 | 低 | 簡單的工具 |
| **分支（Branching）** | If-Then-Else 邏輯 | 中 | 條件式流程 |
| **階層式（Hierarchical）** | 主計畫 -> 子計畫 | 高 | 軟體工程 |
| **搜尋式（Search-Based）** | 在內部嘗試多條路徑 | 最高 | 科學研究 |

---

## 靜態規劃 vs. 動態規劃

### 靜態（Plan-and-Solve）
代理人寫出一份 10 步的計畫，並嚴格依此執行。
- **優點**：效能高，容易平行化。
- **缺點**：脆弱。如果第 2 步失敗，第 3 到第 10 步就全都失效了。

### 動態（Adaptive）
代理人寫出一份計畫，但在每次工具呼叫後都會 **重新評估（Re-evaluate）**。
- **最佳實務**：採用 **Checkpointed Planning（檢查點式規劃）**。在每個主要子目標完成後，代理人都被強制將其進度「Commit」到狀態儲存區，以便在計畫失敗時能進行復原與「Backtracking（回溯）」。

---

## CoT 與 o1 推理

模型內部的「Thinking」視窗（推理階段的擴展，Inference scaling）扮演了 **隱藏規劃者（Hidden Planner）** 的角色。
- 我們不使用獨立的「Planner LLM」，而是使用一個推理模型（Claude Opus 4.7、GPT-5.5 extended thinking、DeepSeek-R2）來產生一份「Mental Draft（心智草稿）」。
- 這份草稿會被轉譯成一個 **Task DAG（Directed Acyclic Graph，有向無環圖）**，由編排器（orchestrator）負責執行。

---

## 遞迴式任務拆解

對於規模龐大的任務（例如「打造一個全端應用程式」），我們會使用 **子代理人生成（Sub-Agent Spawning）**。
1. **Master Agent（主代理人）**：將「Project（專案）」拆解為「Frontend（前端）」、「Backend（後端）」與「DB（資料庫）」。
2. **Sub-Agents（子代理人）**：各自接收一個「Sub-Goal（子目標）」並執行自己的拆解。
3. **Consolidation（整合）**：Master Agent 將各項結果合併。

**關鍵細節**：每個子代理人都只會被賦予 **最小化的上下文（Minimal Context）**（只給它真正需要的部分），以防止 token 膨脹與幻覺。

---

## 樹搜尋（MCTS）

對於高風險的決策，我們會在代理人迴圈中使用 **Monte Carlo Tree Search（MCTS，蒙地卡羅樹搜尋）**。
- 代理人「Simulates（模擬）」10 種可能的工具呼叫。
- 一個 **Reward Model（獎勵模型）**（或一個獨立的 LLM prompt）為每次模擬評分。
- 代理人會選擇獎勵最高的路徑。

---

## 面試問題

### Q：你如何防止代理人在任務拆解過程中陷入「無限遞迴（Infinite Recursion）」？

**強力的回答：**
我們實作 **Decomposition Depth Limits（拆解深度限制）**（通常為 3 層）與 **Granularity Checks（粒度檢查）**。在生成子代理人之前，我們會詢問 Supervisor 模型：「這個任務是否已經小到可以用單一次工具呼叫解決？」如果是，就直接執行；如果不是，就進行拆解。我們也使用一個 **Global Controller（全域控制器）** 來追蹤總「Agent Count（代理人數量）」，以防止可能耗盡 API 預算的遞迴炸彈（fork bomb）。

### Q：為什麼「Plan Revision（計畫修訂）」往往比「Plan Generation（計畫生成）」更昂貴？

**強力的回答：**
計畫生成是一種「全新開始（Fresh Start）」。計畫修訂則需要 **Context Re-evaluation（上下文重新評估）**——模型必須理解 *已經完成了什麼*、*前一步為何失敗*，以及如何在不破壞先前成果的情況下進行修正。這需要更高的「Reasoning Density（推理密度）」。在生產環境中，我們通常會在 **Revision（修訂）** 步驟使用較大的模型（例如 Sonnet 3.7 或 o1），而在初始的計畫生成階段則使用較小的模型。

---

## 參考資料
- Silver et al. "Mastering the game of Go with deep neural networks and tree search"（應用於 LLMs，2024/2025）
- Wang et al. "Self-Consistency Improves Chain of Thought Reasoning"（2022/2025 update）
- LangGraph. "Multi-Agent Planning Patterns"（2025）

---

*下一篇：[錯誤處理與復原](07-error-handling-and-recovery.md)*
