# 案例研究：企業級 RAG 系統

本案例研究將完整走過如何為企業文件搜尋設計一套正式上線（production）的 RAG 系統。內容涵蓋需求蒐集、架構決策與實作細節。

## 目錄

- [問題陳述](#problem-statement)
- [需求分析](#requirements-analysis)
- [系統架構](#system-architecture)
- [元件深入剖析](#component-deep-dives)
- [擴展考量](#scaling-considerations)
- [成本分析](#cost-analysis)
- [經驗教訓](#lessons-learned)
- [面試演練](#interview-walkthrough)

---

## 問題陳述

### 情境

一家金融服務公司想為其內部文件建立一套由 AI 驅動的搜尋系統：
- 500,000 份文件（政策、流程、研究報告）
- 跨多個部門的 5,000 名員工
- 文件每日更新
- 嚴格的合規與稽核要求
- 需要在回答問題時附上引用來源

### 目前的痛點

- 員工每天花費 2 小時以上在搜尋資訊
- 關鍵字搜尋回傳過多不相關的結果
- 知識被各部門各自孤立（siloed）
- 新進員工需要數個月才能進入狀況、產生生產力

---

## 需求分析

### 功能性需求

| 需求 | 優先級 | 備註 |
|-------------|----------|-------|
| 自然語言問答 | P0 | 核心功能 |
| 來源引用 | P0 | 合規要求 |
| 多文件推理 | P1 | 串連跨文件的資訊 |
| 追問 | P1 | 對話脈絡 |
| 文件摘要 | P2 | 快速概覽冗長文件 |

### 非功能性需求

| 需求 | 目標 | 理由 |
|-------------|--------|-----------|
| 延遲（P95） | < 5 秒 | 使用者體驗 |
| 準確率 | > 90% | 信任與採用度 |
| 可用性 | 99.9% | 業務關鍵 |
| 同時在線使用者 | 500 | 尖峰使用量 |
| 文件新鮮度 | < 1 小時 | 政策更新 |

### 安全性需求

- 角色型存取控制（RBAC）
- 所有查詢的稽核日誌記錄
- 資料不離開公司網路
- PII（個資）偵測與處理

---

## 系統架構

### 高階架構

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User Interface                                │
│  (Web App, Slack Bot, API)                                             │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API Gateway                                    │
│  • Authentication    • Rate Limiting    • Request Routing              │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Query Service                                    │
│  • Query understanding   • Permission check   • Orchestration          │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Retrieval   │   │   Reranking   │   │  Generation   │
│   Service     │   │   Service     │   │   Service     │
│               │   │               │   │               │
│ • Hybrid      │   │ • Cross-      │   │ • LLM         │
│   search      │   │   encoder     │   │ • Prompt      │
│ • Filtering   │   │ • Scoring     │   │   building    │
└───────┬───────┘   └───────────────┘   └───────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Data Layer                                       │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Vector DB  │  │ Search Index│  │  Doc Store  │  │  Metadata   │   │
│  │  (Qdrant)   │  │ (Elastic)   │  │   (S3)      │  │  (Postgres) │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      Ingestion Pipeline                                 │
│  Document Upload → Parse → Chunk → Embed → Index → Store Metadata      │
└─────────────────────────────────────────────────────────────────────────┘
```

以流程圖呈現（分層的系統在查詢管線（query pipeline）中向外擴散，並透過資料層（data layer）收斂）：

```mermaid
flowchart TD
    UI[User Interface<br/>Web / Slack / API]
    GW[API Gateway<br/>Auth + rate limit]
    QS[Query Service<br/>Permission + orchestration]

    UI --> GW --> QS

    subgraph PIPELINE[Query Pipeline]
        RS[Retrieval<br/>Hybrid search]
        RR[Reranker<br/>Cross-encoder]
        GS[Generation<br/>Gemini 3 Pro]
        RS --> RR --> GS
    end

    QS --> PIPELINE

    subgraph DATA[Data Layer]
        VDB[(Vector DB)]
        ES[(Search Index)]
        DOC[(Doc Store)]
        META[(Metadata)]
    end

    RS -.semantic.-> VDB
    RS -.keyword.-> ES
    GS -.full text.-> DOC
    QS -.acl.-> META

    GS --> UI
```

### 技術選型（2025 年 12 月更新）

| 元件 | 選擇 | 理由 |
|-----------|--------|-----------|
| **主要 LLM** | Gemini 3.0 Pro | **2.5M context** 原生可處理 100 份以上的文件而不需切碎（fragmentation） |
| **代理型 LLM** | GPT-5.2 | 業界領先的工具使用（tool-use）準確率，適用於複雜的跨文件分析 |
| **檢索器（Retriever）** | Gemini 3 Flash | 在超大 context window 上進行低成本檢索 |
| **Embeddings** | text-embedding-3-large | 品質經過驗證且具成本效益 |
| **Vector DB** | Qdrant（自架） | 兼顧效能、過濾能力與地端（on-prem）合規 |
| **Reranker** | BGE-Reranker-v2-X | 開源的 SoTA，適合地端隔離部署 |

> [!NOTE]
> **轉變：** 正式上線的團隊已從「Small Chunk RAG」轉向 **「Balanced Context RAG」**。在每一個主流前沿模型都具備 1M-2M token context 的情況下，我們不再需要去找出「完美的 512-token chunk」。我們改為檢索整段文件區塊（10k-50k tokens），讓模型原生的 attention 去處理「找針」這件事。

---

## 元件深入剖析

### 文件匯入管線（Ingestion Pipeline）

```python
class IngestionPipeline:
    def __init__(self):
        self.parser = DocumentParser()
        self.chunker = SemanticChunker(
            chunk_size=512,
            chunk_overlap=50
        )
        self.embedder = OpenAIEmbedder(model="text-embedding-3-large")
        self.vector_db = QdrantClient()
        self.metadata_db = PostgresClient()
    
    async def ingest(self, document: Document, user_context: UserContext):
        # 1. Parse document
        parsed = self.parser.parse(document)
        
        # 2. Extract metadata
        metadata = self.extract_metadata(parsed, document)
        
        # 3. Chunk
        chunks = self.chunker.chunk(parsed.text)
        
        # 4. Generate embeddings (batch)
        embeddings = await self.embedder.embed_batch([c.text for c in chunks])
        
        # 5. Store in vector DB with metadata
        points = [
            {
                "id": f"{document.id}_{i}",
                "vector": embedding,
                "payload": {
                    "document_id": document.id,
                    "chunk_index": i,
                    "text": chunk.text,
                    "department": metadata.department,
                    "access_level": metadata.access_level,
                    "created_at": metadata.created_at.isoformat()
                }
            }
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        
        await self.vector_db.upsert(collection="documents", points=points)
        
        # 6. Store full document
        await self.doc_store.put(document.id, parsed.text)
        
        # 7. Store metadata
        await self.metadata_db.insert_document(document.id, metadata)
        
        # 8. Index in Elasticsearch for keyword search
        await self.es_client.index(
            index="documents",
            id=document.id,
            body={"text": parsed.text, **metadata.to_dict()}
        )
```

這段程式碼讀起來像是一連串的線性步驟，但其中有四個寫入（writes）是平行進行的。用序列圖（sequence diagram）把這種扇出（fanout）攤開來看，對於理解「部分失敗」（partial-failure）的模式很重要：

```mermaid
sequenceDiagram
    participant U as Upload Event
    participant P as Parser
    participant C as Chunker
    participant E as Embedder
    participant V as Vector DB
    participant S as Search Index
    participant D as Doc Store
    participant M as Metadata DB

    U->>P: document
    P->>C: parsed text + metadata
    C->>E: chunks
    par Parallel writes
        E->>V: chunk vectors + payloads
        P->>S: full text + metadata
        P->>D: full document blob
        P->>M: document metadata + ACL
    end
    Note over V,M: Document is queryable only<br/>after all four writes commit
```

### 查詢處理（Query Processing）

```python
class QueryService:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.reranker = CohereReranker()
        self.generator = LLMGenerator()
        self.guardrails = GuardrailPipeline()
    
    async def process_query(
        self,
        query: str,
        user_context: UserContext,
        conversation_history: list[Message] = None
    ) -> QueryResponse:
        
        # 1. Input guardrails
        guardrail_result = self.guardrails.check_input(query)
        if not guardrail_result.passed:
            return QueryResponse(
                answer="I cannot help with that request.",
                blocked=True,
                reason=guardrail_result.reason
            )
        
        # 2. Query understanding (optional: rewrite query)
        processed_query = await self.understand_query(query, conversation_history)
        
        # 3. Retrieve candidates with permission filtering
        candidates = await self.retriever.search(
            query=processed_query,
            filters=self.build_permission_filter(user_context),
            top_k=50
        )
        
        # 4. Rerank
        reranked = await self.reranker.rerank(
            query=processed_query,
            documents=candidates,
            top_k=10
        )
        
        # 5. Build context
        context = self.build_context(reranked)
        
        # 6. Generate answer
        answer = await self.generator.generate(
            query=query,
            context=context,
            conversation_history=conversation_history
        )
        
        # 7. Output guardrails
        guardrail_result = self.guardrails.check_output(answer, context)
        if not guardrail_result.passed:
            answer = self.fallback_response()
        
        # 8. Build response with citations
        return QueryResponse(
            answer=answer,
            sources=[self.format_source(doc) for doc in reranked[:5]],
            confidence=self.calculate_confidence(reranked)
        )
    
    def build_permission_filter(self, user_context: UserContext) -> dict:
        return {
            "should": [
                {"key": "access_level", "match": {"value": "public"}},
                {"key": "department", "match": {"value": user_context.department}},
                {"key": "access_list", "match": {"any": [user_context.user_id]}}
            ]
        }
```

### 混合檢索（Hybrid Retrieval）

```python
class HybridRetriever:
    def __init__(self, vector_weight: float = 0.7, keyword_weight: float = 0.3):
        self.vector_db = QdrantClient()
        self.es_client = ElasticsearchClient()
        self.embedder = OpenAIEmbedder()
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
    
    async def search(
        self,
        query: str,
        filters: dict,
        top_k: int = 50
    ) -> list[Document]:
        
        # Parallel retrieval
        vector_results, keyword_results = await asyncio.gather(
            self.vector_search(query, filters, top_k * 2),
            self.keyword_search(query, filters, top_k * 2)
        )
        
        # Reciprocal Rank Fusion
        fused = self.rrf_fusion(
            [vector_results, keyword_results],
            weights=[self.vector_weight, self.keyword_weight],
            k=60
        )
        
        return fused[:top_k]
    
    async def vector_search(self, query: str, filters: dict, top_k: int):
        query_embedding = await self.embedder.embed(query)
        
        results = await self.vector_db.search(
            collection="documents",
            query_vector=query_embedding,
            query_filter=filters,
            limit=top_k
        )
        
        return [
            Document(
                id=r.payload["document_id"],
                chunk_id=r.id,
                text=r.payload["text"],
                score=r.score,
                metadata=r.payload
            )
            for r in results
        ]
    
    def rrf_fusion(self, result_lists: list, weights: list, k: int = 60) -> list:
        scores = defaultdict(float)
        docs = {}
        
        for results, weight in zip(result_lists, weights):
            for rank, doc in enumerate(results):
                rrf_score = weight / (k + rank + 1)
                scores[doc.chunk_id] += rrf_score
                docs[doc.chunk_id] = doc
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [docs[id] for id in sorted_ids]
```

混合檢索流程一覽。兩個平行的檢索器，接著由 RRF 以加權排名（weighted ranks）將兩者融合，再由 cross-encoder 對排序最前面的候選項進行重排（rerank），最後才進行 context 格式化：

```mermaid
flowchart LR
    Q[User Query] --> EMB[Embed Query]
    Q --> KW[Extract Keywords]

    EMB --> VS[Vector Search<br/>top 100]
    KW --> KS[Keyword Search<br/>BM25 top 100]

    VS --> RRF[Reciprocal Rank Fusion<br/>0.7 semantic / 0.3 keyword]
    KS --> RRF

    RRF --> RR[Cross-Encoder Rerank<br/>top 50 to top 10]
    RR --> CTX[Context Format<br/>with citations]
    CTX --> LLM[Generation<br/>Gemini 3 Pro 2.5M ctx]
```

### 以超大 Context 進行生成（2025 年 12 月）

```python
class GeminiGenerator:
    def __init__(self):
        self.client = genai.GenerativeModel("gemini-3.0-pro")
    
    async def generate(
        self,
        query: str,
        context_docs: list[Document],
        conversation_history: list[Message] = None
    ) -> str:
        # 2.5M context allows passing ENTIRE documents, not just snippets
        system_instruction = """
        You are an enterprise knowledge assistant. 
        Analyze the provided documents to answer the query accurately.
        Cite every claim using [[DocName:PageNumber]] format.
        """
        
        contents = [{"text": doc.text} for doc in context_docs]
        contents.append({"text": f"User Query: {query}"})
        
        response = await self.client.generate_content_async(
            contents,
            generation_config=genai.types.GenerationConfig(temperature=0.0)
        )
        return response.text
```

> [!TIP]
> **正式上線的選擇 vs. 最尖端技術**
> 雖然 Gemini 3.1 Pro 提供了 1M-token 的 window，許多正式上線的系統仍然以 **Claude Sonnet 4.6** 或 **GPT-5.5** 作為其主要生成器（generator）的預設選項。
> 
> **為什麼？**
> - **成熟度**：擁有 12 個月以上的正式上線實戰紀錄。
> - **可預測性**：已知的延遲模式，以及在長尾（long-tail）請求上較少出現「幻覺尖峰」（hallucination spikes）。
> - **SDK 穩定度**：與 LangGraph、LlamaIndex 等框架的深度整合。
> - **成本**：針對大量的標準 RAG 進行了優化定價。

---

## 擴展考量

### 處理 500K 份文件

```python
# Sharding strategy for Qdrant
qdrant_config = {
    "collection": "documents",
    "vectors": {
        "size": 3072,  # text-embedding-3-large
        "distance": "Cosine"
    },
    "optimizers": {
        "indexing_threshold": 20000  # Build index after 20K points
    },
    "replication_factor": 2,  # High availability
    "shard_number": 4  # Distribute across nodes
}
```

### 處理 500 名同時在線使用者

```
Load Balancer
     │
     ├──► Query Service (replica 1)
     ├──► Query Service (replica 2)
     ├──► Query Service (replica 3)
     └──► Query Service (replica 4)
            │
            ├──► Vector DB (3-node cluster)
            ├──► LLM API (with retry/fallback)
            └──► Elasticsearch (3-node cluster)
```

### 快取策略

```python
class QueryCache:
    def __init__(self):
        self.exact_cache = Redis(ttl=3600)  # 1 hour
        self.semantic_cache = SemanticCache(threshold=0.95, ttl=1800)
    
    async def get_or_compute(self, query: str, user_context: UserContext) -> QueryResponse:
        # Check exact cache
        cache_key = self.make_key(query, user_context.permissions)
        cached = await self.exact_cache.get(cache_key)
        if cached:
            return cached
        
        # Check semantic cache
        similar = await self.semantic_cache.find_similar(query, user_context.permissions)
        if similar:
            return similar
        
        # Compute
        response = await self.query_service.process_query(query, user_context)
        
        # Cache result
        await self.exact_cache.set(cache_key, response)
        await self.semantic_cache.add(query, user_context.permissions, response)
        
        return response
```

---

## 成本分析

### 每月成本估算（500 名使用者，每位使用者每日 100 次查詢）

| 元件 | 計算方式 | 每月成本 |
|-----------|-------------|--------------|
| LLM（Claude Sonnet） | 1.5M 次查詢 × 2K tokens × $3/1M in + 500 tokens × $15/1M out | ~$20,250 |
| Embeddings | 1.5M 次查詢 × $0.13/1M | ~$200 |
| Reranking（Cohere） | 1.5M × 50 份文件 × $0.001/1K | ~$75 |
| Vector DB（Qdrant Cloud） | 3-node cluster | ~$1,500 |
| Elasticsearch | 3-node cluster | ~$2,000 |
| Compute（Query Service） | 4 個 instances | ~$1,000 |
| **總計** | | **~$25,000/月** |

### 成本優化機會

1. **快取**：30% 的快取命中率（cache hit rate）→ 在 LLM 上節省 $6K
2. **模型路由（Model routing）**：將簡單查詢導向較便宜的模型 → 節省 40%
3. **批次 embeddings**：使用非同步批次處理（async batching）→ 節省 20%
4. **自架 reranker**：以開源方案取代 Cohere → 省下 $75

---

## 經驗教訓

### 哪些做法成效良好

1. **混合搜尋**：結合語意（semantic）+ 關鍵字（keyword）大幅提升了召回率（recall）
2. **重排（Reranking）**：top-5 精準度（precision）提升了 15%
3. **清楚的引用**：建立了使用者的信任
4. **在檢索階段就做權限過濾**：不需要事後（post-hoc）再過濾

### 遭遇的挑戰

1. **表格擷取**：含有複雜表格的 PDF 需要客製化的解析（parsing）
2. **縮寫**：領域專屬的縮寫需要展開
3. **新鮮度**：1 小時的新鮮度要求採用串流匯入（streaming ingestion）
4. **長文件**：100 頁以上的文件需要階層式切塊（hierarchical chunking）

### 如果重來一次會怎麼做

1. 更早一點就從更好的文件解析開始
2. 在擴展之前先建立好評估管線（evaluation pipeline）
3. 從第一天起就實作查詢日誌記錄（query logging）
4. 更早一點與使用者建立回饋迴路（feedback loop）

---

## 面試演練

### 如何在面試中呈現這套設計

**開場（2 分鐘）：**
「我要設計一套用於內部文件搜尋的企業級 RAG 系統。讓我先釐清幾項需求……」

**需求（3 分鐘）：**
- 詢問規模、延遲、準確率的目標
- 釐清安全性需求
- 了解文件類型與更新頻率

**高階設計（5 分鐘）：**
- 畫出架構圖
- 說明關鍵元件
- 為技術選型提出理由

**深入探討（10 分鐘）：**
- 檢索策略（混合搜尋，以及為什麼）
- 安全性（在查詢時進行權限過濾）
- 生成（prompt engineering、引用）
- 擴展（sharding、快取、replicas）

**取捨（5 分鐘）：**
- 成本 vs 延遲（模型選擇）
- 準確率 vs 延遲（重排會增加時間）
- 新鮮度 vs 成本（串流 vs 批次）

**監控（2 分鐘）：**
- 關鍵指標（延遲、準確率、使用者回饋）
- 如何偵測問題
- 持續改善的迴路

---

*下一篇：[案例研究：對話式 AI Agent](02-conversational-agent.md)*
