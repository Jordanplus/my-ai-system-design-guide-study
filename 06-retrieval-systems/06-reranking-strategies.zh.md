# Reranking 策略

Reranking 是檢索的第二階段，使用高精確度模型對一小組候選項（Top 50-100）重新計分。它是「高效搜尋」與「完美 grounding」之間的橋樑：第一階段檢索針對 recall 最佳化，reranking 則針對 precision 最佳化。如今在生產環境中主導市場的有三款 reranker（BGE-Reranker-v2-m3、Cohere Rerank 3、Voyage rerank-2），選擇取決於成本模型、延遲尾端（latency tail）、語言涵蓋範圍，以及你是否需要可自行託管的權重。

## 目錄

- [為何需要 Reranking](#why-reranking)
- [Reranking 架構](#reranking-architectures)
- [Reranking 模型](#reranking-models)
- [實作模式](#implementation-patterns)
- [何時該 Rerank](#when-to-rerank)
- [基於 LLM 的 Reranking](#llm-based-reranking)
- [SLM 蒸餾](#slm-distillation)
- [生產環境考量](#production-considerations)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 為何需要 Reranking

### 品質落差

| 階段 | 模型 | 速度 | 品質 |
|-------|-------|-------|---------|
| Embedding 檢索 | Bi-encoder | 快（ms） | 良好 |
| Reranking | Cross-encoder | 慢（10-100ms） | 更佳 |

**為何會有落差：**
- Bi-encoder 各自獨立對 query 與 document 進行 embedding
- Cross-encoder 共同處理 query 與 document
- 共同處理能捕捉到 bi-encoder 遺漏的互動關係

### 範例

```
Query: "How to configure CUDA memory"

Document 1: "Configure GPU memory using CUDA_VISIBLE_DEVICES..."
Document 2: "Memory management in CUDA applications..."
Document 3: "Configure RAM allocation for machine learning..."

Bi-encoder scores (cosine similarity):
- Doc 1: 0.72
- Doc 2: 0.75  <-- Ranked first (wrong)
- Doc 3: 0.71

Cross-encoder scores (relevance):
- Doc 1: 0.91  <-- Ranked first (correct)
- Doc 2: 0.67
- Doc 3: 0.42
```

Cross-encoder 看得出 query 中的「CUDA memory」與 Doc 1 中的「GPU memory...CUDA」相關。

---

## Reranking 架構

### Bi-Encoder 與 Cross-Encoder

**Bi-Encoder（第一階段）：**
```
Query --> Encoder --> Query Embedding -+
                                      +-> Similarity
Document --> Encoder --> Doc Embedding +
```
- 每份 document 為 O(1)（embedding 已事先計算）
- 無法看見 query 與 document 之間的互動

**Cross-Encoder（Reranking）：**
```
[Query, Document] --> Encoder --> Relevance Score
```
- 每個 query 為 O(n)（需處理每個候選項）
- 能看見完整的 query-document 上下文
- 運用 **Attention Mechanism** 比較 query 中特定字詞如何改變 document 中字詞的意義（late interaction）

### 兩階段管線

生產環境的檢索採用兩階段漏斗：

```
+----------------------------------------------------------------+
|  STAGE 1: Retrieval (Bi-Encoder)                                |
|                                                                 |
|  Query --> Embed --> Top-K candidates (K=100)                   |
|  Scale: Search 1 Billion docs. Cost: Low (ms).                 |
+----------------------------+-----------------------------------+
                             |
                             v
+----------------------------------------------------------------+
|  STAGE 2: Reranking (Cross-Encoder)                             |
|                                                                 |
|  For each candidate:                                            |
|    score = reranker([query, candidate])                         |
|  Scale: Search Top 100 docs. Cost: High (10-100ms).            |
|                                                                 |
|  Return Top-N by reranker score (N=5-10)                        |
+----------------------------------------------------------------+
```

### 多階段管線

針對非常龐大的語料庫：

```
Stage 1: Sparse (BM25)      -> Top 1000
Stage 2: Dense (Bi-encoder) -> Top 100
Stage 3: Cross-encoder      -> Top 10
```

每個階段都以速度換取準確度。

---

## Reranking 模型

### Cross-Encoder 模型

| 模型 | 大小 | 語言 | 品質 |
|-------|------|-----------|---------|
| ms-marco-MiniLM-L-6 | 22M | English | 良好 |
| bge-reranker-base | 278M | English | 非常好 |
| **bge-reranker-v2-m3** | 568M | Multilingual | 極佳 |
| Cohere Rerank v3 | API | Multilingual | 極佳 |
| Jina Reranker v2 | Various | Multilingual（8k+ tokens） | 非常好 |

**「Lost in the Middle」的修正**：reranker 經過訓練，無論相關資訊位於 chunk 的哪個位置都會優先處理，確保「中間」的資料在送進最終 LLM 前能被正確計分。

### 使用 Cross-Encoder

```python
from sentence_transformers import CrossEncoder

# Load model
reranker = CrossEncoder('BAAI/bge-reranker-base')

def rerank(query: str, documents: list[str], top_k: int = 5) -> list[tuple[str, float]]:
    # Create pairs
    pairs = [[query, doc] for doc in documents]

    # Score all pairs
    scores = reranker.predict(pairs)

    # Sort by score
    scored_docs = sorted(
        zip(documents, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return scored_docs[:top_k]
```

### Cohere Rerank

```python
import cohere

co = cohere.Client(api_key="...")

def cohere_rerank(
    query: str,
    documents: list[str],
    top_k: int = 5
) -> list[dict]:
    response = co.rerank(
        model="rerank-english-v3.0",
        query=query,
        documents=documents,
        top_n=top_k,
        return_documents=True
    )

    return [
        {
            "text": result.document.text,
            "score": result.relevance_score,
            "index": result.index
        }
        for result in response.results
    ]
```

### 模型選型指南

| 使用情境 | 推薦模型 | 備註 |
|----------|-------------------|-------|
| English、自行託管 | bge-reranker-base | 良好的平衡 |
| Multilingual | bge-reranker-v2-m3 | 最佳的開源選項 |
| 低延遲 | MiniLM-L-6 | 快 4 倍 |
| 最高品質 | Cohere Rerank v3 | API，大規模下成本高 |
| 大批次 | Jina Reranker | 良好的吞吐量 |
| 長 query（8k+） | Jina Reranker v2 | 可處理長上下文 |

---

## 實作模式

### 模式 1：基本 Reranking

```python
class RerankedRetriever:
    def __init__(
        self,
        vector_db,
        embedding_model,
        reranker,
        retrieval_k: int = 50,
        rerank_k: int = 5
    ):
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.reranker = reranker
        self.retrieval_k = retrieval_k
        self.rerank_k = rerank_k

    def search(self, query: str) -> list[Document]:
        # Stage 1: Retrieve candidates
        query_embedding = self.embedding_model.encode(query)
        candidates = self.vector_db.search(
            query_embedding,
            top_k=self.retrieval_k
        )

        # Stage 2: Rerank
        pairs = [[query, c.text] for c in candidates]
        scores = self.reranker.predict(pairs)

        # Combine and sort
        for candidate, score in zip(candidates, scores):
            candidate.rerank_score = score

        reranked = sorted(candidates, key=lambda x: x.rerank_score, reverse=True)
        return reranked[:self.rerank_k]
```

### 模式 2：批次 Reranking

```python
def batch_rerank(
    queries: list[str],
    candidates_per_query: list[list[str]],
    reranker,
    batch_size: int = 32
) -> list[list[tuple[str, float]]]:
    # Flatten all pairs
    all_pairs = []
    pair_mapping = []  # (query_idx, doc_idx)

    for q_idx, (query, candidates) in enumerate(zip(queries, candidates_per_query)):
        for d_idx, doc in enumerate(candidates):
            all_pairs.append([query, doc])
            pair_mapping.append((q_idx, d_idx))

    # Batch score
    all_scores = []
    for i in range(0, len(all_pairs), batch_size):
        batch = all_pairs[i:i + batch_size]
        scores = reranker.predict(batch)
        all_scores.extend(scores)

    # Reconstruct per-query results
    results = [[] for _ in queries]
    for (q_idx, d_idx), score in zip(pair_mapping, all_scores):
        results[q_idx].append((candidates_per_query[q_idx][d_idx], score))

    # Sort each query's results
    for i in range(len(results)):
        results[i].sort(key=lambda x: x[1], reverse=True)

    return results
```

### 模式 3：非同步 Reranking

```python
import asyncio

class AsyncReranker:
    def __init__(self, reranker, max_concurrent: int = 5):
        self.reranker = reranker
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def rerank_async(
        self,
        query: str,
        documents: list[str]
    ) -> list[tuple[str, float]]:
        async with self.semaphore:
            # Run reranking in thread pool
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                lambda: self.reranker.predict([[query, doc] for doc in documents])
            )
            return sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
```

---

## 何時該 Rerank

### 成本效益分析

| 因素 | 不使用 Reranking | 使用 Reranking |
|--------|-------------------|----------------|
| 延遲 | 50-100ms | 150-300ms |
| 品質（NDCG） | 0.65 | 0.78 |
| 複雜度 | 簡單 | 中等 |
| 成本 | 基準線 | +API 成本或 +運算 |

### 決策框架

**以下情況一律 rerank：**
- 品質至關重要（面向客戶、高風險）
- 檢索到的候選項分數相近
- query 複雜或包含多個部分
- 預算允許延遲增加

**以下情況略過 reranking：**
- 延遲預算非常吃緊（總計 <100ms）
- 檢索到的候選項排序已經明確
- 簡單的 query（單一詞彙查詢）
- 大規模下受成本限制

### 推論時間的取捨

| 階段 | 檢索（K） | Rerank（N） | 延遲 | 品質 |
|-------|---------------|------------|---------|---------|
| **Naive** | 5 | 0 | 50ms | 低 |
| **Standard** | 50 | 5 | 150ms | 高 |
| **Enterprise**| 200 | 20 | 500ms | 最高 |

**關鍵原則**：若你有 200ms 的預算，請在檢索花 50ms、在 reranking 花 150ms。對 Top 50 結果做 reranking 所帶來的 ROI，遠高於從 vector DB 多取一些 chunk。

### 最佳候選數量

在 reranking 之前要檢索多少候選項：

```python
def optimize_candidate_count(test_set, retriever, reranker):
    """Find optimal retrieval_k for reranking."""
    results = {}

    for retrieval_k in [10, 20, 50, 100, 200]:
        ndcg_scores = []
        latencies = []

        for query, relevant_docs in test_set:
            start = time.time()

            # Retrieve
            candidates = retriever.search(query, top_k=retrieval_k)

            # Rerank to top 5
            reranked = reranker.rerank(query, candidates, top_k=5)

            latency = time.time() - start
            latencies.append(latency)

            ndcg = compute_ndcg(reranked, relevant_docs)
            ndcg_scores.append(ndcg)

        results[retrieval_k] = {
            "ndcg": mean(ndcg_scores),
            "latency_p99": percentile(latencies, 99)
        }

    return results

# Typical findings:
# K=20:  NDCG 0.72, latency 120ms
# K=50:  NDCG 0.76, latency 180ms  <-- Often sweet spot
# K=100: NDCG 0.77, latency 280ms  <-- Diminishing returns
```

---

## 基於 LLM 的 Reranking

### 將 LLM 用作 Reranker

LLM 能對相關性計分，但成本高昂：

```python
def llm_rerank(
    query: str,
    documents: list[str],
    model: str = "gpt-4o-mini"
) -> list[tuple[str, float]]:
    prompt = f"""Rate the relevance of each document to the query.
Query: {query}

Documents:
{format_documents(documents)}

For each document, output a relevance score from 0-10.
Format: DOC_NUM: SCORE
"""

    response = llm.generate(prompt)
    scores = parse_scores(response)

    return sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
```

**優點：**
- 能處理複雜的相關性判斷
- 理解細微差異與上下文
- 不需另外維護一個模型

**缺點：**
- 大規模下成本高昂（為 cross-encoder 的 10-100 倍）
- 較慢（1-3s 對比 100ms）
- 非確定性

### Listwise 與 Pointwise 的 LLM Reranking

**Pointwise：** 各自獨立對每份 document 計分
```
For document: [doc text]
Query: [query]
Rate relevance 0-10: _
```

**Listwise：** 將所有 document 一起排序
```
Query: [query]
Rank these documents by relevance:
A: [doc1]
B: [doc2]
C: [doc3]
Output order: _
```

**Listwise 通常較佳**，因為 LLM 能直接比較各份 document。前沿模型（如 o1-mini 或 Sonnet 3.7）在這方面表現極為出色，但會增加 1-2s 的延遲。僅用於高風險的企業級搜尋（法律、醫療）。

### 針對大量 Document 的滑動視窗

```python
def sliding_window_rerank(
    query: str,
    documents: list[str],
    window_size: int = 10,
    step: int = 5
) -> list[str]:
    """Rerank many documents with LLM using sliding window."""
    ranked = list(range(len(documents)))

    for start in range(0, len(documents), step):
        window = ranked[start:start + window_size]

        # LLM ranks this window
        window_docs = [documents[i] for i in window]
        window_order = llm_listwise_rank(query, window_docs)

        # Update rankings
        for new_pos, old_idx in enumerate(window_order):
            ranked[start + new_pos] = window[old_idx]

    return [documents[i] for i in ranked]
```

---

## SLM 蒸餾

為了解決基於 LLM 的 reranking 所面臨的延遲問題，我們如今改用 **蒸餾後的小型語言模型（Distilled Small Language Models, SLMs）**。

- **流程**：取一個龐大的模型（例如 GPT-5.2），讓它對 100 萬組 pair 進行 reranking，再用這些標籤「蒸餾」出一個僅 0.1B 參數的微型模型。
- **結果**：你能在標準 CPU 查詢的延遲（< 10ms）下，取得龐大模型 95% 的 reranking 品質。
- **生產模式：** 平常使用 cross-encoder，當 reranking 分數信心度偏低時改用 LLM 作為後援。

---

## 生產環境考量

### 延遲最佳化

```python
class OptimizedReranker:
    def __init__(self, model_name: str, device: str = "cuda"):
        self.model = CrossEncoder(model_name, device=device)
        # Enable optimizations
        self.model.model.half()  # FP16

    def rerank(self, query: str, documents: list[str]) -> list[tuple[str, float]]:
        with torch.inference_mode():
            pairs = [[query, doc] for doc in documents]
            scores = self.model.predict(
                pairs,
                batch_size=32,
                show_progress_bar=False
            )
        return sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
```

**最佳化技巧：**
- FP16 推論：加速 2 倍
- 批次處理：攤平開銷
- ONNX 匯出：加速 1.5-2 倍
- TensorRT：加速 2-3 倍（NVIDIA）
- 模型蒸餾：加速 4 倍，但有品質取捨

### 快取 Reranker 結果

```python
class CachedReranker:
    def __init__(self, reranker, cache_ttl: int = 3600):
        self.reranker = reranker
        self.cache = TTLCache(maxsize=10000, ttl=cache_ttl)

    def rerank(self, query: str, documents: list[str]) -> list[tuple[str, float]]:
        # Cache key includes query and doc hashes
        key = self._make_key(query, documents)

        if key in self.cache:
            return self.cache[key]

        result = self.reranker.rerank(query, documents)
        self.cache[key] = result
        return result

    def _make_key(self, query: str, documents: list[str]) -> str:
        doc_hash = hashlib.sha256(
            "".join(sorted(documents)).encode()
        ).hexdigest()[:16]
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        return f"{query_hash}:{doc_hash}"
```

### 後援策略

```python
def rerank_with_fallback(
    query: str,
    candidates: list[Document],
    primary_reranker,
    timeout: float = 2.0
) -> list[Document]:
    try:
        # Try reranking with timeout
        result = timeout_call(
            primary_reranker.rerank,
            args=(query, candidates),
            timeout=timeout
        )
        return result
    except TimeoutError:
        # Fallback: return original order
        logger.warning("Reranker timeout, using original order")
        return candidates
    except Exception as e:
        logger.error(f"Reranker error: {e}")
        return candidates
```

---

## 面試問題

### Q：為何 Cross-Encoder 在本質上比 Bi-Encoder 更準確？

**強答案：**
Bi-Encoder 會在得知任何 query *之前*，就為一份 document 建立單一、靜態的向量表示。這會遺失文字中不同部分之間的特定關係。Cross-Encoder 則將 query 與 document 一併作為單一輸入 pair，並運用 **Attention Mechanism** 來比較兩者。它能看出 query 中特定字詞如何改變 document 中字詞的意義（late interaction），使得相關性計分遠比單純對兩個固定向量做數學相似度計算更為細緻。

**實務上：** 第一階段檢索使用 bi-encoder（速度），reranking 使用 cross-encoder（品質）。如此可兼得兩者之長。

### Q：你如何決定要對多少候選項做 rerank？

**強答案：**
這是品質與延遲之間的取捨：

**因素：**
- 每份 document 的 reranker 延遲
- 總延遲預算
- 品質提升曲線（通常呈遞減報酬）
- 第一階段檢索品質

**流程：**
1. 對每份 document 的 reranker 延遲做基準測試
2. 計算在延遲預算內的最大候選數量
3. 在不同 K 值下測試品質
4. 找出拐點（品質對比延遲）

**典型結果：**
- K=20-50 通常為最佳
- 超過 K=100 後，品質增益甚微
- 依第一階段檢索品質做調整

對於 200ms 的 reranking 預算、每份 document 4ms 的情況，我會對約 50 個候選項做 rerank。

### Q：你何時會採用基於 LLM 的 reranking？

**強答案：**
LLM reranking 在以下情況合理：

1. **複雜的相關性判斷：** query 需要理解細微差異、上下文或多跳（multi-hop）推理
2. **低流量：** 無法為訓練／託管一個 cross-encoder 找到充分理由
3. **要求最高品質：** 法律、醫療、安全攸關
4. **管線中已使用 LLM：** 邊際成本較低

**注意事項：**
- 大規模下成本高昂（為 cross-encoder 的 10-100 倍）
- 較慢（1-3s 對比 100ms）
- 非確定性
- 可能需要謹慎的 prompt engineering

**生產模式：** 平常使用 cross-encoder，當 reranking 分數信心度偏低時改用 LLM 作為後援。

### Q：你如何處理極長 query（例如整段文字）的 reranking？

**強答案：**
長 query 為 cross-encoder 帶來「Token Budget」問題，因為這類模型往往有 512 或 1024 token 的限制。常見的修正方式有 **Sliding Window Reranking** 或 **Query Summarization**。另一種做法是改用 **Jina-Reranker-v2** 這類能處理 8k+ tokens 的專門模型。先用一個快速、短上下文的模型做「First-Pass Rerank」，再用高上下文的 LLM 對 top 5 候選項做「Second-Pass Rerank」也很常見。

---

## 參考資料

- Nogueira and Cho. "Passage Re-ranking with BERT" (2019)
- Nogueira et al. "Multi-Stage Document Ranking with BERT" (2019/2025 update)
- BAAI BGE Reranker: https://huggingface.co/BAAI/bge-reranker-base
- Cohere Rerank: https://docs.cohere.com/docs/rerank
- Sun et al. "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents" (2023)

---

*上一篇： [Hybrid Search](05-hybrid-search.md) | 下一篇： [GraphRAG](07-graph-rag.md)*
