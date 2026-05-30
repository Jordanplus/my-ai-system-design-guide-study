# 常見問題：AI 工程、RAG 與 Agent

針對現代 AI 系統設計最常被問到的問題，提供簡短、直接的解答。每則解答都會指向深入探討該主題的章節。

## 目錄

- [一般問題：AI 工程師角色](#general)
- [RAG 與檢索](#rag)
- [Agent 與工具使用](#agents)
- [模型與選型](#models)
- [評估與可觀測性](#evaluation)
- [推論與成本](#inference)
- [記憶與狀態](#memory)
- [安全與防護](#security)

---

## General

### 什麼是 AI 工程師？

AI 工程師是在大型語言模型之上打造生產系統的人。這個角色介於傳統軟體工程與機器學習研究之間：較少訓練模型，更多的是圍繞既有模型進行系統設計。日常工作涵蓋 prompt 與 context 工程、檢索管線、agent 迴圈、評估框架，以及讓這一切持續上線運作的基礎設施。參見 [AI 就業市場趨勢](06-job-market-trends-2026.md)。

### AI 工程師與 ML 工程師有什麼差別？

ML 工程師負責訓練、微調並交付模型。AI 工程師則是把既有模型（通常透過 API）組合成產品。ML 工程師把時間花在資料集與訓練迴圈上；AI 工程師把時間花在 prompt、RAG、agent、eval 與延遲上。在同時做這兩件事的大公司，這條界線會變得模糊。參見 [轉職指南](../TRANSITION_GUIDE.md)。

### 我要如何成為 AI 工程師？

如果你已經會寫生產級程式碼，差距其實很小：了解 LLM 的行為、學會 RAG 與 agent 模式、學會評估，並掌握一套推論堆疊即可。[轉職指南](../TRANSITION_GUIDE.md) 會把你目前的角色（後端、前端、QA、PM、資料、DevOps）對應到合適的 AI 角色，以及需要補足的具體技能。

### 從事 AI 工程該學哪一種程式語言？

Python 是 AI 工作的預設語言。TypeScript 是最常見的第二語言，因為前端與邊緣 agent 堆疊都在這裡。C# 與 Go 則出現在企業基礎設施的職缺中。大多數生產級 AI 程式碼讀起來就像一般應用程式碼：HTTP 用戶端、佇列消費者、資料庫呼叫，再加上對模型供應商的呼叫。

### AI 工程是一個好的職涯選擇嗎？

需求強勁，薪資對標資深軟體工程，在前沿實驗室往往更高。風險在於這個堆疊變動很快：去年還重要的框架，今天可能已被淘汰。能跨版本累積複利的技能是評估、系統設計與紮實的除錯能力。參見 [就業市場趨勢](06-job-market-trends-2026.md)。

---

## RAG

### 什麼是 RAG？

Retrieval-Augmented Generation（檢索增強生成）是一種模式：在查詢時擷取外部 context（文件、資料列、程式碼、圖片），放進 LLM 的 prompt 中，讓模型能夠以這些內容為依據作答，而不是憑訓練資料產生幻覺。對任何需要知道訓練截止日之外資訊的 LLM 來說，這是最常見的生產模式。參見 [RAG 基礎](../06-retrieval-systems/01-rag-fundamentals.md)。

### RAG 是如何運作的？

使用者查詢會被轉換為一個搜尋請求，系統從知識儲存（vector DB、關鍵字索引、圖、或混合）中檢索出最相關的 chunk，對它們重新排序，再把排名最前的結果作為 context 傳給 LLM 進行生成。兩個失敗點分別是檢索（正確的 chunk 沒被取回）與生成（模型忽略或誤用了該 chunk）。大多數 RAG 失敗都是檢索失敗。

### 長 context 視窗是否讓 RAG 走入歷史？

並沒有。即使 Claude Opus 4.7、Claude Sonnet 4.6、GPT-5.5 與 Gemini 3.1 Pro 擁有 1M–2M token 的 context 視窗，RAG 在成本、延遲、新鮮度與語料規模上仍勝出。企業資料集（SharePoint、log 封存、程式碼 monorepo）的規模超過任何 context 視窗。RAG 扮演的是過濾器，從資料中找出那 0.01% 值得放進這個高價值視窗的內容。參見 [RAG vs 長 context](../06-retrieval-systems/14-production-rag-at-scale.md)。

### RAG 與微調有什麼差別？

RAG 在查詢時透過 context 注入知識；微調則把行為烙進權重裡。經驗法則是：**RAG 管事實，微調管形式**。當知識會變動、當你需要引用來源、或當資料必須留在模型之外時，使用 RAG。當你想要一致的語氣、嚴格的輸出格式，或在重複任務上降低延遲時，使用微調。參見 [微調策略](../03-training-and-adaptation/02-fine-tuning-strategies.md)。

### 哪一個 vector database 最好？

沒有單一最佳解。Pinecone 在託管規模與 SLA 上勝出。Qdrant 在開源效能上領先（在 1000 萬向量下大約 12ms 的 p99）。Weaviate 擁有最強的原生混合搜尋（在單一查詢中結合 BM25 + dense + metadata）。一旦你需要超過 5000 萬向量的分散式規模，Milvus 就是選擇。如果你已經在用 Postgres 且索引在 1000 萬向量以下，pgvector 是正確答案。參見 [向量資料庫](../06-retrieval-systems/04-vector-databases.md)。

### 什麼是 contextual retrieval？

Contextual retrieval 是 Anthropic 的一項技術，在嵌入與建立索引之前，於每個 chunk 前面加上一段由 LLM 產生的簡短 context 摘要，讓該 chunk 帶著它在文件中的定位。Anthropic 回報，搭配混合搜尋可使檢索失敗減少 49%，再結合 reranker 則可達 67%。參見 [Contextual Retrieval](../06-retrieval-systems/10-contextual-retrieval.md)。

### 什麼是混合搜尋（hybrid search）？

混合搜尋結合稀疏關鍵字檢索（通常是 BM25）與密集向量檢索，並將兩份排序清單融合為一份，通常使用 Reciprocal Rank Fusion。稀疏這一支會抓到精確的 token（產品代碼、函式名稱、罕見名詞）；密集這一支則抓到同義詞與意圖。每一個現代 vector DB 都內建了開箱即用的混合搜尋。參見 [混合搜尋](../06-retrieval-systems/05-hybrid-search.md)。

### 什麼是 GraphRAG？

GraphRAG 會從語料中抽取實體與關係，建立知識圖譜，並以圖的遍歷取代（或搭配）向量相似度來進行查詢。對於**彙整型問題**（「彙整這 50 份合約中的所有法律風險」），向量 RAG 會回傳相關但彼此不連貫的 chunk，這時 GraphRAG 是正確的模式。Microsoft 的 LazyGraphRAG 把昂貴的社群摘要延後到查詢時才做，降低了攝取成本。參見 [GraphRAG](../06-retrieval-systems/07-graph-rag.md)。

### RAG 的最佳 chunk 大小是多少？

沒有通用答案。對散文而言，300–500 token 的 chunk 搭配 50 token 重疊是合理的預設值。程式碼與結構化資料需要較大的 chunk（1000–2000 token）。更大的收益來自**結構感知切塊**（在標題、段落、程式碼區塊處切分）、**contextual chunking**（在前面加上摘要），以及**階層式切塊**（索引小 chunk，回傳其父層 context）。參見 [切塊策略](../06-retrieval-systems/02-chunking-strategies.md)。

---

## Agents

### 什麼是 AI agent？

AI agent 是這樣一個系統：由 LLM 決定下一步要做什麼、執行一個工具、觀察結果，然後再次決定，全部在一個迴圈中進行。最簡單的 agent 是 ReAct 模式：Thought → Action → Observation → 重複。現代 agent（Claude Opus 4.7、GPT-5.5 reasoning、DeepSeek-R2）把推理步驟直接烙進模型本身。參見 [Agent 基礎](../07-agentic-systems/01-agent-fundamentals.md)。

### Agent 與 chatbot 有什麼差別？

chatbot 對訊息做出回應。agent 則在世界中**採取行動**：執行程式碼、呼叫 API、讀檔案、發訊息、預約行程。這個區別很重要，因為行動很難回滾，所以 agent 需要非常不同的護欄、沙箱與人機協作（human-in-the-loop）模式。參見 [Agent 安全](../07-agentic-systems/09-agentic-security-and-sandboxing.md)。

### 什麼是 MCP（Model Context Protocol）？

MCP 是一個開放協定，讓 LLM 應用透過標準介面連接到工具與資料來源。Anthropic 於 2024 年 11 月推出，治理權於 2025 年 12 月移交給 Linux Foundation 的 Agentic AI Foundation。採用情況已全面普及：Anthropic、OpenAI、Google、Microsoft、AWS 都支援它。截至 2026 年 5 月，公開的 MCP server 已超過 2,300 個。參見 [工具使用與 MCP](../07-agentic-systems/03-tool-use-and-mcp.md)。

### 哪一個 agent 框架最好？

三大框架涵蓋了大多數生產需求。**LangGraph**（基於圖，在 2026 年初的 star 數超越 CrewAI）是有狀態多 agent 控制流程並支援 checkpoint 的預設選擇。**CrewAI**（現為 v1.13，在 60% 以上的 Fortune 500 企業中使用）是基於角色的業務自動化首選。**Microsoft Agent Framework**（2026 年 2 月 RC 1.0，2026 Q2 GA）是 AutoGen 與 Semantic Kernel 的整合後繼者，面向企業級 .NET 與 Python。參見 [框架選型指南](../09-frameworks-and-tools/08-framework-selection-guide.md)。

### 什麼是 agentic RAG？

Agentic RAG 把線性的「先檢索再生成」管線換成一個迴圈，由 agent 決定要檢索什麼、評估結果是否夠好、若不夠好就重新查詢。相關模式包括 Self-RAG（模型發出反思 token）、Corrective RAG（獨立的評分器）、Adaptive RAG（由分類器挑選深度）以及多跳分解。每次查詢以三到四次迭代計算，需預留 8–12 秒的預算。參見 [Agentic RAG](../06-retrieval-systems/08-agentic-rag.md)。

### computer-use agent 是如何運作的？

computer-use agent 會對桌面或瀏覽器截圖、決定一個滑鼠與鍵盤動作、執行它，然後再截一張圖。三個生產選項分別是 Claude Computer Use（透過截圖跨 OS 移植）、Google Gemini Computer Use（透過 DOM 感知針對瀏覽器最佳化），以及 OpenAI Operator（聚焦於 web 任務）。Claude Sonnet 4.6 在 OSWorld-Verified 上達到 72.5%，相較於 2024 年 10 月推出時的 14.9% 大幅提升。參見 [computer-use agent](../17-tool-use-and-computer-agents/04-computer-use-agents.md)。

---

## Models

### 現在最好的 LLM 是哪一個？

在 2026 年 5 月並沒有單一最佳模型。排行榜已依任務分裂。**Claude Opus 4.7** 在複雜程式設計的 SWE-bench Pro 上以 64.3% 領先。**GPT-5.5** 在 agentic 終端機工作的 Terminal-Bench 2.0 上以 82.7% 領先。**Gemini 3.1 Pro** 在科學推理的 GPQA Diamond 上以 94.3% 領先。**Claude Sonnet 4.6** 以 40% 的價格交付約 90% 的 Opus 4.7 品質。參見 [模型分類](../02-model-landscape/01-model-taxonomy.md)。

### Claude / GPT / Gemini / DeepSeek 的價格是多少？

定價每月都在變。截至 2026 年 5 月，前沿等級的封閉模型每百萬 input token 約為 $3–15，每百萬 output token 約為 $15–75，而對於重複的前綴，快取可將此降低 75–90%。中階模型（Claude Sonnet 4.6、GPT-5.5-mini、Gemini 3.1 Flash）每百萬約為 $0.30–3 / $1–15。**DeepSeek 重設了價格底線**：V4 Pro 為每 1M $0.435 / $0.87（75% 折扣於 2026 年 5 月 22 日永久化），而 V4 Flash 為每 1M $0.14 / $0.28，並具備 1M context 視窗，在許多任務上比封閉前沿便宜約 10 倍。請務必對照供應商的定價頁面確認最新費率。參見 [定價與成本](../02-model-landscape/03-pricing-and-costs.md)。

### Claude Opus 與 Claude Sonnet 有什麼差別？

Opus 是 Anthropic 的前沿等級：最聰明、最慢、最貴。Sonnet 是生產主力：以 40% 的價格達到約 90% 的 Opus 品質。Haiku 是快速等級：便宜、低延遲，適合做路由與分類。正確的模式是把簡單查詢路由到 Haiku、中等查詢路由到 Sonnet，只有困難的才送到 Opus。參見 [模型選型](../02-model-landscape/04-model-selection-guide.md)。

### 我應該使用開源模型嗎？

在高流量下的每次查詢成本、資料落地（data residency）或微調需求方面，答案是肯定的。開放權重的品質已縮小到與封閉前沿相差 5–15 分以內（Qwen3-Embedding-8B 在 MTEB Multilingual 上領先，Llama 4 Maverick 與 DeepSeek V4 Pro 都是具競爭力的前沿選擇）。代價在於營運面：你得自行承擔推論堆疊、GPU 帳單與安全修補。參見 [模型版圖](../02-model-landscape/01-model-taxonomy.md)。

### 什麼是 prompt caching？

prompt caching 會在推論伺服器上讓固定 prompt 前綴的 KV 快取保持熱狀態，使後續呼叫只需為新的 token 付費。所有主要供應商都支援它。快取讀取比全新 token 便宜 75–90%。但有個前提：快取寫入通常多花 25%，所以唯有當你在 TTL（通常為 5 分鐘）內至少重複使用同一前綴 3–5 次時，快取才划算。參見 [KV 快取與 context 快取](../04-inference-optimization/02-kv-cache-and-context-caching.md)。

---

## Evaluation

### 要如何評估一個 LLM？

LLM 評估是分層的：用於快速迭代的**無參考指標**（透過 LLM-as-judge 的忠實度、相關性、連貫性）、用於回歸的**黃金測試集**，以及**任務特定指標**（QA 用 exact match、翻譯用 BLEU、程式碼用 pass@k）。專門針對 RAG 時，使用 RAG Triad：context 相關性、忠實度、答案相關性。參見 [LLM 評估](../14-evaluation-and-observability/01-llm-evaluation.md)。

### 什麼是 LLM-as-judge？

LLM-as-judge 用一個 LLM 依據評分標準（正確性、有用性、安全性）為另一個 LLM 的輸出評分。它能擴展到人工評估無法企及的規模，但有已知的偏差：位置偏差、冗長偏差、自我偏好偏差。標準做法是使用更強的模型作為評審（Claude Opus 4.7 或 GPT-5.5 reasoning）、隨機化位置，並對照一小份人工標註樣本進行驗證。

### 哪一個 LLM 可觀測性工具最好？

領先的平台有 **Langfuse**（最佳的自架開源方案，2026 年 1 月被 ClickHouse 收購）、**Braintrust**（最適合具備品質閘門的 eval 驅動 CI/CD）、**LangWatch**（最適合 agent 模擬）、**LangSmith**（LangChain 原生），以及 **Arize Phoenix**（OTel 原生）。請依部署模式（SaaS vs 自架）、是否需要 CI/CD 閘控，以及你對某特定框架的依賴程度來挑選。參見 [可觀測性](../14-evaluation-and-observability/02-observability.md)。

### 什麼是 RAGAS？

RAGAS（Retrieval Augmented Generation Assessment）是一個用於 RAG 評估的 Python 函式庫。它提供無參考指標（忠實度、答案相關性、context 相關性）與基於參考的指標（context recall、context precision），皆以 LLM-as-judge 計算。它是任何 RAG eval 管線事實上的起點。參見 [RAG 評估](../06-retrieval-systems/13-rag-evaluation-patterns.md)。

---

## Inference

### 什麼是 vLLM？

vLLM 是一個開源 LLM 推論引擎，首創了 PagedAttention（以虛擬記憶體式的方式配置 KV 快取）。當工作負載是「Llama、Mistral、Qwen 或 DeepSeek 在連續批次處理下」時，它是預設的開源推論引擎。在主要引擎中，它最容易營運、修補也最完善。多模態部署因 2026 年 2 月的一個 CVE，必須執行 v0.18.2+。參見 [服務基礎設施](../04-inference-optimization/06-serving-infrastructure.md)。

### vLLM 與 SGLang 有什麼差別？

兩者都是開源推論引擎。vLLM 的模型覆蓋更廣、營運更成熟。SGLang 因採用非同步約束解碼，在結構化輸出與 function-calling 工作負載上有約 29% 更高的吞吐量，並透過 RadixAttention 具備同類最佳的前綴快取重用。重要提醒：截至 2026 年 5 月，SGLang 的多模態路徑存在未修補的 CVE，因此多模態流量應改在 vLLM v0.18.2+ 上執行。

### 什麼是 TensorRT-LLM？

NVIDIA 的推論引擎。在 H100/H200/B200 上提供比 vLLM 與 TGI 高 2–4 倍的吞吐量，但代價是 1–2 週的設定時間，以及對 NVIDIA 的硬性鎖定。當你已承諾投入 NVIDIA 算力，且吞吐量的差距足以支付這份營運稅時，它是正確的選擇。

### 要如何最佳化 LLM 推論成本？

五個高槓桿的做法：**模型階梯（model cascading）**（把簡單查詢路由到小模型、困難的送到前沿）、**prompt caching**（重複前綴省 75–90%）、**語意快取（semantic caching）**（對相似查詢完全跳過 LLM 呼叫）、**量化**（FP8 或 4-bit 權重，在一張 GPU 上塞進更多）、以及**連續批次處理**（vLLM/SGLang 在迭代層級進行批次）。它們合起來常能在不損失品質的情況下把推論成本砍掉 10 倍。參見 [成本最佳化](../04-inference-optimization/07-cost-optimization-playbook.md)。

### 什麼是 speculative decoding？

speculative decoding 讓 LLM 在一次前向傳遞中產生多個 token，做法是由一個較便宜的「草稿」模型（或主模型上的額外 head，例如 Medusa）預測接下來的數個 token，再於目標模型上以單次平行傳遞一次驗證它們全部。其收益是 wall-clock 生成速度快 2–3 倍，且零品質損失。已內建於 vLLM 與 TensorRT-LLM。參見 [speculative decoding](../04-inference-optimization/03-speculative-decoding.md)。

---

## Memory

### 哪一個 AI agent 記憶框架最好？

截至 2026 年 5 月，四個成熟的選項是 **Mem0**（最廣泛的獨立記憶層，在 LoCoMo 上得 92.5、在 LongMemEval 上得 94.4）、**Zep**（具時間感知、原生對話摘要的生產管線）、**Letta**（為長時間運行 agent 提供 OS 式分頁、記憶無上限），以及 **Cognee**（以知識圖譜為先，適合 RAG 密集的工作流程）。依使用情境挑選：chatbot 個人化 → Mem0；大規模生產 agent → Zep；長時程任務 agent → Letta；以 KG 為依據的 RAG → Cognee。參見 [Agentic 記憶](../08-memory-and-state/04-agentic-memory-mem0.md)。

### Agent 的短期記憶與長期記憶有什麼差別？

短期記憶存在於 LLM 的 context 視窗中（當前回合、工具輸出、暫存區）。長期記憶則跨工作階段持久化於 vector DB、圖或關聯式儲存中。記憶架構又進一步細分為：**情節式（episodic）**（過往的軌跡）、**語意式（semantic）**（從使用者／世界抽取出的事實）、**程序式（procedural）**（習得的技能、playbook）。為某個事實挑選正確的層級很重要：一個被提升到長期記憶的工作階段偏好，會洩漏到其他工作階段。參見 [記憶架構](../08-memory-and-state/01-memory-architectures.md)。

### 知識圖譜如何幫助 AI agent？

知識圖譜會明確地儲存實體與關係（User → OWNER_OF → Project_A）。它讓 agent 能對結構化關係進行**確定性**檢索，這是向量搜尋做不到的。最強的模式是混合：向量搜尋以相似度找到入口節點，圖遍歷再展開相關 context。可用於合規、多跳推理，以及任何把關係視為一等公民的領域（法律、生醫、金融）。參見 [長期記憶](../08-memory-and-state/03-long-term-memory.md)。

---

## Security

### 什麼是 prompt injection？

prompt injection 是 LLM 時代的 SQL injection：使用者輸入或被檢索到的文件中的惡意內容會覆寫系統指令，使模型去做它不該做的事。**直接注入（direct injection）**位於使用者 prompt 中。**間接注入（indirect injection）**則藏在模型所讀取的文件裡（一個網頁、一封 email、一份 PDF）。OWASP LLM Top 10 將它列為第一名的 LLM 風險。參見 [prompt injection 防禦](../05-prompting-and-context/08-prompt-injection-defense.md)。

### 要如何防範 prompt injection？

沒有萬靈丹：prompt injection 無法像 SQL 那樣被完全「跳脫（escape）」。生產級的防禦堆疊會結合：**輸入隔離**（用 XML 標籤標記不可信內容）、**雙 LLM 模式**（在主模型看到輸入之前，由小型守衛模型先分類意圖）、**金絲雀 token（canary token）**（偵測模型是否洩漏了系統 prompt）、**最小權限工具範圍**，以及對破壞性工具呼叫的**人機協作**。參見 [Agent 安全](../07-agentic-systems/09-agentic-security-and-sandboxing.md)。

### 什麼是 OWASP LLM Top 10？

OWASP Top 10 for LLM Applications（v2.0，2025 年發布）是 LLM 安全風險的權威清單。前幾項包括：prompt injection、不安全的輸出處理、訓練資料投毒、模型阻斷服務、供應鏈漏洞、敏感資訊外洩、不安全的外掛設計、過度授權（excessive agency）、過度依賴，以及模型竊取。2026 年針對 agentic 應用的更新將目標劫持（goal hijacking）、身分濫用與級聯故障新增為頂級風險。參見 [LLM 安全](../12-security-and-access/01-llm-security.md)。

### 什麼是 AI agent 中的沙箱（sandboxing）？

沙箱會把 agent 產生並執行的程式碼與主機系統隔離。標準模式使用短生命週期的 micro-VM（E2B、Docker、Firecracker），它們在 10ms 內啟動、執行程式碼，然後被銷毀。沒有沙箱時，一個被 prompt 注入的 agent 可能會 `rm -rf /` 或外洩機密。有了沙箱，最壞情況也只是一個被銷毀的拋棄式容器。

---

## 延伸閱讀

- [題庫（110 道資深面試題）](01-question-bank.md)
- [答題框架](02-answer-frameworks.md)
- [常見陷阱](03-common-pitfalls.md)
- [白板練習](04-whiteboard-exercises.md)
- [AI 就業市場趨勢](06-job-market-trends-2026.md)

---

*有應該收錄在此的問題嗎？歡迎在 repo 上開 issue 或 PR。*
