# Agent 記憶與狀態

記憶讓 agent 能夠隨時間學習並維持脈絡。Agent 記憶已從「對話歷史」演進為一套**多層認知架構（Multi-Tiered Cognitive Architecture）**，包含四個具名層級（Working、Episodic、Semantic、Procedural），每一層都有自己的寫入模式、延遲預算與失效模式。正式環境系統（Mem0、Letta、Anthropic Memory Tool + Skills、Zep/Graphiti、LangMem）如今都把記憶選型視為一級的架構決策。

形塑本章的 2026 年研究浪潮：A-MEM（NeurIPS 2025）、HippoRAG（multi-hop 圖檢索）、多層記憶架構（Multi-Layered Memory Architectures）、HaluMem（operation-level 記憶幻覺基準）、MINJA / MemoryGraft（query-only 記憶投毒攻擊），以及 NVIDIA 把脈絡壓縮進權重的 TTT-E2E test-time-training 方法。

## 目錄

- [記憶階層](#hierarchy)
- [短期記憶：推理軌跡](#short-term)
- [Episodic 記憶：過往經驗](#episodic)
- [Semantic 記憶：人格](#semantic)
- [Procedural 記憶：習得的技能與工作流程](#procedural-memory-learned-skills-and-workflows)
- [取捨：事實 X 該放在哪裡？](#tradeoffs)
- [正式環境實作（2026 年 5 月）](#production-implementations)
- [失效模式與緩解措施](#failure-modes)
- [Mem0 與個人化](#mem0)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 記憶階層

Agent 對儲存採用分層方式：

| 層級 | 類型 | 技術 | 用途 |
|------|------|------------|---------|
| **L1** | Working Memory | Context Window / KV Cache | 當前任務步驟、區域變數 |
| **L2** | Episodic Memory | Vector DB / Graph | 「我上次做了什麼？」 |
| **L3** | Semantic Memory | SQL / Knowledge Graph | 使用者偏好、「真相」 |
| **L4** | Procedural Memory | Skills Registry / Tool Policies / Workflow Graph | 「我該如何執行這個任務？」 |

### 各層級的實務特性

各層級的差異不僅在於用途。讀取模式、寫入模式、延遲預算與時效性期望，各自都會把選型推向不同的儲存技術：

| 維度 | L1 Working | L2 Episodic | L3 Semantic | L4 Procedural |
|---|---|---|---|---|
| **儲存的內容** | 當前回合、工具輸出、scratchpad、system prompt | 過往 session、軌跡、帶時間戳的觀察 | 萃取後的事實、偏好、實體關係 | 技能、playbook、system-prompt 指令、程式/工具序列 |
| **讀取模式** | 每個 token、每個回合（在 attention 中） | 依相似度 + 近期性 + 重要性取 Top-k | 在提及實體/主題時觸發查詢 | 在比對到符合的任務簽章時載入 |
| **寫入模式** | 由 inference engine 持續 append；KV-cache mutation | append-only log；在回合邊界 commit | 萃取、去重、upsert；在寫入時做衝突解決 | 在成功/失敗後做反思式寫入；明確的人工或自我編輯 |
| **延遲預算** | <50ms（常駐於 GPU HBM） | 100-300ms（vector ANN + rerank） | 200-800ms（圖遍歷 + LLM 萃取） | 50-500ms（檔案讀取或小型索引查詢） |
| **時效性期望** | token 級新鮮；session 結束即遺失 | 數小時至數月；可容忍陳舊 | 應反映*當前*狀態；陳舊即為 bug | 緩慢變動；更新是刻意為之 |
| **儲存技術** | HBM 中的 KV cache（vLLM PagedAttention blocks） | Vector DB（Pinecone、Weaviate、Qdrant）、append-only log | Knowledge graph（Neo4j、Graphiti）、KV store、bitemporal 關聯式列 | 檔案系統（Claude `/memories/`、以 `SKILL.md` 形式的 Skills）、prompt registry、fine-tuned LoRA |
| **查詢語意** | 位置 + attention | 相似度 + 近期性 + 重要性（Park 等人的加權法） | 實體-關係比對、結構化查詢、bitemporal 過濾 | 任務簽章比對，常為檔名或 tag 查詢 |
| **逐出（Eviction）** | 滑動視窗、對 KV block hash 做 LRU | 衰減評分、合併進 L3、歸檔至冷儲存 | 透過時間性 `valid_to` 取代；為 GDPR 做明確刪除 | 手動淘汰、與較新技能做 A/B、版本鎖定 |

**這在實務上的意涵：**當一個事實到來時，架構問題不是「我們該記住它嗎？」而是「該放在*哪一層*、採用哪種時效性契約、套用哪種逐出規則？」選錯層級會產生可預期的失效模式（被提升到 L3 的 session 偏好會跨 session 外洩；被留在 L2 的穩定使用者事實會在兩週內被逐出）。詳見下方的[取捨：事實 X 該放在哪裡？](#tradeoffs)。

---

## 短期記憶：推理軌跡

正式環境的 agent 不再只儲存「Messages」；它們儲存的是**狀態物件（State Object）**。
- **Scratchpad**：prompt 中一個專屬區段，agent 在此「寫筆記」給自己，且這些內容不會顯示給使用者。
- **KV Cache Tiling**：對於長時間執行的 agent，我們使用 **Prefix Caching** 把「System Instruction」與「Standard Tools」保持在 GPU 記憶體中的熱狀態，只置換動態的任務狀態。

---

## Episodic 記憶：過往經驗

Episodic 記憶儲存的是「Runs」或「Trajectories」。
- 如果某個 agent 上週二爬取某網站失敗了，episodic 記憶應該防止它今天再次嘗試同一個失敗的 selector。
- **模式**：當任務完成時，總結「習得的教訓（Lessons Learned）」並把它們存入 vector DB。在新任務開始時，對類似的過往任務執行**自我搜尋（Self-Search）**。

---

## Semantic 記憶：人格

Semantic 記憶儲存關於使用者或環境的「事實」。
- *「使用者偏好 JSON 輸出。」*
- *「正式環境 DB 在凌晨 3 點至 4 點之間離線。」*

**最佳實務**：為 semantic 記憶使用 **Knowledge Graph**。不同於 vector search（其結果是模糊的），圖能對實體與關係提供確定性的檢索（例如 `User` -- `OWNER_OF` --> `Project_A`）。

---

## Procedural 記憶：習得的技能與工作流程

Procedural 記憶儲存的是做事情的方法。episodic 記憶回答的是「之前發生了什麼？」，semantic 記憶回答的是「什麼是真的？」，而 procedural 記憶回答的是：

「完成這類任務的正確流程是什麼？」

這一層捕捉可重複使用的技能、工具使用模式、操作程序，以及工作流程偏好。

範例：

* 「產生週報時，先從 Snowflake 拉取 metrics，接著與 dashboard 對照驗證，然後總結異常。」
* 「回應客訴時，先分類緊急程度、檢索政策、草擬回覆，並在信心不足時升級處理。」
* 「撰寫 SQL 時，務必先檢視 schema、產生查詢、執行驗證，並說明假設。」

Procedural 記憶對 agentic 系統特別重要，因為許多任務並不只是記住事實的問題。它們需要遵循正確的動作序列。

---

## 取捨：事實 X 該放在哪裡？

第一順位的決策不是「哪一層」，而是*「誰來承擔出錯的代價？」*。L2 的一次檢索遺漏只會讓單一回合失敗。L3 的一個壞事實會讓*每一個*回合都失敗，直到被修正為止。L4 的一個被投毒的技能會傳播到未來每一次的呼叫。

### 層級選擇表

| 事實 / 考量 | 層級 | 理由 |
|---|---|---|
| 「使用者的 API rate limit 是 1000 req/min」 | L3，搭配 bitemporal `valid_to` | 租戶範圍的事實；可依實體查詢；必須支援取代。不放 L4——它是資料，不是程序。 |
| 「部署我們服務的步驟」 | L4，作為帶版本的技能 | 含條件分支的多步驟流程。技能可組合；semantic triple 不行。 |
| 「agent 上一次嘗試此任務的失敗紀錄」 | L2 原始紀錄，*接著*若可一般化則把教訓反思進 L4 | 原始軌跡屬於 episodic；一般化後的教訓（「絕不在尖峰時段執行 migration」）值得做一次 Reflexion 風格的 L4 寫入。 |
| 「使用者偏好簡短的回應」 | L3 | 穩定偏好，可依 `user_id` 查詢，單一 triple。 |
| 「使用者*在這場對話中*要求簡短的回應」 | 僅 L1 | session 範圍；不要拿可能是暫時性的偏好污染 L3。 |
| 當前天氣、今日股價 | 無：呼叫工具 | 快速變動且在他處已有真相來源的事實，絕不應進入記憶。 |
| 「Project Phoenix 的團隊成員為 A、B、C」 | L3，作為圖片段 | 具 multi-hop 遍歷價值；採 Graphiti 或 Neo4j 風格的儲存。 |

### 成本取捨

- **L1 主導*延遲成本***：TTFT 隨脈絡大小擴大；working memory 越長，第一個 token 越慢。KV-cache 壓力會把昂貴的加速器記憶體推向飽和。
- **L2 在規模下主導*儲存成本***：append-only log 隨使用量線性成長。[Day-30 問題](https://cipherbuilds.ai/blog/day-30-agent-memory-problem)描述了未經修剪的 episodic store 如何在一個月後腐蝕 agent 品質。
- **L3 主導*寫入放大成本***：每個回合都可能觸發萃取、去重、衝突解決。Mem0 的設計明確地以寫入時的工作量換取檢索速度。
- **L4 主導*治理成本***：一個壞技能會傳播到未來每一次呼叫。Anthropic 的「[Claude Dreaming](https://www.mindstudio.ai/blog/what-is-claude-dreaming-anthropic-agent-memory)」排程式合併以透過審查為技能更新把關，正是對此的回應。

### 升級規則

有趣的設計問題是*L2 episode 何時升級為 L3 或 L4*。站得住腳的規則是基於門檻，而非隱含衰減：

1. **同一模式的 N 次獨立觀察**（N=3 至 5 是典型值）。
2. **依來源做信心加權**：使用者陳述 > 工具輸出 > 模型推論。
3. 在合併步驟做**人工或 LLM 評審審查**（而非每個回合）。
4. **排程式批次合併**，而非同步的每回合寫入（避免寫入放大）。
5. **雙向**：L3 中的 semantic 事實可被重新實例化為特定任務的 episodic 脈絡。記憶不是單行道。

---

## 正式環境實作（2026 年 5 月）

這些具名系統的差異，較少在於「它們儲存什麼」，而更多在於*寫入紀律*、*檢索演算法*與*治理姿態*。

| 系統 | 適用場景 | 它擅長之處 | 它的不足之處 |
|---|---|---|---|
| **[Mem0](https://github.com/mem0ai/mem0)** | 大規模的跨 session 個人化 | 混合 graph + vector + KV。在 2026 年 4 月的 single-pass 重新設計後，於 LoCoMo 達 92.5、LongMemEval 達 94.4（[benchmarks](https://mem0.ai/blog/ai-memory-benchmarks-in-2026)）。在正面對決中以 26% 的準確度優於 OpenAI 內建記憶。 | 每筆記憶 8K 字元上限（不適用於文件）；cloud-first 姿態造成資料主權摩擦；無正式的信念狀態模型（僅能覆寫或 append）。 |
| **[Letta（前身為 MemGPT）](https://docs.letta.com/concepts/memgpt/)** | 以連貫性為產品本身的長時間執行自主 agent | OS 風格的虛擬脈絡分頁，橫跨 core / recall / archival 層級；agent 使用 tool call 把資料分頁進出。當使用者體驗是「agent 永遠記得」時表現最佳。 | 每回合延遲高於 Mem0 風格。未針對跨使用者檢索精度做最佳化。 |
| **[Anthropic Memory Tool + Skills](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)** | 在單一基底上掛載檔案系統式的 L3 與 L4 | 記憶位於 `/memories/`；Skills 以 `SKILL.md` 套件加上選用腳本的形式存在；Managed Agents 每個 session 在 `/mnt/memory/` 掛載記憶並提供 immutable 版本控制（2026 年 4 月 23 日 GA）。排程式的「Claude Dreaming」在 session 之間進行合併。 | 檔案系統語意把複雜度推給 agent（agent 必須把自己的目錄結構安排妥當）。 |
| **[Zep + Graphiti](https://github.com/getzep/graphiti)** | 在意「這是何時變為真的？」的時間性事實 | 開源的時間性 knowledge graph。每條 edge 都有 `valid_from` / `valid_to` / `invalid_at`。在 DMR 上以 94.8% 對 93.4% 勝過 MemGPT。Bitemporal 查詢可區分「我們在 3 月 12 日相信什麼」與「現在什麼是真的」。 | 寫入路徑比僅有 vector 的 store 更重（圖萃取、去重、衝突解決）。 |
| **[LangMem + LangGraph](https://langchain-ai.github.io/langmem/)** | 當你想要四種記憶類型搭配 LangGraph 編排時 | 支援 episodic、semantic *以及* procedural。LangMem 中的 procedural 記憶讓 agent 能根據回饋更新自己的 system prompt。背景萃取在 out-of-band 執行。 | 與 LangGraph 耦合；若你不在 LangChain 技術棧上則吸引力較低。 |
| **[OpenAI ChatGPT Memory](https://openai.com/index/memory-and-new-controls-for-chatgpt/)** | 消費級的對話連續性，而非正式環境級的 agent 記憶 | 雙層架構：明確的「saved memories」加上預先注入脈絡的輕量對話摘要。在推論時跳過檢索步驟以降低延遲。 | 相較於 Mem0 風格的檢索損失精度。無供企業整合用的細粒度程式化 API。 |
| **Cursor / Windsurf** | 為軟體工程 agent 提供具程式庫感知的 L2/L3 | 在開啟專案時索引程式庫；以 `@`-mentions 提供明確脈絡。Windsurf 的「Memories」在約 48 小時的使用中學習架構模式。 | 鎖定於程式碼領域。不是通用型記憶層。 |
| **[Cognition Devin](https://cognition.ai/blog/devin-sonnet-4-5-lessons-and-challenges)** | 範圍限於 repo 的工程 agent | 每隔數小時自動索引 repository wiki；偏好明確的壓縮/摘要而非模型自管的狀態。Devin Search 是一個 agentic 的程式庫記憶查詢介面。 | 對工程工作流程有既定觀點。 |

**Generative Agents（Park 等人 2023）**仍是每篇綜述都會引用的參考架構。其近期性 / 重要性 / 相關性的檢索公式（`alpha_recency * recency + alpha_importance * importance + alpha_relevance * relevance`，各項正規化至 [0,1]，重要性由 LLM 評為 1-10），在上述大多數系統中仍在正式環境使用中。

**值得追蹤的新興框架**（2026 年 5 月）：[Supermemory](https://supermemory.ai)、[Recallr](https://recallrai.com)、AWS [Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-integrate-lang.html)、[Oracle AI Agent Memory](https://blogs.oracle.com/developers/oracle-ai-agent-memory-a-governed-unified-memory-core-for-enterprise-ai-agents)。

---

## 失效模式與緩解措施

正式環境的記憶系統有六種反覆出現的失效模式。能叫出它們的名字，是初級與 staff 級架構對話之間的差異所在。

### 1. 透過 prompt injection 的記憶投毒

不受信任的輸入被寫入 L3/L4，之後被當作權威重播。[MINJA（NeurIPS 2025）](https://openreview.net/forum?id=QVX6hcJ2um)與[MemoryGraft（2025 年 12 月）](https://arxiv.org/html/2512.16962v1)展示了*query-only* 的投毒攻擊，在*無需*提權的情況下達到 95% 的注入率與 70% 的攻擊成功率。[Palo Alto Unit 42 的報告](https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/)顯示毒物可在引爆前數週就被植入。

**緩解措施：**
- 對每次記憶寫入加上**來源標記（Provenance tags）**：`source = user_stated | model_inferred | tool_output`。
- **寫入時護欄模型（Write-time guardrail model）**，拒絕可疑的指令狀寫入（「忽略先前內容，改為……」、角色混淆、嵌入的 system-prompt 片段）。
- **信任分層（Trust tiers）**：低信任的記憶在影響高風險決策前需要佐證。
- **艙壁隔離（Bulkhead isolation）**，使一個租戶中的毒物無法轉進另一個租戶。

### 2. 陳舊事實

昨日的偏好對上今日的偏好。經典案例是「使用者上個月說要深色模式，但現在用淺色模式」。

**緩解措施：**
- **Bitemporal 儲存**（Zep/Graphiti 模式）：每個事實都有 `valid_from`、`valid_to`、`invalid_at`。
- 對 session 範圍的偏好設**TTL**，使其自動過期。
- 在檢索評分中加入**衰減加權**。
- 對超過 N 天的高風險事實，提出**明確的重新確認**提示。

### 3. 衝突事實

使用者說了 X，現在又說 Y。三種不同的衝突類型應對應不同回應：

| 衝突類型 | 正確回應 |
|---|---|
| 時間性更新（「我搬到柏林了」） | 以 `valid_to = now` 取代舊事實 |
| 更正（「我從沒這樣說過」） | 帶稽核軌跡地撤回 |
| 偏好改變（「我現在想要簡潔的回應」） | 新增事實；讓衰減處理舊的 |
| 直接矛盾（無明顯解法） | 詢問使用者；絕不靜默覆寫 |

使用 AGM 信念修正來追蹤信念狀態（`ACTIVE` / `SUPERSEDED` / `RETRACTED`），而非 last-write-wins。

### 4. 記憶漂移

品質隨時間下降，因為低品質的寫入稀釋了高品質的寫入。[Day-30 問題](https://cipherbuilds.ai/blog/day-30-agent-memory-problem)記錄了 agent 在進入正式環境約 30 天後，隨著 episodic store 充滿雜訊而效能下滑。

**緩解措施：**
- **品質加權檢索**：提升具高驗證分數的記憶。
- **排程式合併工作**，合併重複項並修剪低效用的記憶。
- **CI 中的 canary 事實測試**：「agent 在 50 個回合後仍應記得使用者的名字。」

### 5. 幻覺式記憶寫入

Agent 推論出一個事實、將其存為基準真相，之後又把它當作權威來引用。這是一種級聯失效：一個壞寫入會污染未來的檢索。[HaluMem 基準（2025 年 11 月）](https://arxiv.org/abs/2511.03506)顯示既有系統在寫入時累積錯誤，並向前傳播至 QA 階段。

**緩解措施：**
- **schema 強制的記憶物件**，將 `confirmed_facts`（附來源）與 `inferred_facts`（附信心值）分為不同欄位。
- 在沒有明確使用者訊號或工具輸出佐證的情況下，絕不自動把推論提升為已確認。
- 在 CI 中採 HaluMem 風格的分階段評估：分別量測萃取精度、更新正確性與 QA 準確度，而非以單一端對端指標衡量。

### 6. 跨租戶外洩

Vector ANN 回傳了來自另一租戶的鄰居；快取的 prompt 含有另一租戶的資料。[實地量測](https://medium.com/@isuruig/multi-tenant-ai-infrastructure-the-5-isolation-layers-that-determine-whether-your-customers-data-stays-separate-340aaeef4922)顯示，在未隔離的多租戶 RAG 中，良性查詢的自然外洩率約為 95%。

**緩解措施：**
- **實體分離**：採每租戶獨立的 collection，而非以 metadata 過濾的共享索引。
- 透過 service-account 權限在*儲存*層強制租戶範圍，而非在應用程式碼中。
- 每租戶獨立的 KV-cache prefix。
- 對記憶 blob 採每租戶獨立的加密金鑰，使跨命名空間的讀取在密碼學層就失敗。

---

## Mem0 與 Agentic 個人化

**Mem0**、Zep、Letta 與 Cognee 是 agent 技術棧中「智慧記憶」的標準框架。
- 它會自動從對話中萃取「使用者洞察（User Insights）」。
- 它提供一個「Memory API」，agent 可呼叫以 `remember` 或 `forget` 特定的資訊三元組。
- **影響**：agent 之所以感覺「有生命」，是因為它記得你 3 個月前在另一場 session 提過的某個細節。

---

## 面試問題

### Q：在 agentic 系統中，你如何處理「衝突記憶」？

**強答案：**
衝突記憶（例如使用者上週說「我喜歡藍色」，現在卻說「我喜歡紅色」）可透過**時間性加權（Temporal Weighting）**或**明確爭議處理（Explicit Disputing）**來處理。在我的架構中，我會為每個記憶三元組指派一個 `timestamp` 與一個 `confidence_score`。若新事實與舊事實衝突，會提示 agent 去「解決衝突」——詢問使用者以澄清，或預設採用最新的時間戳。我們也使用**衰減函數（Decay Functions）**，讓較舊、未被強化的記憶最終從活躍索引中被修剪掉。

### Q：為何單靠「Context Window」對 staff 級的 Agent 架構而言並不足夠？

**強答案：**
首先是**成本與延遲**：即便有 context caching，每個回合都填滿 1M token 的脈絡仍貴得令人卻步。其次是**訊噪比**：大型 context window 會遭受「in-context learning」退化——模型被無關的歷史回合分散注意力。staff 級的架構會使用**選擇性記憶檢索（Selective Memory Retrieval）**（對歷史做 RAG），只拉入最相關的 3-5 次歷史互動，讓 Reasoning Engine 專注於當前的子目標。

### Q：你會如何為正式環境的 AI agent 設計 procedural 記憶？

**強答案：**

我會把 procedural 記憶設計為**技能登錄（skills registry）、工作流程圖（workflow graph）與工具使用政策（tool-use policies）**的組合。每個程序會定義任務類型、所需步驟、可用工具、驗證檢查、失效模式與升級規則。在每次執行後，agent 可進行反思，並在發現更好的做法時更新該程序。例如，若某個 NL2SQL agent 反覆失敗是因為它略過了 schema 檢視，我們可以把 schema 檢視編碼為所有 SQL 生成任務在 procedural 記憶中必備的第一步。

### Q：episodic 記憶在什麼時候會從資產變成負擔？

**強答案：**

Episodic 記憶在三種具名模式下會變成負擔。第一是**索引超載**：加入 1,000 筆低品質觀察，會在檢索時把那 10 筆高品質的觀察淹沒。這在 RAG 意義上是一種災難性遺忘。第二是**Day-30 漂移模式**：agent 品質在進入正式環境約 30 天後下降，因為 episodic store 充滿了檢索無法與訊號區分的雜訊。第三是**陳舊脈絡滲漏**：在某一組態下成功過的過往軌跡，在新組態下成為*錯誤*的脈絡。一個對 Stripe 成功的工具序列，在使用者已切換到 Adyen 時會主動產生誤導。

緩解措施是品質加權檢索、合併進 L3，以及對情境敏感軌跡設下硬性的近期性截斷。更深層的教訓是：episodic 記憶從第一天起就需要一套*修剪政策*。少了它，它就是會隨使用量線性累積的技術債。

### Q：當 agent 能寫入自己的長期 store 時，你如何防止記憶投毒？

**強答案：**

困難之處在於，近期的攻擊（MINJA、MemoryGraft）是*query-only* 的——無需提權。毒物會在引爆前數週就被植入。因此威脅模型是「每一筆輸入都可能成為未來的權威記憶」。防禦分為四層：

1. **寫入時的來源標記（Provenance）**：每筆記憶都帶有 `source`（user-stated、model-inferred、tool-output）、`timestamp` 與 `trust_tier`。
2. **寫入時護欄模型**：一個較小的分類器在可疑的指令狀寫入觸及 store 之前就拒絕它們。
3. **佐證門檻**：高風險決策不能僅憑單一低信任記憶就做出；它們需要多筆獨立的佐證寫入。
4. **CI 中的 canary 測試**：合成的毒物 payload 絕不能傳播進輸出。每週執行。

最重要的架構分離是：agent 的工具表面與其記憶寫入表面不應共享信任。工具輸出應先經過 sanitizer，才能成為記憶。

### Q：記憶層級選擇：你會把以下各項放在哪裡，為什麼？(a) 使用者的 API rate limit、(b) 部署我們服務的步驟、(c) agent 上一次嘗試此任務的失敗紀錄、(d) 今日股價。

**強答案：**

(a) **L3 semantic**，搭配 bitemporal validity。它是一個帶有取代生命週期、且範圍限於租戶的事實。不放 L4，因為它是資料，不是程序。

(b) **L4 procedural**，作為帶版本的技能或 playbook。它是一個含條件分支的多步驟流程。技能可組合；semantic triple 不行。

(c) **L2 episodic 原始紀錄**，並在該失敗揭示出可一般化的教訓時，做一次*反思跳接（reflection hop）*到 L4。原始軌跡屬於 episodic。那個教訓（「絕不在尖峰時段執行 migration」）值得一次 Reflexion 風格的 procedural 寫入。

(d) **無——呼叫工具。**具備即時真相來源的快速變動事實絕不應進入記憶。它們在定義上就會變得陳舊。

通則：資料放 L3，程序放 L4，觀察放 L2，且絕不儲存具備即時來源的快速變動事實。

### Q：帶我走一遍你會為 episodic-到-semantic 轉換設計的合併政策。episode 何時會變成事實？

**強答案：**

我採用基於門檻的升級政策，而非隱含衰減：

- **頻率門檻**：同一模式的 N 次獨立觀察（3 至 5 是典型值）。
- **信心加權**：使用者陳述 > 工具輸出 > 模型推論。
- **評審審查**：一個排程式批次合併工作，對候選升級項目執行 LLM 評審（高風險領域則由人工審查）。
- **排程而非同步**：合併在 out-of-band 以 cron 進行，而非每回合。這避免了寫入放大。
- **雙向**：L3 中的 semantic 事實可被重新實例化為特定任務的 episodic 脈絡。記憶雙向流動。

要避免的陷阱是僅憑衰減權重的隱含合併。它在小規模下行得通，卻在正式環境規模下靜默失效，因為對於「這個事實為何出現在 L3？」沒有任何稽核軌跡。

### Q：你的 agent 記憶 store 橫跨 10K 個租戶，共有 50M 筆記憶。你如何保證跨租戶隔離，而若隔離失敗，你的影響範圍（blast radius）有多大？

**強答案：**

該架構有五層隔離：

1. **儲存層的實體分離**：採每租戶獨立的 collection 或 shard，而非以 metadata 過濾的共享索引。共享索引加 tenant-id 的模式在出現 bug 時會 fail open。
2. **透過 service-account 範圍限定來強制執行**：應用程式碼無法退出租戶範圍；該資料庫角色對其他租戶不具可見性。
3. **每租戶獨立的 KV-cache prefix**：防止快取的 prompt 在租戶之間外洩。
4. **每租戶獨立的加密金鑰**：即使因 bug 被回傳，跨命名空間的位元組也無法讀取。
5. **對每一次跨命名空間查詢嘗試做稽核記錄**：縱深偵測。

**若隔離失敗的影響範圍**：單一個壞 vector 查詢可能外洩某個查詢 embedding 的*鄰域*——可能是某一租戶數百筆紀錄。實地量測顯示在未隔離的多租戶 RAG 中,自然外洩率約 95%。緩解之道不是「更謹慎的應用程式碼」；而是無法被應用程式 bug 繞過的結構性分離。

### Q：HaluMem 顯示記憶幻覺在寫入時累積，然後傳播。你會如何為正式環境記憶加上儀表化以捕捉這點？

**強答案：**

多數團隊落入的陷阱是僅在 QA 階段（端對端）量測記憶品質。HaluMem 證明 60-80% 的記憶錯誤源自*萃取*（寫入）時並向前傳播。你需要對三個獨立的指標加上儀表化：

1. **萃取精度**：當 agent 把一個事實寫入 L3 時，該事實是否確實受到來源觀察的支持？每日抽樣寫入，以較強的評審做評估。
2. **更新正確性**：當衝突事實到來時，衝突解決邏輯是否產生了正確的結果？使用 bitemporal 查詢偵測「未帶取代 metadata 卻翻轉了的事實」。
3. **QA 準確度**：端對端的回想正確性。

在此之上，執行**影子模式重播（shadow-mode replay）**：寫入會以影子模式經過一個 verifier 模型；live 寫入與 shadow-verifier 寫入之間的不一致，會標記出潛在的幻覺供審查。CI 中的 **canary 事實**確保記憶系統不會靜默退化。**週期性的全 store 稽核**抽樣隨機記憶，並詢問「這是否仍與來源對話一致？」

### Q：NVIDIA 的 TTT-E2E 透過 test-time training 把脈絡壓縮進權重。這在 L1-L4 階層中位於何處,又引入了什麼新的失效模式？

**強答案：**

TTT-E2E 位於 L1 與 L4 *之間*。它讓脈絡衍生的資訊在該 session 的其餘時間裡成為模型本身的一部分。其吸引力在於延遲：不論脈絡長度為何，成本皆為常數（依 NVIDIA 在 H100 上的 benchmark，於 128K 時加速 2.7 倍、於 2M token 時加速 35 倍）。

新的失效模式是治理。在權重中的記憶有：

- **無稽核軌跡**：你無法檢視「這個模型現在相信什麼？」
- **無逐出介面**：一旦壓縮進權重,你就無法刪除一筆記憶，除非回滾模型狀態。
- **GDPR 被遺忘權的挑戰**：該法規框架假設資料是 at rest，而非在權重中。
- **更難偵測投毒**：沒有可檢視的 store 可掃描 canary 簽章。

正確的框定方式：TTT-E2E 把記憶治理從儲存層移到了訓練與部署管線。成本並未被消除；只是被搬移了。對 2026 年 5 月的多數正式環境團隊而言，這是一個值得追蹤的研究方向，而非可部署的架構。

---

## 參考資料

### 正式環境框架
- [Mem0: Production-Ready AI Agents with Scalable Long-Term Memory (ECAI 2025)](https://arxiv.org/abs/2504.19413)
- [Mem0 AI Memory Benchmarks 2026](https://mem0.ai/blog/ai-memory-benchmarks-in-2026)
- [Letta (formerly MemGPT) documentation](https://docs.letta.com/concepts/memgpt/)
- [MemGPT: Towards LLMs as Operating Systems (arXiv 2310.08560)](https://arxiv.org/abs/2310.08560)
- [Anthropic Memory Tool documentation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [Anthropic Claude Sonnet 4.6 Skills announcement](https://www.anthropic.com/news/claude-sonnet-4-6)
- [Claude Dreaming: scheduled memory consolidation](https://www.mindstudio.ai/blog/what-is-claude-dreaming-anthropic-agent-memory)
- [Zep: Temporal Knowledge Graph Architecture (arXiv 2501.13956)](https://arxiv.org/abs/2501.13956)
- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [LangMem documentation](https://langchain-ai.github.io/langmem/)
- [OpenAI Memory and new controls for ChatGPT](https://openai.com/index/memory-and-new-controls-for-chatgpt/)
- [Cognition: Rebuilding Devin for Claude Sonnet 4.6](https://cognition.ai/blog/devin-sonnet-4-5-lessons-and-challenges)

### 研究（2023-2026）
- [Generative Agents: Interactive Simulacra of Human Behavior (Park et al. 2023)](https://arxiv.org/abs/2304.03442)
- [Reflexion: Language Agents with Verbal Reinforcement Learning (Shinn et al. 2023)](https://arxiv.org/abs/2303.11366)
- [HippoRAG: Neurobiologically Inspired Long-Term Memory (Gutierrez et al. 2024)](https://arxiv.org/abs/2405.14831)
- [A-MEM: Agentic Memory for LLM Agents (Xu et al. NeurIPS 2025)](https://arxiv.org/abs/2502.12110)
- [Multi-Layered Memory Architectures (arXiv 2603.29194, March 2026)](https://arxiv.org/abs/2603.29194)
- [Memp: Exploring Agent Procedural Memory (Aug 2025)](https://arxiv.org/html/2508.06433v2)
- [LEGOMem: Modular Procedural Memory for Multi-agent LLM (Oct 2025)](https://arxiv.org/pdf/2510.04851)
- [Rethinking Memory Mechanisms of Foundation Agents (Feb 2026 survey)](https://arxiv.org/abs/2602.06052)
- [Position: Episodic Memory is the Missing Piece (arXiv 2502.06975)](https://arxiv.org/pdf/2502.06975)

### 安全、投毒與幻覺
- [HaluMem: Operation-Level Memory Hallucination Benchmark (Nov 2025)](https://arxiv.org/abs/2511.03506)
- [MINJA Memory Injection Attack (NeurIPS 2025)](https://openreview.net/forum?id=QVX6hcJ2um)
- [MemoryGraft Persistent Memory Compromise (Dec 2025)](https://arxiv.org/html/2512.16962v1)
- [Palo Alto Unit 42: Indirect prompt injection poisons AI long-term memory](https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/)
- [Multi-tenant AI Infrastructure: 5 Isolation Layers](https://medium.com/@isuruig/multi-tenant-ai-infrastructure-the-5-isolation-layers-that-determine-whether-your-customers-data-stays-separate-340aaeef4922)
- [The Day-30 Problem: agent memory drift](https://cipherbuilds.ai/blog/day-30-agent-memory-problem)

### 基礎設施
- [NVIDIA TTT-E2E: Reimagining LLM Memory (May 2026)](https://developer.nvidia.com/blog/reimagining-llm-memory-using-context-as-training-data-unlocks-models-that-learn-at-test-time/)
- [vLLM PagedAttention](https://docs.vllm.ai/en/latest/design/paged_attention/)
- [Anthropic Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

---

*下一篇：[Planning and Decomposition](06-planning-and-decomposition.md)*
