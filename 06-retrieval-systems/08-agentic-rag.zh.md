# Agentic RAG

Agentic RAG 從「線性管線（Linear Pipeline）」轉向 **「推理迴圈（Reasoning Loop）」**。它不再只檢索一次，而是由 agent 決定*何時*以及*要*檢索什麼來解決一個查詢。主流的生產環境模式包括 Self-RAG（模型發出 reflection token）、Corrective RAG（具備修正路由的檢索評估器）、Adaptive RAG（由分類器選擇管線深度）、針對文件的 ReAct，以及 multi-hop 查詢分解。LangGraph 是最常見的有狀態迴圈控制流程執行環境；LlamaIndex Workflows 則常用於單一管線、檢索密集型的變體。

## 目錄

- [線性 RAG vs. Agentic RAG](#comparison)
- [Self-RAG（自我反思）](#self-rag)
- [Corrective RAG（CRAG）](#crag)
- [Multi-Hop 推理迴圈](#multi-hop)
- [Agentic 過濾與計畫修訂](#planning)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 線性 RAG vs. Agentic RAG

| 模型 | 線性 RAG | Agentic RAG |
|-------|------------|-------------|
| **結構** | 預先決定的順序 | 動態迴圈 |
| **自我修正** | 無 | 高（可重新檢索） |
| **查詢複雜度**| 簡單（1 步） | 困難（多步） |
| **延遲** | 低（固定） | 可變（多回合） |

**原則**：當查詢需要「綜合性的佐證（Synthesized Proof）」而不只是「文件匹配（Document Match）」時，才使用 Agentic RAG。要為它編列預算：一個 3-4 次迭代的迴圈端到端通常需要 8-12s，因此若你的 UX 需要 3s 以下的回應時間，就應該把簡單查詢路由到快速路徑（Adaptive RAG）。

---

## Self-RAG（自我反思）

在 2024/2025 年開始流行的 **Self-RAG** 使用「Critic Token」來評估自己的工作成果。

1. **Retrieve（檢索）**：模型取出 Top-K 個 chunk。
2. **Evaluate（評估）**：資訊是否相關？（CRITIC：`Relevant`）
3. **Generate（生成）**：答案是否有依據支撐？（CRITIC：`Supported`）
4. **Iterate（迭代）**：若答案缺乏支撐，模型會*自動*觸發更廣泛的搜尋。

---

## Corrective RAG（CRAG）

CRAG 在檢索與生成之間加入了一層「可靠性層（Reliability Layer）」。

- **邏輯**： 
  - 若檢索結果**正確（Correct）**：直接生成。
  - 若檢索結果**模稜兩可（Ambiguous）**：使用 Web-Search 工具來補充。
  - 若檢索結果**不正確（Incorrect）**：捨棄該脈絡，改用外部搜尋或 fallback 邏輯。

---

## Multi-Hop 推理迴圈

對於像「收購 Figma 的那家公司，其 CEO 是誰？」這類問題，系統必須：
1. **Hop 1**：搜尋「誰收購了 Figma？」（結果：Adobe）。
2. **Hop 2**：搜尋「Adobe 的 CEO」（結果：Shantanu Narayen）。

**Agentic 模式**：agent 維護一個「State Object（狀態物件）」，並在每次檢索後更新其「Sub-goal（子目標）」，直到整條推理鏈完成。

---

## Agentic 過濾與計畫修訂

現代 agent 使用 **Sub-Step Plans（子步驟計畫）**。
- agent 不會做一次大型檢索，而是寫下一份計畫：「我會先查我們的內部資料庫找 X，接著我會查公開 API 找 Y。」
- **修訂式規劃（Revised planning）**：若步驟 1 失敗，agent 會*重寫*步驟 2。

---

## 面試問題

### Q：Agentic RAG 中的「推理－檢索平衡（Reasoning-Retrieval Balance）」是什麼？

**優秀的回答：**
在 agentic 迴圈中，每一個「推理回合」都會增加 token 成本與使用者延遲。生產環境工程師的目標是找出「檢索門檻（Retrieval Threshold）」。我們會使用 **Token-Budgeting（token 預算）**，只允許 agent 進行 3-5 個「回合」，之後就強制給出最終答案。我們也會使用 **Speculative Retrieval（推測式檢索）**——agent 預測它接下來會採取的 2 個步驟，並同時為兩者進行檢索，以降低往返延遲。

### Q：為什麼 Agentic RAG 通常能帶來更高的品質，卻有較低的「可靠性（Reliability，即確定性 Determinism）」？

**優秀的回答：**
Agentic RAG 之所以是非確定性的，是因為模型在每一步都在「決定」自己的路徑。使用者查詢的微小變動，可能導致 agent 選擇不同的工具或搜尋策略，進而產生不同的答案格式。標準的緩解做法是採用 **Constrained Agent Frameworks（受限 agent 框架）**（例如 LangGraph 或 DSPy），其中「可能路徑的圖（Graph of possible paths）」被嚴格定義，即使在這些路徑*之間*的選擇仍是隨機的。

---

## 參考資料
- Asai et al. "Self-RAG: Learning to Retrieve, Generate, and Critique" (2024/2025)
- Yan et al. "Corrective Retrieval Augmented Generation (CRAG)" (2024)
- LangChain. "Agentic RAG with LangGraph" (2025)

---

*下一篇：[進階檢索模式](09-advanced-retrieval-patterns.md)*
