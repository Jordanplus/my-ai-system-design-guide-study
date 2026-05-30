# 錯誤處理與復原

Agent 會以非確定性（non-deterministic）的方式失敗。錯誤處理已經從「Try-Catch 區塊」演進到 **Agentic 自我修正（Self-Correction）** 與 **有狀態回滾（Stateful Rollbacks）**，而 LangGraph 與 Microsoft Agent Framework 等框架則提供了原生的 checkpoint/resume 基本元件。

## 目錄

- [Agent 失敗的分類學](#fail-types)
- [自我修正迴圈](#correction)
- [有狀態回滾（Checkpointing）](#rollbacks)
- [「卡在迴圈中」的修正方法](#stuck)
- [優雅降級](#degradation)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## Agent 失敗的分類學

1. **幻覺工具（Hallucinated Tools）**：呼叫一個並不存在的工具。
2. **Schema 違規（Schema Violation）**：對一個真實存在的工具傳入錯誤的參數。
3. **環境錯誤（Environment Error）**：工具存在，但外部 API 掛了。
4. **邏輯停滯（Logical Stall）**：Agent 反覆執行同一個失敗的動作（ReAct 死亡迴圈）。

---

## 自我修正迴圈

現在錯誤被視為 **資訊的 Token（Tokens of Information）**。

- **模式（Pattern）**：當一個工具失敗時，錯誤訊息不只是被記錄下來而已；它會被當成 prompt 餵回給模型：*「Action failed with error: X. Reflect on why this happened and provide an alternative strategy.」*
- **推理模型（Reasoning Models）**（Claude Opus 4.7 extended thinking、GPT-5.5 reasoning、DeepSeek-R2）：這些模型在這方面表現極佳，因為它們會在隱藏的 Chain-of-Thought 過程中「內化」這個錯誤，進而帶來高出許多的一次性（one-shot）復原率。

---

## 有狀態回滾（Checkpointing）

對於長時間執行的 agent 來說，第 9 步的錯誤不應該讓整個專案崩潰。

- **Checkpoints**：高可靠度的系統（使用 LangGraph 或類似工具）會在每一次成功的工具呼叫後，將「狀態快照（State Snapshot）」儲存到 DB。
- **回滾（The Rollback）**：如果 agent 進入了邏輯停滯狀態，supervisor agent 可以將 **common-state 重設** 到第 5 步——也就是最後一個「安全（Safe）」狀態——並強制走一條不同的路徑。

---

## 「卡在迴圈中」的修正方法

無限迴圈是 agentic 系統中第 #1 的成本黑洞。

**解決方案**：**基於計數器的介入（Counter-Based Intervention）**。
1. 如果在同一個 session 中，同一個 `(Tool, Args)` tuple 出現了 3 次，orchestrator 就會中斷模型。
2. 它會注入一道強制性的 **「轉向指令（Pivot Instruction）」**：*「You have tried searching for 'X' three times. This path is dead. You MUST try a different tool or admit you are stuck.」*

---

## 優雅降級

如果高度推理的 agent（Claude Opus 4.7、GPT-5.5 reasoning）持續失敗，我們會降級到：
- **簡化版 Agent（Simplified Agent）**：一個搭配更少、更可靠工具的較小模型。
- **僅 RAG 模式（RAG-only Mode）**：停用各種動作，僅根據知識庫提供概念性的答案。
- **升級給人類處理（Human Escalation）**：（見下一章）。

---

## 面試問題

### Q：為什麼傳統的「例外處理（Exception Handling）」（Try/Catch）對 Agentic 系統來說並不足夠？

**強而有力的回答：**
在傳統軟體中，例外（exception）是一道「停止（Stop）」命令。在 agentic 系統中，模型才是「駕駛（Driver）」。如果系統只是停下來，使用者的任務就失敗了。我們改用 **錯誤注入（Error Injection）** 來取代例外處理。我們在平台層級攔截例外，並將它轉化為給模型的 **合成觀察（Synthesized Observation）**。這讓模型得以「推理（Reason）」並繞過這個失敗。Try/Catch 只能修正程式碼；錯誤注入則能讓模型修正 **計畫（Plan）**。

### Q：你如何處理「靜默失敗（Silent Failures）」（也就是工具回傳 200 OK，但資料是錯的）？

**強而有力的回答：**
靜默失敗是最危險的。我們會實作 **輸出驗證 Agent（Output Validation Agents）**。對於關鍵步驟，我們不會直接接受工具的輸出。我們會把輸出導向一個「驗證 Agent（Verifier Agent）」（通常是一個較小、較快的模型），它唯一的工作就是檢查：*「這個工具輸出真的有回答到所提供的查詢嗎？」* 如果 Verifier 說「沒有」，它就會觸發一個自我修正迴圈，彷彿這是一個硬性錯誤（hard error）一般。

---

## 參考資料
- LangGraph. "Persistence and Checkpointing" (2025)
- Shinn et al. "Reflexion: Learning from Errors" (2024 update)
- Microsoft. "Managing Hallucinations in Agentic Systems" (2025)

---

*下一篇：[Human-in-the-Loop 模式](08-human-in-the-loop-patterns.md)*
