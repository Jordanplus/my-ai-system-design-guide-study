# 向量資料庫

向量資料庫是專門用於儲存、索引與搜尋高維度 embedding 的系統。市場已分化為 **Managed Serverless（託管無伺服器）** 與 **Specialized High-Performance（專用高效能）** 兩類引擎。我們不再問「它支援向量搜尋嗎？」（Postgres、Redis 與 Mongo 全都支援）。我們要問的是 **「它能否擴展到 100M+ 向量，同時維持 sub-100ms P99 與完整的 metadata filtering？」**

## 目錄

- [什麼是向量資料庫](#what-is-a-vector-database)
- [向量搜尋基礎](#vector-search-fundamentals)
- [索引演算法](#indexing-algorithms)
- [競爭態勢](#competitive-landscape)
- [資料庫詳細比較](#detailed-database-comparison)
- [Metadata Filtering](#metadata-filtering)
- [查詢模式](#query-patterns)
- [生產環境維運](#production-operations)
- [託管 vs 自架（TCO 分析）](#managed-vs-self-hosted-tco-analysis)
- [選型框架](#selection-framework)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 什麼是向量資料庫

向量資料庫儲存 embedding（dense vector），並能在其上進行快速的相似度搜尋。

```
Traditional DB:      SELECT * FROM docs WHERE category = 'tech'
Vector DB:           SELECT * FROM docs ORDER BY similarity(embedding, query_embedding) LIMIT 10
```

### 核心能力

| 能力 | 用途 |
|------------|---------|
| 向量儲存 | 持久化儲存高維度 embedding |
| 相似度搜尋 | 快速找出最近鄰 |
| Metadata filtering | 將向量搜尋與屬性過濾結合 |
| CRUD 操作 | 隨資料變動更新 embedding |
| 擴展性 | 處理數百萬到數十億向量 |

### 為什麼不用通用資料庫？

傳統資料庫雖可儲存向量，但缺乏最佳化的搜尋：

| 方法 | 搜尋複雜度 | 規模化下的可行性 |
|----------|-------------------|-------------------|
| 暴力搜尋（PostgreSQL pgvector） | O(n * d) | 到約 1M 向量為止可行 |
| ANN 索引（專用向量 DB） | O(log n) 或 O(1) | 可行，數十億級 |

---

## 向量搜尋基礎

### 精確 vs 近似搜尋

**精確（暴力搜尋）：**
- 將查詢與每一個已儲存向量比較
- 每次查詢 O(n * d)
- 完美準確度

**近似最近鄰（ANN）：**
- 使用索引結構來修剪搜尋空間
- 次線性複雜度
- recall 略低（通常 95-99%）

### 距離度量

| 度量 | 公式 | 範圍 | 最適用於 |
|--------|---------|-------|----------|
| Cosine | 1 - (a . b) / (norm(a) * norm(b)) | [0, 2] | 文字 embedding |
| Euclidean (L2) | sqrt(sum((a - b)^2)) | [0, inf) | 影像 embedding |
| Dot product | a . b | (-inf, inf) | 已正規化的向量 |

**對於文字 embedding：** 使用 cosine 相似度（若已預先正規化則用 dot product）。

### Recall vs Latency 的取捨

```
                    ^ Recall
                    |
               100% | ------------------ Brute force
                    |         *          Well-tuned ANN
                    |      *
                    |   *
                95% |*                   Fast ANN
                    |
                    +-----+-------+------> Latency
                       1ms      10ms
```

ANN 索引以部分準確度換取速度。請依你的需求進行調校。

---

## 索引演算法

### HNSW（Hierarchical Navigable Small World）

生產環境 **記憶體內（in-memory）** 向量搜尋中最熱門的演算法。

**運作方式：**
1. 建立一張以向量為節點的圖
2. 連接到鄰近的鄰居
3. 多層抽象（階層式）
4. 搜尋：從最上層往下導航，貪婪式最近鄰

```
Layer 2:   *--------*--------*
           |        |        |
Layer 1:   *--*--*--*--*--*--*
           |  |  |  |  |  |  |
Layer 0:   ********************  (all vectors)
```

**優點：**
- 極佳的 recall/latency 取捨
- 不需訓練
- 原生支援更新

**缺點：**
- 記憶體密集（圖結構）
- 索引大小：約為向量資料的 1.5-2x
- 1536 維的 10M 向量需要約 80GB 的 RAM

**關鍵參數：**
- `M`：每個節點的最大連接數（16-64）
- `ef_construction`：建構期的探索程度（100-500）
- `ef_search`：查詢期的探索程度（50-200）

### DiskANN（以 SSD 為基礎）

**petabyte 規模** 搜尋的業界標準。

**運作方式：**
- 將圖保存在 SSD（NVMe）上，RAM 中僅保留極小的索引
- 使用 Vamana 演算法進行高效的磁碟式圖走訪

**優點：**
- 在數十億級資料集上比 HNSW 便宜 10x，且 latency 損失低於 5ms
- 相較 HNSW，RAM 需求減少 90-95%

**缺點：**
- latency 略高於純記憶體內的 HNSW
- 最適合非即時搜尋應用

**範例：** 一個 1536 維的 1 億向量索引，使用 HNSW 將需要近 1TB 的 RAM。改用 DiskANN，RAM 需求下降 90-95%，同時維持 sub-10ms 的查詢時間。

### IVF（Inverted File Index）

將向量分割成多個叢集，只搜尋相關的叢集。

**運作方式：**
1. 使用 k-means 建立 centroid
2. 將每個向量指派給最近的 centroid
3. 查詢時：找出最近的 centroid，搜尋這些叢集

**優點：**
- 記憶體用量低於 HNSW
- 可使用量化（IVF-PQ）

**缺點：**
- 需要訓練
- 更新需要重新分群或採用混合做法

**關鍵參數：**
- `nlist`：叢集數量（經驗法則為 sqrt(n)）
- `nprobe`：查詢時要搜尋的叢集數

### Product Quantization（PQ）

壓縮向量以降低記憶體用量並加速比較。

**運作方式：**
1. 將向量切分為多個子向量
2. 將每個子向量量化到一個 codebook
3. 儲存編碼而非完整向量

**記憶體縮減：** 通常 4-32x

**取捨：** 因量化損失而導致準確度降低

### Flat Index（暴力搜尋）

無近似，精確搜尋。

**使用時機：**
- 少於 100K 向量
- 準確度至關重要
- latency 預算寬鬆

### 演算法比較

| 演算法 | 記憶體 | 建構時間 | 查詢速度 | Recall | 更新 |
|-----------|--------|------------|-------------|--------|---------|
| HNSW | 高 | 中 | 非常快 | 95-99% | 良好 |
| DiskANN | 低（SSD） | 中 | 快 | 95-99% | 尚可 |
| IVF | 中 | 快 | 快 | 90-98% | 尚可 |
| IVF-PQ | 低 | 快 | 快 | 85-95% | 尚可 |
| Flat | 低 | 無 | 慢 | 100% | 即時 |

---

## 競爭態勢

### 向量原生（專用）

| 資料庫 | 類型 | 最適用於 | 計價模式 |
|----------|------|----------|---------------|
| **Pinecone** | 託管雲端（serverless 標準） | 易於起步、規模化、託管 SLA | 依 vector-hour 計價 |
| **Qdrant** | 開源 / 雲端（Rust，高效能） | 自架掌控、在常見工作負載上是最快的開源方案（10M 向量時約 12ms p99） | 依 GB（雲端）或免費 |
| **Weaviate** | 開源 / 雲端 | 單一查詢中的原生混合搜尋（BM25 + dense + metadata）、多模態 | 依 dimension-hour 計價 |
| **Milvus** | 開源 / 雲端（Zilliz） | 分散式規模（50M+ 向量）、異質節點型別、分層儲存 | 免費（自架）或 Zilliz Cloud |
| **Chroma** | 開源 | 原型開發、本機開發、嵌入式使用 | 免費 |

### 通用型（外掛 / 擴充套件）

| 資料庫 | 類型 | 最適用於 | 計價模式 |
|----------|------|----------|---------------|
| **pgvector (v0.8+)** | PostgreSQL 擴充套件 | 小規模、既有 PG（現支援 HNSW + IVFFlat） | 僅計算費用 |
| **Elasticsearch (v9.0)** | 搜尋引擎 | 採用 cross-entropy fusion 的混合搜尋 | 依授權計費 |

---

## 資料庫詳細比較

### 功能矩陣

| 功能 | Pinecone | Qdrant | Weaviate | Milvus | pgvector |
|---------|----------|--------|----------|--------|----------|
| **語言** | 專有 | Rust | Go | Go/C++ | C |
| 託管選項 | 是 | 是 | 是 | 是（Zilliz） | 透過雲端 PG |
| 自架 | 否 | 是 | 是 | 是 | 是 |
| **Serverless** | 是（最佳） | 是 | 是 | 是（Zilliz） | 否 |
| **Cloud-Native** | 任意 | 任意 | 任意 | 僅 K8s | 任意 |
| Metadata filtering | 良好 | 極佳 | 良好 | 良好 | 透過 SQL |
| **混合搜尋** | 原生 | 原生 | 原生 | 原生 | 多階段（受限） |
| 最大向量數 | 數十億 | 數十億 | 數十億 | 數十億 | 約 10M |
| HNSW 索引 | 是 | 是 | 是 | 是 | 是 |

---

## Metadata Filtering

對於多租戶與過濾類使用情境至關重要。

```python
# Pinecone
results = index.query(
    vector=query_embedding,
    top_k=10,
    filter={"tenant_id": "123", "category": {"$in": ["tech", "science"]}}
)

# Qdrant
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    limit=10,
    query_filter=Filter(
        must=[
            FieldCondition(key="tenant_id", match=MatchValue(value="123")),
            FieldCondition(key="category", match=MatchAny(any=["tech", "science"]))
        ]
    )
)
```

**效能影響：** 過濾發生在搜尋過程中，而非搜尋之後。預先過濾的索引較快，但彈性較低。

**為什麼 metadata filtering 常常是瓶頸：** 在 naive 的向量搜尋中，我們先找出「Top K」最近鄰，**然後**再依 metadata 過濾。如果過濾條件非常嚴格，過濾後可能得到 0 筆結果。專用資料庫現在使用 **搭配 HNSW 的 Pre-Filtering（預先過濾）**，在走訪圖時只考慮滿足布林 metadata 約束的節點。這需要專用的 bitmask 或硬體加速（SIMD）才能維持低 latency。

**Disk-Native Metadata：** 像 **Qdrant** 這類現代資料庫會將 metadata 卸載到磁碟對映的 segment，使其能執行複雜過濾（例如：全文 + geo + 向量）而不致耗盡 RAM。

---

## 查詢模式

### 模式 1：簡單語意搜尋

```python
def semantic_search(query: str, top_k: int = 5) -> list[Document]:
    query_embedding = embed(query)
    results = vector_db.search(query_embedding, top_k=top_k)
    return [Document(id=r.id, text=r.payload["text"], score=r.score) for r in results]
```

### 模式 2：過濾搜尋

```python
def filtered_search(query: str, filters: dict, top_k: int = 5) -> list[Document]:
    query_embedding = embed(query)
    results = vector_db.search(
        query_embedding,
        top_k=top_k,
        filter=filters  # {"tenant_id": "abc", "created_after": "2025-01-01"}
    )
    return results
```

### 模式 3：混合搜尋（Dense + Sparse）

```python
def hybrid_search(query: str, alpha: float = 0.5, top_k: int = 5) -> list[Document]:
    # Dense (semantic)
    dense_embedding = embed(query)
    dense_results = vector_db.search(dense_embedding, top_k=top_k * 2)

    # Sparse (keyword)
    sparse_results = bm25_search(query, top_k=top_k * 2)

    # Combine with reciprocal rank fusion
    combined = reciprocal_rank_fusion(
        [dense_results, sparse_results],
        weights=[alpha, 1 - alpha]
    )

    return combined[:top_k]
```

部分資料庫（Weaviate、Qdrant、Pinecone）原生支援混合搜尋：

```python
# Weaviate native hybrid
results = client.query.get("Document", ["text"]).with_hybrid(
    query=query,
    alpha=0.5  # 0 = BM25 only, 1 = vector only
).with_limit(5).do()
```

### 模式 4：Multi-Vector 查詢

用於 parent-child 或多面向檢索：

```python
def multi_vector_search(queries: list[str], top_k: int = 5) -> list[Document]:
    all_results = []

    for query in queries:
        embedding = embed(query)
        results = vector_db.search(embedding, top_k=top_k)
        all_results.extend(results)

    # Dedupe and rerank
    unique = dedupe_by_id(all_results)
    reranked = rerank(queries[0], unique)  # Use primary query for reranking

    return reranked[:top_k]
```

---

## 生產環境維運

### 容量規劃

```python
def estimate_resources(
    num_vectors: int,
    dimensions: int,
    metadata_size_bytes: int = 500
) -> dict:
    # Vector storage
    vector_size = dimensions * 4  # float32
    total_vector_storage = num_vectors * vector_size

    # Index overhead (HNSW ~1.5x)
    index_overhead = total_vector_storage * 1.5

    # Metadata
    metadata_storage = num_vectors * metadata_size_bytes

    # Total
    total_gb = (total_vector_storage + index_overhead + metadata_storage) / 1e9

    # QPS estimate (rough)
    qps_per_gb = 50  # depends heavily on config
    estimated_qps = total_gb * qps_per_gb

    return {
        "storage_gb": total_gb,
        "estimated_qps": estimated_qps,
        "recommended_replicas": max(1, int(total_gb / 50))  # ~50GB per replica
    }
```

### 索引維護

```python
class VectorDBMaintenance:
    def __init__(self, client):
        self.client = client

    def add_documents(self, documents: list[Document]):
        """Upsert documents with batching."""
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            embeddings = embed_batch([d.text for d in batch])

            self.client.upsert([
                {
                    "id": doc.id,
                    "vector": embedding,
                    "payload": doc.metadata
                }
                for doc, embedding in zip(batch, embeddings)
            ])

    def delete_documents(self, doc_ids: list[str]):
        """Delete by document ID."""
        self.client.delete(ids=doc_ids)

    def update_metadata(self, doc_id: str, metadata: dict):
        """Update metadata without re-embedding."""
        self.client.set_payload(
            collection_name="documents",
            payload=metadata,
            points=[doc_id]
        )
```

### 高可用性

```
+-------------------------------------------------------------+
|                    Load Balancer                              |
+----------------------------+--------------------------------+
                             |
            +----------------+----------------+
            v                v                v
     +--------------+ +--------------+ +--------------+
     |  Replica 1   | |  Replica 2   | |  Replica 3   |
     |   (Read)     | |   (Read)     | |   (Primary)  |
     +--------------+ +--------------+ +--------------+
                                             |
                                       (Replication)
                                             |
                                       +-----v-----+
                                       |  Storage   |
                                       +-----------+
```

**關鍵模式：**
- 寫入採 leader-follower
- 以 read replica 擴展查詢
- 採非同步複寫以達成 HA

### 監控

```python
VECTOR_DB_METRICS = [
    "query_latency_p50",
    "query_latency_p99",
    "queries_per_second",
    "index_size_gb",
    "vector_count",
    "filter_latency",
    "upsert_latency",
    "cache_hit_rate"
]

def alert_rules():
    return {
        "query_latency_p99_high": {
            "condition": "query_latency_p99 > 500ms",
            "severity": "warning"
        },
        "query_latency_p99_critical": {
            "condition": "query_latency_p99 > 2000ms",
            "severity": "critical"
        },
        "low_recall": {
            "condition": "bench_recall < 0.90",
            "severity": "warning"
        }
    }
```

---

## 託管 vs 自架（TCO 分析）

### 成本比較

| 面向 | Pinecone（Serverless） | 自架（Qdrant/Milvus） |
|--------|-----------------------|-----------------------------|
| **維運負擔** | 零 | 高（需要 K8s + SRE） |
| **擴展** | 即時（可縮容至零） | 手動（節點佈建） |
| **成本（小規模）** | $0 - $100/mo | $50/mo（最小執行個體） |
| **成本（規模化）** | 依 token/向量計，較高 | 單位成本低 |

### 託管服務計價（僅供參考，請務必在供應商頁面查證）

| 供應商 | 模式 | 範例：10M 向量、1536 維 |
|----------|-------|--------------------------------|
| Pinecone | Pod-based 或 Serverless | serverless 約 $70-150/month |
| Qdrant Cloud | 依 GB | 約 $50/month（20GB） |
| Weaviate Cloud | 依維度 | 約 $100/month |
| Zilliz (Milvus) | 依 CU | 約 $75/month |

### 自架成本

```python
def estimate_self_hosted_cost(
    vectors: int,
    dimensions: int,
    cloud: str = "aws"
) -> dict:
    storage_gb = (vectors * dimensions * 4 * 2.5) / 1e9  # 2.5x for index

    # Instance sizing
    if storage_gb < 50:
        instance = "r6g.large"  # 16 GB RAM, ~$60/month
    elif storage_gb < 200:
        instance = "r6g.xlarge"  # 32 GB RAM, ~$120/month
    else:
        instance = "r6g.2xlarge"  # 64 GB RAM, ~$240/month

    return {
        "storage_gb": storage_gb,
        "instance": instance,
        "monthly_compute": instance_pricing[instance],
        "monthly_storage": storage_gb * 0.10,  # EBS
        "total_monthly": instance_pricing[instance] + storage_gb * 0.10
    }
```

### 決策：託管 vs 自架

| 因素 | 託管 | 自架 |
|--------|---------|-------------|
| 維運負擔 | 低 | 高 |
| 小規模時的成本 | 較高 | 較低 |
| 大規模時的成本 | 變動 | 通常較低 |
| 掌控度 | 較少 | 完整 |
| 法遵 | 視情況而定 | 完全掌控 |
| 廠商鎖定 | 是 | 否（若為開源） |

**結論**：先從 Serverless 起步。只有在你擁有 >500M 向量或有嚴格的 **On-Prem/GPU-Local** 需求時，才考慮自架。

---

## 選型框架

### 決策樹

```
Need < 100K vectors?
+-- Yes -> pgvector (if already using PostgreSQL)
|          +-- Chroma (for prototyping)
|
+-- No -> Need managed service?
          +-- Yes -> Cloud-first?
          |          +-- Yes -> Pinecone (easiest)
          |          +-- No -> Qdrant Cloud or Zilliz
          |
          +-- No -> Need enterprise features?
                    +-- Yes -> Milvus on Kubernetes
                    +-- No -> Qdrant or Weaviate self-hosted
```

### 評估準則

| 準則 | 權重 | 應提出的問題 |
|-----------|--------|------------------|
| 規模 | 高 | 現在有多少向量？一年後呢？ |
| Latency | 高 | p99 需求為何？ |
| 維運能量 | 高 | 我們有能力維運它嗎？ |
| 成本 | 中 | 預算限制？ |
| 功能 | 中 | 混合搜尋？多模態？ |
| 鎖定風險 | 低-中 | 偏好開源嗎？ |

### 概念驗證檢查清單

在正式採用某個向量資料庫之前：

- [ ] 載入具代表性的資料量
- [ ] 在目標 QPS 下對查詢 latency 進行基準測試
- [ ] 測試 metadata filtering 效能
- [ ] 驗證更新／刪除效能
- [ ] 測試故障復原
- [ ] 評估監控與可觀測性
- [ ] 計算總體擁有成本

---

## 面試問題

### Q：你會如何在 Pinecone 與自架方案之間做選擇？

**優秀回答：**
決策取決於數項因素：

**選擇 Pinecone 的時機：**
- 團隊缺乏維運有狀態基礎設施的能量
- 需要快速推進（以天計而非以週計）
- 規模中等（低於 100M 向量）
- 預算可負擔託管服務的溢價
- 法遵允許依賴雲端廠商

**選擇自架（Qdrant、Milvus）的時機：**
- 具備 Kubernetes 與維運專業
- 對規模化下的成本敏感
- 需要對資料的完全掌控
- 有特定的法遵需求
- 想避免廠商鎖定

對多數新創而言，我會先採用 Pinecone 或 Qdrant Cloud 以追求速度，待成本在規模化下變得難以負擔時再評估遷移。由於各向量 DB 的 API 相似，切換成本屬中等。

### Q：說明 HNSW 如何運作，以及你在什麼情況下不會使用它。

**優秀回答：**
HNSW 建立一張向量的階層式圖：

**運作方式：**
1. 將向量作為節點插入多層圖中
2. 較高層的節點較少、跳躍較大
3. 搜尋：從最上層開始，貪婪式導航至最近鄰
4. 逐層下降直到最底層（所有向量）

**它的優點：**
- O(log n) 查詢複雜度
- 不需訓練
- 支援即時更新
- 極佳的 recall/latency 取捨

**不適用的時機：**
- 非常小的資料集（<10K）：暴力搜尋就夠用
- 記憶體極度受限：HNSW 的圖會用掉 1.5-2x 的向量大小
- 需要精確搜尋：HNSW 是近似的
- 在嚴格 latency 下有大量更新工作負載：更新可能造成暫時性的效能退化

替代方案：
- 記憶體受限時用 IVF-PQ
- 兼顧成本效益的數十億級規模用 DiskANN
- 精確搜尋用 Flat index
- 非常高維度的 sparse 向量用 LSH

### Q：你在什麼情況下會選用磁碟式索引（如 DiskANN）而非記憶體式索引（HNSW）？

**優秀回答：**
當索引的記憶體成本超出預算，或超過單一高記憶體節點的容量時，我會選用磁碟式索引。例如，一個 1536 維的 1 億向量索引，使用 HNSW 將需要近 1TB 的 RAM。改用 DiskANN，我可以把那 1TB 的大部分儲存在 NVMe SSD 上，將 RAM 需求降低 90-95%，同時維持 sub-10ms 的查詢時間。對非即時搜尋應用而言，這代表了 TCO（總體擁有成本）的大幅降低。

### Q：為什麼 metadata filtering 在向量資料庫中常常是瓶頸？

**優秀回答：**
在 naive 的向量搜尋中，我們先找出「Top K」最近鄰，**然後**再依 metadata 過濾它們（例如「只要 2024 年的文件」）。如果過濾條件非常嚴格，過濾後可能得到 0 筆結果。專用資料庫現在使用 **搭配 HNSW 的 Pre-Filtering（預先過濾）**，在走訪圖時只考慮滿足布林 metadata 約束的節點。這在計算上代價高昂，因為它破壞了 HNSW 的「短路（short-circuit）」邏輯，需要專用的 bitmask 或硬體加速（SIMD）才能維持低 latency。

### Q：你如何在向量資料庫中處理多租戶？

**優秀回答：**
有三種主要做法：

**1. Metadata filtering（最常見）：**
```python
results = db.search(
    vector=query,
    filter={"tenant_id": current_tenant}
)
```
- 優點：簡單、單一索引
- 缺點：所有租戶共用資源，可能因 bug 而洩漏資料

**2. 每租戶一個 collection：**
```python
results = db.collection(f"tenant_{tenant_id}").search(vector=query)
```
- 優點：強隔離、可依租戶分別擴展
- 缺點：collection 眾多、維運負擔大

**3. 每租戶一個 namespace（Pinecone）：**
```python
results = index.query(vector=query, namespace=tenant_id)
```
- 優點：在單一索引內達成隔離
- 缺點：與廠商綁定

**我會這樣選擇：**
- 多數情況採 metadata filtering（簡單、具成本效益）
- 高安全需求採獨立 collection
- 切勿事後過濾（先取回全部、再過濾），因為有洩漏風險

---

## 參考資料

- Malkov and Yashunin. "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs" (HNSW, 2018)
- Microsoft Research. "Vamana/DiskANN: A Disk-based Index for ANN Search" (2019/2023)
- Pinecone Documentation: https://docs.pinecone.io/
- Pinecone. "The Managed Architecture of Serverless Vector DBs" (2024)
- Qdrant Documentation: https://qdrant.tech/documentation/
- Weaviate Documentation: https://weaviate.io/developers/weaviate
- Milvus Documentation: https://milvus.io/docs
- pgvector: https://github.com/pgvector/pgvector

---

*上一篇：[Embedding 模型](03-embedding-models.md) | 下一篇：[混合搜尋](05-hybrid-search.md)*
