# AI 就業市場趨勢 - 2026 年 5 月

> **最後查證：2026 年 5 月 17 日。** 本章節提煉了 AI 招聘領域當下實際正在發生的事——企業張貼的職稱、他們篩選的技能、薪酬範圍，以及你會遇到的面試形式。資料來源為 2026 年 4 月至 5 月間 100 多份公開職缺、招聘報告與招募人員訊號。

本章節適合規劃下一步職涯的工程師、建立評核標準的招聘主管，以及做組織設計決策的工程領導者。它與 [TRANSITION_GUIDE.md](../TRANSITION_GUIDE.md)（如何轉職到 AI 領域）以及[題庫](01-question-bank.md)（該學什麼）相輔相成。

---

## 目錄

- [三大頭條轉變](#the-three-headline-shifts)
- [2026 年的職位分類](#role-taxonomy-in-2026)
- [依職涯層級劃分的技能](#skills-by-career-level)
- [職缺實際要求什麼](#what-job-listings-actually-require)
- [薪酬現實](#compensation-reality)
- [地理與產業分布](#geographic--industry-distribution)
- [面試流程模式](#interview-process-patterns)
- [值得關注的新興職位](#emerging-roles-to-watch)
- [策略性要點](#strategic-takeaways)
- [參考資料](#references)

---

## 三大頭條轉變

如果你什麼都不讀，至少把這三件事內化於心。

### 1. 市場矛盾地同時火熱與冰冷。

2026 年第一季有約 52,050 個科技職位裁員（Oracle 30K、Amazon、Meta、Dell），是 2023 年以來最高的第一季裁員數（[Kore1](https://www.kore1.com/tech-layoffs-2026/)；[Tom's Hardware](https://www.tomshardware.com/tech-industry/tech-industry-lays-off-nearly-80-000-employees-in-the-first-quarter-of-2026-almost-50-percent-of-affected-positions-cut-due-to-ai)）。與此同時，AI 職位季增 +8.9%、年增 +4.8%，有約 275,000 個 AI 職位待填補（[Allwork.space](https://allwork.space/2026/05/ai-hiring-is-rising-even-as-tech-layoffs-surge-140/)）。初階/入門工程師受衝擊最大——例行性程式碼生成、QA 測試、基礎前端工作被不成比例地裁撤。資深 + 專才型 AI 職位則維持韌性。

**意涵：** 在 2026 年，「科技招聘」與「AI 招聘」並非同一個故事。如果你的職涯是通才型的中階 SWE 工作，你正感受到冰冷的市場。如果你是資深層級的 AI 專才，你正處於賣方市場。

### 2. 職稱正在塌縮；工作正在碎片化。

多數公司現在把「AI Engineer」當作總稱來張貼職缺，但在這個職位內部，你會很快專精到 RAG、agents、evals、fine-tuning 或平台工作。[「未來 18 個月內，多數 AI 職稱將塌縮成『AI Engineer』；威望性標籤只會在前沿實驗室存活」](https://www.ivanturkovic.com/2026/04/24/ai-job-titles-2026-naming-chaos/)。獨立的「Prompt Engineer」職稱已實質上從各大求職網站消失——技能存活了下來，但職稱沒有（[PE Collective](https://pecollective.com/blog/is-prompt-engineering-a-real-career/)；[Medium - Prompt Engineering Is Dead 2026](https://medium.com/write-a-catalyst/prompt-engineering-is-dead-2026-ai-systems-engineering-7acdbbcb2160)）。

**意涵：** 如果你還在招聘「Prompt Engineer」，你已落後 18 個月。定義出實際的問題（eval 的嚴謹度？agent 除錯？面向客戶的調校？），然後針對那個具體職位去招人。

### 3. Forward Deployed Engineer 是 2026 年的爆紅職位。

FDE 在 2025 年中還不是前沿實驗室中一個獨立的類別。到了 2026 年 5 月，OpenAI、Anthropic 與 Google 全都在招聘數百名。Google/Box 的執行長公開稱它為「科技業最搶手的工作」（[Fast Company](https://www.fastcompany.com/91541878/google-box-ceos-say-this-is-the-most-in-demand-job-in-tech)；[Hashnode FDE 指南](https://hashnode.com/blog/a-complete-2026-guide-to-the-forward-deployed-engineer)）。中至資深層級的 TC 穩定在 $350-550K。

**意涵：** 前沿 AI 的買家（Fortune 500、政府、生技）將駐點的工程師現場存在感當作合約交付項目來要求。FDE 之所以存在，是因為買家重視它——而不是因為它是交付軟體最有效率的方式。

---

## 2026 年的職位分類

### 既有職稱（仍在強力招聘）

| 職稱 | 描述 | 在哪裡張貼 |
|-------|-------------|-------------------|
| **AI Engineer** | 事實上的通用型 AI 職稱。其他職稱正在塌縮併入它。 | 通用——多數職缺 |
| **LLM Engineer** | 聚焦於 transformer fine-tuning、RAG、agents。與 ML Engineer 有所區別。 | 中大型公司；[iSmart LLM JD 2026](https://www.ismartrecruit.com/job-descriptions/llm-engineer) |
| **ML Engineer / ML+AI Software Engineer** | 經典的訓練與部署職位。 | [levels.fyi ML/AI focus](https://www.levels.fyi/t/software-engineer/focus/ml-ai) |
| **Applied AI Engineer** | 前沿實驗室中嵌入客戶端的變體。 | [Anthropic Applied AI](https://job-boards.greenhouse.io/anthropic/jobs/5116274008) |
| **Member of Technical Staff (MTS)** | 刻意模糊的職稱，使研究與工程之間界線模糊。 | OpenAI、Anthropic、Thinking Machines、Mistral（[Scout AI on MTS](https://scoutnow.ai/blog/rebirth-member-of-technical-staff)） |
| **AI Research Engineer / Research Scientist** | 僅限前沿實驗室；偏好 PhD。 | [Sundeep Teki - AI Research Eng 2026](https://www.sundeepteki.org/advice/the-ultimate-ai-research-engineer-interview-guide-cracking-openai-anthropic-google-deepmind-top-ai-labs) |
| **AI Solutions Architect** | 在企業端比重很高。 | EY、Caterpillar、Deloitte（[EY listing](https://careers.ey.com/ey/job/Amsterdam-AI-Solution-Architect-1083-HP/1258705801/)） |
| **AI Platform Engineer** | 擁有內部 LLM-ops 平台。 | [Augment Code spec 2026](https://www.augmentcode.com/guides/ai-platform-engineering-leader-job-spec) |
| **AI Engineering Manager** | 薪酬最高的單一職位；中位數 $293.5K（[AI Pulse benchmarks](https://theaimarketpulse.com/salaries/)）。 | 在規模擴張型公司以上普遍存在 |
| **AI Product Manager** | 幾乎每一家 B2B SaaS 都需要。 | 通用（[Aakash Gupta](https://www.aakashg.com/product-manager-requirements/)） |
| **AI Technical Program Manager (TPM)** | 專精方向：「Responsible AI TPM」、「AI Infrastructure TPM」、「GenAI Customer Performance TPM」 | Microsoft、AMD、Together AI |

### 自 2025 年以來的新職稱

| 職稱 | 為何出現 | 在哪裡張貼 |
|-------|----------------|-------------------|
| **Forward Deployed Engineer (FDE)** | 前沿 AI 買家將駐點工程列為交付項目來要求。 | OpenAI、Anthropic、Google（[Anthropic FDE](https://job-boards.greenhouse.io/anthropic/jobs/4985877008)） |
| **AI Evaluation Engineer** | Eval 工作成熟為一門獨立學科。 | OpenAI（[Applied Evals](https://openai.com/careers/software-engineer-applied-evals-san-francisco/)、[Frontier Evals](https://openai.com/careers/research-engineer-frontier-evals-and-environments-san-francisco/)）、Apple、Scale AI、Distyl、Apex |
| **Agentic Systems Engineer / AI Agent Engineer** | Agents 成為它們自己的工程面向。 | Teradata、GE Vernova、Deloitte、OpenAI（[Agent Infrastructure SWE](https://openai.com/careers/software-engineer-agent-infrastructure-san-francisco/)） |
| **AI Reliability Engineer** | 生產環境的 AI 需要類似 SRE 的紀律；與傳統 SRE 有所區別。 | Anthropic（[Staff/Sr AI Reliability](https://www.anthropic.com/jobs)）；AI SRE 作為一個類別正由 Resolve.ai、Rootly 定義中。 |
| **AI Security Engineer / LLM Red Team Specialist** | prompt-injection 防禦與 jailbreak 研究成為一門學科。 | Life360（[Principal AI Security Engineer](https://www.remoterocketship.com/us/company/life360/jobs/principal-ai-security-engineer-ai-native-platform-united-states-remote/)）；[Practical DevSecOps](https://www.practical-devsecops.com/emerging-ai-security-roles/) 列舉了 10 個新興 AI 安全職位。 |
| **MCP Engineer / MCP Software Engineer** | MCP 的採用使伺服器開發成為它自己的專業。 | Descope（[MCP SWE](https://careers.descope.com/p/fe57f6224769-mcp-model-context-protocol-software-engineer)） |
| **AI Operator / Computer-Use Specialist** | 與 OpenAI Operator 及 Claude Cowork 緊密相關。 | $75-120K 專才層級（[Coasty](https://coasty.ai/blog/best-computer-use-platform-2026-20260402)） |

### 正在消失或整併的職位

- **Prompt Engineer（獨立職稱）：** 職稱正在消亡。技能仍是基本門檻。
- **Distillation Engineer：** 以一項*職責*的形式出現在 fine-tuning/inference engineer 的職缺裡，而非自己被廣泛張貼的需求。

---

## 依職涯層級劃分的技能

### L4-L5（中階 IC，3-5 年資）

- Python 生產環境熟練度——**71% 的 AI 職缺**（[Second Talent](https://www.secondtalent.com/resources/most-in-demand-ai-engineering-skills-and-salary-ranges/)）
- 至少實作過一個主要 LLM 供應商 SDK（OpenAI、Anthropic、Bedrock）以及一個編排框架——最常見的是 LangChain/LangGraph（佔 agentic AI 職缺的 34.3%；[Agentic Engineering Jobs](https://agentic-engineering-jobs.com/langchain-job-market-2026)）
- Vector DB 基礎：Pinecone、Weaviate、pgvector——特定工具的經驗幾週內就能學會；概念性理解最重要
- RAG：chunking、hybrid search、BM25、reranking、retrieval evals
- 容器化：Docker（15.4%）、Kubernetes（17.6%）
- 雲端：AWS（32.9%）、Azure（26%）

### L6-L7（資深 / Staff）

- 端到端交付過生產環境的 LLM 系統——「交付過真實系統的業界經驗，是比學術資歷更好的訊號」
- 跨 vector indexes、GPU memory、agent state 的多租戶隔離
- Eval 框架（LangSmith / Langfuse / Braintrust）；eval 把關的 CI/CD
- Fine-tuning / LoRA / QLoRA / RLHF
- 成本最佳化——token 預算、model routing、caching
- 「把 LLMs、vector stores 與 RAG 當作標準系統設計的一部分來推理，而非當成一門小眾專業」（[Design Gurus](https://designgurus.substack.com/p/system-design-interviews-changed)）

### L8+（Principal / 領導型 IC）

- 擁有 agent 編排層、model-routing、服務所有工程團隊的 LLMOps 平台
- 對非確定性系統的執行期治理
- 為 SOC 2 / HIPAA / EU AI Act 合規進行架構設計——在 AI Act 第 27 條下觸發 DPIA + FRIA
- 「定義技術願景並擴展工程團隊，比單純的寫程式本領更重要」

### 管理職軌（EM / Director）

- AI Engineering Manager 中位數 $293.5K——薪酬最高的單一職位（[AI Pulse](https://theaimarketpulse.com/salaries/)）
- 招聘評核標準現在會加重評估：「你能不能把這個人放進一個有 PM 和初階工程師的房間裡，讓他主導技術方向而不把事情搞砸」——受訪的 7 位招聘主管中有 5 位這麼認為（[Design Gurus](https://designgurus.substack.com/p/system-design-interviews-changed)）
- 在前沿實驗室，使命契合度與安全判斷力被高度加權（[Anthropic EM guide](https://www.gethireready.com/interview-guides/engineering-manager-anthropic)）

### PM 職軌（AI PM / AI TPM）

- 「AI 是新的基準線，而非加分技能」
- 4 年以上 PM 經驗，理想上是 B2B SaaS 或 AI 驅動的產品
- 關鍵：「不到 4 分之 1 的資深 AI PM 候選人達到技術流暢度 + 產品嚴謹度的門檻」（[Aakash Gupta](https://www.aakashg.com/product-manager-requirements/)）
- 「能展示出可運作原型的候選人，勝過只能口頭描述的人」

---

## 職缺實際要求什麼

### 必備（在 100 多份職缺中被明確列為必需）

- Python 生產環境程式碼，3 年以上
- LLM API 整合（OpenAI / Anthropic / Bedrock）
- RAG pipeline 經驗，包含 vector DB、chunking、retrieval evals
- 生產級別的可觀測性與 eval pipelines
- 雲端 + Kubernetes + IaC
- Agent 除錯 / 多步驟工作流程追蹤
- 安全敏感職位的 prompt injection / jailbreak 防禦

### 加分項（被明確列為「plus」或「bonus」）

- 發表論文或 OSS 貢獻；對應用型職位而言，3-5 個專案的可運作作品集勝過一篇論文
- CUDA / GPU 層級最佳化——在 NVIDIA/前沿實驗室是必備，在其他地方是加分
- Distillation / 模型壓縮
- 分散式 inference 經驗
- 用於舊有企業整合的 Java/C++
- 超越 RLHF 的強化學習

### 職缺中的頂尖技術棧（2026 年 5 月）

依出現頻率排名：

1. **Python**——71% 的所有 AI 職缺
2. **PyTorch / JAX**——在前沿實驗室普遍存在
3. **LangChain / LangGraph**——佔 agentic 職缺的 34.3%，第 1 名框架
4. **LlamaIndex**——在 38% 的 LangChain 職缺中共同出現
5. **AWS（32.9%）/ Azure（26%）/ GCP / Vertex / Bedrock**
6. **Kubernetes（17.6%）+ Docker（15.4%）**
7. **Vector DBs：** Pinecone、Weaviate、Qdrant、Chroma、pgvector
8. **MCP (Model Context Protocol)**——在尖端團隊中現已成為[「一項基本要求」](https://medium.com/@adnanmasood/the-rise-of-model-context-protocol-mcp-skills-5f0d6a1c3579)
9. **可觀測性：** LangSmith、Langfuse、Braintrust、Arize
10. **Inference 引擎：** vLLM、SGLang、TensorRT-LLM
11. **Terraform / Helm / Ray / Kubeflow / MLflow / Feast**——內部平台技術棧
12. **供應商 SDKs：** OpenAI Agents SDK、Claude SDK、Vercel AI SDK、Mastra、Pydantic AI

### 依公司層級劃分

- **前沿實驗室**（Anthropic、OpenAI、xAI）：PyTorch/JAX、vLLM/自訂 inference、內部 evals、MCP servers、CUDA/GPU 層級最佳化
- **規模擴張型公司**（Cursor、Harvey、Sierra、Decagon、Glean、Perplexity）：TypeScript + Python 混用、LangGraph / OpenAI Agents SDK、Pinecone/pgvector、LangSmith/Braintrust evals
- **企業**（Deloitte、EY、Caterpillar、Citi）：以 Azure 為重、Bedrock、LangChain、聚焦治理/MLOps、地端能力

### 非技術性要求

- **溝通 / 跨職能協作**——在資深以上是基本門檻
- **面向客戶的能力**——對 FDE 職位是承重要素；Anthropic 要求 3 年以上「技術性、面向客戶的職位」經驗
- **OSS 貢獻**——Anthropic 明確表示：[「如果你做過有趣的獨立研究、寫過具洞見的部落格文章，或對開源軟體做出實質貢獻，請把那些放在你履歷的最頂端」](https://www.sundeepteki.org/advice/how-to-get-hired-at-openai-anthropic-and-google-deepmind-in-2026)
- **發表論文**——AI Research Engineer 必需；Anthropic 技術人員中僅約 50% 持有 PhD
- **使命契合度**——Anthropic 透過行為與價值觀關卡明確篩選此項
- **法規經驗：** 企業端的 SOC 2 / HIPAA / FedRAMP；歐盟營運的 EU AI Act 熟悉度（FRIA/DPIA）
- **安全許可（security clearance）**——Lockheed 及聯邦相關職位必需

---

## 薪酬現實

> 僅限公開來源範圍。請以 [levels.fyi](https://www.levels.fyi/) 查證最新資料。除另有註明，所有數字皆為美元。

| 層級 / 公司 | 層級 | 總薪酬 |
|---|---|---|
| **Anthropic (SF)** | Senior SWE | $316K 底薪 / $563K TC |
| **Anthropic (SF)** | Lead SWE | $332K 底薪 / $785K TC |
| **OpenAI (SF)** | 全部 SWE | $251K – $1.28M+ TC |
| **OpenAI (SF)** | L5 SWE | $336K 底薪 + $774K 股票 = $1.15M TC |
| **OpenAI MTS / Research Scientist** | - | $245K – $685K 底薪 |
| **Cursor (Anysphere)** | SWE | $850K – $1.28M TC |
| **Sierra** | SWE | $200K – $460K TC；中位數 $450K |
| **Thinking Machines Lab** | 全部工程 | $450K – $500K 底薪（第一季 H-1B 申報） |
| Google AI Engineer | L3-L6 | $183K – $583K TC；中位數 $280K |
| Microsoft AI Engineer | 全部 | $238K – $355K+ TC；中位數 $282K |
| **美國全國 AI Engineer** | 入門（0-2 年） | $90-135K 底薪 / $110-160K TC |
| **美國全國 AI Engineer** | 中階（3-5 年） | $140-210K 底薪 / $170-260K TC |
| **美國全國 AI Engineer** | 資深（6-9 年） | $180-280K 底薪 / $220-350K+ TC |
| **美國全國 AI Engineer** | Staff/Principal（10 年以上） | $250-400K+ 底薪 / $350-600K+ TC |
| RAG Engineer Senior | - | $195-290K 底薪；在前沿實驗室 $400K+ TC |
| LLM Fine-Tuning Specialist | - | $195K-$350K |
| AI Security Engineer | - | $152-210K |
| LLM Red Team Specialist | - | $160-230K |
| **AI Engineering Manager** | - | 中位數 $293.5K（薪酬最高的單一職位） |
| AI Product Manager | - | $141K – $250K（中位數 $159K） |
| **Agentic AI Architect** | - | $260K – $420K 底薪 |
| London（量化基金 / FAANG） | Senior ML | £140-180K 底薪；£200K+ TC |
| London（Google DeepMind） | Senior | £110-155K 底薪 + RSU |
| Berlin / Germany | Senior | €95-130K |
| **Bangalore（頂尖 GCC / AI-first）** | Senior | ₹1-2 Cr TC |
| Bangalore（應屆 PhD / 頂尖 MS） | 入門 | ₹22-32 LPA |
| Singapore | 平均 | S$221,200 |
| Singapore（Principal/Lead） | 10 年以上 | S$323,505 |

**資料來源：** [levels.fyi Anthropic](https://www.levels.fyi/companies/anthropic/salaries/software-engineer)、[OpenAI](https://www.levels.fyi/companies/openai/salaries/software-engineer)、[Cursor](https://www.levels.fyi/companies/cursor/salaries/software-engineer)、[Sierra](https://www.levels.fyi/companies/sierra/salaries/software-engineer)、[Pin AI Comp Guide 2026](https://www.pin.com/blog/ai-compensation-salary-guide/)、[Kore1 salary guide](https://www.kore1.com/ai-engineer-salary-guide/)、[AI Pulse benchmarks](https://theaimarketpulse.com/salaries/)、[Career Check London 2026](https://www.careercheck.io/blog/ml-engineer-salary-london-2026)、[Zen van Riel Europe](https://zenvanriel.com/job/ai-engineer-salary-europe/)、[Scaler India](https://www.scaler.com/topics/ai-ml-engineer-salary-complete-guide/)。

### 薪酬洞察

前沿實驗室 MTS 薪酬（Anthropic/OpenAI 中位數約 $600-795K）與企業 AI 工程（中階約 $170-260K）之間的差距是 **3-5 倍**。睜大眼睛選擇你的公司層級。

---

## 地理與產業分布

- **集中度：** 65% 以上的 AI 工程師位於 SF + NYC
- **雙層市場：** Indeed Hiring Lab 報告約 95% 的招聘公司「沒有」張貼過 AI 職缺——採用高度集中於最大型的公司（[Indeed Hiring Lab 2026 年 1 月](https://www.hiringlab.org/2026/01/16/ai-adoption-accelerating-still-concentrated-among-largest-firms/)）
- **企業採用：** 截至 2026 年第一季，72% 的企業在生產環境中至少有一個 AI 工作負載（[Medha Cloud](https://medhacloud.com/blog/ai-adoption-statistics-2026)）
- **顧問業榮景：** BCG 報告其 2025 年 144 億美元營收中有 25%（36 億美元）來自 AI 顧問業務（[Metaintro BCG](https://www.metaintro.com/blog/bcg-25-percent-ai-revenue-consulting-jobs-2026)）
- **國際招聘年增 82%**；67% 的公司提供搬遷補助方案
- **遠端友善：** LangChain 生態系 35.2% 遠端、48.4% 混合、16.4% 嚴格現場
- **Indeed AI Tracker：** 2025 年 12 月所有職缺的 4.2%——在更廣泛的招聘疲弱中持續成長

---

## 面試流程模式

2026 年 5 月在 AI 原生公司的標準流程：

1. **招募人員初篩**（30 分鐘）——文化/使命 + 薪酬 + 簽證
2. **技術電話初篩**（60-90 分鐘）——實務性編碼，生產風格
3. **帶回家作業**（48 小時 - 3 天）——在 LangChain、Mistral、Eightfold 很常見；打造一個小型 RAG/agent 系統。[「這不是測試你能不能打造，而是你『怎麼』打造——程式碼品質、evals、錯誤處理」](https://github.com/alexeygrigorev/ai-engineering-field-guide/blob/main/interview/01-interview-process.md)
4. **現場/線上連續關卡**（4-6 小時）：編碼關卡 + AI 系統設計 + 專案深度探討 + 行為面試。[「純白板關卡大多已消失，連 Google 的形式現在都是協作式的」](https://designgurus.substack.com/p/system-design-interviews-changed)
5. **招聘主管 / 價值觀關卡**——在 Anthropic 是明確的關卡

### AI 職位的特定要點

- **系統設計關卡**現在預期會涉及 LLM 基礎設施、GPU 排程、vector stores、RAG、eval 把關的 CI、成本/延遲取捨
- 在 Meta、Canva、Google、Microsoft、Sierra、Cursor 的 **AI 輔助編碼關卡**明確允許使用 AI 工具（Cursor、Copilot、Claude）——評估 prompt 技巧與輸出驗證
- **帶回家作業的透明度：** 附上一則「AI 稽核註記」——你用 AI 做了什麼、你改了什麼、為什麼。透明勝過隱匿
- **Sierra：** 僅限 SF 或 NY 辦公室親自進行；2 小時的「Plan + Build + Present」agent 評估，沒有演算法關卡
- **Cursor：** 8 小時帶回家作業，使用他們自己的產品、文件有限，並提供一個 Slack 頻道——評估產品直覺、自主性、系統設計
- **Anthropic：** 「聽起來像是前一晚才趕出來的答案，是個糟糕的訊號」

### 前沿實驗室的特定要點

- **Anthropic：** 90 分鐘、4 個層級漸進加難的編碼題，測試你是否寫出能吸收新需求的乾淨模組化程式碼。價值觀關卡是明確的。
- **OpenAI：** 「設計 OpenAI Playground」——thread/message 歷史的線框圖 + API + DB schema；多租戶安全雲端 IDE
- **Mistral（Paris）：** 5 關流程、不接受遠端，並有一個專門的「LLM 理論」階段，涵蓋 transformer 內部機制與對齊

---

## 值得關注的新興職位

這些職位在 2026 年 5 月成長最快——如果你正在規劃 12 個月的職涯軌跡，押注它們。

### Forward Deployed Engineer (FDE)
- **為何：** 前沿 AI 買家（Fortune 500、政府、生技）將駐點工程列為合約交付項目來要求
- **薪酬：** 在前沿實驗室中至資深層級 $350-550K
- **技能：** RAG、fine-tuning、distillation、MCP、面向客戶的溝通、在客戶現場進行 evals
- **在哪裡：** OpenAI、Anthropic、Google、ElevenLabs、Cohere、Mistral、規模擴張型公司

### AI Evaluation Engineer
- **為何：** Eval 成熟為一門學科；生產環境需要 eval 把關的 CI/CD
- **薪酬：** 約聘 $100-110/小時；前沿實驗室全職 $200-400K
- **技能：** LLM-as-judge 校準、錯誤分析方法論、統計修正、資料集策展、回歸偵測
- **在哪裡：** OpenAI（Applied Evals、Frontier Evals）、Apple、Scale AI、Distyl、Apex

### Agentic Systems Engineer
- **為何：** 多 agent 與 tool-use 是一等公民的系統工程
- **薪酬：** 典型 $84-250K；agentic AI architect $260-420K
- **技能：** LangGraph / 多 agent 編排、MCP、A2A protocol、agent 除錯、tool 設計、sandbox 安全
- **在哪裡：** Teradata、GE Vernova、Deloitte、OpenAI（Agent Infrastructure）

### AI Reliability Engineer
- **為何：** 生產環境的 AI 需要類似 SRE 的紀律來應對非確定性系統
- **薪酬：** 在前沿實驗室資深層級 $250-400K（Anthropic 正在張貼 Staff/Sr 職位）
- **技能：** AI agents 的事件應變、失控迴圈的圍堵、成本異常偵測、多供應商備援
- **在哪裡：** Anthropic；「AI SRE」類別正由 Resolve.ai、Rootly 定義中

### AI Security Engineer / LLM Red Team Specialist
- **為何：** 在 2026 年 5 月 AI 安全的轉折點（Mythos 揭露、Daybreak、MDASH、首個在野的 AI 打造之零時差漏洞）之後，prompt injection + jailbreak 研究成為獨立學科
- **薪酬：** 視專精方向 $152-230K
- **技能：** 間接 prompt injection 防禦、jailbreak 研究、constitutional classifiers、模型供應鏈信任、MCP 威脅建模
- **在哪裡：** Life360、前沿實驗室、聚焦安全的企業

### MCP Engineer
- **為何：** MCP 生態系的成熟使伺服器開發成為它自己的專業
- **技能：** MCP server 設計（HTTP/STDIO）、OAuth resource server 模式、agent-card 簽章、MCP 安全
- **在哪裡：** Descope、與 Anthropic 立場一致的規模擴張型公司、Fortune 500 的內部平台

---

## 策略性要點

給規劃下一步的**工程師**：

1. **定位成專才，而非「Prompt Engineer」。** 挑一門學科（evals、agents、RAG、FDE、MLOps）並建立深度。
2. **可運作作品集 > 論文。** 交付 3-5 個帶有 evals 與可觀測性的生產級專案。對應用型職位，Anthropic、OpenAI 與規模擴張型公司全都把這個看得比發表論文重。
3. **FDE 是高槓桿的。** 如果你能把技術深度與面向客戶的溝通配對在一起，前沿實驗室的 FDE 薪酬是市場頂端——僅次於獨角獸的創辦人/staff 股權。
4. **市場是二分的。** 通才型的中階 SWE 工作正被裁撤。資深 AI 專才處於賣方市場。據此規劃你的軌跡。

給建立評核標準的**招聘主管**：

1. **為具體問題招人，而非為「AI Engineer」招人。** 如果你寫一份通用的 AI Engineer JD，你會得到通用的候選人。
2. **優先評估已交付的系統。** 一份模擬你實際工作負載的帶回家作業（為我們的領域打造一個小型 RAG agent），比演算法謎題更具預測力。
3. **AI 輔助編碼關卡現在是標準。** 觀看候選人 prompt + 驗證模型輸出，比封鎖 AI 使用更有資訊量。
4. **薪酬分級很重要。** 前沿實驗室的薪酬正在對下兩個層級造成留才壓力。如果你是招聘 AI 人才的企業，請校準到當地市場再加上資深以上 15-25% 的 AI 溢價。

給做組織設計的**工程領導者**：

1. **把職位對應到工作，而非對應到職稱。** 「AI Engineer」是你的總稱。在它之內：明確命名專精方向（RAG lead、agent lead、eval lead、platform lead）。
2. **Eval Engineer 是一個真實的職位。** 別讓一個功能工程師去擁有他正試圖改善的那個指標。把度量與交付分開。
3. **FDE 只有在客戶 ARR 超過約 $500K 時才划算。** 低於此，使用 solutions engineering。高於此，FDE 透過文件無法一般化的客戶特定工程，賺回它的薪酬。
4. **AI Reliability Engineer 是你還不知道自己需要的那個職位。** 當你的第一個 agent 在凌晨 3 點陷入迴圈、在迴圈守衛觸發前燒掉 $50K 的 API 花費時，你會希望自己 6 個月前就有這個職位。

---

## 參考資料

本章節取材自截至 2026 年 5 月 17 日的 100 多份公開職缺、招聘報告與招募人員訊號。主要來源：

### 招聘市場報告
- [Ivan Turkovic - AI Job Titles 2026: A CTO's Guide to the Naming Chaos](https://www.ivanturkovic.com/2026/04/24/ai-job-titles-2026-naming-chaos/)
- [Kore1 - AI Engineer Salary Guide 2026](https://www.kore1.com/ai-engineer-salary-guide/)
- [Kore1 - Tech Layoffs Q1 2026](https://www.kore1.com/tech-layoffs-2026/)
- [Pin - AI Compensation Benchmarks 2026](https://www.pin.com/blog/ai-compensation-salary-guide/)
- [Allwork.space - AI Hiring Rising vs Layoffs](https://allwork.space/2026/05/ai-hiring-is-rising-even-as-tech-layoffs-surge-140/)
- [Tom's Hardware - Q1 2026 Layoffs](https://www.tomshardware.com/tech-industry/tech-industry-lays-off-nearly-80-000-employees-in-the-first-quarter-of-2026-almost-50-percent-of-affected-positions-cut-due-to-ai)
- [Indeed Hiring Lab - Jan 2026 AI in Postings](https://www.hiringlab.org/2026/01/22/january-labor-market-update-jobs-mentioning-ai-are-growing-amid-broader-hiring-weakness/)
- [Indeed Hiring Lab - AI Adoption Concentration](https://www.hiringlab.org/2026/01/16/ai-adoption-accelerating-still-concentrated-among-largest-firms/)
- [Second Talent - Top 10 In-Demand AI Engineering Skills](https://www.secondtalent.com/resources/most-in-demand-ai-engineering-skills-and-salary-ranges/)
- [World Economic Forum - AI Added 1.3M Jobs](https://www.weforum.org/stories/2026/01/ai-has-already-added-1-3-million-new-jobs-according-to-linkedin-data/)
- [AI Pulse - AI & ML Engineer Salary Benchmarks 2026](https://theaimarketpulse.com/salaries/)
- [Agentic Engineering Jobs - LangChain Market 2026](https://agentic-engineering-jobs.com/langchain-job-market-2026)

### 薪酬資料
- [levels.fyi - Anthropic](https://www.levels.fyi/companies/anthropic/salaries/software-engineer)
- [levels.fyi - OpenAI](https://www.levels.fyi/companies/openai/salaries/software-engineer)
- [levels.fyi - Cursor](https://www.levels.fyi/companies/cursor/salaries/software-engineer)
- [levels.fyi - Sierra](https://www.levels.fyi/companies/sierra/salaries/software-engineer)
- [levels.fyi - Google AI](https://www.levels.fyi/companies/google/salaries/software-engineer/title/ai-engineer)
- [levels.fyi - Microsoft AI](https://www.levels.fyi/companies/microsoft/salaries/software-engineer/title/ai-engineer)
- [Entrepreneur - OpenAI Salaries (Federal Filing)](https://www.entrepreneur.com/business-news/how-much-openai-employees-make-salaries-685000)
- [Career Check - ML Engineer Salary London 2026](https://www.careercheck.io/blog/ml-engineer-salary-london-2026)
- [Zen van Riel - AI Engineer Salary Europe](https://zenvanriel.com/job/ai-engineer-salary-europe/)
- [Scaler - AI/ML Engineer Salary India](https://www.scaler.com/topics/ai-ml-engineer-salary-complete-guide/)
- [Morgan McKinley - Singapore AI/ML Engineer](https://www.morganmckinley.com/sg/salary-guide/data/ai-ml-engineer/singapore)

### 前沿實驗室職涯來源
- [Anthropic - Careers](https://www.anthropic.com/careers)
- [Anthropic - Forward Deployed Engineer](https://job-boards.greenhouse.io/anthropic/jobs/4985877008)
- [Anthropic - Applied AI Engineer](https://job-boards.greenhouse.io/anthropic/jobs/5116274008)
- [OpenAI Careers](https://openai.com/careers/search/)
- [OpenAI - Applied Evals](https://openai.com/careers/software-engineer-applied-evals-san-francisco/)
- [OpenAI - Frontier Evals & Environments](https://openai.com/careers/research-engineer-frontier-evals-and-environments-san-francisco/)
- [OpenAI - Agent Infrastructure SWE](https://openai.com/careers/software-engineer-agent-infrastructure-san-francisco/)
- [Sundeep Teki - How to Get Hired at OpenAI/Anthropic/DeepMind 2026](https://www.sundeepteki.org/advice/how-to-get-hired-at-openai-anthropic-and-google-deepmind-in-2026)
- [Sundeep Teki - AI Research Engineer Interview Guide](https://www.sundeepteki.org/advice/the-ultimate-ai-research-engineer-interview-guide-cracking-openai-anthropic-google-deepmind-top-ai-labs)
- [Sundeep Teki - FDE Interviews](https://www.sundeepteki.org/advice/the-definitive-guide-to-forward-deployed-engineer-interviews-in-2026)
- [Hashnode - Complete 2026 Guide to FDE](https://hashnode.com/blog/a-complete-2026-guide-to-the-forward-deployed-engineer)

### 面試流程來源
- [Design Gurus - System Design Interviews Changed in 2026](https://designgurus.substack.com/p/system-design-interviews-changed)
- [IGotAnOffer - Anthropic Interview Process](https://igotanoffer.com/en/advice/anthropic-interview-process)
- [Jobright - Anthropic Technical Interview 2026](https://jobright.ai/blog/anthropic-technical-interview-questions-complete-guide-2026/)
- [Sierra - The AI-Native Interview](https://sierra.ai/blog/the-ai-native-interview)
- [Alexey Grigorev - AI Engineering Field Guide (Interview Process)](https://github.com/alexeygrigorev/ai-engineering-field-guide/blob/main/interview/01-interview-process.md)
- [interviewing.io - Meta AI-Assisted Coding Interview](https://interviewing.io/blog/how-to-use-ai-in-meta-s-ai-assisted-coding-interview-with-real-prompts-and-examples)
- [Exponent - OpenAI System Design 2026](https://www.tryexponent.com/blog/openai-system-design-interview)
- [Exponent - Anthropic System Design 2026](https://www.tryexponent.com/blog/anthropic-system-design-interview)

### 新興職位涵蓋
- [AI Career Lab - Agentic-AI Job Guide 2026](https://theaicareerlab.com/blog/agentic-ai-jobs-guide-2026)
- [Practical DevSecOps - Top 10 Emerging AI Security Roles](https://www.practical-devsecops.com/emerging-ai-security-roles/)
- [Fast Company - Google/Box CEOs: FDE most in-demand](https://www.fastcompany.com/91541878/google-box-ceos-say-this-is-the-most-in-demand-job-in-tech)
- [Computerworld - FDE career emerging from AI shift](https://www.computerworld.com/article/4171867/heres-one-career-emerging-from-the-ai-shift-forward-deployed-engineers.html)
- [Rootly - AI SRE Guide 2026](https://rootly.com/ai-sre-guide)
- [Resolve.ai - What is an AI SRE](https://resolve.ai/glossary/what-is-ai-sre)
- [Medium - Rise of MCP Skills](https://medium.com/@adnanmasood/the-rise-of-model-context-protocol-mcp-skills-5f0d6a1c3579)

### 合規與法規
- [EU AI Act Implementation Timeline](https://artificialintelligenceact.eu/implementation-timeline/)
- [Secure Privacy - EU AI Act 2026 Compliance](https://secureprivacy.ai/blog/eu-ai-act-2026-compliance)
- [Augment Code - EU AI Act 2026 Guide](https://www.augmentcode.com/guides/eu-ai-act-2026)

---

*另見：[題庫](01-question-bank.md) | [答題框架](02-answer-frameworks.md) | [AI 職位的行為面試](05-behavioral-for-ai-roles.md) | [職涯轉換指南](../TRANSITION_GUIDE.md)*
