# 大規模生產級 RAG

生產級 RAG 已經不再是一個週末就能搞定的小專案。它是一套分散式系統，包含檢索流水線、快取層、路由邏輯、自我修正迴圈、多租戶隔離以及成本控制，而且全都得在嚴格的延遲 SLA 之下運作。當 RAG 在生產環境中失敗時，大約有 73% 的故障出在檢索而非生成，因此那些成功的企業部署，會把知識來源（而非模型）視為首要的投資重點。

## 目錄

- [RAG 與長上下文的取捨](#rag-vs-long-context)
- [查詢路由與分類](#query-routing)
- [RAG 的語意快取](#semantic-caching)
- [多索引策略](#multi-index)
- [RAG 流水線最佳化](#pipeline-optimization)
- [Corrective RAG：自我檢查式檢索](#corrective-rag)
- [自適應檢索](#adaptive-retrieval)
- [成本最佳化模式](#cost-optimization)
- [故障模式與除錯](#failure-modes)
- [監控與告警](#monitoring)
- [擴展至數百萬份文件](#scaling)
- [多租戶 RAG 隔離](#multi-tenant)
- [真實世界架構範例](#architectures)
- [系統設計面試切入點](#interview)
- [參考資料](#references)

---

## RAG 與長上下文的取捨

如今每個主流前沿模型家族都已支援 100 萬以上 token 的上下文視窗（Claude Opus 4.7、Claude Sonnet 4.6、GPT-5.5、Gemini 3.1 Pro、Qwen 3.6 Plus、Llama 4 Maverick），問題已經不再是「該用 RAG 還是長上下文？」，而是「各自在什麼時候勝出？」

### 決策矩陣

```
                    Small Corpus           Large Corpus
                    (<100K tokens)         (>1M tokens)
                 +---------------------+---------------------+
  Static Data    |  Long Context Wins  |  RAG Required       |
  (rarely        |  - Stuff it all in  |  - Can't fit in     |
   changes)      |  - Simpler arch     |    context window   |
                 |  - No index needed  |  - Index + retrieve |
                 +---------------------+---------------------+
  Dynamic Data   |  Hybrid Approach    |  RAG Required       |
  (updates       |  - Cache context    |  - Incremental      |
   frequently)   |  - Invalidate on    |    indexing          |
                 |    change           |  - Real-time updates |
                 +---------------------+---------------------+
  Multi-User     |  RAG Preferred      |  RAG Required       |
  (per-user      |  - Personalized     |  - Tenant isolation  |
   data)         |    retrieval        |  - Access control    |
                 +---------------------+---------------------+
```

### 正面交鋒比較

| 面向 | RAG | 長上下文（1M tokens） |
|-----------|-----|--------------------------|
| **平均查詢成本** | ~$0.0001 | ~$0.10 |
| **平均延遲（p50）** | ~1s | ~30-45s |
| **特定事實的精確度** | 高（精準檢索） | 在中段位置會劣化 |
| **跨文件綜整** | 弱（上下文有限） | 強（能看見全部內容） |
| **語料規模上限** | 無限 | ~1M tokens |
| **資料新鮮度** | 數分鐘（增量索引） | 需要完整重新載入 |
| **1000 QPS 時的成本** | ~$100/天 | ~$100,000/天 |

### 「迷失在中段（Lost in the Middle）」問題

LLM 並不會在整個上下文視窗中均勻地分配注意力。相較於放在開頭或結尾的資訊，位於長上下文中段的資訊會出現超過 30% 的準確度劣化。RAG 完全迴避了這個問題，因為它只把最相關的 chunk 放進一段簡短、聚焦的上下文裡。

### 最佳實務：混合模式

致勝的架構會結合兩者：先用 RAG 從大型語料中檢索出最佳候選，再把這些候選載入長上下文視窗以進行跨文件推理。

```
  User Query
      |
      v
+------------------+     +-------------------+
|  RAG Retrieval   |---->|  Long Context     |
|  (Find top 20    |     |  Synthesis        |
|   from 10M docs) |     |  (Reason across   |
+------------------+     |   20 docs deeply) |
                          +-------------------+
                                  |
                                  v
                          Final Answer with
                          Cross-Doc Citations
```

**經驗法則**：如果你的語料能塞進上下文，「而且」你能承受其延遲，「而且」你能承受其成本，那就用長上下文。否則就用 RAG。對於大多數有成本與延遲限制的生產系統而言，RAG 仍然是正確的預設選擇。

---

## 查詢路由與分類

並非每個查詢都需要檢索。生產系統會對進來的查詢進行分類，並把它們路由到最佳的處理路徑。

### 四路徑路由器

```
                         User Query
                             |
                             v
                    +------------------+
                    |  Query Classifier |
                    |  (LLM or trained  |
                    |   classifier)     |
                    +--------+---------+
                             |
            +--------+-------+-------+--------+
            |        |               |        |
            v        v               v        v
        +------+ +--------+    +--------+ +--------+
        |Direct| |Simple  |    |Complex | |Agentic |
        | LLM  | |  RAG   |    |  RAG   | |  RAG   |
        +------+ +--------+    +--------+ +--------+
        "What    "What is      "Compare   "Analyze
        is 2+2?" our refund    Q3 vs Q4   all legal
                  policy?"     revenue    risks in
                               trends"    these 50
                                          contracts"
```

### 分類訊號

| 訊號 | Direct LLM | Simple RAG | Complex RAG | Agentic RAG |
|--------|-----------|------------|-------------|-------------|
| **需要私有資料** | 否 | 是 | 是 | 是 |
| **單跳（single-hop）即可回答** | 是 | 是 | 否 | 否 |
| **需要多個來源** | 否 | 否 | 是 | 是 |
| **需要推理鏈** | 否 | 否 | 可能 | 是 |
| **對時效敏感的資料** | 否 | 可能 | 可能 | 是 |

### 實作：輕量級路由器

```python
class QueryRouter:
    """Routes queries to the optimal retrieval strategy."""

    def __init__(self, classifier_model: str = "gpt-4o-mini"):
        self.classifier = classifier_model
        self.route_counts = Counter()  # for monitoring

    async def classify(self, query: str, user_context: dict) -> str:
        # Step 1: Rule-based fast path
        if self._is_trivial(query):
            return "direct_llm"

        # Step 2: Check if query references private/org data
        if not self._needs_retrieval(query, user_context):
            return "direct_llm"

        # Step 3: LLM-based complexity classification
        complexity = await self._assess_complexity(query)

        if complexity == "simple":
            return "simple_rag"
        elif complexity == "multi_hop":
            return "complex_rag"
        else:
            return "agentic_rag"

    def _is_trivial(self, query: str) -> bool:
        """Fast regex/keyword check for trivial queries."""
        trivial_patterns = [
            r"^(what is|define|explain)\s+\w+$",
            r"^(hi|hello|thanks|bye)",
        ]
        return any(re.match(p, query.lower()) for p in trivial_patterns)

    async def _assess_complexity(self, query: str) -> str:
        """Use a small, fast model to classify complexity."""
        prompt = f"""Classify this query's retrieval complexity:
        - "simple": needs one document lookup
        - "multi_hop": needs 2-3 lookups, comparison, or synthesis
        - "agentic": needs planning, tool use, or iterative search

        Query: {query}
        Classification:"""

        result = await llm_call(self.classifier, prompt, max_tokens=10)
        return result.strip().lower()
```

### 領域專屬路由

對於擁有多個知識領域的系統，在檢索之前先把查詢路由到正確的索引。

```python
# Rule-based domain routing
DOMAIN_RULES = {
    "revenue|sales|quota|ARR":     "financial_index",
    "policy|handbook|PTO|benefits": "hr_index",
    "API|endpoint|SDK|integration": "engineering_index",
    "compliance|GDPR|SOC2|audit":   "legal_index",
}

# Embedding-based domain routing (for ambiguous queries)
class DomainRouter:
    def __init__(self):
        self.domain_centroids = {}  # pre-computed per domain

    def route(self, query_embedding: list[float]) -> str:
        similarities = {
            domain: cosine_sim(query_embedding, centroid)
            for domain, centroid in self.domain_centroids.items()
        }
        return max(similarities, key=similarities.get)
```

---

## RAG 的語意快取

語意快取能辨識出某個新查詢在意義上與先前查詢實質相同，並重用快取的結果。生產系統回報，在調校得當的語意快取下，可達到最高 68% 的成本降低與 65 倍的延遲改善。

### 三層快取架構

```
  User Query
      |
      v
+---------------------+
| Layer 1: Exact Cache |  Hash(query) -> response
| (Redis/Memcached)    |  TTL: 1 hour
| Hit rate: ~15-25%    |  Latency: <5ms
+----------+----------+
           | miss
           v
+---------------------+
| Layer 2: Semantic    |  Embed(query) -> nearest neighbor
| Cache (Vector DB)    |  Threshold: cosine > 0.95
| Hit rate: ~20-35%    |  Latency: <50ms
+----------+----------+
           | miss
           v
+---------------------+
| Layer 3: Document    |  Cache retrieved chunks
| Cache               |  Skip re-embedding
| (saves embedding $) |  TTL: until doc changes
+----------+----------+
           | miss
           v
    Full RAG Pipeline
```

### 語意快取實作

```python
class SemanticCache:
    """Cache RAG responses by query semantic similarity."""

    def __init__(self, vector_store, similarity_threshold: float = 0.95):
        self.vector_store = vector_store
        self.threshold = similarity_threshold
        self.response_store = {}  # query_id -> cached response

    async def get(self, query: str) -> Optional[CachedResponse]:
        # Step 1: Exact match (fast path)
        exact_key = hashlib.sha256(query.encode()).hexdigest()
        if exact_key in self.response_store:
            return self.response_store[exact_key]

        # Step 2: Semantic match
        query_embedding = await embed(query)
        results = self.vector_store.search(
            query_embedding, top_k=1
        )

        if results and results[0].score >= self.threshold:
            cached_id = results[0].metadata["response_id"]
            cached = self.response_store.get(cached_id)
            if cached and not cached.is_expired():
                return cached

        return None

    async def put(
        self, query: str, response: str,
        sources: list[str], ttl_seconds: int = 3600
    ):
        query_embedding = await embed(query)
        response_id = str(uuid4())

        # Store the embedding for future similarity lookups
        self.vector_store.upsert(
            id=response_id,
            embedding=query_embedding,
            metadata={"response_id": response_id}
        )

        # Store the actual response
        self.response_store[response_id] = CachedResponse(
            response=response,
            sources=sources,
            created_at=time.time(),
            ttl=ttl_seconds,
        )
```

### 快取失效策略

| 策略 | 觸發條件 | 使用情境 |
|----------|---------|----------|
| **TTL-based（基於存活時間）** | 固定時間到期 | 一般查詢、新聞 |
| **Event-driven（事件驅動）** | 文件更新的 webhook | 知識庫 |
| **Version-tagged（版本標記）** | 文件版本不符 | 合規關鍵場景 |
| **Confidence-gated（信心門檻）** | 檢索分數過低 | 高波動領域 |

**關鍵守則**：永遠要把來源文件 ID 與回應一併快取。當任何來源文件被更新時，就讓所有引用到它的快取項目失效。

```python
# Webhook-based cache invalidation
@app.post("/webhook/document-updated")
async def on_document_updated(doc_id: str):
    # Find all cache entries that used this document
    affected = cache_index.find_by_source(doc_id)
    for entry in affected:
        semantic_cache.invalidate(entry.response_id)
    logger.info(f"Invalidated {len(affected)} cache entries for doc {doc_id}")
```

---

## 多索引策略

單一的整體式索引無法擴展。生產系統會依領域、租戶或文件類型來切分其向量索引，以提升檢索精確度與運維上的隔離性。

### 索引切分模式

```
Pattern 1: Per-Domain Indexes
+--------+  +--------+  +--------+  +--------+
|  Legal |  |   HR   |  |Finance |  |  Eng   |
| Index  |  | Index  |  | Index  |  | Index  |
+--------+  +--------+  +--------+  +--------+
    |            |            |           |
    +----------- +-----+------+-----------+
                       |
                 Query Router
                       |
                  User Query


Pattern 2: Per-Tenant Indexes (Silo Model)
+----------+  +----------+  +----------+
| Tenant A |  | Tenant B |  | Tenant C |
|  Index   |  |  Index   |  |  Index   |
| (Acme)   |  | (Globex) |  | (Wayne)  |
+----------+  +----------+  +----------+


Pattern 3: Shared Index with Metadata Filtering (Pool Model)
+-------------------------------------------+
|           Shared Vector Index              |
|  +-------+  +-------+  +-------+          |
|  | doc_1 |  | doc_2 |  | doc_3 |  ...     |
|  | t:A   |  | t:B   |  | t:A   |          |
|  +-------+  +-------+  +-------+          |
|                                            |
|  WHERE tenant_id = "A"  <-- filter         |
+-------------------------------------------+
```

### 何時使用各種模式

| 模式 | 隔離性 | 成本 | 運維複雜度 | 最適合 |
|---------|-----------|------|----------------------|----------|
| **Per-Domain（按領域）** | 中 | 中 | 中 | 擁有不同知識領域的內部工具 |
| **Per-Tenant Silo（按租戶獨立）** | 最強 | 高 | 高 | 企業級 SaaS、受監管產業 |
| **Shared Pool（共享池）** | 最弱 | 低 | 低 | 中小企業 SaaS、對成本敏感的產品 |
| **Hybrid Bridge（混合橋接）** | 可設定 | 中 | 高 | 混合型客群（企業＋中小企業） |

### 階層式索引策略

對於非常大型的語料，採用兩層索引：用一個粗粒度的「摘要索引」做路由，再用細粒度的「chunk 索引」追求精確度。

```
  Query: "What is the refund policy for enterprise plans?"
      |
      v
+--------------------+
| Summary Index      |  Contains doc-level summaries
| (10K entries)      |  Fast, broad search
+--------+-----------+
         |
         | Top 3 matching docs identified
         v
+--------------------+
| Chunk Index        |  Contains 500-token chunks
| (2M entries)       |  Precise, targeted search
| Filtered to 3 docs |
+--------+-----------+
         |
         v
   Top 5 chunks -> LLM
```

---

## RAG 流水線最佳化

天真的循序式 RAG 流水線會在每一步都疊加延遲。生產級流水線會運用平行化、批次處理與非同步處理，以達成低於一秒的 SLA。

### 循序式 vs 最佳化流水線

```
SEQUENTIAL (Naive):
Query -> Embed(200ms) -> Search(150ms) -> Rerank(300ms) -> Generate(800ms)
Total: ~1450ms

OPTIMIZED (Parallel + Cached):
Query ----+---> Embed(200ms) ---> Vector Search(150ms) ---+
          |                                                |--> RRF Merge -> Rerank(300ms) -> Generate(800ms)
          +---> BM25 Keyword Search(100ms) ---------------+
          |
          +---> Cache Check(5ms) -- HIT --> Return cached (5ms total)

With cache miss: ~1050ms (embedding + keyword in parallel)
With cache hit:  ~5ms
```

### 平行檢索

```python
async def parallel_retrieve(
    query: str,
    query_embedding: list[float],
    indexes: list[str],
) -> list[Chunk]:
    """Run vector search, keyword search, and graph traversal in parallel."""

    tasks = [
        vector_search(query_embedding, index="main", top_k=20),
        bm25_search(query, index="main", top_k=20),
        # Optionally, graph-based retrieval for entity queries
        graph_search(query, max_hops=2, top_k=10),
    ]

    # All retrieval strategies execute concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out failures (graceful degradation)
    valid_results = [r for r in results if not isinstance(r, Exception)]

    # Merge with Reciprocal Rank Fusion
    merged = reciprocal_rank_fusion(valid_results, k=60)

    return merged[:20]  # top 20 after fusion
```

### 批次嵌入

當同時處理資料攝取或多個查詢時，將嵌入呼叫批次化以最大化 GPU 使用率。

```python
class EmbeddingBatcher:
    """Batch embedding requests to reduce per-call overhead."""

    def __init__(self, model: str, batch_size: int = 64, max_wait_ms: int = 50):
        self.model = model
        self.batch_size = batch_size
        self.max_wait = max_wait_ms / 1000
        self.queue: asyncio.Queue = asyncio.Queue()
        self._running = True

    async def embed(self, text: str) -> list[float]:
        """Submit a single text and wait for its embedding."""
        future = asyncio.Future()
        await self.queue.put((text, future))
        return await future

    async def _batch_loop(self):
        """Background loop that collects and processes batches."""
        while self._running:
            batch = []
            try:
                # Wait for at least one item
                item = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )
                batch.append(item)

                # Collect more items up to batch_size or max_wait
                deadline = time.time() + self.max_wait
                while len(batch) < self.batch_size and time.time() < deadline:
                    try:
                        item = await asyncio.wait_for(
                            self.queue.get(),
                            timeout=max(0, deadline - time.time())
                        )
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break

                # Process the batch
                texts = [t for t, _ in batch]
                embeddings = await embed_batch(self.model, texts)

                for (_, future), emb in zip(batch, embeddings):
                    future.set_result(emb)

            except asyncio.TimeoutError:
                continue
```

### 串流生成搭配提前檢索

在使用者打完字之前就開始檢索（偵測到停頓時），並在生成 token 產生的同時把它們串流出去。

```
Timeline:
0ms     User starts typing...
300ms   Pause detected -> trigger retrieval speculatively
500ms   User submits query
        Retrieval already 200ms in -> finishes at 650ms
650ms   Reranking begins
950ms   First generation token streams to user
1800ms  Full response complete

vs. without speculation:
0ms     User submits query
200ms   Embedding
350ms   Retrieval
650ms   Reranking
1500ms  First token
2300ms  Full response complete
```

---

## Corrective RAG：自我檢查式檢索

Corrective RAG（CRAG）在檢索與生成之間加入了一個驗證層。系統會在生成回應之前，先評估檢索到的文件是否真的能回答該查詢。

### CRAG 決策迴圈

```
  User Query
      |
      v
  Retrieve Top-K
      |
      v
+------------------+
| Relevance Grader  |  "Are these docs relevant to the query?"
| (LLM or trained   |
|  classifier)      |
+--------+---------+
         |
    +----+----+--------+
    |         |        |
    v         v        v
 CORRECT   AMBIGUOUS  WRONG
    |         |        |
    v         v        v
 Generate  Supplement  Discard &
 directly  with web    re-retrieve
           search      with reformulated
                       query
```

### 實作

```python
class CorrectiveRAG:
    """Self-correcting RAG pipeline with retrieval quality checks."""

    def __init__(self, max_corrections: int = 2):
        self.max_corrections = max_corrections

    async def answer(self, query: str) -> RAGResponse:
        attempts = 0
        current_query = query
        all_sources = []

        while attempts <= self.max_corrections:
            # Step 1: Retrieve
            chunks = await retrieve(current_query, top_k=10)

            # Step 2: Grade relevance
            grade = await self._grade_relevance(query, chunks)

            if grade.verdict == "correct":
                # High-confidence retrieval, generate directly
                return await self._generate(query, chunks, all_sources)

            elif grade.verdict == "ambiguous":
                # Supplement with additional search
                web_results = await web_search(current_query)
                chunks = self._merge_and_dedupe(chunks, web_results)
                return await self._generate(query, chunks, all_sources)

            else:  # "wrong"
                # Reformulate query and retry
                current_query = await self._reformulate(
                    original_query=query,
                    failed_query=current_query,
                    reason=grade.reason,
                )
                all_sources.extend(chunks)
                attempts += 1

        # Exhausted retries: generate best-effort with disclaimer
        return await self._generate_with_caveat(query, all_sources)

    async def _grade_relevance(
        self, query: str, chunks: list[Chunk]
    ) -> RelevanceGrade:
        """Use LLM to grade whether chunks answer the query."""
        prompt = f"""Given this query and retrieved documents, assess relevance.

Query: {query}

Documents:
{self._format_chunks(chunks)}

Respond with:
- verdict: "correct" (docs clearly answer the query)
- verdict: "ambiguous" (docs partially relevant, need supplementing)
- verdict: "wrong" (docs are irrelevant to the query)
- reason: brief explanation

JSON response:"""

        result = await llm_call(prompt, response_format="json")
        return RelevanceGrade(**json.loads(result))
```

### Self-RAG：評論型 token（Critic Tokens）

Self-RAG 以行內評論型 token 來延伸這個模式。模型會在每一步評估自己的輸出：

1. **[Retrieve]**：我應該檢索嗎？（是／否）
2. **[Relevant]**：檢索到的資訊相關嗎？（是／否）
3. **[Supported]**：我的答案有獲得證據支持嗎？（完全／部分／否）
4. **[Useful]**：這個答案實際上有用嗎？（1-5 分）

只要任何一項評論檢查未通過，模型就會繞回到較早的步驟。

---

## 自適應檢索

並非每個查詢都能從檢索中受益。自適應檢索會動態決定是否要檢索、要檢索多少，以及要從哪些來源檢索。

### 檢索決策樹

```
  User Query
      |
      v
  "Does this query need external knowledge?"
      |
  +---+---+
  |       |
  No      Yes
  |       |
  v       v
Direct   "How complex is the retrieval need?"
 LLM      |
answer  +-+--+---------+
        |    |         |
        v    v         v
     Single Multi    Agentic
      hop   hop      (planning
        |    |       required)
        v    v         |
     1 index 2-3       v
     top-5  indexes  Full agent
             top-10  loop
```

### 查詢複雜度估算器

```python
class AdaptiveRetriever:
    """Decides retrieval strategy based on query characteristics."""

    async def retrieve(self, query: str) -> RetrievalPlan:
        # Fast heuristics first
        if self._is_general_knowledge(query):
            return RetrievalPlan(strategy="none", reason="general knowledge")

        if self._is_simple_lookup(query):
            return RetrievalPlan(
                strategy="single_hop",
                indexes=["primary"],
                top_k=5,
            )

        # LLM-based assessment for ambiguous cases
        plan = await self._plan_retrieval(query)
        return plan

    def _is_general_knowledge(self, query: str) -> bool:
        """Check if query is about widely known facts."""
        general_indicators = [
            "what is", "who is", "define", "explain the concept",
        ]
        has_org_refs = bool(re.search(
            r"(our|my|the company|internal|proprietary)", query.lower()
        ))
        is_general = any(
            query.lower().startswith(g) for g in general_indicators
        )
        return is_general and not has_org_refs

    def _is_simple_lookup(self, query: str) -> bool:
        """Check if query can be answered with a single document."""
        single_hop_patterns = [
            r"what is (the|our) .+ policy",
            r"how (do I|to) .+",
            r"where (can I|do I) find",
        ]
        return any(re.search(p, query.lower()) for p in single_hop_patterns)
```

### 考量 Token 預算的檢索

依據可用的 token 預算與預期的回應複雜度，來調整檢索的投入程度。

```python
def plan_retrieval_budget(query: str, max_budget_tokens: int = 4000):
    """Allocate token budget across retrieval and generation."""

    complexity = estimate_complexity(query)  # 1-5 scale

    if complexity <= 2:
        # Simple query: small context, save tokens for generation
        return {"context_tokens": 1000, "generation_tokens": 3000, "top_k": 3}
    elif complexity <= 4:
        # Medium: balanced
        return {"context_tokens": 2500, "generation_tokens": 1500, "top_k": 8}
    else:
        # Complex: heavy retrieval, concise generation
        return {"context_tokens": 3500, "generation_tokens": 500, "top_k": 15}
```

---

## 成本最佳化模式

在規模化的情況下，RAG 成本會在嵌入、檢索、重排序與生成等環節上層層疊加。未經最佳化的系統，花費可能比實際所需多出 10 到 50 倍。

### 典型 RAG 查詢的成本拆解

```
Component         Cost per Query    % of Total    Optimization
-----------------------------------------------------------------
Embedding         $0.000005         ~1%           Batch + cache
Vector Search     $0.00001          ~2%           Index optimization
Reranking         $0.0001           ~15%          Skip for simple queries
LLM Generation    $0.0005-0.005     ~80%          Model tiering, caching
-----------------------------------------------------------------
Total (naive)     ~$0.001-0.006
Total (optimized) ~$0.0001-0.001    (5-10x reduction)
```

### 分層模型策略

```
                Query Complexity
                Low         Medium        High
             +----------+----------+----------+
 Generation  |  Small   |  Mid     |  Large   |
 Model       |  Model   |  Model   |  Model   |
             | (4o-mini)| (Claude  | (Claude  |
             |          |  Sonnet) |  Opus)   |
             | ~$0.0002 | ~$0.002  | ~$0.02   |
             +----------+----------+----------+

 Reranking   |  Skip    | Lightweight| Cross-  |
             |          | reranker   | encoder |
             +----------+----------+----------+
```

### 漸進式細節模式

先用最少量的檢索來回答。只有在使用者提出追問，或是信心偏低時，才升級處理。

```python
class ProgressiveRAG:
    """Start cheap, escalate only when needed."""

    async def answer(self, query: str, session: Session) -> str:
        # Level 1: Try semantic cache
        cached = await self.cache.get(query)
        if cached:
            return cached.response  # Cost: ~$0

        # Level 2: Fast retrieval + small model
        chunks = await retrieve(query, top_k=3)
        response = await generate(
            query, chunks, model="gpt-4o-mini"
        )

        # Check confidence
        if response.confidence > 0.85:
            await self.cache.put(query, response)
            return response.text  # Cost: ~$0.0003

        # Level 3: Deep retrieval + reranking + larger model
        chunks = await retrieve(query, top_k=15)
        reranked = await rerank(query, chunks, top_k=5)
        response = await generate(
            query, reranked, model="claude-sonnet-4-5"
        )

        if response.confidence > 0.7:
            await self.cache.put(query, response)
            return response.text  # Cost: ~$0.003

        # Level 4: Full agentic pipeline (expensive but thorough)
        return await self.agentic_pipeline.run(query)  # Cost: ~$0.05
```

### 成本護欄

```python
class CostGuard:
    """Prevent runaway costs in production RAG."""

    def __init__(self):
        self.daily_budget = 500.0  # $500/day
        self.per_query_limit = 0.10  # $0.10 max per query
        self.per_user_hourly = 1.0  # $1/user/hour

    async def check(self, user_id: str, estimated_cost: float) -> bool:
        daily_spent = await self.get_daily_spend()
        if daily_spent + estimated_cost > self.daily_budget:
            raise BudgetExceededError("Daily budget exhausted")

        user_spent = await self.get_user_hourly_spend(user_id)
        if user_spent + estimated_cost > self.per_user_hourly:
            raise RateLimitError("User hourly budget exceeded")

        if estimated_cost > self.per_query_limit:
            # Downgrade to cheaper strategy
            return False  # signals caller to use cheaper path

        return True
```

---

## 故障模式與除錯

生產級 RAG 系統具有會層層相乘的故障機率。在三個階段各有 95% 可靠度的情況下，整體可靠度會降至 0.95 x 0.95 x 0.95 = 0.86。理解各種故障模式至關重要。

### RAG 故障分類學

```
+------------------------------------------------------------------+
|                    RAG Failure Modes                               |
+------------------------------------------------------------------+
|                                                                    |
|  RETRIEVAL FAILURES          GENERATION FAILURES                   |
|  +---------------------+    +-------------------------+           |
|  | Missing documents   |    | Hallucination despite   |           |
|  | (not indexed)       |    | good context            |           |
|  +---------------------+    +-------------------------+           |
|  | Wrong chunks        |    | Ignoring retrieved      |           |
|  | (low precision)     |    | context                 |           |
|  +---------------------+    +-------------------------+           |
|  | Missed chunks       |    | Over-reliance on one    |           |
|  | (low recall)        |    | source                  |           |
|  +---------------------+    +-------------------------+           |
|  | Stale embeddings    |    | Citation fabrication    |           |
|  | (drift)             |    |                         |           |
|  +---------------------+    +-------------------------+           |
|                                                                    |
|  SYSTEM FAILURES             QUALITY FAILURES                      |
|  +---------------------+    +-------------------------+           |
|  | Index unavailable   |    | Chunking artifacts      |           |
|  +---------------------+    +-------------------------+           |
|  | Embedding service   |    | Context window overflow |           |
|  | timeout             |    +-------------------------+           |
|  +---------------------+    | Answer too vague        |           |
|  | Reranker OOM        |    | (over-hedging)          |           |
|  +---------------------+    +-------------------------+           |
|                                                                    |
+------------------------------------------------------------------+
```

### 切塊的 80% 法則

據估計，RAG 品質問題中有 80% 可追溯到切塊（chunking）決策，而非檢索或生成。常見的切塊故障：

- **Chunk 太小**：失去上下文。「它要 $200」——什麼東西要 $200？
- **Chunk 太大**：稀釋相關性。一個 2000-token 的 chunk 中，只有一句話真正相關。
- **邊界切割**：一個表格或清單被切分到兩個 chunk。
- **缺少 metadata**：chunk 缺乏標題、文件名稱或章節脈絡。

### 除錯檢查清單

```
When RAG quality drops, investigate in this order:

1. RETRIEVAL QUALITY (check first -- most common root cause)
   [ ] Log the query and retrieved chunks side by side
   [ ] Compute retrieval precision@K manually for 20 failing queries
   [ ] Check if relevant documents exist in the index at all
   [ ] Compare BM25 vs vector results -- if BM25 wins, embeddings are stale

2. CHUNKING QUALITY (check second)
   [ ] Sample 50 random chunks -- do they make sense in isolation?
   [ ] Check chunk boundaries for tables, lists, code blocks
   [ ] Verify metadata (title, section, doc_id) is present

3. RERANKING QUALITY (check third)
   [ ] Compare pre-rerank vs post-rerank orderings
   [ ] Check if reranker is pushing relevant results down

4. GENERATION QUALITY (check last)
   [ ] Test with perfect context (manually curated) -- does LLM still fail?
   [ ] Check for context window overflow (truncated chunks)
   [ ] Verify system prompt is not conflicting with retrieved context
```

### Agentic RAG 故障模式

Agentic RAG 引入了三種額外的故障模式：

1. **檢索抖動（Retrieval Thrash）**：代理人反覆檢索卻無法收斂到答案。追蹤記錄會顯示近乎重複的查詢，以及來回擺盪的搜尋詞。修法：限制在 3 至 5 次檢索迭代，並追蹤每個 session 內查詢的唯一性。

2. **工具風暴（Tool Storms）**：代理人在單一回合內過度呼叫工具。修法：設定每個查詢的工具呼叫上限與成本上限。

3. **上下文膨脹（Context Bloat）**：代理人累積了過多檢索到的 chunk，導致上下文視窗溢出。修法：實作一個滑動視窗，在上下文超過門檻時丟棄最舊的 chunk。

---

## 監控與告警

生產級 RAG 需要超越標準應用程式指標之外的專屬監控。如今大約有 60% 的新 RAG 部署從第一天起就納入系統化評估（相較於早期 RAG 世代「先上線、之後再評估」的模式，這是急遽的提升）。

### RAG 監控堆疊

```
+--------------------------------------------------------------------+
|                    RAG Observability Layers                          |
+--------------------------------------------------------------------+
|                                                                      |
|  L1: INFRASTRUCTURE          L2: PIPELINE                           |
|  +----------------------+   +-----------------------------+         |
|  | Latency (p50/p95/p99)|   | Retrieval precision@K      |         |
|  | Error rates          |   | Retrieval recall@K         |         |
|  | Throughput (QPS)     |   | Reranker effectiveness     |         |
|  | Cache hit rate       |   | Chunk utilization rate     |         |
|  | Index size/growth    |   | Context window fill rate   |         |
|  +----------------------+   +-----------------------------+         |
|                                                                      |
|  L3: QUALITY                 L4: BUSINESS                           |
|  +----------------------+   +-----------------------------+         |
|  | Faithfulness score   |   | User satisfaction (thumbs) |         |
|  | Answer relevancy     |   | Task completion rate       |         |
|  | Hallucination rate   |   | Escalation to human rate   |         |
|  | Citation accuracy    |   | Cost per successful query  |         |
|  +----------------------+   +-----------------------------+         |
|                                                                      |
+--------------------------------------------------------------------+
```

### 關鍵指標與告警

| 指標 | 目標 | 告警門檻 | 應對動作 |
|--------|--------|-----------------|--------|
| **p95 延遲** | <2s | >5s | 擴充檢索基礎設施 |
| **快取命中率** | >40% | <20% | 調校相似度門檻 |
| **檢索 Precision@5** | >0.7 | <0.5 | 重新評估切塊方式 |
| **忠實度（Faithfulness）** | >0.9 | <0.8 | 稽核生成 prompt |
| **幻覺率** | <5% | >10% | 收緊接地（grounding）prompt |
| **空檢索率** | <2% | >5% | 檢查索引覆蓋範圍 |
| **每次查詢成本** | <$0.005 | >$0.02 | 檢視模型分層策略 |

### 端到端追蹤記錄

每個查詢都應該產生一筆追蹤記錄，以單一 request ID 串連起所有流水線階段。

```python
@dataclass
class RAGTrace:
    request_id: str
    timestamp: datetime
    query: str
    route: str                    # "simple_rag", "complex_rag", etc.
    cache_hit: bool
    retrieval_latency_ms: float
    chunks_retrieved: int
    chunks_after_rerank: int
    rerank_latency_ms: float
    generation_model: str
    generation_latency_ms: float
    total_latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    faithfulness_score: float     # 0-1, computed async
    user_feedback: Optional[str]  # thumbs up/down

    def to_dict(self) -> dict:
        return asdict(self)
```

### 自動化品質抽樣

對生產查詢的抽樣執行離線評估，以在使用者察覺之前偵測到品質飄移。

```python
async def nightly_quality_check(sample_size: int = 200):
    """Sample production queries and evaluate RAG quality."""
    traces = await get_recent_traces(limit=sample_size)

    scores = []
    for trace in traces:
        # Re-run the query with evaluation
        eval_result = await evaluate_rag_response(
            query=trace.query,
            response=trace.response,
            retrieved_chunks=trace.chunks,
            metrics=["faithfulness", "relevancy", "context_precision"],
        )
        scores.append(eval_result)

    avg_faithfulness = mean([s.faithfulness for s in scores])
    avg_relevancy = mean([s.relevancy for s in scores])

    if avg_faithfulness < 0.85:
        alert("RAG faithfulness degraded", severity="high")
    if avg_relevancy < 0.70:
        alert("RAG relevancy degraded", severity="medium")

    publish_metrics("rag.nightly.faithfulness", avg_faithfulness)
    publish_metrics("rag.nightly.relevancy", avg_relevancy)
```

---

## 擴展至數百萬份文件

從數千份文件擴展到數百萬份，會在索引吞吐量、檢索延遲與索引管理上帶來挑戰。

### 擴展面向

```
Documents:   1K  -->  100K  -->  1M  -->  100M
             |        |         |         |
Chunks:      10K      1M        10M       1B
             |        |         |         |
Index Size:  50MB     5GB       50GB      5TB
             |        |         |         |
Strategy:    Single   Single    Sharded   Distributed
             Node     Node +    Index     Cluster +
                      Replicas             Tiered
```

### 規模化的攝取流水線

```
  Document Sources
  (S3, DBs, APIs, File Shares)
         |
         v
+-------------------+
| Ingestion Queue   |  (Kafka / SQS)
| - Deduplication   |
| - Priority queue  |
+--------+----------+
         |
    +----+----+----+----+
    |    |    |    |    |     Parallel workers
    v    v    v    v    v
  +--+ +--+ +--+ +--+ +--+
  |W1| |W2| |W3| |W4| |W5|  Parse + Chunk + Embed
  +--+ +--+ +--+ +--+ +--+
    |    |    |    |    |
    +----+----+----+----+
         |
         v
+-------------------+
| Vector DB Cluster |
| (Sharded by       |
|  doc_type or      |
|  tenant_id)       |
+-------------------+
```

### 分片（Sharding）策略

| 策略 | 運作方式 | 優點 | 缺點 |
|----------|-------------|------|------|
| **Hash-based（雜湊）** | shard = hash(doc_id) % N | 分佈均勻 | 需要跨分片查詢 |
| **Range-based（區間）** | 依日期區間分片 | 基於時間的查詢很快 | 分片大小不均 |
| **Domain-based（領域）** | 依文件類型分片 | 無需跨分片查詢 | 各領域不平衡 |
| **Tenant-based（租戶）** | 依 tenant_id 分片 | 完美隔離 | 許多小型分片 |

### 索引維護

在數百萬份文件的規模下，索引維護會成為關鍵的運維課題。

```python
class IndexMaintenanceScheduler:
    """Scheduled tasks for index health at scale."""

    async def run_daily(self):
        # 1. Detect and re-embed stale documents
        stale_docs = await find_docs_with_old_embeddings(
            older_than_days=90,
            embedding_model_version="v2"  # current is v3
        )
        if stale_docs:
            await enqueue_reembedding(stale_docs)

        # 2. Remove orphaned vectors (doc deleted but vector remains)
        orphans = await find_orphaned_vectors()
        if orphans:
            await delete_vectors(orphans)

        # 3. Compact and optimize indexes
        for shard in await list_shards():
            if shard.fragmentation_pct > 20:
                await compact_shard(shard.id)

        # 4. Verify index health
        for shard in await list_shards():
            health = await check_shard_health(shard.id)
            if not health.ok:
                alert(f"Shard {shard.id} unhealthy: {health.reason}")
```

### 用於檢索的唯讀副本

把讀取與寫入路徑分離開來，讓資料攝取永遠不會拖累查詢延遲。

```
  Ingestion Pipeline              Query Pipeline
        |                              |
        v                              v
  +-----------+     Replication   +-----------+
  |  Primary  | ----------------> |  Replica  |
  |  (Write)  |                   |  (Read)   |
  +-----------+                   +-----------+
                                  |  Replica  |
                                  |  (Read)   |
                                  +-----------+
                                  |  Replica  |
                                  |  (Read)   |
                                  +-----------+
```

---

## 多租戶 RAG 隔離

多租戶 RAG 是 SaaS 產品最常見的生產模式。把隔離做錯，就意味著資料會在租戶之間外洩，這是一個關鍵性的安全故障。

### 三種隔離模型

```
SILO MODEL (Strongest Isolation)
+----------+  +----------+  +----------+
| Tenant A |  | Tenant B |  | Tenant C |
| +------+ |  | +------+ |  | +------+ |
| |Index | |  | |Index | |  | |Index | |
| +------+ |  | +------+ |  | +------+ |
| |Cache | |  | |Cache | |  | |Cache | |
| +------+ |  | +------+ |  | +------+ |
+----------+  +----------+  +----------+
Cost: $$$$    Best for: Enterprise, Regulated Industries


POOL MODEL (Cost-Efficient)
+-------------------------------------------+
|              Shared Index                  |
|  [A] [B] [A] [C] [B] [A] [C] [B] [C]    |
|                                            |
|  Every query includes:                     |
|  WHERE tenant_id = ? (MANDATORY)           |
+-------------------------------------------+
Cost: $       Best for: SMB SaaS


BRIDGE MODEL (Hybrid)
+----------+  +----------------------------+
| Tenant A |  |     Shared Pool            |
| (Enterprise) | [B] [C] [D] [E] [F] [G]  |
| +------+ |  |                            |
| |Dedicated|  | WHERE tenant_id = ?       |
| |Index | |  +----------------------------+
| +------+ |
+----------+
Cost: $$      Best for: Mixed customer base
```

### 安全性：縱深防禦（Defense in Depth）

```python
class TenantIsolatedRetriever:
    """Enforces tenant isolation at every retrieval layer."""

    async def retrieve(
        self, query: str, tenant_id: str, user_id: str
    ) -> list[Chunk]:
        # Layer 1: Tenant ID is MANDATORY in every query
        if not tenant_id:
            raise SecurityError("tenant_id required for retrieval")

        # Layer 2: Validate user belongs to tenant
        if not await self.authz.user_in_tenant(user_id, tenant_id):
            raise AuthorizationError("User not in tenant")

        # Layer 3: Apply tenant filter at the database level
        chunks = await self.vector_db.search(
            query_embedding=await embed(query),
            filter={"tenant_id": {"$eq": tenant_id}},  # ALWAYS filtered
            top_k=10,
        )

        # Layer 4: Post-retrieval verification
        for chunk in chunks:
            assert chunk.metadata["tenant_id"] == tenant_id, \
                f"Cross-tenant leak detected: {chunk.id}"

        # Layer 5: Audit log
        await self.audit_log.record(
            action="retrieve",
            tenant_id=tenant_id,
            user_id=user_id,
            chunk_ids=[c.id for c in chunks],
        )

        return chunks
```

### 具租戶意識的攝取

租戶脈絡必須在流水線的每一個階段都被注入，從攝取一路貫穿到生成。

```
Document Upload (Tenant A)
        |
        v
  +---------------------+
  | Validate Ownership  |  Does this doc belong to Tenant A?
  +---------------------+
        |
        v
  +---------------------+
  | Chunk + Embed       |  Attach tenant_id to every chunk
  +---------------------+
        |
        v
  +---------------------+
  | Index with Metadata |  {"tenant_id": "A", "doc_id": "...", ...}
  +---------------------+
        |
        v
  +---------------------+
  | Invalidate Cache    |  Clear Tenant A's cache entries
  +---------------------+             for affected documents
```

### 防範吵鬧鄰居（Noisy Neighbor）

在 pool 模型中，某一個租戶的高度使用量可能會拖累所有租戶的效能。

```python
class TenantRateLimiter:
    """Per-tenant rate limiting and resource quotas."""

    def __init__(self):
        self.tenant_limits = {
            "free":       {"qps": 5,   "daily_queries": 500},
            "pro":        {"qps": 50,  "daily_queries": 10_000},
            "enterprise": {"qps": 200, "daily_queries": 100_000},
        }

    async def check(self, tenant_id: str, tier: str) -> bool:
        limits = self.tenant_limits[tier]

        current_qps = await self.redis.get(f"qps:{tenant_id}")
        if current_qps and int(current_qps) >= limits["qps"]:
            raise RateLimitError(f"QPS limit ({limits['qps']}) exceeded")

        daily_count = await self.redis.get(f"daily:{tenant_id}")
        if daily_count and int(daily_count) >= limits["daily_queries"]:
            raise RateLimitError("Daily query limit exceeded")

        # Increment counters
        pipe = self.redis.pipeline()
        pipe.incr(f"qps:{tenant_id}")
        pipe.expire(f"qps:{tenant_id}", 1)  # 1-second window
        pipe.incr(f"daily:{tenant_id}")
        pipe.expire(f"daily:{tenant_id}", 86400)
        await pipe.execute()

        return True
```

---

## 真實世界架構範例

### 範例 1：客戶支援 RAG

```
+------------------------------------------------------------------+
|                   Customer Support RAG System                     |
+------------------------------------------------------------------+
|                                                                    |
|  Customer Query                                                    |
|       |                                                            |
|       v                                                            |
|  +------------+    +---------+    +------------------+             |
|  | Query      |--->| Semantic|--->| Intent           |             |
|  | Normalizer |    | Cache   |    | Classifier       |             |
|  +------------+    +---------+    +--------+---------+             |
|                     (hit->skip)            |                       |
|                                   +--------+---------+             |
|                                   |                  |             |
|                                   v                  v             |
|                             +-----------+    +-------------+      |
|                             | Knowledge |    | Order/Acct  |      |
|                             | Base RAG  |    | Database    |      |
|                             | (articles,|    | (SQL lookup)|      |
|                             |  FAQs)    |    +-------------+      |
|                             +-----------+           |              |
|                                   |                 |              |
|                                   +--------+--------+              |
|                                            |                       |
|                                            v                       |
|                                   +------------------+             |
|                                   | Response Gen     |             |
|                                   | (with citations  |             |
|                                   |  + confidence)   |             |
|                                   +--------+---------+             |
|                                            |                       |
|                                   +--------+---------+             |
|                                   |                  |             |
|                                   v                  v             |
|                            confidence > 0.8    confidence < 0.8   |
|                            Auto-respond        Route to human      |
|                                                                    |
+------------------------------------------------------------------+

Scale: 50K articles, 2M customer interactions/month
Latency SLA: p95 < 3s
Cache hit rate: ~45%
Auto-resolution rate: ~60%
```

### 範例 2：企業知識平台

```
+------------------------------------------------------------------+
|              Enterprise Multi-Tenant Knowledge Platform            |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+                                              |
|  | Auth + Tenant    |                                              |
|  | Resolution       |                                              |
|  +--------+---------+                                              |
|           |                                                        |
|           v                                                        |
|  +------------------+                                              |
|  | Query Router     |                                              |
|  +--+----+----+-----+                                              |
|     |    |    |                                                     |
|     v    v    v                                                     |
|  +----+ +----+ +--------+                                          |
|  |Docs| |Wiki| |Tickets |  Per-domain indexes                     |
|  |Idx | |Idx | |Idx     |  (all tenant-filtered)                   |
|  +----+ +----+ +--------+                                          |
|     |    |    |                                                     |
|     +----+----+                                                     |
|          |                                                          |
|          v                                                          |
|  +------------------+                                              |
|  | Cross-Encoder    |                                              |
|  | Reranker         |                                              |
|  +--------+---------+                                              |
|           |                                                        |
|           v                                                        |
|  +------------------+     +-------------------+                    |
|  | Tiered LLM       |<--->| Permission Filter |                    |
|  | Generation        |     | (doc-level ACLs)  |                    |
|  +------------------+     +-------------------+                    |
|           |                                                        |
|           v                                                        |
|  +------------------+                                              |
|  | Response + Audit |                                              |
|  | Trail            |                                              |
|  +------------------+                                              |
|                                                                    |
+------------------------------------------------------------------+

Scale: 200 tenants, 10M documents total, 500K queries/day
Isolation: Bridge model (5 enterprise silos + shared pool)
Ingestion: Async via Kafka, ~50K docs/day
```

### 範例 3：法律文件分析

```
  User: "Summarize indemnification clauses across all vendor contracts"
      |
      v
  +---------------------+
  | Agentic RAG Planner |
  +---------------------+
      |
      | Plan: 1. Find all vendor contracts
      |        2. Extract indemnification clauses
      |        3. Synthesize comparison
      |
      v
  +---------------------+    +-------------------+
  | Step 1: Metadata    |--->| Filter: doc_type  |
  | Search              |    | = "vendor_contract"|
  +---------------------+    +-------------------+
      |                            |
      | 47 contracts found         |
      v                            v
  +---------------------+    +-------------------+
  | Step 2: Section     |--->| Filter: section   |
  | Retrieval           |    | = "indemnification"|
  +---------------------+    +-------------------+
      |                            |
      | 43 relevant sections       |
      v                            |
  +---------------------+         |
  | Step 3: Long Context|<--------+
  | Synthesis           |
  | (load 43 sections   |
  |  into 1M context)   |
  +---------------------+
      |
      v
  Comparative summary with
  per-contract citations
```

---

## 系統設計面試切入點

### Q：設計一套 RAG 系統，要在 500 個租戶之間每秒服務 10,000 次查詢，且 p99 延遲為 2 秒。

**優質回答：**

我會把這套系統設計成四層。

**第 1 層：路由與快取。** 一個查詢路由器會對每個進來的查詢進行分類（direct LLM、simple RAG、complex RAG）。一個三層快取（精確匹配、語意快取、文件快取）能處理約 40-50% 的流量。這代表實際只有 5,000-6,000 QPS 會真正打到檢索流水線。

**第 2 層：檢索。** 我會使用 bridge 隔離模型——前 20 大的企業租戶取得專屬索引（silo），其餘 480 個則共享一個套用強制 tenant_id 過濾的池化索引。檢索會平行執行混合搜尋（向量＋BM25），並用 Reciprocal Rank Fusion 來合併結果。向量資料庫叢集會依租戶層級分片，並複製副本以提升讀取吞吐量。

**第 3 層：生成。** 一個分層模型策略會把簡單查詢路由到小型模型，把複雜查詢路由到較大型模型。這樣能在維持困難查詢品質的同時，把平均成本壓低。按租戶的速率限制則可防範吵鬧鄰居。

**第 4 層：可觀測性。** 每個查詢都會產生一筆追蹤記錄，內含延遲拆解、檢索分數與成本。每晚的品質檢查會抽樣 500 個查詢，並評估忠實度與相關性。若 p95 延遲超過 3 秒，或忠實度跌破 0.85，就會觸發告警。

**成本估算**：在 10K QPS、假設 50% 快取命中率、且小型／大型模型呈 70/30 分配的情況下，每日成本大約是 $2,000-5,000 的生成費用，再加上 $500-1,000 的基礎設施費用。

### Q：當 RAG 系統檢索到不相關的文件，但 LLM 仍然生成出一個聽起來頭頭是道的答案時，你會如何處理這種情況？

**優質回答：**

這是最危險的 RAG 故障模式，因為它會產生聽起來信心十足、且立基於真實（但不相關）文件的幻覺。我會在三個環節上加以處理：

首先，在檢索階段，實作一個相關性評分器——一個分類器（或一次 LLM 呼叫），針對查詢為每個檢索到的 chunk 評分。如果所有 chunk 的分數都低於門檻，系統就應該要嘛升級到網路搜尋（Corrective RAG 模式），要嘛回應「我沒有足夠的資訊」，而不是從薄弱的上下文中硬生成。

其次，在生成階段，使用受約束的 prompt，指示模型在證據不足時明確說明。在輸出中納入信心分數，並把低信心的答案路由給人工審查。

第三，在監控方面，追蹤檢索分數與使用者回饋之間的關聯。如果在檢索分數很高的查詢上，使用者卻給出倒讚，那麼重排序器或切塊策略很可能就是根本原因。記錄完整的追蹤（查詢、檢索到的 chunk、生成的答案、使用者回饋），這樣你才能針對特定的故障案例進行除錯。

### Q：在查詢量沒有增加的情況下，你的 RAG 系統成本在過去一個月翻了三倍。你會如何診斷並修復？

**優質回答：**

我會依此順序進行調查：

首先，檢查 **快取命中率**。如果它下降了，就代表更多查詢打到了完整流水線。常見原因：語意快取門檻被改動、在資料更新後快取失效執行得過於激進，或是查詢分佈出現偏移、與已快取的查詢不再吻合。

其次，檢查 **模型路由分佈**。如果查詢分類器把更多查詢路由到昂貴的大型模型，光是這一點就能讓成本翻三倍。看看是查詢複雜度發生了偏移，還是分類器的行為產生了飄移。

第三，檢查 agentic RAG 路徑中的 **檢索抖動**。如果 Corrective RAG 迴圈重試得更頻繁（也許是因為嵌入過時或檢索品質劣化），那麼每個查詢都會做出多次檢索與生成呼叫。追蹤記錄會顯示每個查詢的平均迭代次數。

第四，檢查 **嵌入流水線**。如果文件被不必要地重新嵌入（重複攝取、缺乏去重），嵌入成本就會飆升。

修法取決於根本原因，但常見的介入手段有：調校語意快取門檻、為每個查詢實作成本上限以強制走更便宜的後備路徑、修正嵌入過時問題以減少 corrective 檢索迴圈，以及在攝取流水線中加入去重。

---

## 參考資料

- Asai et al. "Self-RAG: Learning to Retrieve, Generate, and Critique" (2024)
- Yan et al. "Corrective Retrieval Augmented Generation (CRAG)" (2024)
- Shi et al. "RAGRouter: Learning to Route Queries to Multiple RAL Models" (2025)
- Redis. "RAG at Scale: How to Build Production AI Systems in 2026"
- Anthropic. "1M Token Context Window General Availability" (March 2026)
- RAGAS Framework. "Context Precision, Recall, Faithfulness, and Relevancy Metrics"
- AWS. "Multi-Tenant RAG with Amazon Bedrock Knowledge Bases" (2025)
- Microsoft. "Design a Secure Multitenant RAG Inferencing Solution" (2025)

---

*下一篇：[15-rag-evaluation-and-testing.md](15-rag-evaluation-and-testing.md)*
