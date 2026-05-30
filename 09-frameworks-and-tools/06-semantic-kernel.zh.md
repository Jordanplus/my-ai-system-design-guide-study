# Semantic Kernel

**Semantic Kernel (SK)** 是 Microsoft 用於企業級 AI 編排的引擎。對於投入 **Azure/Microsoft 生態系**與 **C#/.NET** 架構的組織而言，它仍是主要的橋樑；不過其多數的未來發展動能，如今都納入 **Microsoft Agent Framework**（AutoGen + SK 的整合後繼者，RC 1.0 於 2026 年 2 月推出，GA 預計於 2026 年第二季）之中。

## 目錄

- [企業級 DNA](#dna)
- [Plugins 與 Planners](#plugins)
- [Memory 與 Connectors](#memory)
- [多語言支援（C# vs. Python）](#multi-language)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 企業級 DNA

LangChain 受到新創公司青睞，而 Semantic Kernel 則受到**銀行與 Fortune 500 企業**的偏好。
- **Dependency Injection**：SK 遵循標準的企業級設計模式。
- **強型別（Strong Typing）**：對 C# 型別的第一級支援，使其在大規模、任務關鍵型系統中具有高度可靠性。
- **安全性**：與 Azure Active Directory（Microsoft Entra ID）及 Managed Identities 深度整合。

---

## Plugins 與 Planners

1. **Kernel Functions**：邏輯的基本單位（原生程式碼或 LLM prompts）。
2. **Plugins**：一組函式的集合（例如「GitHub Plugin」或「SQL Plugin」）。
3. **Planners**：SK 的 planners 已從單純的 ReAct 演進為**階層式 Planners（Hierarchical Planners）**，能夠協調橫跨多天的長時間執行業務流程。

---

## Memory 與 Connectors

Semantic Kernel 使用 **Connectors** 來抽象化底層的基礎設施。
- **通用 Connectors**：以單一介面對接 OpenAI、Mistral 與本地端的 Onyx 模型。
- **Vector Store 抽象化**：在 Azure AI Search、Pinecone 與 Qdrant 之間無縫切換，而無須變更核心業務邏輯。

---

## 多語言支援

SK 是少數將 C# 與 Python 視為平等地位的主流框架之一。
- **模式**：以 Python 進行開發與原型設計；再以 C# 部署核心編排，以兼顧效能與型別安全。
- **邏輯共享**：跨兩種語言皆可運作的共享 prompt 範本（.yaml）。

---

## 面試問題

### Q：為什麼 Staff Engineer 會選擇 Semantic Kernel 而非 LangChain？

**有力的回答：**
**架構一致性**。如果一個組織已經建構於 .NET/Azure 技術堆疊之上，Semantic Kernel 便能融入其既有的 CI/CD、監控（App Insights）與安全（Entra ID）流程之中。LangChain 往往讓人覺得像是一塊「外掛」的技術。此外，SK 的**強型別（Strong Typing）**與 **Dependency Injection** 模式，可避免大型 LangChain 專案常見的「義大利麵式程式碼（spaghetti code）」。對於處理敏感財務資料的企業而言，安全性與稽核方面的**原生 Azure 整合**是決定性的因素。

### Q：Semantic Kernel 中的「Function Calling」抽象化是什麼？

**有力的回答：**
SK 採用**以 Plugin 為基礎的模型**。每個函式（原生 C# 或以 LLM 為基礎）都會註冊到 Kernel 中。當 LLM 判斷自己需要某個工具時，Kernel 會在 Plugin 登錄表中查找該函式、驗證參數，並加以執行。SK 現在支援**自動意圖偵測（Automatic Intent Detection）**：Kernel 能根據當前的 context window，在使用者開口詢問之前，便主動建議他們可能需要哪個 Plugin。

---

## 參考資料
- Microsoft Learn. "Semantic Kernel Documentation" (2025)
- Azure Architecture Center. "AI Design Patterns with Semantic Kernel" (2025)
- Build 2025. "The Future of Copilots with SK" (2025 Conference Recap)

---

*下一篇：[AutoGen 與 CrewAI](07-autogen-crewai.md)*
