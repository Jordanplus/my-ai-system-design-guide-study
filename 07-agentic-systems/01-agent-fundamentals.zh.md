# Agent 基礎

Agent 是由 LLM 驅動的系統，已從「聊天」進化到「自主問題解決」。其定義已從單純的 ReAct 迴圈，轉變為運用內建「System 2」思考的 **Closed-Loop Reasoning Systems（閉迴路推理系統）**（Claude Opus 4.7 extended thinking、GPT-5.5 reasoning、DeepSeek-R2、Gemini 3.1 Pro Deep Think）。

## 目錄

- [The Agent Formula](#formula)
- [System 1 (LLM) vs. System 2 (Reasoning Model)](#systems)
- [Agency Levels (Autonomous Spectrum)](#levels)
- [Core Components](#components)
- [The Agent Lifecycle](#lifecycle)
- [Interview Questions](#interview-questions)
- [References](#references)

---

## The Agent Formula

現代的 agency 經常被描述為：
`Agent = Reasoning Model + Tool Use + Persistent Memory + Environment Feedback`

**細微差異**：在 2023 年，agent 只是包覆在 chat model 外層的「wrapper」。如今，agent 越來越趨向**整合化（Integrated）**。前沿模型（Claude Opus 4.7、具備 reasoning 的 GPT-5.5、DeepSeek-R2）已將「Thinking」流程內建於 pre-training 中，使 agent loop 更加穩定，較不易發生「停滯（stalling）」。

---

## System 1 vs. System 2 Thinking

設計 agent 架構時，必須選擇正確的「思考模式（Thinking Mode）」：

| 模式 | 認知類型 | 類比 | 目前的技術堆疊 |
|------|----------------|---------|---------------|
| **System 1** | 快速、直覺、反應式 | 反射動作 | Claude Haiku 4.5 / Sonnet 4.6 / GPT-5.5-mini / Gemini 3.1 Flash |
| **System 2** | 緩慢、邏輯、規劃 | 深思熟慮 | Claude Opus 4.7 / GPT-5.5 reasoning / DeepSeek-R2 / Gemini 3.1 Pro Deep Think |

**設計模式**：在「Fast UI」與「Routing」場景使用 System 1 模型；在「Decision Gates」與「Complex Planning」場景使用 System 2 模型。

---

## Agency Levels

並非每個自主系統都是「Agent」。我們依據 **Level of Agency（自主程度）** 對其進行分類：

1. **L0：Scripted Chains（腳本化串接）**：固定順序（例如標準的 LangChain）。
2. **L1：Tool-Enabled（具工具能力）**：模型會挑選工具，但不會進行規劃。
3. **L2：ReAct Agent**：「Thought -> Action -> Observation」的簡單迴圈。
4. **L3：Autonomous Planner（自主規劃者）**：將目標拆解為由子任務組成的圖（graph）。
5. **L4：Ambient Agent（環境式 Agent）**：在背景執行，僅在必要時才介入。

---

## Core Components

### 1. The Reasoning Model（決策核心）
Agent 的 CPU。它決定「邁向成功的路徑」。

### 2. Tools（四肢）
讓 agent 得以影響外部世界的介面（API、瀏覽器、資料庫）。
> [!Note]
> **Model Context Protocol (MCP)** 如今已成為工具互通性的業界標準，並獲得 Anthropic、OpenAI、Google、Microsoft 與 AWS 的採用。其治理權已於 2025 年 12 月移交給 Linux Foundation 旗下的 Agentic AI Foundation。

### 3. Memory（經驗）
- **短期（Short-term）**：Context window（KV Cache）。
- **長期（Long-term）**：Vector DB 或持久化狀態（例如 Mem0）。

---

## The Agent Lifecycle

1. **Intake（接收）**：接收使用者目標。
2. **Decomposition（拆解）**：將目標拆分為子步驟。
3. **Execution（執行）**：呼叫工具並處理結果。
4. **Reflection（反思）**：評估該次觀察是否讓 agent 更接近目標。
5. **Completion（完成）**：為使用者彙整出最終佐證結果。

---

## Interview Questions

### Q：為什麼「Reasoning Model」（如 Claude Opus 4.7 或具備 extended thinking 的 GPT-5.5）在 agency 上會比標準 LLM 更出色？

**強力解答：**
標準 LLM（System 1）是基於模式比對來預測*下一個 token*。當它們在 tool call 中遇到錯誤時，往往會幻覺出一個修正方案，而不是承認失敗。Reasoning Model 則在 inference 期間運用 **Chain-of-Thought (CoT)**，會在輸出回應前透過多個隱藏回合進行「思考」。對 agent 而言，這代表更高的 **Path Reliability（路徑可靠性）**——由於模型已在內部模擬過失敗情境，因此明顯較不容易陷入無限迴圈，或重複嘗試同一個會失敗的動作。

### Q：在長時間執行的任務中，你會如何防止「Agentic Drift（Agent 偏移）」？

**強力解答：**
Agentic Drift 發生於子步驟讓 agent 偏離原始目標太遠，以致失去脈絡的情況。標準的解決方案是 **Goal Anchoring（目標錨定）**：將「Original Objective（原始目標）」以釘選的 system message 形式納入，並使用 **Secondary Observer Model（次要觀察模型）**（一個較小、較便宜的模型）對 agent 的每個動作相對於原始目標進行評分。若分數低於門檻，agent 就會被強制從根節點「重新規劃（re-plan）」。

---

## References
- Kahneman, D. "Thinking, Fast and Slow"（應用於 AI，2025）
- OpenAI. "Learning to Reason with LLMs"（2024）
- DeepSeek. "R1: Cold-Start Data for Reasoning"（2025）

---

*下一篇：[Reasoning Loops: ReAct and Beyond](02-reasoning-loops-react-and-beyond.md)*
