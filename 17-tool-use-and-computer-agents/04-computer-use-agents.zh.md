# 電腦操作代理(Computer-Use Agents)

電腦操作代理讓 LLM 能夠看見螢幕、針對畫面進行推理,並透過滑鼠點擊與鍵盤輸入來執行動作——就和人類操作電腦的方式一樣。模型不是呼叫結構化的 API,而是直接處理原始像素。本章涵蓋它們的運作方式、何時優於傳統自動化,以及如何圍繞它們設計正式生產系統。

## 目錄

- [什麼是電腦操作代理?](#what-are-computer-use-agents)
- [截圖—推理—動作迴圈](#the-screenshot-reason-act-loop)
- [Claude Computer Use:工具與 API](#claude-computer-use-tools-and-api)
- [架構:沙箱化環境](#architecture-sandboxed-environments)
- [瀏覽器自動化 vs 桌面自動化](#browser-vs-desktop-automation)
- [與傳統自動化的比較](#comparison-with-traditional-automation)
- [何時電腦操作勝過 API 呼叫](#when-computer-use-beats-api-calls)
- [錯誤處理與復原](#error-handling-and-recovery)
- [效能:延遲、成本、吞吐量](#performance-latency-cost-throughput)
- [真實世界應用](#real-world-applications)
- [安全性考量](#security-considerations)
- [程式碼範例](#code-examples)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 什麼是電腦操作代理?

電腦操作代理是一個透過解讀截圖並發出低階輸入指令(滑鼠移動、點擊、鍵盤輸入)來操控圖形介面的 LLM。它取代了人機互動迴圈中的人類角色。

```
Traditional Tool Use:           Computer Use:

User Request                    User Request
     |                               |
     v                               v
 LLM reasons                    LLM reasons
     |                               |
     v                               v
 Structured API call             Screenshot captured
 {"tool": "search",                  |
  "query": "..."}                    v
     |                          LLM sees pixels, finds button
     v                               |
 API returns JSON                    v
     |                          Mouse click at (x=340, y=220)
     v                               |
 LLM formats answer                  v
                                New screenshot captured
                                     |
                                     v
                                LLM verifies result, continues...
```

關鍵差異在於:傳統工具使用需要具有已知 schema 的預先定義 API。電腦操作則適用於任何具有視覺介面的應用程式——不需要 API。

### 全貌(2026)

目前已有多家供應商提供電腦操作能力:

| 供應商 | 代理 | 方法 | 主要優勢 |
|----------|-------|----------|--------------|
| Anthropic | Claude Computer Use | 視覺 + 座標推理 | 桌面 + 瀏覽器、成熟的 API |
| OpenAI | ChatGPT Agent Mode | 以 Operator 為基礎的瀏覽器代理 | 深度網頁瀏覽 |
| Google | Project Mariner | Gemini 視覺—語言模型 | Chrome 整合 |
| Microsoft | UFO/UFO2 | Windows UI Automation + 視覺 | 原生 Windows 支援 |
| Amazon | Nova Act | 專為瀏覽器打造的模型 | 電子商務工作流程 |

---

## 截圖—推理—動作迴圈

每個電腦操作代理都遵循相同的核心迴圈,通常稱為「代理迴圈」(agent loop)或「動作迴圈」(action loop):

```
+------------------+
|  Capture Screen  |<-----------+
+--------+---------+            |
         |                      |
         v                      |
+------------------+            |
|  Send to LLM     |            |
|  (screenshot +   |            |
|   task context)  |            |
+--------+---------+            |
         |                      |
         v                      |
+------------------+            |
|  LLM Reasons     |            |
|  about next      |            |
|  action           |           |
+--------+---------+            |
         |                      |
    +----+----+                 |
    |         |                 |
    v         v                 |
 [Action]  [Done]               |
    |                           |
    v                           |
+------------------+            |
| Execute Action   |            |
| (click, type,    |            |
|  scroll, key)    |            |
+--------+---------+            |
         |                      |
         +----------------------+
```

每次迭代:
1. **截圖(Capture)**:擷取目前顯示狀態的截圖。
2. **傳送(Send)**:將截圖(base64 影像)連同對話歷史一起傳給 LLM。
3. **推理(Reason)**:模型分析螢幕上的內容,判斷朝向目標的下一步。
4. **動作(Act)**:模型輸出一個工具呼叫(例如 `click at (450, 320)`),由執行環境(runtime)執行。
5. **重複(Repeat)**:擷取新的截圖,迴圈持續進行,直到模型發出完成訊號。

模型透過對話歷史在各次迭代之間維持脈絡,這些歷史持續累積截圖與動作,如同對過往事件的視覺「記憶」。

---

## Claude Computer Use:工具與 API

Claude 為電腦操作開放了三個內建工具。這些是 Anthropic 定義的工具——你不需要撰寫實作;Claude 知道如何產生對它們的呼叫,而你的執行環境會針對該環境執行這些呼叫。

### 三個工具

**1. `computer` —— 完整 GUI 控制**

控制虛擬顯示器上的滑鼠與鍵盤。功能:
- `screenshot` —— 擷取目前螢幕狀態
- `left_click`、`right_click`、`double_click`、`triple_click` —— 在指定座標進行滑鼠點擊
- `left_click_drag` —— 從一點拖曳到另一點
- `type` —— 輸入一段文字字串
- `key` —— 按下鍵盤按鍵(例如 `ctrl+c`、`Return`、`Escape`)
- `scroll` —— 在某座標處向上/下/左/右捲動
- `move` —— 將游標移動到指定座標
- `hold_key` —— 在執行另一個動作的同時按住修飾鍵
- `wait` —— 暫停指定的時間長度

**2. `bash` —— Shell 指令執行**

在持續性 session 中執行 shell 指令:
- 各指令共享狀態(環境變數、工作目錄)
- 支援多行腳本
- 輸出會被擷取並以文字回傳

**3. `text_editor` —— 檔案操作**

具備下列指令的結構化檔案編輯:
- `view` —— 讀取檔案內容(可選擇行數範圍)
- `create` —— 建立含內容的新檔案
- `str_replace` —— 取代檔案中特定的字串(必須是唯一相符項)
- `insert` —— 在指定行號插入文字

### API 請求結構

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    tools=[
        {
            "type": "computer_20250124",
            "name": "computer",
            "display_width_px": 1280,
            "display_height_px": 800,
            "display_number": 1
        },
        {
            "type": "bash_20250124",
            "name": "bash"
        },
        {
            "type": "text_editor_20250124",
            "name": "str_replace_based_edit_tool"
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "Open Firefox, navigate to github.com, and find repos trending today."
        }
    ],
    betas=["computer-use-2025-01-24"]
)
```

回應將包含 `tool_use` 區塊,你的執行環境必須執行這些區塊,並以 `tool_result` 訊息回饋。

---

## 架構:沙箱化環境

電腦操作代理必須在隔離的環境中執行。模型能完全控制滑鼠與鍵盤——你絕不會希望它在你的正式生產工作站上擁有這種控制權。

### 標準架構:Docker + VNC

```
+-----------------------------------------------------+
|  Docker Container                                   |
|                                                     |
|  Xvfb (Virtual X11) + Mutter (WM) + Tint2 (Panel)  |
|         |                                           |
|         v                                           |
|  +------------------+     +-------------------+     |
|  | Virtual Desktop  |---->| Screenshot Capture|     |
|  | 1280x800         |     | (scrot/maim)      |     |
|  | Firefox, apps    |     +--------+----------+     |
|  +------------------+              |                |
|                                    v                |
|                           +--------+----------+     |
|                           | Agent Runtime     |     |
|                           | - Calls Claude API|     |
|                           | - Executes actions|     |
|                           | - Manages loop    |     |
|                           +-------------------+     |
+-----------------------------------------------------+
```

### 雲端託管的替代方案

像 E2B(e2b.dev)這類服務提供預先配置好的沙箱化環境:
- 預先安裝瀏覽器與工具的臨時(ephemeral)VM
- 用於截圖擷取與輸入注入的 API
- session 結束後自動清理
- 無需管理 Docker 的額外負擔

### 關鍵環境元件

| 元件 | 用途 | 範例 |
|-----------|---------|---------|
| Xvfb | 虛擬 X11 顯示伺服器 | 在沒有實體顯示器的情況下建立 framebuffer |
| Mutter/Xfwm | 視窗管理員 | 處理視窗定位、調整大小 |
| Tint2 | 工作列面板 | 顯示執行中的應用程式 |
| xdotool | 輸入注入 | 執行滑鼠/鍵盤指令 |
| scrot/maim | 截圖擷取 | 將顯示畫面拍成 PNG 快照 |

---

## 瀏覽器自動化 vs 桌面自動化

| 面向 | 僅限瀏覽器 | 完整桌面 |
|-----------|-------------|--------------|
| 範圍 | 僅限 Web 應用程式 | 任何 GUI 應用程式 |
| 設定複雜度 | 較低(headless 瀏覽器) | 較高(完整桌面環境) |
| 效能 | 較快(截圖較小) | 較慢(全螢幕擷取) |
| 可靠性 | 較高(版面可預期) | 較低(OS 差異) |
| 使用情境 | 網頁抓取、表單填寫 | 老舊軟體、跨應用程式工作流程 |

瀏覽器自動化控制的是 Web 瀏覽器(瀏覽、填寫表單、點擊按鈕、處理 SPA)。桌面自動化控制的是整個 OS 環境(啟動應用程式、使用原生對話框、與重型用戶端(thick-client)軟體互動、跨多個應用程式串接操作)。

---

## 與傳統自動化的比較

Selenium、Playwright 與 Puppeteer 透過直接存取 DOM 來自動化瀏覽器。電腦操作代理則處理像素。兩者在正式生產中各有其用武之地。

| 特性 | Selenium/Playwright | 電腦操作代理 |
|---------|--------------------|--------------------|
| 速度 | 快(直接存取 DOM) | 慢(截圖 + LLM) |
| 可靠性 | 脆弱(selector 變動) | 穩健(視覺辨識) |
| 維護 | 需持續更新 selector | 極少(可適應 UI 變更) |
| 反爬蟲偵測 | 經常被封鎖 | 較難被偵測 |
| 每個動作的成本 | 約 $0.001 | 約 $0.01-0.05 |
| 非 Web 支援 | 否 | 是(任何 GUI) |

**混合式做法(Hybrid approaches)**在正式生產中效果最佳:由 Playwright 處理高流量、定義明確的流程(登入、瀏覽),而由電腦操作代理處理動態、不可預測的步驟(視覺驗證、新穎版面、反爬蟲網站)。

---

## 何時電腦操作勝過 API 呼叫

**在下列情況使用電腦操作:**沒有 API 存在(老舊系統)、反爬蟲防護封鎖了 Selenium、需要視覺判斷(圖表驗證、PDF 版面)、UI 變動速度快過 selector 能被維護的速度,或工作流程橫跨多個桌面應用程式。

**在下列情況堅持使用 API:**有結構化 API 可用(永遠優先選用)、延遲很重要(亞秒級)、流量很高(每小時數千個動作),或需要確定性(相同輸入、相同輸出)。

---

## 錯誤處理與復原

電腦操作代理的失敗方式與以 API 為基礎的工具不同。主要的失敗模式:

### 1. 誤點(座標錯誤)

模型從截圖計算座標,但可能差個幾像素:
- **緩解措施**:在每次點擊後使用 `screenshot` 來驗證預期的狀態變化是否發生。
- **復原措施**:如果點到了錯誤的元素,模型可以針對新狀態進行推理並修正方向。

### 2. 過時的截圖

螢幕可能在擷取與動作執行之間發生變化(動畫、彈出視窗、載入中):
- **緩解措施**:在截圖前加入短暫等待。當頁面正在載入時使用 `wait` 動作。
- **復原措施**:在繼續之前重新擷取並重新評估。

### 3. 無限迴圈

模型在沒有進展的情況下重複相同的動作:
- **緩解措施**:設定最大迭代次數(例如每個任務 50 個動作)。
- **復原措施**:在 N 次重複的相同動作後,強制採用不同的做法或升級交由人工處理。

### 4. 非預期的對話框

Cookie 橫幅、彈出視窗、權限對話框會在非預期的時機出現:
- **緩解措施**:在 system prompt 中納入處理常見對話框的指示。
- **復原措施**:模型的視覺推理通常能自然地處理這些情況——它看見對話框並將其關閉。

### 5. 解析度與縮放不匹配

模型是在特定解析度下訓練的。不匹配會造成座標錯誤:
- **緩解措施**:使用建議的解析度(1280x800),並將顯示縮放設為 100%。
- **復原措施**:調整 `display_width_px` 與 `display_height_px` 以符合實際顯示器。

### 錯誤處理模式

代理迴圈應追蹤動作歷史並偵測重複。如果同一個動作連續被發出 3 次以上,就注入一則訊息,告訴模型嘗試不同的做法。永遠設定一個硬性的最大迭代次數上限(例如 50),並在每個動作後擷取一張驗證截圖以偵測狀態變化。完整的代理迴圈請參見下方的「程式碼範例」一節。

---

## 效能:延遲、成本、吞吐量

### 延遲分解

代理迴圈的每次迭代涉及:

```
Screenshot capture:     ~100ms
Image encoding (base64): ~50ms
API call (with image):   ~2-5s  (model inference)
Action execution:        ~100ms
                        --------
Total per action:        ~2.5-5.5s
```

一個典型的 10 步任務需要 25-55 秒。相較之下,Playwright 在不到 2 秒內就能完成相同的 10 個步驟。

### 每個動作的成本

每個動作會傳送一張截圖(約 800KB base64)加上對話歷史:

| 模型 | 每個動作的成本(約) | 備註 |
|-------|-------------------------|-------|
| Claude Sonnet 4 | $0.01-0.03 | 多數任務的建議選擇 |
| Claude Opus 4 | $0.05-0.15 | 用於複雜的視覺推理 |

一個 20 步的工作流程使用 Sonnet 約花費 $0.20-0.60,使用 Opus 約 $1.00-3.00。

### 吞吐量最佳化

- **平行 session**:執行多個 Docker container 以處理並行任務。
- **選擇性截圖**:只在不確定的動作後擷取;在輸入文字後略過。
- **降低解析度**:使用 1024x768 而非 1920x1080,以減少 token 成本。
- **提早終止**:訓練模型一旦驗證目標達成就立即發出完成訊號。

---

## 真實世界應用

| 應用 | 運作方式 | 為何使用電腦操作 |
|------------|--------------|------------------|
| 老舊系統整合 | 代理在大型主機(mainframe)/重型用戶端 UI 中瀏覽,將資料擷取為結構化格式 | 老舊軟體沒有 API 存在 |
| 表單填寫 / 資料輸入 | 讀取來源文件,逐欄填寫 Web 表單,處理多頁精靈(wizard) | 政府入口網站、具有複雜條件邏輯的保險理賠 |
| QA 與視覺測試 | 以使用者身分瀏覽應用程式,驗證視覺呈現,以自然語言回報問題 | 超越像素差異比對(pixel-diff)——能理解版面與 UX |
| 競爭情報 | 瀏覽產品頁面,從 JS 渲染的 widget 擷取定價資料 | 可在封鎖傳統爬蟲的網站上運作 |

---

## 安全性考量

| 風險 | 會發生什麼 | 緩解措施 |
|------|-------------|------------|
| **可見的機密** | 模型在截圖中看見密碼、session、通知 | 臨時(ephemeral)container,使用後清除憑證 |
| **不受限制的動作** | 代理可執行 shell 指令、瀏覽任何地方、下載檔案 | 防火牆規則、唯讀檔案系統、session 時間限制、對破壞性操作採用 HITL |
| **資料外洩** | 傳送給 LLM 供應商的截圖含有敏感資料 | 受監管產業採用地端(on-premise)部署、遮蔽敏感 UI 欄位 |
| **透過 UI 的 prompt injection** | 惡意網站顯示文字以操控代理 | 在 system prompt 中加入警告,反對遵循與任務相牴觸的螢幕指示 |

最高原則:**除非在完全沙箱化的 container 中,否則絕不在你的正式生產工作站上,或在可存取真實憑證的情況下,執行電腦操作代理**。

---

## 程式碼範例

### 最小化代理迴圈

```python
import anthropic, base64, subprocess

client = anthropic.Anthropic()

def capture_screenshot():
    subprocess.run(["scrot", "/tmp/screen.png", "-o"], check=True)
    with open("/tmp/screen.png", "rb") as f:
        return base64.standard_b64encode(f.read()).decode()

def execute_action(action):
    name = action["action"]
    if name == "left_click":
        x, y = action["coordinate"]
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])
    elif name == "type":
        subprocess.run(["xdotool", "type", "--", action["text"]])
    elif name == "key":
        subprocess.run(["xdotool", "key", action["text"]])

def run_agent(task: str, max_steps: int = 30):
    messages = [{"role": "user", "content": task}]
    tools = [
        {"type": "computer_20250124", "name": "computer",
         "display_width_px": 1280, "display_height_px": 800},
        {"type": "bash_20250124", "name": "bash"},
        {"type": "text_editor_20250124", "name": "str_replace_based_edit_tool"},
    ]
    for step in range(max_steps):
        response = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=4096,
            tools=tools, messages=messages, betas=["computer-use-2025-01-24"],
        )
        if response.stop_reason == "end_turn":
            return [b.text for b in response.content if b.type == "text"]

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name == "computer":
                execute_action(block.input)
                tool_results.append({
                    "type": "tool_result", "tool_use_id": block.id,
                    "content": [{"type": "image", "source": {
                        "type": "base64", "media_type": "image/png",
                        "data": capture_screenshot()}}],
                })
            elif block.name == "bash":
                r = subprocess.run(block.input["command"],
                    shell=True, capture_output=True, text=True)
                tool_results.append({
                    "type": "tool_result", "tool_use_id": block.id,
                    "content": r.stdout + r.stderr,
                })
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
    return ["Max steps reached"]
```

### 沙箱化環境的 Dockerfile

```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    xvfb mutter tint2 xdotool scrot firefox-esr python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install anthropic
ENV DISPLAY=:1
COPY agent.py /agent.py
CMD Xvfb :1 -screen 0 1280x800x24 & sleep 1 && mutter & tint2 & \
    sleep 1 && python3 /agent.py
```

---

## 面試問題

### Q:某客戶每天有 500 份保險理賠 PDF,必須輸入到一個沒有 API 的老舊 Web 入口網站。請設計一個使用電腦操作代理的系統。

**優秀答案:**
我會建構一個分三階段的流水線(pipeline)。第一,文件處理階段,使用 LLM 從 PDF 中擷取結構化資料(理賠編號、理賠人姓名、金額、日期)。第二,電腦操作代理階段,每筆理賠由一個在隔離的 Docker container 中、具備虛擬顯示器的 Claude Computer Use 代理處理。代理瀏覽該 Web 入口網站,使用擷取出的資料填寫表單欄位,並在送出後擷取一張確認截圖。第三,驗證階段,使用另一次獨立的 LLM 呼叫,將確認截圖與預期資料進行比對,以捕捉任何輸入錯誤。

為了擴展規模,我會平行執行 10-20 個 container,每個依序處理理賠。以代理每筆理賠約 2 分鐘計算,20 個 container 在 8 小時的工作日內可處理 600 筆理賠。我會為重試 3 次後仍失敗的理賠加入一個 dead-letter queue,交由人工審查。

以每筆理賠 $0.50 的成本計算(約 20 個動作、每個 $0.025),500 筆理賠每天為 $250——這很可能比它所取代的人工資料輸入團隊更便宜。

### Q:請比較電腦操作代理與 Selenium 在 Web 自動化上的差異。你會在何時選擇哪一種?

**優秀答案:**
Selenium 直接與 DOM 互動——它快速、具確定性,而且便宜。但當 selector 變動時它會壞掉、會被反爬蟲系統封鎖,而且無法處理需要視覺判斷的任務。

電腦操作代理每個動作慢 100 倍、貴 10 倍,但它們能適應 UI 變更,因為它們處理的是像素而非 selector。它們更能應對反爬蟲偵測,因為它們會產生類似人類的互動模式。而且它們能針對視覺版面進行推理——驗證圖表是否正確渲染,或從 Selenium 無法檢視的 canvas 元素讀取內容。

對於高流量、穩定且目標網站在我控制之下的工作流程,我會選擇 Selenium。對於一次性任務、頻繁變動的第三方網站、跨應用程式的桌面工作流程,以及任何維護 selector 的人力成本超過 LLM 推理成本的任務,我會選擇電腦操作代理。

最好的正式生產系統會兩者並用:由 Playwright 處理可預期的步驟(身分驗證、瀏覽),而由電腦操作代理處理動態步驟(解讀結果、做出判斷)。

---

## 參考資料

- Anthropic. "Computer Use Tool" API Documentation (2025)
- Anthropic. "Bash Tool" and "Text Editor Tool" API Documentation (2025)
- E2B. "Sandboxed Cloud Environments for AI Agents" (2025)
- OSWorld Benchmark: Desktop Agent Evaluation Suite (2025)
- WebArena Benchmark: Web Agent Evaluation Suite (2024)

---

*下一篇:[建構工具使用代理](05-building-tool-agents.md)*
