# OpenCoder：AI 程式設計 Agent 全景

AI 程式設計 agent 的版圖已經爆炸性成長。本指南涵蓋開放權重（open-weight）程式設計模型、agentic IDE、開源 agent，以及如何為你的工程工作流程挑選合適的工具。

## 目錄

- [AI 程式設計版圖（2026）](#landscape)
- [開放權重程式設計模型](#models)
- [AI 原生 IDE](#ides)
- [開源程式設計 Agent](#agents)
- [Benchmark 深入解析](#benchmarks)
- [成本比較](#costs)
- [選型指南](#selection)
- [生產環境架構](#production)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## AI 程式設計版圖（2026）

程式設計 AI 的版圖可分為三個明確的層次：

```
┌─────────────────────────────────────────────────────────────┐
│                    AI CODING STACK (2026)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LAYER 3: CODING AGENTS (Autonomous, multi-turn)           │
│  ┌──────────────┐ ┌────────────┐ ┌────────────────────┐   │
│  │  Claude Code │ │  OpenHands │ │  Cline / Aider     │   │
│  │  (Anthropic) │ │  (Open)    │ │  (Open)            │   │
│  └──────────────┘ └────────────┘ └────────────────────┘   │
│                                                             │
│  LAYER 2: AI IDEs (Completion + editing, developer-in-loop)│
│  ┌──────────────┐ ┌────────────┐ ┌────────────────────┐   │
│  │    Cursor    │ │  Windsurf  │ │  GitHub Copilot    │   │
│  └──────────────┘ └────────────┘ └────────────────────┘   │
│                                                             │
│  LAYER 1: CODING MODELS (The brains behind everything)     │
│  ┌──────────────┐ ┌────────────┐ ┌────────────────────┐   │
│  │  Opus 4.7    │ │  GPT-5.5   │ │ DeepSeek V4 Pro    │   │
│  │  Sonnet 4.6  │ │ Gemini 3.1 │ │ Qwen 3.6 Coder     │   │
│  └──────────────┘ └────────────┘ └────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 開放權重程式設計模型

這些模型可以自行架設（self-host）、進行 fine-tuning，並在不依賴任何 API 的情況下部署。

### Qwen2.5-Coder（阿里巴巴）

一個實力堅強的開源程式設計模型家族。截至 2026 年 5 月，開源程式設計領域的領先者是 Qwen 3.6 Coder 與 DeepSeek V4 Pro；而 Qwen 2.5 Coder 在較小型硬體上的自行架設部署中，仍是熱門選擇：

| 模型 | 參數量 | Context | HumanEval+ | 備註 |
|-------|------------|---------|------------|-------|
| Qwen2.5-Coder-32B-Instruct | 32B | 128K | 88.2% | 最佳開源程式設計模型 |
| Qwen2.5-Coder-7B-Instruct | 7B | 128K | 79.3% | 出色的小型模型 |
| Qwen2.5-Coder-1.5B | 1.5B | 32K | 65.8% | 邊緣／裝置端使用 |

**優勢：**
- 在程式設計 benchmark 上表現強勁；在 SWE-bench Verified 上可與前沿閉源模型競爭
- 支援 100 種以上程式語言
- 出色的 fill-in-the-middle（FIM）補全能力
- Apache 2.0 授權 — 完全可商用

```python
# Self-hosted with vLLM
from vllm import LLM

model = LLM(
    model="Qwen/Qwen2.5-Coder-32B-Instruct",
    tensor_parallel_size=2,  # 2× A100 80GB
)
response = model.generate("def fibonacci(n: int) -> list[int]:")
```

### DeepSeek-Coder-V2（DeepSeek）

| 模型 | 參數量 | 架構 | HumanEval+ |
|-------|------------|-------------|------------|
| DeepSeek-Coder-V2-Instruct | 236B (MoE) | MoE | 90.2% |
| DeepSeek-Coder-V2-Lite | 16B (MoE) | MoE | 81.1% |

**優勢：**
- MoE 架構 → 每個 token 僅啟用 21B 參數（高效率）
- 在競技程式設計（CodeForces 題目）上表現強勁
- 開放權重；對中文有強力支援

### StarCoder2（BigCode / Hugging Face）

| 模型 | 參數量 | Context | 備註 |
|-------|------------|---------|-------|
| StarCoder2-15B | 15B | 16K | 最佳中型開源程式設計 LM |
| StarCoder2-7B | 7B | 16K | 高效率，支援 80 種以上語言 |
| StarCoder2-3B | 3B | 16K | 輕量、可在裝置端執行 |

**優勢：**
- 完全開放（BigCode OpenRAIL-M 授權）
- 非常適合 IDE 補全（低延遲）
- 在 Stack Overflow / GitHub 資料上表現強勁

### DeepSeek-R1-Distill（用於程式設計）

| 模型 | 參數量 | 數學／程式 | 備註 |
|-------|------------|-----------|-------|
| DeepSeek-R1-Distill-Qwen-32B | 32B | 出色 | 將推理能力蒸餾（distill）至較小模型 |
| DeepSeek-R1-Distill-Llama-8B | 8B | 良好 | 極小型推理模型 |

**使用情境**：當你需要在自行架設規模下獲得具備推理品質的程式碼生成時。

### 開源模型選型指南

```
Simple completions (< 100ms latency needed)?
  → StarCoder2-3B or Qwen2.5-Coder-1.5B (local, fast)

Best quality self-hosted?
  → Qwen2.5-Coder-32B-Instruct (2× A100)

Budget < 1× A100 GPU?
  → Qwen2.5-Coder-7B-Instruct (1× RTX 4090 sufficient)

Need reasoning + coding?
  → DeepSeek-R1-Distill-Qwen-32B

Competitive programming / algorithmic?
  → DeepSeek-Coder-V2 or DeepSeek-R1
```

---

## AI 原生 IDE

### Cursor

**官網：** cursor.sh | **基礎：** VS Code fork | **定價：** $20/mo Pro

Cursor 是領先的 AI 原生 IDE。主要能力：

| 功能 | 說明 |
|---------|-------------|
| **Composer** | 多檔案 agentic 編輯（Cursor 對應於 Claude Code 的功能） |
| **Ctrl+K** | 行內程式碼生成 |
| **Tab** | 預測式補全（比 Copilot 更聰明） |
| **@-mentions** | 將檔案、URL、文件附加到 context |
| **.cursorrules** | 專案層級的 AI 指示（類似 CLAUDE.md） |
| **模型選擇** | GPT-5.5、Claude Sonnet 4.6 / Opus 4.7、Gemini 3.1 Pro、DeepSeek V4 Pro |

**最適合**：希望在熟悉的 GUI 中進行 agentic 編輯的前端／全端開發者。

**限制**：閉源；你的程式碼會傳送到 Cursor 的伺服器（他們提供 Privacy Mode）。

### Windsurf（由 Codeium 推出）

**官網：** codeium.com/windsurf | **基礎：** VS Code fork | **定價：** 免費方案 + $15/mo Pro

Windsurf 透過 **Flows** 做出差異化（請勿與 CrewAI Flows 混淆）：

| 功能 | 說明 |
|---------|-------------|
| **Cascade** | Windsurf 的 agentic 編輯模式 |
| **Flows** | 確定性的 agentic 序列（agent 與使用者和諧協作） |
| **模型選擇** | 任意：GPT-5.5、Claude Sonnet 4.6 / Opus 4.7、Gemini 3.1 Pro、DeepSeek V4 |
| **免費方案** | 慷慨的免費額度 |

**最適合**：想要 Cursor 般的體驗，同時擁有免費方案與模型彈性的團隊。

### GitHub Copilot（Microsoft/OpenAI）

| 功能 | 狀態（2026 年 5 月） |
|---------|---------------------|
| 補全 | ✅ 以安裝量計仍是市場領導者 |
| Copilot Workspace | ✅ 多檔案 agentic 編輯（已 GA） |
| 模型 | GPT-5.5（預設）、Claude Sonnet 4.6 / Opus 4.7（可選用） |
| 企業功能 | ✅ IP 保護、組織政策、可關閉的程式碼引用 |

**最適合**：已經在 Microsoft/GitHub 生態系中的企業團隊。

**2026 的現實**：對大多數開發者而言，Copilot 的補全品質已被 Cursor/Windsurf 超越，但其企業功能與 GitHub 整合使其在大型組織中維持主導地位。

---

## 開源程式設計 Agent

### OpenHands（前身為 OpenDevin）

**GitHub：** github.com/All-Hands-AI/OpenHands | **授權：** MIT

領先的開源自主程式設計 agent：

```bash
# Run with Docker
docker pull docker.all-hands.dev/all-hands-ai/openhands:latest
docker run -it --rm \
  -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:latest \
  -e LLM_API_KEY=$ANTHROPIC_API_KEY \
  -e LLM_MODEL=claude-3-7-sonnet-20250219 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -p 3000:3000 \
  docker.all-hands.dev/all-hands-ai/openhands:latest
# Access at http://localhost:3000
```

**架構：**
```
User request
    ↓
OpenHands Controller
    ├── CodeActAgent (main strategy)
    ├── Docker Sandbox (isolated execution)
    ├── File editor (str_replace_editor)
    └── Browser (playwright for web tasks)
```

**主要功能：**
- **任意 LLM**：可搭配 Claude Sonnet 4.6 / Opus 4.7、GPT-5.5、Gemini 3.1 Pro、DeepSeek V4、本地 Ollama 使用
- **Docker sandbox**：agent 在隔離的容器中執行
- **Web UI**：類聊天介面；展示 agent 的推理過程
- **API 存取**：提供 REST API 以整合至 CI
- **SWE-bench 分數**：約 55-60%（依後端模型而定）

### Aider

**GitHub：** github.com/paul-gauthier/aider | **授權：** Apache 2.0

以終端機為先（terminal-first）、git 原生的程式設計 agent：

```bash
pip install aider-chat

# Works directly with your git repo
aider --model claude-3-7-sonnet-20250219

# Add files to context
/add src/auth.py src/models.py

# Give task
> Add JWT authentication to the User model
```

**Aider 的獨特之處：**
- **Git 原生**：邊做邊 commit 變更；維持乾淨的 git 歷史
- **Context maps**：維護整個程式碼庫的對照圖（即使是不在 context 中的檔案）
- **語音模式**：可用口說下達任務
- **架構模式**：在動到程式碼之前先討論設計

```bash
# SWE-bench Verified benchmarks (May 2026)
# Aider + Claude Sonnet 4.6  → ~74%
# Aider + Claude Opus 4.7    → ~87%
# Aider + GPT-5.5            → ~88%
```

### Cline（VS Code 擴充套件）

**GitHub：** github.com/cline/cline | **授權：** Apache 2.0

用於自主程式設計的開源 VS Code 擴充套件：

```
VS Code
  └── Cline Extension
        ├── Any model (Claude, GPT, Gemini, Ollama)
        ├── File system access (read/write any file)
        ├── Terminal (bash commands)
        ├── Browser (playwright)
        └── MCP servers (any MCP tool)
```

**主要差異化特色：**
- **MCP 原生**：開箱即用的完整 MCP 支援
- **逐動作授權**：每一個 shell 指令、檔案編輯都需要使用者核准
- **模型彈性**：支援任何 OpenAI 相容的 API 端點（包含本地 Ollama）
- **免費**：開源，無需訂閱

**最適合**：想要免費獲得 Cursor 般體驗，並擁有完整模型彈性的開發者。

---

## Benchmark 深入解析

### SWE-bench Verified（2026 年 3 月）

agentic 軟體工程的黃金標準。衡量解決真實 GitHub issue 的能力。

| Agent / 系統 | 分數 | 模型後端 | 備註 |
|---------------|-------|---------------|-------|
| GPT-5.5（single-shot 領先者） | 88.7% | OpenAI | 在 SWE-Bench Verified 上居 #1（2026 年 5 月） |
| Claude Opus 4.7（Anthropic） | 87.6% | Anthropic | 在 SWE-Bench Pro 上以 64.3% 領先 |
| Claude Code | ~87% | Claude Opus 4.7 / Sonnet 4.6 | Anthropic 的官方 agent |
| OpenHands（最佳配置） | ~75% | Claude Sonnet 4.6 | 開源 |
| Aider | ~74% | Claude Sonnet 4.6 / Opus 4.7 / GPT-5.5 | 開源 CLI |
| SWE-agent | ~55% | GPT-5.5 | Princeton 研究基準線 |

> [!NOTE]
> SWE-bench 分數對後端模型高度敏感。同一個 agent 搭配 claude-3-7-sonnet 時，分數通常比搭配 GPT-4o 高出 10-15%。

### HumanEval+（開源模型）

| 模型 | HumanEval+ 分數 |
|-------|-----------------|
| Claude 3.7 Sonnet | 93.6% |
| GPT-4o | 90.2% |
| Qwen2.5-Coder-32B-Instruct | 88.2% |
| DeepSeek-Coder-V2-Instruct | 90.2% |
| StarCoder2-15B | 73.3% |

### LiveCodeBench（執行階段評估，訊號更強）

LiveCodeBench 使用全新的競技程式設計題目（不在訓練資料中）：

| 模型 | LiveCodeBench 分數 |
|-------|---------------------|
| o3 (high) | 68.1% |
| Claude 3.7 Sonnet | 54.2% |
| GPT-4.5 | 38.7% |
| Qwen2.5-Coder-32B | 43.2% |
| DeepSeek-R1 | 57.0% |

**洞見**：LiveCodeBench 分數遠低於 HumanEval，因為它測試的是全新題目。o3 與 DeepSeek-R1 因其推理能力而居於主導地位。

---

## 成本比較

### 閉源 API vs. 開源自行架設

**情境：每天 1,000 個程式設計任務，每個平均 5K tokens**

| 做法 | 每月成本 | 品質 | 延遲 |
|----------|-------------|---------|---------|
| Claude 3.7 Sonnet (API) | ~$9,000 | ★★★★★ | 中等 |
| GPT-4o (API) | ~$7,500 | ★★★★ | 中等 |
| o3-mini (API) | ~$3,300 | ★★★★★（推理） | 慢 |
| Qwen2.5-Coder-32B (4×A100) | ~$4,000（基礎設施） | ★★★★ | 快 |
| DeepSeek-V3 (Together AI) | ~$1,350 | ★★★★ | 中等 |

**關鍵洞見**：相較於 Claude API，自行架設 Qwen2.5-Coder-32B 在約每天 500 個以上任務時開始具成本競爭力。對於每天少於 200 個任務的情況，一旦把工程管理成本納入考量，API 幾乎總是更便宜。

---

## 選型指南

### 快速決策樹

```
What is your primary need?

├─ IDE coding assistance (completions + chat)?
│  ├─ Microsoft ecosystem / enterprise? → GitHub Copilot
│  ├─ Want best quality? → Cursor (Pro)
│  └─ Want free + model choice? → Windsurf or Cline
│
├─ Autonomous agent for standalone coding tasks?
│  ├─ Best quality, don't mind proprietary? → Claude Code
│  ├─ Need open-source? → OpenHands
│  ├─ CLI-first, git-native? → Aider
│  └─ VS Code embedded, MCP-native? → Cline
│
├─ Self-hosted model for custom deployment?
│  ├─ Best quality? → Qwen2.5-Coder-32B
│  ├─ Need reasoning? → DeepSeek-R1-Distill-32B
│  ├─ Fast completions? → Qwen2.5-Coder-7B or StarCoder2-7B
│  └─ Edge/on-device? → Qwen2.5-Coder-1.5B or StarCoder2-3B
│
└─ CI/CD pipeline integration?
   ├─ Best results? → Claude Code SDK (headless)
   ├─ Open-source? → OpenHands REST API
   └─ Git-native? → Aider CLI in GitHub Actions
```

### 比較矩陣

| 面向 | Claude Code | Cursor | OpenHands | Aider | Cline |
|-----------|-------------|--------|-----------|-------|-------|
| 自主性 | 完整 | 中等 | 完整 | 完整 | 完整 |
| 模型綁定 | Claude | 任意 | 任意 | 任意 | 任意 |
| 開源 | ❌ | ❌ | ✅ | ✅ | ✅ |
| CI/Headless | ✅ | ❌ | ✅ | ✅ | ❌ |
| GUI | CLI | 完整 IDE | Web UI | 終端機 | VS Code |
| MCP | ✅ | ✅ | 部分 | ❌ | ✅ |
| Git 原生 | 部分 | 部分 | ✅ | ✅ | 部分 |
| 價格 | API 費用 | $20/mo | 免費 + API | 免費 + API | 免費 + API |

---

## 生產環境架構

### 企業級程式設計 Agent 平台

以下說明如何建構一個內部 AI 程式設計平台：

```
┌────────────────────────────────────────────────────────────┐
│             ENTERPRISE CODING AGENT PLATFORM                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Developer                                                 │
│     ↓ (Jira ticket / PR description)                      │
│  ┌──────────────────────────────────┐                      │
│  │        TASK INTAKE LAYER         │                      │
│  │  • Parse task from Jira/GitHub   │                      │
│  │  • Classify: simple/complex      │                      │
│  │  • Route to appropriate agent    │                      │
│  └──────────────┬───────────────────┘                      │
│                 │                                          │
│    Simple fix   │   Complex feature                        │
│        ↓        │        ↓                                 │
│  ┌──────────┐   │  ┌──────────────────┐                    │
│  │  Aider   │   │  │   Claude Code    │                    │
│  │ (cheap)  │   └→ │  SDK (headless)  │                    │
│  └────┬─────┘      └────────┬─────────┘                    │
│       │                     │                              │
│       └─────────────────────┘                              │
│                 ↓                                          │
│  ┌──────────────────────────────────┐                      │
│  │         REVIEW LAYER             │                      │
│  │  • Git diff → PR creation        │                      │
│  │  • Auto-run CI tests             │                      │
│  │  • Human review (required)       │                      │
│  └──────────────────────────────────┘                      │
│                 ↓                                          │
│         Merge to main (human approved)                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 關鍵生產環境決策

| 決策 | 選項 | 建議 |
|----------|---------|----------------|
| Agent 使用的模型 | Claude 3.7、GPT-4o、開源 | 以 Claude 3.7 Sonnet 取得最佳結果 |
| 任務匯入 | 手動、Jira webhook、GitHub label | 以 GitHub label 觸發 Actions 工作流程 |
| 程式碼執行 | 本地、Docker、E2B | Docker（可重現、隔離） |
| 人工審查 | PR、Slack 核准、自動化 | 必須進行 PR 審查，絕不自動合併 |
| 成本控管 | 最大回合數、模型路由 | max_turns=20，簡單任務用 Haiku |

---

## 面試問題

### Q：你如何在 Claude Code、Cursor 與 OpenHands 之間做選擇？

**有力的回答：**
這取決於三個軸向：

1. **介面需求**：如果開發者想要 GUI（在 context 中查看變更），就用 Cursor 或 Windsurf。如果任務是腳本化／headless 的（在 CI 中修 bug、產生測試），就用 Claude Code SDK 或 OpenHands。

2. **模型控制**：如果你需要使用任意模型（或自己 fine-tune 過的模型），就用 OpenHands 或 Aider。如果你能接受僅用 Anthropic 並想要業界頂尖的結果，就用 Claude Code。

3. **開源需求**：企業資安團隊通常要求使用可供稽核的開源工具。OpenHands（MIT）與 Aider（Apache 2.0）就是答案。

對於一間典型的新創公司，我會建議：日常開發用 Cursor，批次任務（從 GitHub issue 產生 PR）用 Claude Code，自行架設的 CI pipeline 則用 OpenHands。

### Q：為什麼像 Qwen2.5-Coder 這樣的開放權重程式設計模型對企業很重要？

**有力的回答：**
三個理由：

1. **資料隱私**：傳送到閉源 API 的程式碼有可能被用於訓練或暴露給第三方。對於醫療（HIPAA）、金融（SOX）與政府團隊而言，任何專有程式碼都不能離開內部網路。在地端（on-prem）執行的 Qwen2.5-Coder-32B 解決了這個問題。

2. **規模化成本**：在每月 100 萬次以上的程式碼生成請求下，自行架設會比 API 定價便宜 40-60%，尤其是補全（相對於 agentic 任務）。

3. **Fine-tuning**：開放權重可進行領域特化。一家法律科技公司可以針對其內部 DSL（領域特定語言）進行 fine-tune。API 不允許這麼做。

Qwen2.5-Coder-32B 與 Claude 3.7 Sonnet 之間的品質差距確實存在，但正在縮小。對於補全與較簡單的任務，開源模型往往「夠好用」。

### Q：你會如何為 CI 中的 AI 程式設計 agent 設計測試策略？

**有力的回答：**
我會採用三層評估：

**1. 功能測試**（自動化、每次執行）：
```
Agent output → Run pytest → Pass rate metric
```

**2. 基準真值比較**（每週）：
```
Known bug → Agent fix → Compare to expert fix
Metric: Semantic similarity of diff (not byte-exact)
```

**3. 人工評估**（抽樣 5% 的 agent PR）：
```
Senior engineer rates: Correctness, Style, Safety, 1-5 scale
```

我也會追蹤 **regression rate（迴歸率）** — 如果某個 agent 的修正引入了新的失敗測試，那就是一次嚴重失敗。agent 應該執行完整的測試套件，並且只有在提升或維持通過率時才算成功。

---

## 參考資料

- Qwen2.5-Coder: https://qwenlm.github.io/blog/qwen2.5-coder/
- DeepSeek-Coder-V2: https://github.com/deepseek-ai/DeepSeek-Coder-V2
- StarCoder2: https://huggingface.co/blog/starcoder2
- OpenHands: https://github.com/All-Hands-AI/OpenHands
- Aider: https://aider.chat/
- Cline: https://github.com/cline/cline
- Cursor: https://cursor.sh/
- Windsurf: https://codeium.com/windsurf
- SWE-bench Leaderboard: https://www.swebench.com/
- LiveCodeBench: https://livecodebench.github.io/

---

*上一篇：[Claude Code](09-claude-code.md) | 下一篇：[框架選型指南](08-framework-selection-guide.md)*
