# Microsoft Agent Framework、CrewAI 與 Agent SDK 全景

過去一年來，多代理（multi-agent）框架的版圖出現了顯著的整併。Microsoft **讓 AutoGen 退役**，並將其與 Semantic Kernel 合併為統一的 **Microsoft Agent Framework**（RC 1.0，2026 年 2 月；GA 目標為 2026 年第二季）。CrewAI 演進至 v1.13，具備企業級功能，並據報已被超過 60% 的財星五百大企業採用。與此同時，每一家主要的 AI 實驗室都推出了自家的 agent SDK：Anthropic 的 Claude Agent SDK、OpenAI 的 Agents SDK，以及 Google 的 ADK。

## 目錄

- [CrewAI：管理者觀點](#crewai)
- [Microsoft Agent Framework（AutoGen 的繼任者）](#microsoft-agent-framework)
- [Agent SDK 全景](#agent-sdk-landscape)
- [Swarm 與點對點通訊](#swarms)
- [框架比較矩陣](#comparison)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## CrewAI：管理者觀點

CrewAI 是圍繞 **Process** 這個概念所建構的。
- **角色導向代理（Role-Based Agents）**：你定義一個「Researcher」、一個「Writer」與一個「Manager」。
- **任務（Tasks）**：具有特定產出的明確目標。
- **流程編排（Process Orchestration）**：Sequential（循序）、Hierarchical（階層）或 Consensual（共識導向）。

### CrewAI Flows

CrewAI **Flows** 在經典的 Crew 模式之上加入了一層 **狀態機（state-machine）**：

```python
from crewai.flow.flow import Flow, listen, start

class ContentFlow(Flow):
    @start()
    def research_topic(self):
        # Returns research output
        return research_crew.kickoff({"topic": self.state["topic"]})
    
    @listen(research_topic)
    def write_article(self, research):
        # Triggered after research completes
        return writing_crew.kickoff({"research": research})
    
    @listen(write_article)
    def publish(self, article):
        # Final step
        return publisher.publish(article)
```

### CrewAI v1.13 重點

CrewAI v1.13 標誌著朝向企業級生產就緒的轉捩點：

- **Enterprise SSO**：完整記載適用於企業部署的單一登入（Single Sign-On）
- **RBAC 改進**：角色導向存取控制（Role-Based Access Control），並提供完整的權限參考矩陣
- **GPT-5 相容性**：針對 OpenAI 的 GPT-5 及更新的 o 系列模型修正問題，這些模型已不再支援 `stop` 參數
- **A2A 任務執行**：以結構化、確定性的方式進行 Agent-to-Agent 動態任務委派
- **NVIDIA NemoClaw 整合**：在基礎設施層級進行政策強制執行，以實現安全的企業部署
- **RuntimeState RootModel**：為複雜工作流程提供統一的狀態序列化

**使用情境**：在結構明確的場景中（內容生產流程、資料分析工作流程），CrewAI + Flows 是進行 **業務流程自動化** 的最佳框架。CrewAI 表示其已支撐約 20 億次的代理式（agentic）執行。

> *2026 年 5 月驗證。來源：docs.crewai.com/en/changelog*

---

## Microsoft Agent Framework（AutoGen 的繼任者）

### 合併：AutoGen + Semantic Kernel = Agent Framework

Microsoft 在 2025 年底讓 AutoGen 作為獨立產品退役，並將其與 Semantic Kernel 合併為統一的 **Microsoft Agent Framework**。Release Candidate 1.0 已於 2026 年 2 月推出，GA 目標為 2026 年第二季。

**這次合併結合了哪些能力：**
- **來自 AutoGen**：用於單一與多代理對話模式的簡單抽象（group chat、round-robin、handoff）
- **來自 Semantic Kernel**：企業級的工作階段管理、型別安全、filter、遙測（telemetry），以及廣泛的 model/embedding 支援

### 遷移路徑

AutoGen 會持續收到錯誤修正與安全性修補，但 **新功能僅會進入 Agent Framework**。Microsoft 提供了官方的遷移指南。若要開啟新專案，請直接使用 Agent Framework。

### 關鍵能力

```python
# Microsoft Agent Framework: Graph-based workflow
from agent_framework import Agent, Workflow, HandoffStep

planner = Agent("Planner", model="gpt-5.5", system_message="Decompose tasks.")
executor = Agent("Executor", model="gpt-5.5-mini", system_message="Execute sub-tasks.")

workflow = Workflow(
    steps=[
        HandoffStep(from_agent=planner, to_agent=executor),
    ],
    state_management="session",  # Built-in session persistence
)
```

**框架重點：**
- **統一的 .NET 與 Python**：跨兩種語言採用相同的程式設計模型
- **圖形導向工作流程（Graph-based Workflows）**：具備明確控制的 sequential、concurrent、handoff 與 group chat 模式
- **狀態管理（State Management）**：為長時間執行與 human-in-the-loop 場景提供穩健的工作階段持久化
- **MCP 支援**：原生整合 Model Context Protocol 以存取工具
- **多供應商（Multi-provider）**：支援 OpenAI、Azure OpenAI、Anthropic、Google 與本地模型

> *2026 年 5 月驗證。來源：learn.microsoft.com/en-us/agent-framework*

---

## Agent SDK 全景

如今每一家主要的 AI 實驗室都推出了自家的 agent 框架。截至 2026 年 5 月的全景如下：

### Claude Agent SDK（Anthropic）

Claude Agent SDK（自 Claude Code SDK 更名而來）提供了與驅動 Claude Code 相同的工具、agent 迴圈與情境管理，並以 Python 與 TypeScript 函式庫的形式提供。

- **內建工具**：檔案讀取、命令執行、程式碼編輯——代理無需自訂工具實作即可立即運作
- **Supervisor 模式**：具備委派能力的階層式代理樹
- **部署**：支援 AWS Bedrock、Google Vertex AI 與 Azure
- **截至 2026 年 5 月**：Python v0.1.48+、TypeScript v0.2.71+

### OpenAI Agents SDK

OpenAI 推出的輕量級框架，使用原生的 Python/TypeScript 結構來打造多代理工作流程：

- **Handoff 導向**：代理之間使用 `Handoff(TargetAgent)` 互相委派——無需中央 supervisor
- **Guardrails**：內建輸入驗證與安全性檢查
- **MCP 整合**：原生支援 MCP server 工具
- **即時代理（Realtime agents）**：透過 gpt-realtime-1.5 支援語音代理

### Google Agent Development Kit（ADK）

Google 推出的框架，針對 Google 生態系最佳化，但與模型無關：

- **多語言**：Python、TypeScript、Java、Go（截至 2026 年 5 月皆已達 1.0+）
- **A2A 原生**：內建 Agent-to-Agent 協定支援，以進行跨供應商的編排
- **Vertex AI 整合**：部署至 Agent Engine Runtime 以獲得受管託管
- **圖形導向（Graph-based）**：代理工作流程被建模為有向圖

> *2026 年 5 月驗證。*

---

## Swarm 與 P2P

兩個框架（以及更廣泛的 SDK 全景）都採用了 **Swarm 模式**。
- **Handoff**：代理不再透過中央 supervisor，而是將對話「交接（Hand off）」給最相關的專家。
- **範例**：一個「Sales Agent」察覺使用者正在詢問技術問題，於是將對話串交接給「Support Agent」。

---

## 框架比較矩陣

| 功能 | CrewAI | MS Agent Framework | LangGraph | Claude Agent SDK | OpenAI Agents SDK | Google ADK |
|---------|--------|-------------------|-----------|-----------------|-------------------|------------|
| **核心抽象** | Task/Process/Flow | Workflow/Agent | State/Graph | Supervisor/Tools | Handoff/Agent | Agent Graph |
| **架構** | 宣告式 + 狀態機 | Graph Workflows | 命令式 DAG | 階層式樹 | Swarm Handoff | 有向圖 |
| **易用性** | 高 | 中 | 低 | 中 | 高 | 中 |
| **控制力** | 低至中 | 中至高 | 高 | 中 | 低至中 | 中至高 |
| **最適用於** | 業務自動化 | 企業級 .NET/Python | 複雜編排 | 程式撰寫／工具代理 | 快速多代理 | Google Cloud AI |
| **多語言** | Python | .NET + Python | Python | Python + TS | Python + TS | Python、TS、Java、Go |
| **MCP 支援** | 是 | 是 | 透過工具 | 原生 | 是 | 是 |
| **A2A 支援** | 透過擴充套件 | 規劃中 | 透過工具 | 否（直接） | 否（直接） | 原生 |

---

## 面試問題

### Q：你在什麼情況下會選用 CrewAI 而非 LangGraph？

**強力回答：**
**速度 vs. 精準度**。當我需要為某個標準流程（例如內容生成或資料分析）非常快速地建立一組代理團隊時，我會使用 **CrewAI**。它開箱即提供「Planning」與「Cooperation」的高階抽象。而當我需要對每一個狀態轉換進行 **細粒度控制（Granular Control）**、需要多輪的 human-in-the-loop 觸發，或是有不適合套用「角色扮演團隊」隱喻的複雜錯誤復原邏輯時，我就會切換到 **LangGraph**。

### Q：Microsoft 讓 AutoGen 退役並改以 Agent Framework 取代。這對既有的 AutoGen 部署有何影響？

**強力回答：**
AutoGen 會持續收到錯誤修正與安全性修補，因此既有部署不會立即失效。然而，**所有新功能的開發** 都在 Agent Framework 上。遷移路徑有完善的文件記載：AutoGen 的 `AssistantAgent` 對應到 Agent Framework 的 `Agent` 類別、`GroupChat` 對應到新的 `Workflow` 模式，而 Semantic Kernel 的企業級功能（工作階段管理、遙測、filter）現在皆可原生使用。遷移的關鍵效益在於 **統一的 .NET 與 Python 支援**，以及能對多代理執行路徑提供明確控制的 **圖形導向工作流程**。對於新專案，請直接從 Agent Framework 開始。

### Q：你如何防止代理彼此不斷對話卻無法解決任務的「無限迴圈（Infinite Loops）」？

**強力回答：**
我們會使用 **終止條件（Termination Conditions）** 與 **最大對話輪數（Max Conversational Turns）**。我們也會實作一個「Critic Agent」，其唯一職責就是偵測對話是否陷入停滯。若 Critic 偵測到循環，它就會觸發 user proxy 來中斷，或強制將 group chat 管理者切換到另一條推理路徑。我們同時也會監控 **Token 速度（Token Velocity）**：如果一對代理在 2 分鐘內用掉了 100K token 卻毫無進展，我們就會自動終結該工作階段。在 2026 年，像 Microsoft Agent Framework 與 LangGraph 這類框架提供了內建的工作流程逾時與狀態檢查點（checkpointing），使迴圈偵測更具系統性。

---

## 參考資料
- CrewAI. "The Multi-Agent Process Engine" (2025/2026, v1.13)
- Microsoft. "Agent Framework Overview" (2026) — learn.microsoft.com/en-us/agent-framework
- Microsoft. "AutoGen to Agent Framework Migration Guide" (2026)
- Anthropic. "Claude Agent SDK" (2026) — platform.claude.com/docs/en/agent-sdk
- OpenAI. "Agents SDK Documentation" (2026)
- Google. "Agent Development Kit" (2026) — google.github.io/adk-docs
- OpenAI Swarm. "Lightweight Multi-Agent Orchestration" (2024 tech report)

---

*下一篇：[框架選擇指南](08-framework-selection-guide.md)*
