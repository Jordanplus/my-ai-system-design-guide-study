# 框架選型指南

過去一年間,AI 框架的版圖已大幅整併。每一家主要的 AI 實驗室如今都推出了自己的 agent SDK,Microsoft 將 AutoGen 與 Semantic Kernel 合併為統一的 Agent Framework,而互通協定(MCP、A2A)也已成為基本配備。本指南提供一套**決策矩陣(Decision Matrix)**,協助你依據生產環境需求、團隊專業能力與系統規模來選擇技術堆疊。

## 目錄

- [框架版圖](#landscape)
- [決策矩陣](#matrix)
- [自建 vs. 採購 vs. 框架](#build-vs-buy)
- [應避免的反模式](#anti-patterns)
- [Staff 等級的建議](#recommendation)
- [面試問題](#interview-questions)

---

## 框架版圖

### 編排與 Agent 框架

| 框架 | 層級 | 主要價值 | 關鍵弱點 |
|-----------|------|---------------|--------------|
| **LangGraph** | L1(核心) | 精確的狀態控制、以圖為基礎 | 複雜、學習曲線陡峭 |
| **DSPy** | L1(核心) | 可靠性與最佳化 | 前期成本(訓練) |
| **LlamaIndex**| L2(資料) | 進階檢索(RAG) | 邏輯彈性 |
| **CrewAI** | L3(應用) | 商業流程速度、企業級 RBAC | 隱藏失敗 |
| **MS Agent Framework** | L1(企業) | 統一 .NET + Python,取代 AutoGen + SK | RC 狀態(GA Q2 2026) |

### Agent SDK(各實驗室專屬)

| 框架 | 層級 | 主要價值 | 關鍵弱點 |
|-----------|------|---------------|--------------|
| **Claude Agent SDK** | L1(Agent) | 內建工具、生產級 agent loop | 需要 Anthropic API |
| **OpenAI Agents SDK** | L1(Agent) | 輕量化交接(handoffs)、guardrails | 以 OpenAI 為中心 |
| **Google ADK** | L1(Agent) | 多語言、原生 A2A + Google Cloud | 偏向 Google 生態系 |

### 編碼 Agent

| 框架 | 層級 | 主要價值 | 關鍵弱點 |
|-----------|------|---------------|--------------|
| **Claude Code** | L1(編碼) | 自主式 CLI 編碼 agent | 需要 Anthropic API |
| **Cursor / Windsurf** | L2(IDE) | 緊密的 IDE + agent 整合 | 閉源基礎設施 |
| **OpenHands** | L2(編碼) | 開源自主式 agent | 需自行託管 |

> **2026 年 4 月備註**:Semantic Kernel 已不再列為獨立框架。它已被併入 Microsoft Agent Framework。現有的 SK 使用者應規劃遷移。

---

## 決策矩陣

**請使用以下邏輯來選擇你的技術堆疊:**

### 核心編排
1. **是純粹的 RAG 應用嗎?** → **LlamaIndex**。
2. **是否需要長時間運行的狀態 / Human-in-the-loop?** → **LangGraph**。
3. **高可靠性(99%+)與跨模型可移植性是否至關重要?** → **DSPy**。
4. **你是 C#/.NET 的企業團隊嗎?** → **Microsoft Agent Framework**(取代 Semantic Kernel + AutoGen)。
5. **你正在為商業使用者打造高階自動化嗎?** → **CrewAI + Flows**。

### Agent SDK(依你的主要模型供應商選擇)
6. **在 Claude / Anthropic API 上打造 agent?** → **Claude Agent SDK**(Python/TS,內建檔案/程式碼/命令工具)。
7. **在 OpenAI API 上打造 agent?** → **OpenAI Agents SDK**(輕量化交接、guardrails、MCP 支援)。
8. **在 Google Cloud / Gemini 上打造 agent?** → **Google ADK**(原生 A2A、Vertex AI 部署、多語言)。
9. **需要跨廠商的 agent 通訊?** → 在以上任一框架之上使用 **A2A 協定**。

### 編碼 Agent
10. **你正在執行檔案系統層級的自主式編碼任務嗎?** → **Claude Code**(CLI)或 **Cline**(VS Code)。
11. **需要能搭配任何 LLM 運作的開源編碼 agent?** → **OpenHands**(Docker)。
12. **想要最佳的 AI IDE 體驗?** → **Cursor**(閉源)或 **Windsurf**(Codeium)。

---

## 自建 vs. 採購 vs. 框架

身為 Staff Engineer,你必須抗拒**框架臃腫(Framework Bloat)**。

- **使用框架**的時機:當它能解決一個**非瑣碎的電腦科學問題**時(例如狀態持久化、貝氏 prompt 最佳化、向量-圖連結)。
- **自建(薄封裝)**的時機:當你只是對 LLM 進行簡單呼叫時。框架會帶來延遲、版本更新的擾動,以及除錯的額外負擔,對於單輪(single-turn)agent 而言並不值得。

---

## 應避免的反模式

1. **框架硬塞(Framework Tunnelling)**:試圖將複雜的邏輯流程硬塞進一個不支援它的框架(例如用純 RAG 函式庫來做編碼 agent)。
2. **黃金鎚子(The Golden Hammer)**:只因為 LangChain 很熱門就使用它,而其實一段 50 行的 Python 腳本會更快、更便宜。
3. **忽略可觀測性(Observability)**:在沒有 LLOps 層(LangSmith/Phoenix)的情況下就部署任何框架。

---

## Staff 等級的建議

對於一個現代化、生產等級的 agentic 系統:
- **編排**:LangGraph(用於狀態與迴圈)或 Microsoft Agent Framework(用於 .NET 團隊)。
- **Agent SDK**:配合你的模型供應商 —— Claude Agent SDK(Anthropic)、Agents SDK(OpenAI)、ADK(Google)。三者皆支援 MCP 以進行工具存取。
- **最佳化**:DSPy(為不同模型層級編譯 prompt)。
- **檢索**:LlamaIndex(用於多階段 RAG)。
- **可觀測性**:LangSmith(用於追蹤與評估)。
- **跨廠商 agent**:A2A 協定,用於跨越組織邊界的 agent 對 agent 協調。
- **自主式編碼**:Claude Code(CLI)或 Cline(VS Code),用於檔案層級的編輯任務。
- **開源編碼 agent**:OpenHands,用於自行託管或 CI pipeline 整合。

**2026 年的洞察**:
1. Agentic 編碼工具(Claude Code、Cursor、OpenHands)並非編排框架的替代品 —— 它們是一個**全新的類別**,運作在檔案系統層級,位於 LLM API 之上、但在應用程式邏輯之下。
2. 協定層已趨成熟:**MCP 用於 agent 對工具**,而 **A2A 用於 agent 對 agent**,兩者正逐漸成為基礎設施標準,而非可有可無的附加元件。請將你的架構設計為同時支援兩者。
3. 每家實驗室都推出自己的 agent SDK,這帶來了**廠商鎖定(vendor lock-in)的風險**。透過使用 MCP 進行工具存取(可在各 SDK 間移植)以及 A2A 進行 agent 協調(廠商中立)來緩解此風險。

> *更新於 2026 年 5 月。*

---

## 面試問題

### Q:為什麼我們會看到一股趨勢,從「Prompting(下提示)」轉向「Programming(寫程式)」(DSPy)?

**強力的回答:**
**工業化(Industrialization)**。Prompt 工程是「煉金術」:它不一致且無法規模化。透過 DSPy 這類框架以程式設計的方式操作 LLM,讓我們能將 AI 視為一門**軟體工程學科**。我們可以套用 CI/CD、單元測試(metrics)與自動化最佳化。這讓 AI 從「非決定性的魔法」轉變為一個更大型分散式系統中**可預測的元件**,而這正是任何關鍵任務(mission-critical)生產環境的必要條件。

### Q:如果你必須打造一個能跨 OpenAI、Anthropic 與本地 Llama 模型運作的系統,你會如何設計其架構?

**強力的回答:**
我會用 **DSPy** 作為 prompt 層,並用 **LangGraph** 作為編排層。DSPy 的 **Signatures** 讓我能將任務定義與模型的特定行為解耦。接著我會使用一個**通用模型閘道(Universal Model Gateway)**(例如 LiteLLM 或內部代理)來處理不同的 API 格式。在工具存取方面,我會使用 **MCP** —— 它與模型無關,因此無論底層啟用的是哪個 LLM,同一套 MCP server 都能運作。如果我需要跨團隊的 agent 協調,我會在邊界層使用 **A2A**。這套堆疊確保了:當我因為成本或延遲因素需要從 GPT-4o 切換到 Claude Sonnet 4 時,我不必重寫 50 個 prompt;我只需要重新編譯或更新設定即可。

### Q:在每家 AI 實驗室都推出自己的 agent SDK(Claude Agent SDK、OpenAI Agents SDK、Google ADK)的情況下,你如何避免廠商鎖定?

**強力的回答:**
關鍵在於**將編排層與模型層分離**。我會使用一個與框架無關的編排器,例如 LangGraph 或一層薄的自建封裝,來處理核心的工作流程邏輯。各模型專屬的 SDK 在原型開發時、或當你已確定要押注單一供應商時很有用,但對於生產環境中的多廠商系統,我會將模型互動藏在一層抽象之後(LiteLLM 閘道或 DSPy signatures)。在工具存取方面,**MCP** 提供了可移植性 —— 同一套 MCP server 可搭配任何 SDK 運作。在 agent 協調方面,**A2A** 提供了廠商中立的 agent 對 agent 通訊。實務上的準則是:在葉節點(個別的 agent 實作)使用各實驗室專屬的 SDK,但讓編排圖保持廠商中立。

---

## 參考資料
- Google Cloud. "Enterprise Generative AI Reference Architecture" (2025)
- Gartner. "Magic Quadrant for AI Application Frameworks" (2025)
- Gartner. "Predicts 2026: 40% of Enterprise Apps to Feature AI Agents" (2025)
- Thoughtworks. "Technology Radar: The Rise of Agentic Frameworks" (Nov 2024/2025)
- Microsoft. "Agent Framework Overview" (2026)
- Anthropic. "Claude Agent SDK" (2026)
- Google. "Agent Development Kit" (2026)
- OpenAI. "Agents SDK" (2026)

---

*新章節:[第 10 章:文件處理](../10-document-processing/01-ocr-and-layout.md)*
