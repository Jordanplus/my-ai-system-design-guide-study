# Claude Code：自主編碼代理

Claude Code 是 Anthropic 的 **terminal 原生自主編碼代理 (autonomous coding agent)**。不同於只提供補全建議的 IDE 外掛，Claude Code 扮演的是一位全端軟體工程師：它會讀取你的程式碼庫、編輯檔案、執行命令、跑測試，並反覆迭代直到任務完成。

## 目錄

- [Claude Code 是什麼](#what-it-is)
- [核心架構](#architecture)
- [核心工具](#tools)
- [CLAUDE.md 清單模式](#claude-md)
- [執行 Claude Code](#running)
- [Sub-Agent 與平行化](#subagents)
- [自訂 MCP 整合](#mcp-integration)
- [安全性與權限模型](#safety)
- [生產環境應用：CI Pipeline](#production)
- [比較：Claude Code 與其他替代方案](#comparison)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## Claude Code 是什麼

Claude Code 由 Anthropic 於 2025 年初發布，它是：

- **一個 CLI 工具**：在你的 terminal 中執行 `claude` 命令
- **一個 MCP 原生代理**：使用 bash、text_editor 與 computer 工具
- **一個 SDK**：可以嵌入到 Python/TypeScript 應用程式中
- **不只是聊天機器人**：它會自主地規劃、實作並驗證

```
# Install
pip install claude-code  # or: npm install -g @anthropic-ai/claude-code

# Run interactively
claude

# Run headlessly (for CI)
claude -p "Add unit tests for all functions in src/utils.py" --output-format json
```

**與 Copilot/Cursor 的關鍵差異：**
- Copilot/Cursor：建議程式碼，由你選擇接受或拒絕
- Claude Code：**自主地實作整個任務**，並執行測試來驗證

---

## 核心架構

```
┌─────────────────────────────────────────────────────────┐
│                   CLAUDE CODE ARCHITECTURE               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  User Request                                           │
│       ↓                                                 │
│  ┌─────────────┐    ┌──────────────┐                   │
│  │  Claude 3.7 │    │  CLAUDE.md   │                   │
│  │   Sonnet    │ ←  │  (manifest)  │                   │
│  │ (Extended   │    └──────────────┘                   │
│  │  Thinking)  │                                       │
│  └──────┬──────┘                                       │
│         │ Tool calls                                    │
│         ↓                                               │
│  ┌──────────────────────────────────────┐              │
│  │           TOOL LAYER                 │              │
│  │  ┌─────────┐ ┌───────────┐ ┌──────┐ │              │
│  │  │  bash   │ │text_editor│ │  MCP │ │              │
│  │  └────┬────┘ └─────┬─────┘ └──┬───┘ │              │
│  └───────┼────────────┼──────────┼─────┘              │
│          │            │          │                      │
│   Shell cmds     File edits    Custom tools             │
│   (test, lint,   (read/write)  (DB, APIs,               │
│    git, build)                  internal)               │
└─────────────────────────────────────────────────────────┘
```

Claude Code 以 **Claude 3.7 Sonnet** 作為其骨幹模型，並針對複雜的規劃任務預設啟用 Extended Thinking。

---

## 核心工具

Claude Code 擁有三個原生工具，並支援自訂的 MCP 工具：

### 1. `bash` — Shell 執行

```python
# Claude calls this internally:
bash(command="pytest tests/ -v --tb=short", timeout=60)
# Returns: stdout, stderr, exit_code
```

**Claude 用它來做什麼：**
- 執行測試套件（`pytest`、`jest`、`cargo test`）
- Git 操作（`git diff`、`git commit`、`git log`）
- 建置命令（`npm build`、`make`、`docker build`）
- 套件安裝（`pip install`、`npm install`）

bash session 在多輪對話間是**持久的 (persistent across turns)** — 環境變數與工作目錄會在同一個 session 內延續。

### 2. `text_editor` — 檔案操作

```python
# Read a file
text_editor(command="view", path="/project/src/auth.py")

# Find in file
text_editor(command="view", path="/project/src/auth.py", view_range=[1, 50])

# Edit (surgical replacement)
text_editor(
    command="str_replace",
    path="/project/src/auth.py",
    old_str="def authenticate(user, password):",
    new_str="def authenticate(user: str, password: str) -> AuthResult:"
)

# Create new file
text_editor(command="create", path="/project/tests/test_auth.py", file_text="...")
```

**為什麼精準替換 (surgical replacement) 優於整檔重寫：**
- 保留檔案上下文
- 降低幻覺（只更動需要更動的部分）
- 產生原子化、可審查的 diff

### 3. `computer` — GUI 自動化（選用）

完整的桌面控制（截圖、滑鼠、鍵盤）— 用於瀏覽器測試與 UI 驗證。需要沙箱環境。

---

## CLAUDE.md 清單模式

`CLAUDE.md` 檔案是高效使用 Claude Code 的**最重要單一模式**。它會把持久的專案上下文注入到每一個 Claude Code session 中。

```markdown
# CLAUDE.md — Project: E-Commerce API

## Architecture
- Python 3.11 FastAPI backend
- PostgreSQL 15 with Alembic migrations
- Redis for session caching
- All API responses must be Pydantic models

## Test Commands
- Run all tests: `pytest tests/ -v`
- Run single test: `pytest tests/test_auth.py::test_login -v`
- Lint: `ruff check . --fix`
- Type check: `mypy src/`

## Coding Standards
- Always add type hints
- Never use `global` variables
- All database queries through SQLAlchemy ORM, never raw SQL
- New features require tests with >80% coverage

## Forbidden Patterns
- Do NOT use `os.system()` — use `subprocess.run()` instead
- Do NOT commit secrets — use environment variables
- Do NOT modify `alembic/versions/` — create new migrations

## Architecture Decisions
- Auth: JWT tokens, 1hr expiry, refresh token pattern
- Errors: Always return RFC 7807 Problem Details format
- Logging: structlog with JSON output, always include request_id
```

**巢狀 CLAUDE.md 檔案：**
```
project/
  CLAUDE.md          # global project rules
  src/
    auth/
      CLAUDE.md      # auth-specific rules (stricter security)
    payments/
      CLAUDE.md      # payment-specific rules (PCI compliance notes)
```

當 Claude 在某個目錄下工作時，會自動讀取最接近的 CLAUDE.md。

---

## 執行 Claude Code

### 互動模式

```bash
# Start session (reads CLAUDE.md automatically)
claude

# With specific model
claude --model claude-3-7-sonnet-20250219

# With MCP config
claude --mcp-config .claude/mcp.json
```

### Headless 模式（用於腳本化）

```bash
# Single task, JSON output
claude -p "Fix all type errors in src/" \
  --output-format json \
  --max-turns 20

# Pipe from file
echo "Refactor src/utils.py to use async/await" | claude -p -

# Stream output
claude -p "Add logging to all API endpoints" --output-format stream-json
```

### Python SDK

```python
import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def run_coding_task(task: str) -> str:
    options = ClaudeCodeOptions(
        max_turns=30,
        allowed_tools=["bash", "str_replace_based_edit_tool"],
        system_prompt_suffix="Always run tests after making changes.",
    )
    
    messages = []
    async for message in query(prompt=task, options=options):
        messages.append(message)
    
    return messages[-1].content[0].text

result = asyncio.run(run_coding_task(
    "Add input validation to all POST endpoints in src/api/"
))
```

---

## Sub-Agent 與平行化

Claude Code 支援針對大型程式碼庫進行 **sub-agent 派發 (sub-agent dispatch)**：

```
Main Claude Code session
    ↓
"This codebase has 5 modules. I'll spawn sub-agents for each."
    ├── Sub-agent 1: Fix auth module tests
    ├── Sub-agent 2: Add type hints to utils/
    ├── Sub-agent 3: Migrate payments to async
    └── Sub-agent 4: Update API documentation
```

每個 sub-agent 平行執行，接著由主代理審查並合併結果。

**何時使用 sub-agent：**
- 程式碼庫超過 50K 行程式碼
- 平行且獨立的變更（無共享狀態）
- 模組層級的重構任務

---

## 自訂 MCP 整合

Claude Code 會從 `~/.claude/config.json` 或 `.claude/mcp.json` 讀取 MCP server：

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "description": "Live library documentation"
    },
    "postgres": {
      "command": "uvx",
      "args": ["mcp-server-postgres"],
      "env": {"DATABASE_URL": "postgresql://localhost/myapp"},
      "description": "Direct DB access for schema inspection"
    },
    "jira": {
      "command": "uvx",
      "args": ["mcp-server-jira"],
      "env": {"JIRA_URL": "https://company.atlassian.net"},
      "description": "Task tracking integration"
    }
  }
}
```

有了這份設定，Claude Code 可以：
1. 在撰寫程式碼前查閱最新的函式庫文件（Context7）
2. 在撰寫 SQL 前讀取實際的 DB schema（postgres MCP）
3. 在完成實作後將 Jira ticket 標記為完成（jira MCP）

---

## 安全性與權限模型

Claude Code 採用**分層權限模型 (layered permission model)**：

```
Permission Level    Who approves       What it covers
────────────────────────────────────────────────────────
Auto               Claude (no prompt)  Read files, run tests
Ask per-turn       User confirms       Shell command execution
Explicit allow     User pre-approves   Specific commands/dirs
Blocked            Never runs          Network calls outside allowlist
```

### 設定

```json
{
  "permissions": {
    "allow": [
      "bash(pytest*)",           // Always allow test runs
      "bash(ruff*)",             // Always allow linting
      "bash(git diff*)",         // Always allow git reads
      "str_replace_based_edit_tool"  // Always allow file edits
    ],
    "deny": [
      "bash(rm -rf*)",           // Block destructive deletions
      "bash(curl https://external*)", // Block external network
      "bash(pip install*)"       // Block package installs without approval
    ]
  }
}
```

### 生產環境安全規則

1. **務必沙箱化**：在 Docker 容器或 E2B 雲端 VM 中執行
2. **Git 隔離**：開始前先建立一個 feature branch；合併前先審查 diff
3. **人工檢查點**：對於生產環境部署，要求由人工審查最終的 diff
4. **密鑰掃描**：對每一份 Claude Code 的輸出執行 `truffleHog` 或 `git-secrets`
5. **速率限制**：設定 `max_turns` 以防止失控的迴圈（建議：20-30）

---

## 生產環境應用：CI Pipeline

### GitHub Actions 整合

```yaml
# .github/workflows/ai-fix.yml
name: AI Bug Fix
on:
  issues:
    types: [labeled]

jobs:
  ai-fix:
    if: github.event.label.name == 'ai-fix'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Claude Code
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          pip install claude-code
          
          ISSUE_BODY="${{ github.event.issue.body }}"
          
          claude -p "Fix the following bug: $ISSUE_BODY
          
          Rules:
          - Read the relevant files first
          - Make minimal changes
          - Run tests and verify they pass
          - Do not change unrelated code
          " --output-format json --max-turns 15 > result.json
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          title: "AI Fix: ${{ github.event.issue.title }}"
          body: "Automated fix by Claude Code"
          branch: "ai-fix/${{ github.event.issue.number }}"
```

### CI 的成本模型

| 任務類型 | 平均輪數 | 平均 Token | 預估成本 |
|-----------|-----------|------------|----------------|
| 修復 Bug（小型） | 8 | 15K | $0.23 |
| 測試產生 | 12 | 25K | $0.38 |
| 功能實作 | 20 | 50K | $0.75 |
| 大型重構 | 30 | 100K | $1.50 |

*以每天 100 次 CI 執行計算：依任務組合不同，約 $75-150/天。*

---

## 比較：Claude Code 與其他替代方案

| 功能 | Claude Code | Cursor/Windsurf | Cline | OpenHands |
|---------|-------------|-----------------|-------|-----------|
| **介面** | CLI + SDK | IDE（VS Code 分支） | VS Code 擴充套件 | Web UI + CLI |
| **模型** | 僅限 Claude | 任意（GPT、Claude、Gemini） | 任意 | 任意 |
| **自主性** | 完全 | 中等（需要點擊） | 完全 | 完全 |
| **CI/Headless** | ✅ 原生 | ❌ | ✅ | ✅ |
| **MCP 支援** | ✅ 原生 | ✅ | ✅ | ✅ |
| **CLAUDE.md** | ✅ | ❌（類似：.cursorrules） | ❌ | ❌ |
| **開源** | ❌ | ❌ | ✅ | ✅ |
| **最適合** | 後端開發者、CI/CD | UI/前端開發者、視覺化 | 任何開發者 | 自架團隊 |

### SWE-bench Verified 分數（2026 年 5 月）

| 代理 | 分數 | 備註 |
|-------|-------|-------|
| GPT-5.5（原始模型領先者） | 88.7% | SWE-Bench Verified 排行榜 #1 |
| Claude Opus 4.7（原始模型） | 87.6% | 在 SWE-Bench Pro 以 64.3% 領先 |
| Claude Code（Opus 4.7 / Sonnet 4.6） | ~87% | Anthropic 的官方代理 |
| OpenHands + Claude Sonnet 4.6 | ~75% | 開源框架 |
| Aider + Claude Sonnet 4.6 / GPT-5.5 | ~74% | 開源 CLI |
| Devin（商用） | ~65% | Cognition AI 產品 |
| SWE-agent + GPT-5.5 | ~55% | Princeton 研究基準 |

---

## 面試問題

### Q：Claude Code 與 GitHub Copilot 有何不同？

**理想答案：**
Copilot 是一個**補全工具 (completion tool)** — 它會在你打字時預測接下來幾行程式碼。Claude Code 是一個**自主代理 (autonomous agent)** — 你給它一項任務（例如「為這個 API 加入身分驗證」），它會讀取程式碼庫、規劃實作、編輯多個檔案、執行測試、修復失敗，並且只在測試通過時才結束。兩者的體驗有本質上的差異：Copilot 幫助你更快地寫程式；Claude Code 則是替你寫程式，而你負責審查輸出。

### Q：什麼是 CLAUDE.md，為什麼它如此關鍵？

**理想答案：**
CLAUDE.md 就像是專門為 AI 同事撰寫的 `README`。沒有它，Claude Code 會把你的專案當成一個通用的 Python/JS 專案。有了它，Claude 就會知道：你確切的測試命令、你的禁用模式（不准用 raw SQL、要用 ORM）、你的架構決策（JWT 驗證、特定的錯誤格式），以及你的編碼規範。它把一個通用代理轉變成一位**專案專家 (project-specialist)**。我看過在有一份寫得好的 CLAUDE.md 後，任務完成速度快了 2-3 倍、錯誤減少了 60%。

### Q：你如何在生產環境的 CI 中安全地執行 Claude Code？

**理想答案：**
三個層次：
1. **沙箱**：在沒有對外網路存取的 Docker 容器內執行 Claude Code。只有 git repo 與測試執行器是可存取的。
2. **權限白名單 (allow-list)**：使用 permissions 設定，精確地列出哪些 bash 命令是被允許的（測試執行器、linter），並封鎖具破壞性的操作（rm -rf、未經審查的 pip install）。
3. **人工關卡 (human gate)**：Claude Code 會輸出一個帶有 diff 的 branch。由人工在 PR 中審查 diff 並合併。Claude 絕不會直接合併到 main。這讓人類的判斷在最終決策中保持參與。

### Q：對於高流量的 CI，你如何處理 Claude Code 的成本？

**理想答案：**
我用三種方式來最佳化：
1. **任務範圍界定 (task scoping)**：Claude Code 對於獨立、有界限的任務（修復 bug、產生測試）具有成本效益。我不會用它來做開放式的探索 — 那種情況用人工仍然比較便宜。
2. **最大輪數 (max turns)**：設定 `max_turns=15` 可以防止失控的工作因循環推理而燒掉超過 $10。
3. **模型路由 (model routing)**：對於簡單的 bug 修復（語法錯誤、明顯的錯字），我透過 SDK 使用 Claude 3.5 Haiku — 便宜 5 倍。對於架構性的重構，我則使用啟用 Extended Thinking 的 Claude 3.7 Sonnet。

---

## 參考資料

- Anthropic. "Claude Code: Building Agentic Coding Experiences" (2025) — https://docs.anthropic.com/claude-code
- Anthropic. "Claude Code SDK Documentation" — https://github.com/anthropics/claude-code
- Anthropic. "CLAUDE.md Best Practices" — https://docs.anthropic.com/claude-code/settings#claudemd
- SWE-bench Verified Leaderboard — https://www.swebench.com/

---

*下一篇：[OpenCoder / AI 編碼代理全景](10-opencoderguide.md)*
