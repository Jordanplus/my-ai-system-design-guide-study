# 🔄 轉職進入 AI 工程職位

> 一份具體、針對特定角色的指南，協助工程師、PM、QA 與管理者轉入聚焦 AI 的職位。
> **沒有空泛的建議。每一條路徑都對應到真實的技能、真實的 repo 章節，以及真實的課程。**

---

## 這份指南適合誰

你目前的工作是軟體工程師、QA、PM、EM 或資料工程師，而你想轉入聚焦 AI 的角色。這份指南會把你**既有的技能**對應到特定的 AI 角色，明確告訴你**該補齊哪些缺口**，並指引你到本 repo 與課程中正確的章節去填補它們。

---

## AI 角色全貌

在挑選路徑之前，先了解這些目標角色實際上是什麼:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI ROLE LANDSCAPE                            │
│                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │   APPLICATION LAYER  │    │     INFRASTRUCTURE LAYER     │  │
│  │                      │    │                              │  │
│  │  LLM App Engineer    │    │  MLOps / AI Infra Engineer   │  │
│  │  AI Product Engineer │    │  AI Platform Engineer        │  │
│  │  Agentic Systems Eng │    │  AI Reliability Engineer     │  │
│  └──────────────────────┘    └──────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │    QUALITY LAYER     │    │     LEADERSHIP LAYER         │  │
│  │                      │    │                              │  │
│  │  AI Eval Engineer    │    │  AI Product Manager          │  │
│  │  AI Quality Engineer │    │  AI Engineering Manager      │  │
│  │  Red Team Analyst    │    │  AI Program Manager          │  │
│  └──────────────────────┘    └──────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │    RESEARCH LAYER    │    │     SPECIALIST LAYER         │  │
│  │                      │    │                              │  │
│  │  Applied AI Scientist│    │  Agentic Coding Specialist   │  │
│  │  Fine-tuning Engineer│    │  RAG Architect               │  │
│  │  Alignment Researcher│    │  AI Safety Engineer          │  │
│  └──────────────────────┘    └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 依現職角色劃分的轉職路徑

---

### 1. 🖥️ 後端工程師 → AI 工程

**為什麼後端是最好的起點:** 你已經理解 API、延遲、資料庫、分散式系統以及生產環境的可靠性。AI 應用全都需要這些。缺口主要是領域知識，而不是工程基本功。

#### 目標角色

```
Backend Engineer
      │
      ├──► LLM Application Engineer       (most common transition, 3–6 months)
      ├──► Agentic Systems Engineer        (3–9 months)
      ├──► AI Infrastructure / MLOps Eng  (6–12 months, needs GPU/serving knowledge)
      └──► RAG Architect                  (4–8 months)
```

#### 技能缺口分析

| 你已具備 | 待補齊的缺口 | 優先順序 |
|-----------------|--------------|----------|
| REST API 設計 | LLM API 整合模式 | 🔴 高 |
| 資料庫設計 | 向量資料庫 (Qdrant、Pinecone、Weaviate) | 🔴 高 |
| 非同步/串流 | 串流式 LLM 回應、token streaming | 🔴 高 |
| 認證與多租戶 | 多租戶 RAG 隔離 | 🔴 高 |
| 快取 (Redis、CDN) | prompt caching、語意快取 | 🟡 中 |
| 監控 (Prometheus) | LLM 可觀測性 (traces、evals) | 🟡 中 |
| CI/CD | LLMOps pipeline、模型版本管理 | 🟡 中 |
| 無 | embedding 模型與向量數學 | 🟡 中 |
| 無 | prompt engineering 基礎 | 🟡 中 |
| 無 | RAG pipeline 架構 | 🟡 中 |
| 無 | agent 框架 (LangGraph、CrewAI) | 🟢 較低 |
| 無 | fine-tuning 概念 (LoRA、RLHF) | 🟢 較低 |

#### 你的 90 天計畫

**第 1 個月: LLM 整合**
- 學習 OpenAI / Anthropic API (streaming、function calling、structured output)
- 建立一套簡單的 RAG 系統: PDF 匯入 → Qdrant → LLM 回應
- 閱讀本 repo: [01-foundations](01-foundations/)、[02-model-landscape](02-model-landscape/)、[05-prompting-and-context](05-prompting-and-context/)
- 課程: *ChatGPT Prompt Engineering for Developers* (DeepLearning.AI，免費)

**第 2 個月: 生產環境模式**
- 為你的 RAG 系統加入多租戶隔離
- 加入 LangSmith 或 Langfuse tracing  
- 實作 prompt caching 以節省成本
- 閱讀本 repo: [06-retrieval-systems](06-retrieval-systems/)、[12-security-and-access](12-security-and-access/)、[08-memory-and-state](08-memory-and-state/)
- 課程: *Building and Evaluating Advanced RAG* (DeepLearning.AI，免費)

**第 3 個月: Agentic 系統**
- 建立一個帶工具 (網路搜尋、程式碼執行) 的 LangGraph agent
- 用 RAGAS 或 Phoenix 加入評估 pipeline
- 在適當的成本控管與速率限制下部署
- 閱讀本 repo: [07-agentic-systems](07-agentic-systems/)、[09-frameworks-and-tools](09-frameworks-and-tools/)、[14-evaluation-and-observability](14-evaluation-and-observability/)
- 課程: *AI Agents in LangGraph* (DeepLearning.AI，免費)

#### 作品集專案構想
- 具備存取控制的多租戶文件問答服務
- 會在 GitHub PR 留言的 agentic 程式碼審查器
- 由 RAG 驅動、附帶評估 pipeline 的內部知識庫

---

### 2. 🎨 前端工程師 → AI 產品工程

**為什麼這個轉職行得通:** 前端工程師理解 UX、即時 UI 更新與使用者行為。AI 產品的成敗取決於 UX——串流回應、漸進式渲染、載入狀態、回饋收集。你的技能比你想像中更有價值。

#### 目標角色

```
Frontend Engineer
      │
      ├──► AI Product Engineer         (3–6 months — highest demand)
      ├──► AI UX Engineer              (3–6 months, UX focus)
      └──► Full-Stack LLM Engineer     (6–9 months, add backend LLM skills)
```

#### 技能缺口分析

| 你已具備 | 待補齊的缺口 | 優先順序 |
|-----------------|--------------|----------|
| 串流 UI (SSE、WebSocket) | LLM token streaming 整合 | 🔴 高 |
| 狀態管理 | 對話狀態、session memory | 🔴 高 |
| 使用者回饋模式 | AI 回饋收集 (按讚、評分) | 🔴 高 |
| 表單驗證 | prompt 輸入驗證與淨化 | 🟡 中 |
| 非同步錯誤處理 | LLM timeout、fallback、retry 模式 | 🟡 中 |
| A/B 測試 | LLM A/B 測試與變體追蹤 | 🟡 中 |
| 無 | 基礎 prompt engineering | 🟡 中 |
| 無 | LLM API 整合 (至少一家供應商) | 🟡 中 |
| 無 | 理解 context window | 🟡 中 |
| 無 | 基礎 RAG 概念 (它是什麼、為何需要) | 🟢 較低 |

#### 你的 90 天計畫

**第 1 個月: 把 LLM 整合進 UI**
- 建立一個串流聊天介面 (Next.js + Vercel AI SDK)
- 實作妥當的載入狀態、逐 token 渲染、error boundary
- 加入回饋小工具 (讚/倒讚、重新生成按鈕)
- 課程: *ChatGPT Prompt Engineering for Developers* (DeepLearning.AI，免費)

**第 2 個月: AI 的 UX 模式**
- 以 session 狀態實作對話記憶
- 為 RAG 回應加入引用渲染
- 為你的團隊建立一個 prompt playground UI
- 閱讀本 repo: [08-memory-and-state](08-memory-and-state/)、[05-prompting-and-context](05-prompting-and-context/)

**第 3 個月: 評估整合**
- 為你的 UI 加上儀表，以收集回饋訊號
- 把回饋連接到 Langfuse 或 LangSmith 專案
- 在兩個 prompt 變體之間執行一次基本的 A/B 測試
- 閱讀本 repo: [14-evaluation-and-observability](14-evaluation-and-observability/)
- 課程: *Evaluating and Debugging Generative AI* (DeepLearning.AI + W&B，免費)

#### 作品集專案構想
- 具備 AI 建議與行內引用的串流文件編輯器
- 帶有持久脈絡的多步驟 AI 表單精靈
- 顯示各功能品質指標的 AI 回饋儀表板

---

### 3. 🧪 QA 工程師 → AI Eval 工程師

**為什麼 QA 是最被低估的路徑:** AI 評估本質上是一種新形態的 QA。手動測試案例設計、邊界案例思維、迴歸防範——這些正是 AI 系統所需要的。但工具不同，而且面對非確定性輸出時的心態需要轉變。

#### 目標角色

```
QA Engineer
      │
      ├──► AI Eval Engineer            (3–6 months — best fit, fast transition)
      ├──► AI Quality Engineer         (3–6 months)
      └──► Red Team Analyst            (6–9 months, security focus)
```

#### 技能缺口分析

| 你已具備 | 待補齊的缺口 | 優先順序 |
|-----------------|--------------|----------|
| 測試案例設計 | eval 資料集建立 (dimensional sampling) | 🔴 高 |
| 迴歸測試思維 | 把 eval 套件當作 CI 品質關卡 | 🔴 高 |
| 缺陷回報 | 錯誤分析方法論 (open/axial coding) | 🔴 高 |
| 測試自動化 | LLM-as-judge 評估器自動化 | 🔴 高 |
| 非功能性測試 | 幻覺、偏見、毒性偵測 | 🟡 中 |
| 使用者驗收測試 | 人工標註工作流 | 🟡 中 |
| 無 | tracing 與可觀測性建置 | 🟡 中 |
| 無 | RAGAS 指標 (faithfulness、relevance、recall) | 🟡 中 |
| 無 | 基礎 prompt engineering | 🟢 較低 |
| 無 | 用於 eval pipeline 的 Python 腳本 | 🟢 較低 |

#### 你的 90 天計畫

**第 1 個月: 錯誤分析基礎**
- 在任一 LLM 應用 (你自己的或開源的) 上建置 Langfuse 或 Phoenix tracing
- 進行 3 輪手動錯誤分析: 檢視 50 筆 trace、撰寫筆記、分類
- 閱讀本 repo 的 evals 配套指南:
  - [AI Evals: Comprehensive Study Guide](ai_evals_comprehensive_study_guide.md)
  - [AI Evals: LangWatch + Langfuse Guide](ai_evals_complete_guide_langwatch_langfuse.md)
- 要閱讀的課程章節: *Error Analysis: The Secret Sauce* (位於 evals 指南內，第 3 章)

**第 2 個月: 打造評估器**
- 撰寫 3 個以程式碼為基礎的評估器 (JSON schema 檢查、格式驗證器、以 regex 為基礎)
- 撰寫 1 個帶有 Train/Dev/Test 校準的 LLM-as-judge 評估器
- 引入 `judgy` 進行統計偏差校正
- 閱讀本 repo: [14-evaluation-and-observability](14-evaluation-and-observability/)
- 課程: *Quality and Safety for LLM Applications* (DeepLearning.AI + WhyLabs，免費)

**第 3 個月: CI/CD 整合**
- 把評估器接進 GitHub Actions 工作流——每次 PR 都跑 eval
- 定義品質關卡 (faithfulness > 0.85、格式通過率 > 0.99)
- 建立每週 eval 報告儀表板
- 課程: *Evals for AI* (Maven，Hamel + Shreya——付費，為了職涯轉換很值得)

#### 作品集專案構想
- 為某個公開 LLM 應用打造的開源 eval 套件
- 部落格文章:「我如何把 QA 方法論應用在抓出 LLM 失敗上」
- 搭配 LangSmith + GitHub Actions 的 eval pipeline 範本 repo

---

### 4. 📋 產品經理 → AI 產品經理

**為什麼 PM 處於獨特的有利位置:** AI 產品失敗的原因不是模型不好，而是糟糕的產品決策 (問錯問題、錯的 eval 標準、錯的成功指標)。理解 AI 失敗模式的 PM 極為稀有且備受重視。

#### 目標角色

```
Product Manager
      │
      ├──► AI Product Manager           (3–6 months — direct analog)
      ├──► AI Program Manager           (3–6 months, coordination focus)
      └──► Head of AI Product           (9–18 months, leadership path)
```

#### 技能缺口分析

| 你已具備 | 待補齊的缺口 | 優先順序 |
|-----------------|--------------|----------|
| 使用者研究 | 把錯誤分析當作顧客之聲 | 🔴 高 |
| 成功指標定義 | AI 專屬指標 (faithfulness、完成率) | 🔴 高 |
| 路線圖優先排序 | 從 eval 資料進行失敗模式優先排序 | 🔴 高 |
| A/B 測試 | LLM A/B 測試設計 (prompt 變體、模型) | 🔴 高 |
| 利害關係人溝通 | 向合作夥伴說明 AI 的限制 | 🟡 中 |
| PRD 撰寫 | AI 系統能力文件與限制文件 | 🟡 中 |
| 無 | 從高層次理解 LLM 如何運作 (不需寫程式) | 🟡 中 |
| 無 | RAG pipeline 概念 | 🟡 中 |
| 無 | tracing / 可觀測性工具 (Langfuse UI) | 🟡 中 |
| 無 | prompt engineering 基礎 | 🟢 較低 |

#### 你的 90 天計畫

**第 1 個月: 建立技術詞彙**
- 閱讀本 repo 的 foundations，「不要」跳過去看程式碼:
  - [01-foundations](01-foundations/) —— 從概念上理解 transformer
  - [02-model-landscape](02-model-landscape/) —— 了解有哪些模型存在、各自成本如何
  - [GLOSSARY.md](GLOSSARY.md) —— 學習這套詞彙
- 課程: *AI for Everyone* (Coursera，Andrew Ng，免費) —— 專為非技術角色設計

**第 2 個月: 親自負責錯誤分析**
- 請你的工程團隊建置 Langfuse 或 LangSmith
- 親自檢視來自你產品的 100 筆以上 trace——做筆記、找出模式
- 與你的團隊執行一場錯誤分析會議; 由你主導失敗模式分類
- 閱讀本 repo: [14-evaluation-and-observability](14-evaluation-and-observability/)
- 閱讀: [AI Evals Comprehensive Study Guide](ai_evals_comprehensive_study_guide.md) 第 3 章 (錯誤分析)

**第 3 個月: 定義你的 eval 策略**
- 為你的產品撰寫一份「AI 品質規格」: 定義每個功能「好」的樣子是什麼
- 與工程師合作，為這些標準加上 eval 儀表
- 為你的下一季設定成功指標，其中要納入 AI 品質關卡 (而不只是使用者成長)
- 課程: *Evals for AI* (Maven，Hamel + Shreya —— 明確為 PM 設計)

#### 讓你以 AI PM 身分脫穎而出的技能
- 你曾親自檢視過 trace (多數 PM 會把這件事外包出去)
- 你能以量化方式定義失敗模式，而不只是質化描述
- 你能溝通品質改善的成本 (調整 prompt vs. 升級模型 vs. fine-tuning)
- 你理解 RAG、fine-tuning 與 prompt engineering 之間的差異——以及各自在何時最適合採用

---

### 5. 👨‍💼 工程經理 → AI 工程經理

**EM 的轉職關乎領導力的演進:** AI 方面的技術素養是必要的，但並不充分。關鍵轉變在於管理非確定性系統、管理在沒有 ground truth 之下評估品質的團隊，以及應對一個每 3–6 個月就改變一次的領域。

#### 目標角色

```
Engineering Manager
      │
      ├──► AI Engineering Manager       (6–12 months)
      ├──► Director of AI Engineering   (12–24 months)
      └──► VP of AI / Head of AI        (18–36 months)
```

#### 身為 AI EM 有什麼改變

| 傳統 EM | AI EM 的新增項目 |
|----------------|-----------------|
| Sprint 規劃 | 由 eval 驅動的迭代週期 |
| PR 審查標準 | 把 eval 套件當作新的「測試通過」門檻 |
| 招募後端/前端人才 | 招募 LLM、向量搜尋、evals 專長人才 |
| 針對服務中斷的事件回應 | 針對品質迴歸的事件回應 |
| 帶有 feature flag 的路線圖 | 帶有模型升級風險的路線圖 |
| 以交付為基礎的績效考核 | 納入 AI 品質責任歸屬的績效考核 |

#### 你的 90 天計畫

**第 1 個月: 技術深度**
- 閱讀整個 [09-frameworks-and-tools](09-frameworks-and-tools/) 以理解工具全貌
- 閱讀 [09-claude-code.md](09-frameworks-and-tools/09-claude-code.md) 與 [10-opencoderguide.md](09-frameworks-and-tools/10-opencoderguide.md) —— 你將管理使用這些工具的團隊
- 理解成本: 閱讀 [02-model-landscape/03-pricing-and-costs.md](02-model-landscape/03-pricing-and-costs.md)
- 課程: *Generative AI with LLMs* (Coursera，DeepLearning.AI) —— 給你足夠的深度去主導技術討論

**第 2 個月: 流程與團隊設計**
- 重新設計你的團隊對「完成」的定義，納入 eval 關卡
- 建立 eval 文化: 每週 trace 審查、在 retro 中檢視品質指標
- 定義你的 AI 事件處理手冊: 當幻覺率飆升時該怎麼辦?
- 閱讀本 repo: [13-reliability-and-safety](13-reliability-and-safety/)、[14-evaluation-and-observability](14-evaluation-and-observability/)

**第 3 個月: 策略與招募**
- 為你的團隊定義 AI 技能矩陣: 誰具備什麼、缺了什麼
- 為 AI 工程師打造一份面試評分標準 (以 [00-interview-prep](00-interview-prep/) 作為來源)
- 為下一季設定團隊層級的 AI 品質 OKR
- 課程: *CS294 LLM Agents* (Berkeley，免費) —— 給你進行策略對話所需的深度

---

### 6. 🛠️ DevOps / 平台工程師 → MLOps / AI 基礎設施工程師

**為什麼平台工程師在這裡如魚得水:** Kubernetes、CI/CD、可觀測性、成本管理、SLA——這些你全都做過。AI 專屬的新增項目是 GPU 排程、模型服務以及 LLMOps pipeline。

#### 目標角色

```
DevOps / Platform Engineer
      │
      ├──► MLOps Engineer               (3–6 months)
      ├──► AI Infrastructure Engineer   (6–9 months)
      └──► AI Platform Engineer         (9–12 months)
```

#### 技能缺口分析

| 你已具備 | 待補齊的缺口 | 優先順序 |
|-----------------|--------------|----------|
| 容器編排 (K8s) | GPU node pool、NVIDIA device plugin | 🔴 高 |
| CI/CD pipeline | LLMOps pipeline (模型 eval、部署關卡) | 🔴 高 |
| 可觀測性技術棧 | LLM 專屬指標 (token throughput、TTFT) | 🔴 高 |
| 成本管理 | GPU 成本最佳化、用於訓練的 spot instance | 🔴 高 |
| 機密管理 | 多家 LLM 供應商的 API key 輪替 | 🟡 中 |
| 無 | 用於自架模型服務的 vLLM / TGI | 🟡 中 |
| 無 | 模型版本管理與 registry | 🟡 中 |
| 無 | 量化基礎 (GPTQ、AWQ、GGUF) | 🟡 中 |
| 無 | 基礎 prompt engineering，以理解你正在服務的東西 | 🟢 較低 |

#### 你的 90 天計畫

**第 1 個月: LLM 服務**
- 在本機部署 vLLM 來服務 Llama 3.3 7B 或 Qwen2.5-Coder
- 加入 Prometheus 指標: tokens/sec、延遲 P50/P95/P99、queue depth
- 依據 request queue 設定自動擴縮
- 閱讀本 repo: [04-inference-optimization](04-inference-optimization/)、[11-infrastructure-and-mlops](11-infrastructure-and-mlops/)
- 課程: *Efficiently Serving LLMs* (DeepLearning.AI + Predibase，免費)

**第 2 個月: LLMOps Pipeline**
- 建置 LangSmith 或 Langfuse 以收集 trace
- 打造一道 CI/CD 品質關卡: 在模型部署前先跑 eval 套件
- 實作 prompt 版本控制 (Langfuse prompt registry 或 DSPy)
- 閱讀本 repo: [14-evaluation-and-observability](14-evaluation-and-observability/)

**第 3 個月: 規模與成本**
- 在目標流量下比較自架 vs. API 的成本 (使用 repo 中的定價指南)
- 建立各模型、各團隊、各功能的成本儀表板
- 實作優雅的多供應商故障切換
- 課程: *ML Engineering for Production (MLOps)* (Coursera，DeepLearning.AI)

---

### 7. 📊 資料工程師 → AI 資料 / 特徵工程師

**為什麼資料工程師不可或缺:** 訓練資料是 AI 系統的競爭護城河。資料 pipeline、品質與新鮮度對模型表現的決定性，比架構更大。你的技能能立即派上用場。

#### 目標角色

```
Data Engineer
      │
      ├──► AI Data Engineer             (2–4 months — fastest transition)
      ├──► Embedding Pipeline Engineer  (3–6 months)
      └──► Fine-tuning Data Specialist  (4–8 months)
```

#### 技能缺口分析

| 你已具備 | 待補齊的缺口 | 優先順序 |
|-----------------|--------------|----------|
| ETL pipeline | 用於 RAG 的文件匯入 pipeline | 🔴 高 |
| 資料品質檢查 | eval 資料集品質驗證 | 🔴 高 |
| Schema 設計 | 向量資料庫的 metadata schema | 🔴 高 |
| 串流 pipeline | 即時 embedding 與索引更新 | 🟡 中 |
| 無 | embedding 模型選擇與批次處理 | 🟡 中 |
| 無 | 向量資料庫操作 (upsert、filter、ANN search) | 🟡 中 |
| 無 | 針對不同文件類型的 chunking 策略 | 🟡 中 |
| 無 | 用於 fine-tuning 的標註 pipeline 設計 | 🟢 較低 |
| 無 | RLHF 偏好資料格式 | 🟢 較低 |

#### 你的 90 天計畫

**第 1 個月: RAG 資料 Pipeline**
- 建立一條匯入 pipeline: PDF/HTML/DOCX → 切塊 → embedding → Qdrant
- 加入資料品質關卡: 最小 chunk 大小、去重、語言偵測
- 實作增量同步: 只重新 embedding 有變動的文件
- 閱讀本 repo: [06-retrieval-systems/02-chunking-strategies.md](06-retrieval-systems/02-chunking-strategies.md)、[10-document-processing](10-document-processing/)

**第 2 個月: Eval 資料集工程**
- 使用 dimensional sampling 建立一個測試資料集 (參見 evals 指南)
- 使用 Label Studio 或 Argilla 建置人工標註 pipeline
- 追蹤標註者間一致性; 拒絕低品質標籤
- 閱讀: [AI Evals Comprehensive Study Guide](ai_evals_comprehensive_study_guide.md)，第 12 章 (人工標註)
- 課程: *Finetuning Large Language Models* (DeepLearning.AI，免費)

**第 3 個月: 進階資料工程**
- 建立一條 pipeline，把生產環境 trace 轉成 fine-tuning 範例
- 實作 embedding 漂移偵測: 當文件分佈位移時發出告警
- 在你的領域資料上對 3 個 embedding 模型進行基準測試
- 閱讀本 repo: [03-training-and-adaptation](03-training-and-adaptation/)

---

## 📊 角色比較總覽

```
Role            Months to   Avg Salary    Best Suited For
                First Role   (US, 2026)
────────────────────────────────────────────────────────
Backend         3–6 mo       $170–220K    LLM App / Agentic Engineering
Frontend        3–6 mo       $150–190K    AI Product / UX Engineering
QA              3–6 mo       $140–180K    AI Eval / Quality Engineering
PM              3–6 mo       $160–200K    AI Product Management
DevOps          3–6 mo       $170–220K    MLOps / AI Platform
Data Eng        2–4 mo       $165–210K    RAG Data, Fine-tuning Data
EM              6–12 mo      $200–280K    AI Engineering Manager
```

*薪資為美國市場估算，依據 Levels.fyi 與 LinkedIn 資料，2026 年 5 月。範圍會因公司、地點與經驗層級而有顯著差異。*

---

## 🗺️ 哪些 Repo 章節對應到什麼

當你準備好深入鑽研時，使用這份對照表:

| 主題 | Repo 章節 | 原因 |
|-------|-------------|-----|
| LLM 如何運作 | [01-foundations](01-foundations/) | 一切的基礎 |
| 該用哪個模型 | [02-model-landscape](02-model-landscape/) | 模型選擇是每天都要做的決定 |
| Fine-tuning | [03-training-and-adaptation](03-training-and-adaptation/) | 用於 fine-tuning 資料專家路徑 |
| GPU 服務 / vLLM | [04-inference-optimization](04-inference-optimization/) | MLOps / 平台路徑 |
| Prompt engineering | [05-prompting-and-context](05-prompting-and-context/) | 每個人都需要 |
| RAG pipeline | [06-retrieval-systems](06-retrieval-systems/) | 後端 / 資料工程路徑 |
| Agentic 系統 | [07-agentic-systems](07-agentic-systems/) | 後端 / 資深 AI 工程路徑 |
| Memory 與 state | [08-memory-and-state](08-memory-and-state/) | 所有打造 agent 的工程師 |
| LangGraph、CrewAI、Claude Code | [09-frameworks-and-tools](09-frameworks-and-tools/) | 實務上的工具選擇 |
| 文件解析 | [10-document-processing](10-document-processing/) | 資料工程 / RAG 路徑 |
| GPU 基礎設施、LLMOps | [11-infrastructure-and-mlops](11-infrastructure-and-mlops/) | DevOps / 平台路徑 |
| 多租戶安全 | [12-security-and-access](12-security-and-access/) | 後端 / PM 路徑 |
| Guardrails、red teaming | [13-reliability-and-safety](13-reliability-and-safety/) | QA / Red Team 路徑 |
| RAGAS、LangSmith、evals | [14-evaluation-and-observability](14-evaluation-and-observability/) | QA / PM / 所有角色 |
| 設計模式 | [15-ai-design-patterns](15-ai-design-patterns/) | 資深層級準備 |
| 案例研究 | [16-case-studies](16-case-studies/) | 面試準備、參考設計 |
| Evals 深入探討 | [AI Evals Comprehensive Guide](ai_evals_comprehensive_study_guide.md) | QA / PM 路徑 |
| AI Evals (LangWatch) | [AI Evals LangWatch Guide](ai_evals_complete_guide_langwatch_langfuse.md) | QA / Eval 工程路徑 |
| 面試準備 | [00-interview-prep](00-interview-prep/) | 所有角色 |
| 課程 | [COURSES.md](COURSES.md) | 所有角色 |

---

## 📚 依角色推薦的入門課程

> 完整細節見 [COURSES.md](COURSES.md)

| 你的角色 | 第一門課 | 第二門課 | 第三門課 |
|-----------|-------------|---------------|--------------|
| **後端** | ChatGPT Prompt Engineering for Devs (DL.AI，免費) | Building & Evaluating RAG (DL.AI，免費) | AI Agents in LangGraph (DL.AI，免費) |
| **前端** | ChatGPT Prompt Engineering for Devs (DL.AI，免費) | Building Systems with ChatGPT API (DL.AI，免費) | Evaluating & Debugging GenAI (DL.AI + W&B，免費) |
| **QA** | 本 repo 的 AI Evals Guide (免費) | Quality & Safety for LLM Apps (DL.AI，免費) | Evals for AI – Maven (Hamel + Shreya，付費) |
| **PM** | AI for Everyone (Coursera，免費) | AI Evals Guide 第 3 章 (免費) | Evals for AI – Maven (Hamel + Shreya，付費) |
| **DevOps** | Efficiently Serving LLMs (DL.AI，免費) | Evaluating & Debugging GenAI (DL.AI + W&B，免費) | ML Engineering for Production (Coursera) |
| **資料工程** | Building & Evaluating RAG (DL.AI，免費) | Finetuning LLMs (DL.AI，免費) | 本 repo 的 AI Evals Guide (免費) |
| **EM** | Generative AI with LLMs (Coursera) | AI Agents in LangGraph (DL.AI，免費) | CS294 LLM Agents (Berkeley，免費) |

*DL.AI = DeepLearning.AI*

---

## 應避免的常見錯誤

1. **跳過基本功** —— 在還沒理解 embedding 是什麼之前就一頭栽進 LangChain，會寫出你無法除錯的盲從程式碼 (cargo-cult code)。

2. **先建構、後評估** —— 在沒有衡量品質的辦法之前，什麼都別出貨。在寫下第一個 prompt 之前就先定義你的 eval 標準。

3. **照抄 prompt 卻不理解它們** —— prompt 是工程決策。要理解每個元素為什麼放在那裡。

4. **直到太遲才理會成本** —— 每一次 API 呼叫都有價格。從第一天起就建立成本追蹤。參見 [02-model-landscape/03-pricing-and-costs.md](02-model-landscape/03-pricing-and-costs.md)。

5. **假設模型是瓶頸** —— 在多數生產環境 AI 系統中，瓶頸是檢索品質、prompt 設計或資料品質。模型很少是問題所在。

6. **在生產環境的模型版本字串中使用「latest」** —— 釘住確切的版本。靜默的模型更新會搞壞你的產品。

7. **過度 agent 化** —— 在單一個寫得好的呼叫就能搞定時，卻一開始就上 5 個 agent 的系統。從簡單開始，只在需要時才增加複雜度。

---

## 如何被錄取

**公開地打造作品 (Build in public)。** AI 工程的就業市場獎勵已展示出來的成果:

1. **GitHub 作品集** —— 一個打磨過的端到端專案，勝過 10 個玩具專案
2. **寫一篇部落格文章** —— 描述一個你解決過的真實問題以及你是怎麼解的 (錯誤分析、eval pipeline、RAG 延遲修正)
3. **貢獻開源** —— OpenHands、LlamaIndex、DSPy、RAGAS。即使是文件 PR 也能讓你被注意到。
4. **使用本 repo 的面試準備** —— [00-interview-prep/01-question-bank.md](00-interview-prep/01-question-bank.md) 有 80 道題目並附上強而有力的解答

**在面試中該說什麼:**
- 講出具體的決策:「我選 Qdrant 而非 Pinecone 是因為 X」(而不是「我做了一套 RAG 系統」)
- 引用你遭遇過的失敗模式以及你如何修正它們
- 把至少一個基準爛熟於心 (SWE-bench、RAGAS 分數、你那套服務設定的 TTFT)
- 展現你會思考 eval 與成本，而不只是功能

---

*隸屬於 [AI System Design Guide](README.md) —— 由 [ombharatiya](https://github.com/ombharatiya) 維護*
