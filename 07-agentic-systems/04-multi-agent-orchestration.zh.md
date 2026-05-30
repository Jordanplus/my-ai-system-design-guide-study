# 多代理協作（Multi-Agent Orchestration）

複雜系統鮮少只靠單一代理。它們是由各司其職的專業代理所組成的團隊。協作模式已從「盲目管理者（Blind Managers）」演進為**階層式監督者（Hierarchical Supervisors）**、**動態群集（Dynamic Swarms）**，以及由 A2A 等互通性協定所促成的**跨廠商代理網路（Cross-Vendor Agent Networks）**。Gartner 預測，到 2026 年底，將有 40% 的企業應用程式內建針對特定任務的 AI 代理，而 2025 年初這個比例還不到 5%。

## 目錄

- [為什麼要用多代理？](#why)
- [監督者模式（Supervisor Pattern）](#supervisor)
- [管線模式（Pipeline Pattern）](#pipeline)
- [群集與點對點（P2P）](#swarms)
- [圖式協作（Graph-Based Orchestration，2026 主流模式）](#graph-orchestration)
- [透過 A2A 進行跨廠商代理協作](#cross-vendor)
- [2026 年多代理框架版圖](#framework-landscape)
- [代理團隊中的狀態管理](#state)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 為什麼要用多代理？

擁有 50 個工具的單一代理會面臨**認知負荷（Cognitive Load）**。
1. **專業分工**：「Code Agent」可以使用針對 Python 最佳化的模型，而「Search Agent」則使用針對 RAG 最佳化的模型。
2. **平行處理**：多個代理可以同時處理彼此獨立的子任務。
3. **解耦評估**：你可以將「Writer Agent」與「Researcher Agent」分開來評估。

---

## 監督者模式（階層式）

截至 2026 年最常見的企業模式。

- **監督者（Supervisor）**：一個高推理能力的模型（Claude Opus 4.7、GPT-5.5 reasoning、Gemini 3.1 Pro Deep Think），負責拆解使用者的 prompt 並委派給工作代理。
- **工作代理（Workers）**：快速、具成本效益的模型（Claude Haiku 4.5、Gemini 3.1 Flash、GPT-5.5-mini），負責執行實際工作。
- **審查者（Reviewer）**：另一個獨立的代理，負責根據監督者最初的計畫來驗證整合後的輸出。

**架構**：LangGraph 仍是實作這些具狀態感知（state-aware）階層式迴圈的主流框架。截至 2026 年，Claude Agent SDK、Google ADK 與 Microsoft Agent Framework 都原生支援此模式。

---

## 群集（OpenAI 模式）

於 2024 年底開始流行的**群集（Swarms）**，聚焦在「交接（Handoffs）」。

- 一個代理將對話「交接」給另一個代理。
- **核心概念**：`Handoff(TargetAgent)`。
- **優點**：沒有中央「管理者」的瓶頸。對話會在各個專業實體之間自然流動。

---

## 圖式協作（2026 主流模式）

2026 年的架構動能已明顯轉向**圖式協作（graph-based orchestration）**，將代理工作流程建模為帶有型別化狀態（typed state）的有向圖。

### 為什麼圖式勝出

- **明確的控制流程**：節點是代理或函式；邊定義轉換，包括條件分支與迴圈
- **可視覺化**：團隊可以將工作流程當作圖表來檢視與除錯
- **狀態感知**：型別化的狀態物件在圖中傳遞，使檢查點（checkpointing）與恢復（resumption）成為可能

### 框架支援

| 框架 | 圖模型 | 關鍵差異點 |
|-----------|-------------|-------------------|
| **LangGraph**（24k stars） | 帶有型別化狀態的命令式 DAG | 最成熟、社群最廣 |
| **Google ADK**（17k stars） | 內建 A2A 的代理圖 | 原生整合 Google Cloud |
| **Microsoft Agent Framework** | 工作流程圖（循序、並行、交接） | 統一 .NET + Python、企業治理 |
| **Claude Agent SDK** | 以監督者為基礎的階層式樹 | 內建工具（bash、editor）、可正式上線 |

### 迴紋針模式（Paperclip Pattern，大規模階層式代理）

2026 年一項值得注意的發展是 **Paperclip**（於 2026 年 3 月發布後三週內獲得 44,900 個 GitHub stars）。它採用階層式模型：一個 CEO 代理接收最上層的目標、加以拆解，並委派給管理者代理，由管理者代理生成並協調工作代理。此模式展示了深度階層式的多代理樹如何處理複雜的真實世界任務。

> *於 2026 年 5 月查證。*

---

## 透過 A2A 進行跨廠商代理協作

**Agent-to-Agent（A2A）協定**（參見 [Tool Use and MCP](03-tool-use-and-mcp.md#a2a)）促成了一種全新的多代理模式：**跨廠商協作（cross-vendor orchestration）**。在 A2A 出現之前，多代理系統要求所有代理共用相同的框架與執行環境。如今則是：

1. **代理探索（Agent Discovery）**：協作者透過代理的 **Agent Cards**（描述能力的 JSON metadata）找到專業代理
2. **任務委派（Task Delegation）**：協作者透過 HTTP/SSE 將結構化任務送給遠端代理
3. **非同步進度（Async Progress）**：遠端代理串流回傳狀態更新；協作者可同時平行委派給其他代理
4. **結果收集（Result Collection）**：最終產物被回傳並整合進協作者的狀態中

**正式上線範例**：一個採購系統中，協作者（LangGraph）將法規遵循檢查委派給專業代理（Google ADK）、將庫存查詢委派給一個 MCP 連接的工具，並將合約產生委派給一個 CrewAI crew——它們分別透過 A2A 與 MCP 進行通訊。

> *於 2026 年 5 月查證。來源：a2a-protocol.org*

---

## 2026 年多代理框架版圖

如今每個主要的 AI 實驗室都推出了代理框架。截至 2026 年 5 月，多代理協作的版圖如下：

| 框架 | 提供者 | 多代理模型 | 狀態 |
|-----------|----------|-------------------|--------|
| **LangGraph** | LangChain | 圖式、最具彈性 | 正式上線（126k stars） |
| **Claude Agent SDK** | Anthropic | 內建工具的監督者樹 | GA（Python + TypeScript） |
| **Google ADK** | Google | 圖式並原生支援 A2A | GA（Python、TS、Java、Go） |
| **Microsoft Agent Framework** | Microsoft | 工作流程 + 群組聊天模式 | RC 1.0（2026 年 2 月），GA 訂於 2026 年 Q2 |
| **OpenAI Agents SDK** | OpenAI | 帶有護欄（guardrails）的交接式群集 | GA（Python + TypeScript） |
| **CrewAI** | CrewAI Inc. | 帶有 Flows 的角色制 crews | v1.13（60% 以上的財星 500 大企業採用） |
| **Smolagents** | HuggingFace | 輕量、開源 | 積極開發中 |

**關鍵趨勢**：沒有任何單一框架能在全部四種多代理模式（監督者、群集、管線、辯論）上都表現出色。團隊愈來愈傾向組合多個框架——例如，用 LangGraph 處理複雜協作，搭配 CrewAI 處理面向商業使用者的自動化。

> *於 2026 年 5 月查證。*

---

## 狀態管理

多代理系統中最大的挑戰是**共用黑板（Shared Blackboard）**。

1. **本地狀態（Local State）**：僅特定代理可見的上下文。
2. **全域狀態（Global State）**：所有代理皆可見的共享記憶體（例如最終草稿）。
3. **寫入衝突（Write Conflicts）**：當兩個代理試圖修改同一個全域狀態時。
   - **最佳實務**：使用**交易式交接（Transactional Handoffs）**。代理只有在「擁有」鎖（lock）時才能寫入全域狀態。

---

## 點對點（P2P）辯論

對於高準確度的任務（例如法律或醫療），我們會採用**代理辯論（Agentic Debate）**。
- **代理 A**：提出一個答案。
- **代理 B**：試圖找出代理 A 答案中的瑕疵。
- **代理 A**：根據 B 的批評來修正答案。
- **結果**：收斂出一個比任何單一代理所能產生的都更高品質的結果。

---

## 面試題

### Q：「監督者」多代理架構的主要失效模式有哪些？

**有力的回答：**
首要的失效模式是**拆解失誤（Decomposition Failure）**。如果監督者代理將任務拆解成邏輯上不一致、或帶有隱藏相依性的子任務，工作代理就會針對*錯誤的問題*產生正確的答案。標準的解法是**迭代式規劃（Iterative Planning）**：監督者必須先從工作代理那裡取得「子任務可行性的確認」，工作代理才開始執行。另一種失效模式是**上下文稀釋（Context Dilution）**，亦即全域狀態被工作代理的日誌塞得過於臃腫，導致監督者失去了對「大局」的掌握。

### Q：你如何在「鏈式串接（Sequence of Chains）」與「多代理圖（Multi-Agent Graph）」之間做選擇？

**有力的回答：**
當任務是線性且確定性的（例如 擷取 -> 翻譯 -> 摘要）時，我會使用**鏈式串接（Sequence of Chains）**。當任務是**非線性**或需要**條件式迴圈**時，我會使用**多代理圖**（例如 LangGraph）。舉例來說，如果「翻譯」步驟可能失敗、需要回到「擷取」以取得更多上下文，靜態的鏈就會中斷，但圖可以透過路由回到較早的節點來自我修正。

### Q：什麼情況下你會用 A2A 來進行多代理協作，而不是把所有代理都放在單一框架裡？

**有力的回答：**
當團隊擁有所有代理、它們共用相同的執行環境，且代理呼叫之間的低延遲至關重要時，我會把代理留在單一框架裡。當需要跨越**組織或廠商邊界**時，我才會引入 A2A——例如，當我的協作者需要委派給由另一個團隊維護的法規遵循代理，或當整合第三方的專業代理（例如法律審查服務）時。A2A 會增加 HTTP 的額外開銷，但能透過 Agent Cards 提供**廠商中立性**、**獨立擴展**與**能力探索**。經驗法則是：同一團隊、同一框架；不同團隊或廠商，使用 A2A。

---

## 參考資料
- Wu et al. "AutoGPT: An Autonomous GPT-4 Experiment"（歷史文獻／2025 更新）
- Li et al. "Camel: Communicative Agents for 'Mind' Exploration"（2023/2025）
- OpenAI. "Swarms Framework"（2024/2025）
- Google. "Agent2Agent Protocol"（2025/2026）
- Gartner. "Predicts 2026: AI Agent Market"（2025）
- Andrew Ng. "Agentic Design Patterns"（2025/2026）

---

*下一篇：[Agent Memory and State](05-agent-memory-and-state.md)*
