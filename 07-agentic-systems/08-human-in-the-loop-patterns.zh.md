# Human-in-the-Loop 模式

沒有任何 agent 是 100% 可靠的。**Human-in-the-Loop（HITL）** 正是在高風險環境中確保安全性與正確性的橋樑。生產級技術堆疊已經超越了「核准按鈕」的階段，邁向 **Co-Reasoning（協同推理）** 與 **Interrupt-Based Steering（以中斷為基礎的引導）**，並由 LangGraph（interrupt+resume）與 Microsoft Agent Framework 等框架原生提供支援。

## 目錄

- [HITL 光譜](#spectrum)
- [中斷與斷點](#interrupts)
- [Time-Travel 除錯（狀態編輯）](#time-travel)
- [Co-Reasoning（共享 Scratchpad）](#co-reasoning)
- [以信心度為基礎的升級](#escalation)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## HITL 光譜

| 模式 | Agent 自主性 | 人類角色 | 最適用於 |
|---------|---------------|------------|----------|
| **Human-in-command** | 低 | 主導每一個步驟 | 高風險的法律／醫療 |
| **Human-as-filter** | 中 | 核准／編輯最終輸出 | 內容生成 |
| **Human-as-backup** | 高 | 僅在發生錯誤時介入 | 客戶支援 |
| **Human-on-the-loop** | 最高 | 在任務完成後稽核紀錄 | 高流量分析 |

---

## 中斷與斷點

現代架構（LangGraph、Microsoft Agent Framework）採用 **Deterministic Breakpoints（確定性斷點）**。

- **模式**：系統被硬性編碼為在呼叫某個特定的敏感工具之前「暫停」（例如 `execute_purchase` 或 `delete_user`）。
- **決策**：環境會等待使用者送出 `approve` 或 `reject` 訊號。
- **狀態保存**：在人類採取行動之前，agent 的推理狀態會被「凍結」在資料庫中。

---

## Time-Travel 除錯（狀態編輯）

標準 agent 是「單向」的。如果它們在第 3 步犯了錯，整個工作階段通常就毀了。
- **創新點**：**State Injection（狀態注入）**。人類審查者可以「回到」第 3 步的狀態，編輯 agent 的 observation 或 thought，然後「恢復」執行。
- **影響**：它讓人類能夠把 agent 從錯誤的路徑上「引導」回來，而不必從零開始。

---

## Co-Reasoning（共享 Scratchpad）

人類不再是「裁判」，而是成為 **「夥伴」**。
- Agent 會把它的 **Scratchpad**（內部思考）展示給人類。
- 其特徵可描述為：*「我打算使用工具 A，因為事實 B。你覺得這樣對嗎？」*
- **好處**：在推理錯誤*轉化*為行動*之前*就將其攔截。

---

## 以信心度為基礎的升級

利用支援「Logprobs」或內建推理步驟的模型，我們可以計算出一個 **Uncertainty Score（不確定性分數）**。

- 如果分數超過某個閾值，agent 會 **自動暫停** 並向人類操作員發送通知。
- **範例**：一個嘗試解決複雜帳務爭議的 agent 意識到使用者的意圖含糊不清。它便停下來說：*「我不是 100% 確定該如何處理這個特定的退款案例。請稍候，我去請一位人類專家來看看這件事。」*

---

## 面試問題

### Q：你會如何設計一個不會讓人類操作員「疲乏」的 HITL 系統？

**有力的回答：**
我們使用 **Threshold Tuning（閾值調校）**。我們不會對每一個動作都要求核准。我們只會在以下情況觸發 HITL：1）高風險的「寫入」類工具、2）低信心度的推理步驟，或 3）違反企業所設定之「政策」的行動。此外，我們會提供人類一份 **Contextual Summary（情境摘要）**——我們不會給他們看整份紀錄，而是只展示一句話的「Diff」，說明 agent 想要做什麼。這把「審查的認知負荷」從數分鐘縮短到數秒鐘。

### Q：HITL 中的「Over-Reliance（過度依賴）」風險是什麼？你會如何緩解它？

**有力的回答：**
過度依賴發生在人類開始不讀紀錄就直接點「核准」的時候。我們透過 **Forced Review Checkpoints（強制審查檢查點）**（例如，人類必須在所提議的計畫中至少編輯一個字）或 **Synthetic Error Injections（合成錯誤注入）**（刻意在 1% 的時間裡向人類展示一份「錯誤」的計畫，看看他們是否會抓到）來緩解它。如果他們通過了這個「陷阱」，就繼續進行；如果他們失敗了，就會被標記以接受額外的訓練。

---

## 參考資料
- Wu et al. "Co-reasoning: Human-AI Collaboration Patterns" (2025)
- LangChain. "Human-in-the-loop in LangGraph" (2024/2025)
- Anthropic. "Designing for Safety and Human Oversight" (2024)

---

*下一篇：[Agentic 安全性與沙箱化](09-agentic-security-and-sandboxing.md)*
