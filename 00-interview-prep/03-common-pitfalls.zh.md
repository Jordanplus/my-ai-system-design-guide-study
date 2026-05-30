# AI 系統設計面試中的常見陷阱

本章涵蓋應試者在 AI 系統設計面試中經常犯的錯誤、這些錯誤為何會損害你的評價，以及如何避免它們。

## 目錄

- [架構陷阱](#architecture-pitfalls)
- [技術知識陷阱](#technical-knowledge-pitfalls)
- [溝通陷阱](#communication-pitfalls)
- [面試策略陷阱](#interview-strategy-pitfalls)
- [AI 特有陷阱](#ai-specific-pitfalls)
- [自我檢視清單](#checklists-for-self-review)

---

## 架構陷阱

### 陷阱 1：略過資料管線

**問題所在：**
應試者鉅細靡遺地設計推論路徑，卻幾乎不提資料是如何進入系統的。

**為何重要：**
資料品質決定 AI 系統品質。如果文件擷取管線產出的是垃圾 chunk，再漂亮的 RAG 架構也是枉然。

**面試官會注意到：**
- 沒有提到文件如何被處理
- 假設 embedding 會憑空出現
- 忽略更新與刪除

**較佳做法：**
```
"Before discussing retrieval, let me walk through the data pipeline:

1. Document ingestion: File upload, API integration, crawler
2. Preprocessing: Format conversion, cleaning, metadata extraction
3. Chunking: [Strategy] based on document structure
4. Embedding: Batch processing with [model]
5. Indexing: Upsert to vector database with metadata
6. Updates: Incremental re-indexing on document changes"
```

---

### 陷阱 2：一體適用的模型選擇

**問題所在：**
應試者表示所有事情都會使用 GPT-4（或任何單一模型）。

**為何重要：**
不同任務有不同需求。用前沿模型來做分類是浪費；用小模型來做複雜推理則會失敗。

**面試官會注意到：**
- 沒有討論成本影響
- 沒有考量延遲需求
- 沒有模型 cascade 或路由

**較佳做法：**
```
"Model selection varies by task:

- Intent classification: Fine-tuned BERT or GPT-4o-mini
- Simple responses: Claude Haiku or GPT-4o-mini  
- Complex reasoning: GPT-4o or Claude 3.5 Sonnet
- Code generation: Claude 3.5 Sonnet or Codestral

I would implement a router that classifies query complexity 
and routes to the appropriate model. This typically reduces 
costs 60-70% with minimal quality impact."
```

---

### 陷阱 3：忽略評估層

**問題所在：**
應試者描述了如何建構系統，卻沒說明如何得知它是否能運作。

**為何重要：**
AI 系統會以難以察覺的方式失效。沒有評估，你會交付有瑕疵的系統，且永遠無法偵測到品質劣化。

**面試官會注意到：**
- 沒有提到測試集
- 沒有定義品質指標
- 沒有針對生產環境問題的監控

**較佳做法：**
```
"Evaluation has three layers:

1. Offline: Golden test set evaluated on every change
   - Retrieval: Precision@5, Recall@5, MRR
   - Generation: Faithfulness, relevance (RAGAS)
   - End-to-end: Answer correctness vs ground truth

2. Online: Sampled evaluation in production
   - LLM-as-judge on 5% of requests
   - User feedback (thumbs up/down)
   - Completion rate for task-oriented queries

3. Alerting: Automated detection
   - Quality score drops below threshold
   - Latency exceeds SLA
   - Error rate spikes"
```

---

### 陷阱 4：低估多租戶的複雜度

**問題所在：**
應試者把多租戶 RAG 當成只是加上一個「tenant_id」欄位而已。

**為何重要：**
多租戶 AI 系統在資料外洩、隔離與公平資源分配方面有其獨特的失效模式。

**面試官會注意到：**
- 在檢索後才做過濾（重大警訊）
- 沒有討論快取隔離
- 沒有考量吵鬧鄰居（noisy neighbor）問題

**較佳做法：**
```
"Multi-tenancy for RAG is harder than traditional systems:

1. Retrieval isolation: Filter BEFORE retrieval at the database level
   WRONG: retrieve(query, top_k=100) then filter by tenant
   RIGHT: retrieve(query, top_k=10, filter={tenant_id: X})

2. Context isolation: Never mix tenants in LLM context

3. Cache isolation: Scope all cache keys by tenant
   cache_key = f'{tenant_id}:{query_hash}'

4. Embedding isolation: Consider tenant-specific embedding spaces
   for highest security requirements

5. Audit: Log tenant context for all operations

I would also run regular isolation tests with adversarial 
queries designed to probe for cross-tenant leakage."
```

---

### 陷阱 5：沒有優雅降級

**問題所在：**
當 LLM 供應商當機、被限流或回傳錯誤時，系統沒有任何 fallback。

**為何重要：**
LLM 供應商會發生服務中斷。速率限制會被觸及。失效處理正是區分「生產就緒」與「原型」的關鍵。

**面試官會注意到：**
- 沒有提到 fallback
- 沒有重試策略
- 單一供應商依賴

**較佳做法：**
```
"Reliability layers:

1. Retry with backoff: Transient errors get retried
   - Exponential backoff with jitter
   - Max 3 attempts

2. Fallback providers: If primary fails, try secondary
   - OpenAI → Anthropic → local model
   - Abstract the interface to enable swapping

3. Cached responses: Return cached results for known queries
   - Exact match cache for repeated questions
   - Semantic cache for similar questions

4. Graceful degradation: Partial functionality on failure
   - Retrieval fails → return direct LLM response with disclaimer
   - LLM fails → return relevant chunks without synthesis

5. Circuit breaker: Fail fast when provider is degraded
   - Prevents cascading latency issues"
```

---

## 技術知識陷阱

### 陷阱 6：混淆 embedding 與 generation 模型

**問題所在：**
應試者談到用 embedding 模型來生成文字，或把 generation 當成檢索。

**應知概念：**
- **Embedding 模型：** 將文字映射為向量。用於搜尋／檢索。
- **Generation 模型：** 根據 prompt 產生文字。用於回應。

**兩者如何銜接：**
RAG 使用 embedding 模型進行檢索，然後將檢索到的 chunk 傳給 generation 模型。

---

### 陷阱 7：誤解 context window

**問題所在：**
- 假設 128K context 就代表 128K token 的有用脈絡
- 沒有把 system prompt、檢索到的 chunk 與對話歷史納入計算
- 忽略「lost in the middle」現象

**應知概念：**
- Context window 是上限，而非目標
- 注意力對中段內容會劣化
- 實務上的有用脈絡遠小於上限

**較佳的表達框架：**
```
"While GPT-4o supports 128K tokens, I design for much smaller effective context:

- System prompt: ~500 tokens
- Retrieved context: 3-5 chunks × 500 tokens = 1.5-2.5K
- Conversation history: Last 5 turns × 300 tokens = 1.5K
- Buffer for output: ~2K

Total active context: ~7K tokens, well below limit.

This keeps the model focused on relevant information and 
avoids the lost-in-the-middle problem documented in Liu et al."
```

---

### 陷阱 8：不了解 token 經濟學

**問題所在：**
應試者在討論功能時，並不了解其成本影響。

**應知概念：**
- 計價是以 token 計算，輸入與輸出往往採不同定價
- 對多數供應商而言，輸出 token 的成本是輸入 token 的 2-4 倍
- 串流（streaming）並不會改變成本

**快速參考（2025 年 12 月，請自行核實最新資訊）：**

| 模型 | 輸入/1M | 輸出/1M |
|-------|----------|-----------|
| GPT-4o | $2.50 | $10 |
| GPT-4o-mini | $0.15 | $0.60 |
| Claude 3.5 Sonnet | $3 | $15 |
| Claude 3.5 Haiku | $0.25 | $1.25 |
| Gemini 1.5 Pro | $1.25 | $5 |

**成本計算範例：**
```
10,000 queries/day
Average: 2K input tokens, 500 output tokens
Model: GPT-4o

Daily cost = 10K × (2K × $2.50/1M + 500 × $10/1M)
          = 10K × ($0.005 + $0.005)
          = 10K × $0.01
          = $100/day = $3K/month
```

---

### 陷阱 9：對 RAG 元件的理解流於表面

**問題所在：**
應試者能列出各個元件（chunking、embedding、檢索、生成），卻無法說明每個元件內部的取捨。

**對 chunk 期待的深度：**
- 為什麼要分 chunk？（脈絡上限、檢索精準度）
- Chunk 大小的取捨？（較小＝更精準，較大＝更多脈絡）
- Overlap 的目的？（避免在邊界處遺失脈絡）
- 何時使用語意分塊（semantic chunking）？（結構多變的複雜文件）

**對檢索期待的深度：**
- 為什麼要用混合搜尋（hybrid search）？（dense 擅長語意，sparse 擅長關鍵字）
- 什麼是 reranking？（兩階段：先快速召回，再精準排序）
- 如何處理沒有結果的情況？（fallback 策略）

---

### 陷阱 10：把 prompt 當成魔法

**問題所在：**
應試者含糊帶過「然後我們就 prompt 模型去……」，卻不討論 prompt engineering。

**面試官想看到的：**
- Prompt 結構（system、context、user）
- 指令的清晰度
- 輸出格式的明確規範
- 視情況使用 few-shot 範例
- 對邊界情況的防禦

**較佳做法：**
```
"The generation prompt has this structure:

SYSTEM:
You are a support assistant for [Product]. Answer questions 
using ONLY the provided context. If the context does not 
contain the answer, say 'I don't have information about that.'
Always cite the source document.

CONTEXT:
[Retrieved chunks with source metadata]

USER:
[User's question]

I specify the output format explicitly and use few-shot 
examples for complex response structures. For this use case, 
I also include negative examples showing when to abstain."
```

---

## 溝通陷阱

### 陷阱 11：自說自話、缺乏互動

**問題所在：**
應試者一口氣講了 10-15 分鐘，都沒有和面試官確認。

**為何重要：**
面試是對話。自說自話會錯失面試官在意什麼的訊號。

**較佳做法：**
每 3-5 分鐘確認一次：
- 「我應該深入講檢索，還是接著講生成？」
- 「在我深入細節之前，這個架構合理嗎？」
- 「有沒有哪個元件是你希望我特別著重的？」

---

### 陷阱 12：沒有先帶出結構

**問題所在：**
應試者一開口就講，卻沒有先示意自己會涵蓋哪些內容。

**為何重要：**
面試官心中有一套思維模型。如果他們無法把你的回答對應到自己的預期，你會顯得雜亂無章。

**較佳做法：**
先帶出一張路線圖：
```
"I will structure my answer in four parts:
1. High-level architecture
2. Deep dive on the RAG pipeline
3. Scaling and reliability
4. Evaluation approach

Let me start with the high-level architecture..."
```

---

### 陷阱 13：丟出技術術語卻不解釋

**問題所在：**
應試者拋出像「PagedAttention」或「GQA」這樣的術語卻不解釋。

**為何重要：**
如果面試官不認識這個術語，你會顯得像在賣弄名詞。如果他們認識，可能會追問你答不出來的問題。

**較佳做法：**
在引入術語時附上簡短說明：
```
"I would use vLLM which implements PagedAttention. 
This manages the KV cache like virtual memory, reducing 
fragmentation and enabling higher throughput."
```

---

### 陷阱 14：為錯誤答案辯護

**問題所在：**
當面試官暗示某個做法是錯的，應試者卻變本加厲地堅持，而不重新考量。

**為何重要：**
固執是一個警訊。能虛心受教是很有價值的特質。

**較佳做法：**
```
Interviewer: "What about the case where..."
You: "That is a good point. I had not considered [X]. 
Let me revise my approach..."
```

---

## 面試策略陷阱

### 陷阱 15：解決了另一個問題

**問題所在：**
應試者對某項特定技術過於興奮，於是針對那項技術來設計，而不是針對題目所述的需求。

**範例：**
題目要求設計一個簡單的問答系統，應試者卻設計了一個具備自主研究能力的複雜多代理（multi-agent）系統。

**較佳做法：**
針對需求來設計，再提出延伸方案：
```
"This design meets the core requirements. If we wanted to 
extend it to handle more complex multi-step queries, we 
could add an agent layer, but I would not start there."
```

---

### 陷阱 16：沒有管理時間

**問題所在：**
應試者花了 20 分鐘在架構上，結果沒有時間談評估、可靠性或擴展。

**較佳做法：**
明確分配時間：
- 釐清需求：3-5 分鐘
- 高層次設計：5-7 分鐘
- 深入探討：10-15 分鐘
- 評估／可靠性：5-7 分鐘
- 提問／收尾：3-5 分鐘

留意時鐘並隨之調整。

---

### 陷阱 17：不畫圖

**問題所在：**
應試者僅以口頭描述架構，而不繪製圖表。

**為何重要：**
視覺化溝通更為清晰，也展現出你能與利害關係人溝通的能力。

**較佳做法：**
邊講解邊畫出方塊與箭頭。清楚標示。在整段討論中把圖表當作參照基準。

---

## AI 特有陷阱

### 陷阱 18：把 AI 元件當成黑盒子

**問題所在：**
應試者把「呼叫 LLM」視為一個原子操作，而不了解其內部發生了什麼。

**對資深職位的期待：**
- 了解 prefill 與 decode 階段
- 知道哪些因素會影響延遲（TTFT 與 TPS）
- 了解 KV cache 的影響
- 留意 batching 的效應

---

### 陷阱 19：忽略幻覺（hallucination）風險

**問題所在：**
應試者設計的系統盲目信任 LLM 的輸出。

**為何重要：**
幻覺是 LLM 與生俱來的特性。生產系統必須加以處理。

**較佳做法：**
```
"Hallucination mitigation has multiple layers:

1. Retrieval grounding: Answer from context only
2. Citation enforcement: Every claim cites a source
3. Abstention: Model says 'I don't know' when appropriate
4. Output validation: Check for impossible claims
5. Confidence display: Show users when to verify"
```

---

### 陷阱 20：把安全當成事後補強

**問題所在：**
安全方面的考量擺到最後才談，甚至完全沒談。

**為何重要：**
AI 系統有新型態的攻擊面（prompt injection、資料外洩）。安全必須在設計階段就納入。

**較佳做法：**
將安全織入設計之中：
```
"For the retrieval layer, I use metadata filtering at the 
database level to ensure tenant isolation. The system prompt 
uses instruction hierarchy to resist injection. Output 
passes through a content filter before reaching the user."
```

---

## 自我檢視清單

### 面試前

- [ ] 複習過 RAG 架構模式
- [ ] 了解目前的模型定價（概略即可）
- [ ] 能說明分塊（chunking）策略
- [ ] 了解 embedding 與 generation 的差異
- [ ] 知道常見的評估指標
- [ ] 能討論至少一種 vector database
- [ ] 了解多租戶的挑戰
- [ ] 能討論 prompt engineering 技巧

### 面試中

- [ ] 問了釐清需求的問題
- [ ] 闡明了優先順序與取捨
- [ ] 畫了一張圖
- [ ] 提到了評估做法
- [ ] 討論了失效模式
- [ ] 處理了安全／隔離議題
- [ ] 和面試官做了確認
- [ ] 在各段落之間管理好時間

### 每一段落結束後

- [ ] 我有解釋「為什麼」，而不只是「做什麼」嗎？
- [ ] 我有提到取捨嗎？
- [ ] 我在適用之處有使用具體數字嗎？
- [ ] 我有避免不必要的複雜度嗎？

---

*另見：[Question Bank](01-question-bank.md) | [Answer Frameworks](02-answer-frameworks.md) | [Whiteboard Exercises](04-whiteboard-exercises.md)*
