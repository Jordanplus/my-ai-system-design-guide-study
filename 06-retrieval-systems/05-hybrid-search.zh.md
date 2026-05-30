# Hybrid Search（混合檢索）

Hybrid search 結合了 dense（語意）與 sparse（關鍵字）檢索，以同時獲得兩者的優點。它是生產級 RAG 的基準做法：Elasticsearch 的 `rrf` retriever、OpenSearch hybrid search、Weaviate、Qdrant 以及 Azure AI Search 全都內建了原生的 hybrid pipeline，開箱即用。

## 目錄

- [為什麼要用 Hybrid Search](#why-hybrid-search)
- [Dense 與 Sparse 檢索的比較](#dense-vs-sparse-retrieval)
- [Hybrid Search 架構](#hybrid-search-architectures)
- [融合方法](#fusion-methods)
- [Learned Sparse Embeddings（SPLADE）](#learned-sparse-embeddings-splade)
- [實作模式](#implementation-patterns)
- [調校與最佳化](#tuning-and-optimization)
- [生產環境考量](#production-considerations)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 為什麼要用 Hybrid Search

dense 與 sparse 檢索沒有哪一個是全面更好的，各自擅長不同類型的查詢。

### 查詢類型分析

| 查詢類型 | 範例 | 較佳的檢索方式 |
|------------|---------|------------------|
| 概念性 | "How do transformers learn?" | Dense |
| 特定關鍵字 | "GPT-4 API rate limits" | Sparse |
| 具名實體 | "John Smith's research on BERT" | Sparse |
| 縮寫／代碼 | "What does HTTP 429 mean?" | Sparse |
| 改寫過的句子 | "How to make AI faster" 對比 "LLM optimization" | Dense |
| 混合型 | "What is the cost of GPT-4o API?" | Hybrid |

**細微之處**：在技術文件中，特定的版本號與函式名稱往往承載了 90% 的資訊價值，此時純 dense 檢索會失效。

### 落差問題（The Gap Problem）

Dense 檢索可能會漏掉完全相符的字串：

```
Query: "Configure NVIDIA_VISIBLE_DEVICES"
Document: "Set the NVIDIA_VISIBLE_DEVICES environment variable..."

Dense search may miss this because:
- "NVIDIA_VISIBLE_DEVICES" might tokenize poorly
- Semantic embedding does not capture exact string matching
- Training data may not have this specific term
```

Sparse search（BM25）因為有完全相符的 token，所以能立刻找到它。

---

## Dense 與 Sparse 檢索的比較

### Dense（語意）檢索

使用神經網路 embeddings 來比對語意。

```python
def dense_search(query: str, top_k: int = 10) -> list[Result]:
    query_embedding = embedding_model.encode(query)
    results = vector_db.search(query_embedding, top_k=top_k)
    return results
```

**優點：**
- 能理解改寫與同義詞
- 能捕捉概念上的相似性
- 可跨語言運作（搭配多語言模型）

**缺點：**
- 可能漏掉完全相符的關鍵字
- 難以處理實體、代碼、縮寫
- 需要 embedding model

### Sparse（關鍵字）檢索

使用詞頻與統計量（BM25、TF-IDF）。

```python
def sparse_search(query: str, top_k: int = 10) -> list[Result]:
    tokens = tokenize(query)
    results = bm25_index.search(tokens, top_k=top_k)
    return results
```

**優點：**
- 對完全相符的情況表現極佳
- 能處理罕見詞彙、代碼、實體
- 快速且具可解釋性
- 不需要訓練

**缺點：**
- 會漏掉語意上的相似性
- 無法理解同義詞
- 對詞彙不匹配（vocabulary mismatch）很敏感

### 正面對決比較

| 面向 | Dense | Sparse | Hybrid |
|--------|-------|--------|--------|
| 語意比對 | 最佳 | 差 | 最佳 |
| 完全相符比對 | 差 | 最佳 | 最佳 |
| 罕見詞彙 | 差 | 最佳 | 非常好 |
| Zero-shot 領域 | 非常好 | 最佳 | 最佳 |
| 延遲 | 中等 | 快 | 中等 |
| 實作難度 | 中等 | 簡單 | 複雜 |

---

## Hybrid Search 架構

### 架構 1：平行檢索加融合（Parallel Retrieval with Fusion）

```
                    +------------------+
                    |      Query       |
                    +--------+---------+
                             |
              +--------------+--------------+
              v                             v
    +-------------------+         +-------------------+
    |  Dense Retrieval  |         |  Sparse Retrieval |
    |   (Vector DB)     |         |    (BM25/ES)      |
    +---------+---------+         +---------+---------+
              |                             |
              +--------------+--------------+
                             v
                    +-------------------+
                    |      Fusion       |
                    |  (RRF, weighted)  |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    |  Final Results    |
                    +-------------------+
```

**優點：** 職責劃分清楚，每一邊都能採用同類最佳方案（例如 Pinecone + Algolia），且可獨立調校
**缺點：** 要維護兩套獨立系統，延遲較高（必須等待較慢的那個引擎）

### 架構 2：原生 Hybrid（單一系統）

有些 vector databases 原生支援 hybrid：

```python
# Weaviate
results = client.query.get("Document", ["text"]).with_hybrid(
    query="Configure NVIDIA_VISIBLE_DEVICES",
    alpha=0.5  # 0 = sparse only, 1 = dense only
).do()

# Qdrant (with sparse vectors)
results = client.search(
    collection_name="docs",
    query_vector=NamedVector(name="dense", vector=dense_embedding),
    query_sparse_vector=NamedSparseVector(name="sparse", vector=sparse_vector),
)
```

**優點：** 單一系統，維運更簡單，延遲更低
**缺點：** 融合方式的客製化受限，在分別擴充 keyword 與 vector 基礎設施上彈性較低

### 架構 3：分階段檢索（Staged Retrieval）

```
Query --> Sparse (fast, broad) --> Top 1000
                    |
                    v
          Dense reranking --> Top 100
                    |
                    v
           Cross-encoder --> Top 10
```

**優點：** 有效率，每個階段都會進一步精煉結果
**缺點：** 較複雜，存在早期階段出錯的風險

---

## 融合方法

### Reciprocal Rank Fusion（RRF，倒數排名融合）

RRF 是結合兩個不同搜尋引擎結果的黃金標準。它不看 *score*（分數在不同引擎之間無法相互比較），而是看 **rank（排名）**。

```python
def reciprocal_rank_fusion(
    rankings: list[list[str]],  # List of doc_id lists
    k: int = 60
) -> list[tuple[str, float]]:
    scores = defaultdict(float)

    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] += 1 / (k + rank + 1)

    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_docs
```

**特性：**
- 以名次為基礎，忽略原始分數
- 對分數尺度差異具有穩健性 —— 可避免某個引擎只因為數值分數高就「主宰」整體結果
- k 參數控制對名次的敏感度（k 越大，對位置越不敏感）
- 實作簡單，除了 k 之外不需要調校

**常見的 k 值：** 60（原始論文），實務上為 10-100

### 加權分數融合（Weighted Score Fusion）

結合正規化後的分數：

```python
def weighted_fusion(
    dense_results: list[Result],
    sparse_results: list[Result],
    alpha: float = 0.5  # Weight for dense
) -> list[Result]:
    # Normalize scores to [0, 1]
    dense_normalized = normalize_scores(dense_results)
    sparse_normalized = normalize_scores(sparse_results)

    # Combine
    combined = {}
    for r in dense_normalized:
        combined[r.id] = alpha * r.score
    for r in sparse_normalized:
        combined[r.id] = combined.get(r.id, 0) + (1 - alpha) * r.score

    sorted_docs = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    return sorted_docs

def normalize_scores(results: list[Result]) -> list[Result]:
    if not results:
        return []
    min_score = min(r.score for r in results)
    max_score = max(r.score for r in results)
    range_score = max_score - min_score + 1e-6

    return [
        Result(id=r.id, score=(r.score - min_score) / range_score)
        for r in results
    ]
```

**特性：**
- 使用實際分數（比名次帶有更多資訊）
- 需要分數正規化
- Alpha 控制 dense 與 sparse 之間的平衡

### 相對分數融合（Relative Score Fusion）

將分數分佈納入考量：

```python
def relative_score_fusion(
    dense_results: list[Result],
    sparse_results: list[Result]
) -> list[Result]:
    # Use z-score normalization
    dense_normalized = z_score_normalize(dense_results)
    sparse_normalized = z_score_normalize(sparse_results)

    # Combine
    combined = {}
    for r in dense_normalized:
        combined[r.id] = r.score
    for r in sparse_normalized:
        combined[r.id] = combined.get(r.id, 0) + r.score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

def z_score_normalize(results: list[Result]) -> list[Result]:
    scores = [r.score for r in results]
    mean = sum(scores) / len(scores)
    std = (sum((s - mean) ** 2 for s in scores) / len(scores)) ** 0.5 + 1e-6

    return [Result(id=r.id, score=(r.score - mean) / std) for r in results]
```

### 融合方法比較

| 方法 | 是否使用分數 | 是否依查詢自適應 | 複雜度 |
|--------|-------------|----------------|------------|
| RRF | 否（僅用名次） | 否 | 低 |
| 加權（Weighted） | 是 | 否 | 低 |
| 相對分數（Relative Score） | 是 | 部分 | 中 |
| 學習式（Learned） | 是 | 是 | 高 |

---

## Learned Sparse Embeddings（SPLADE）

生產級技術堆疊在 hybrid search 的 sparse 端，已經從 BM25（單純的詞頻）進展到 **Learned Sparse Embeddings**。

**技術原理**：像 **SPLADE v3** 這類模型，會為字典中的每一個詞預測「重要性權重（importance weights）」。

**為什麼？**：SPLADE 能「擴展」查詢。如果你搜尋 "CPU"，它可能會自動為 "processor" 這個詞加上一點小權重，即使 "processor" 並不在你的查詢中。它把 sparse search 的完全相符能力，與 dense search 的概念性能力，結合在單一儲存格式之中。

### SPLADE 實作

```python
from transformers import AutoModelForMaskedLM, AutoTokenizer

class SpladeEncoder:
    def __init__(self, model_name="naver/splade-cocondenser-ensembledistil"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForMaskedLM.from_pretrained(model_name)

    def encode(self, text: str) -> dict[str, float]:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True)
        outputs = self.model(**inputs)

        # Get sparse weights
        weights = torch.max(
            torch.log(1 + torch.relu(outputs.logits)) * inputs["attention_mask"].unsqueeze(-1),
            dim=1
        ).values.squeeze()

        # Convert to sparse dict
        non_zero = weights.nonzero().squeeze().tolist()
        sparse_vec = {
            self.tokenizer.decode([idx]): weights[idx].item()
            for idx in non_zero
            if weights[idx] > 0
        }

        return sparse_vec
```

**何時該選 SPLADE 而非 BM25 + Dense Hybrid：** SPLADE 產生的 sparse vector 可以儲存在現代 vector databases（如 Milvus 或 Qdrant）中，與 dense vector 並存，讓 hybrid search 能在單一回合內完成，而不需要另外維護一套 Elasticsearch 或 BM25 索引。如果你的資料集含有極為罕見、非語言性的 token（例如獨一無二的序號），這類 token 神經模型在訓練時可能從未見過，那就堅持使用 BM25。

---

## 實作模式

### 模式 1：Elasticsearch + Vector DB

```python
class HybridSearcher:
    def __init__(self, es_client, vector_db, embedding_model):
        self.es = es_client
        self.vector_db = vector_db
        self.embedding_model = embedding_model

    def search(self, query: str, top_k: int = 10, alpha: float = 0.5) -> list[Result]:
        # Parallel retrieval
        dense_future = self.dense_search(query, top_k * 3)
        sparse_future = self.sparse_search(query, top_k * 3)

        dense_results = dense_future.result()
        sparse_results = sparse_future.result()

        # Fusion
        combined = reciprocal_rank_fusion([
            [r.id for r in dense_results],
            [r.id for r in sparse_results]
        ])

        return combined[:top_k]

    async def dense_search(self, query: str, top_k: int) -> list[Result]:
        embedding = self.embedding_model.encode(query)
        return self.vector_db.search(embedding, top_k=top_k)

    async def sparse_search(self, query: str, top_k: int) -> list[Result]:
        response = self.es.search(
            index="documents",
            body={
                "query": {"match": {"content": query}},
                "size": top_k
            }
        )
        return [
            Result(id=hit["_id"], score=hit["_score"])
            for hit in response["hits"]["hits"]
        ]
```

### 模式 2：以 Weaviate 進行原生 Hybrid

```python
import weaviate

def hybrid_search_weaviate(
    client: weaviate.Client,
    query: str,
    alpha: float = 0.5,
    top_k: int = 10
) -> list[dict]:
    result = client.query.get(
        "Document",
        ["text", "title", "source"]
    ).with_hybrid(
        query=query,
        alpha=alpha,  # 0 = BM25 only, 1 = vector only
        fusion_type=weaviate.HybridFusion.RELATIVE_SCORE
    ).with_limit(top_k).do()

    return result["data"]["Get"]["Document"]
```

---

## 調校與最佳化

### Alpha 調校

alpha 參數用於平衡 dense 與 sparse：

```python
def find_optimal_alpha(
    test_queries: list[tuple[str, list[str]]],  # (query, relevant_doc_ids)
    alpha_range: list[float] = [0.0, 0.3, 0.5, 0.7, 1.0]
) -> float:
    best_alpha = 0.5
    best_ndcg = 0

    for alpha in alpha_range:
        ndcg_scores = []
        for query, relevant in test_queries:
            results = hybrid_search(query, alpha=alpha)
            ndcg = compute_ndcg(results, relevant)
            ndcg_scores.append(ndcg)

        avg_ndcg = sum(ndcg_scores) / len(ndcg_scores)
        if avg_ndcg > best_ndcg:
            best_ndcg = avg_ndcg
            best_alpha = alpha

    return best_alpha
```

**最佳實務／常見的觀察結果：**
- 技術文件與程式碼：alpha 0.3-0.4（偏重關鍵字）
- 一般文字：alpha 0.5（平衡）
- 聊天與創意探索：alpha 0.7-0.9（偏重語意）

### 依查詢自適應的 Alpha（Query-Adaptive Alpha）

針對每個查詢預測最佳 alpha：

```python
def predict_alpha(query: str) -> float:
    # Heuristics-based
    has_quotes = '"' in query
    has_code = any(c in query for c in ['_', '()', '{}', '[]'])
    has_numbers = any(c.isdigit() for c in query)

    # More sparse for exact match queries
    if has_quotes or has_code:
        return 0.3
    if has_numbers:
        return 0.4

    # More semantic for natural language
    if len(query.split()) > 5:
        return 0.7

    return 0.5  # Default balanced
```

### 檢索深度（Retrieval Depth）

在融合之前要先取回多少筆結果：

```python
# Rule of thumb: fetch 3-5x more from each source
def hybrid_search(query: str, final_k: int = 10):
    fetch_k = final_k * 4

    dense_results = dense_search(query, top_k=fetch_k)
    sparse_results = sparse_search(query, top_k=fetch_k)

    fused = rrf([dense_results, sparse_results])
    return fused[:final_k]
```

---

## 生產環境考量

### 延遲預算（Latency Budget）

```
Typical hybrid search latency breakdown:

Dense embedding:           30-50ms
Dense retrieval:          30-50ms
Sparse retrieval:         20-40ms  (parallel with dense)
Fusion:                    1-5ms
Total:                   60-100ms
```

**最佳化做法：**
- 讓 dense 與 sparse 平行執行
- 為常見查詢預先計算 embeddings
- 兩邊都採用近似搜尋（approximate search）
- 對重複查詢快取其融合結果

### 快取策略

```python
class HybridSearchCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = TTLCache(ttl=ttl_seconds)

    def search(self, query: str, **kwargs) -> list[Result]:
        cache_key = self._make_key(query, kwargs)

        if cache_key in self.cache:
            return self.cache[cache_key]

        results = self._do_search(query, **kwargs)
        self.cache[cache_key] = results
        return results

    def _make_key(self, query: str, kwargs: dict) -> str:
        return hashlib.sha256(
            f"{query}:{sorted(kwargs.items())}".encode()
        ).hexdigest()
```

### 降級策略（Fallback Strategy）

```python
def hybrid_search_with_fallback(query: str, top_k: int = 10) -> list[Result]:
    try:
        return hybrid_search(query, top_k=top_k)
    except DenseSearchError:
        # Fallback to sparse only
        return sparse_search(query, top_k=top_k)
    except SparseSearchError:
        # Fallback to dense only
        return dense_search(query, top_k=top_k)
```

---

## 面試問題

### Q：什麼情況下你會用 hybrid search 而不是純 dense search？

**理想答案：**
我會在以下情況使用 hybrid search：

1. **查詢中含有特定詞彙：** 產品代碼、API 名稱、錯誤代碼。Dense search 可能會漏掉完全相符的結果。

2. **領域有專門詞彙：** 技術文件、法律、醫療。Sparse 能捕捉這些特定詞彙。

3. **Zero-shot 檢索：** 沒有經過 fine-tuned embeddings 的新領域。Sparse 提供了穩健的基準。

4. **品質至關重要：** Hybrid 很少會比單獨使用其中一種更差，代價是複雜度上升。

**我會在以下情況堅持使用純 dense：**
- 查詢純粹是概念性／語意性的
- 延遲預算非常吃緊
- 以較簡單的架構為優先
- Embedding model 已針對該領域充分調校

這個決定是經驗性的。我會在自己實際的查詢分佈上對 hybrid 與 dense 做 A/B 測試。

### Q：為什麼 Reciprocal Rank Fusion（RRF）比「單純的分數相加」更安全？

**理想答案：**
單純的分數相加很危險，因為向量分數（例如 Cosine Similarity：0.0 到 1.0）與關鍵字分數（例如 BM25：0 到無限大）使用的尺度完全不同。某個幸運命中的關鍵字所得到的極高 BM25 分數，可能會「淹沒」掉 10 筆高度相關的語意命中結果。RRF 忽略絕對分數，只在意相對的順序（rank）。這讓它在數學上對離群值（outliers），以及不同檢索引擎之間的「分數漂移（score-drift）」具有穩健性。

### Q：什麼情況下你會選擇 SPLADE，而不是標準的 BM25 + Dense Hybrid 做法？

**理想答案：**
當我想簡化基礎設施時，我會選擇 SPLADE。SPLADE 產生的 sparse vector 可以儲存在許多現代 vector databases（如 Milvus 或 Qdrant）中，與 dense vector 並存。這讓資料庫能夠在單一回合內完成「hybrid search」，而不需要另外維護一套 Elasticsearch 或 BM25 索引。不過，如果我的資料集含有極為罕見、非語言性的 token（例如獨一無二的序號），這類 token 神經模型在訓練時可能從未見過，那我就會堅持使用 BM25。

### Q：在 hybrid search 中，你如何平衡 dense 與 sparse？

**理想答案：**
alpha 參數控制這個平衡（通常 alpha 代表 dense 的權重）：

**調校做法：**
1. 從 alpha=0.5 開始（等權重）
2. 建立含有查詢與相關性標註的評估集
3. 在 [0.1, 0.3, 0.5, 0.7, 0.9] 範圍內做 alpha 的 grid search
4. 在每個設定下量測 NDCG 或 MRR
5. 選出能最大化評估指標的 alpha

**依查詢自適應的調校：**
- 偵測查詢類型（偏重關鍵字、概念性、混合型）
- 針對每個查詢調整 alpha
- 可使用簡單的啟發式規則，或學習式分類器

**經驗法則：**
- 技術／程式碼查詢：alpha 0.3-0.4
- 一般文字：alpha 0.5
- 對話式：alpha 0.7-0.8

---

## 參考資料

- Cormack et al. "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods" (2009)
- Formal et al. "SPLADE: Sparse Lexical and Expansion Model for First Stage Ranking" (2021/2025)
- Weaviate Hybrid Search: https://weaviate.io/developers/weaviate/search/hybrid
- Qdrant Hybrid Search: https://qdrant.tech/documentation/concepts/hybrid-queries/

---

*上一篇：[Vector Databases](04-vector-databases.md) | 下一篇：[Reranking Strategies](06-reranking-strategies.md)*
