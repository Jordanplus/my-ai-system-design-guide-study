# AI 系統設計的白板演練

本章提供在 AI 導向面試中常見的系統設計演練的詳細逐步解析。每個演練都包含完整的問題陳述、結構化的解題方法，以及能區分出優秀候選人的討論要點。

## 目錄

- [演練 1：企業級 RAG 系統](#exercise-1-enterprise-rag-system)
- [演練 2：客戶支援聊天機器人](#exercise-2-customer-support-chatbot)
- [演練 3：程式碼審查助理](#exercise-3-code-review-assistant)
- [演練 4：文件處理流程](#exercise-4-document-processing-pipeline)
- [演練 5：即時內容審核](#exercise-5-real-time-content-moderation)
- [演練 6：多租戶 AI 平台](#exercise-6-multi-tenant-ai-platform)
- [演練 7：大規模語意搜尋](#exercise-7-semantic-search-at-scale)
- [白板演練技巧](#tips-for-whiteboard-exercises)

---

## 演練 1：企業級 RAG 系統

### 問題陳述

為一家大型企業設計一套以 RAG 為基礎的知識助理，需求如下：

- 來自多個來源（SharePoint、Confluence、Google Drive、內部 wiki）的 1,000 萬份文件
- 50,000 名員工，採用以角色為基礎的存取控制
- 文件持續更新
- 必須在查詢時遵守文件權限
- 95% 的查詢回應時間需低於 3 秒
- 支援多種語言（英文、西班牙文、中文）

### 時間分配（35 分鐘）

| 階段 | 時間 | 重點 |
|-------|------|-------|
| 釐清 | 3 min | 範圍、優先順序、限制條件 |
| 高層次架構 | 7 min | 元件與資料流 |
| 資料流程 | 8 min | 攝取、分塊、建立索引 |
| 查詢流程 | 8 min | 檢索、生成、權限 |
| 可靠性與擴展性 | 5 min | 故障處理、擴展 |
| 評估 | 4 min | 指標與監控 |

### 解題逐步解析

#### 釐清問題

```
1. What is the document size distribution? (PDFs, wikis, code?)
2. How often do permissions change? (Impacts caching strategy)
3. Is conversation history required or single-turn Q&A?
4. What is the accuracy bar? (Can we say "I don't know"?)
5. Are there compliance requirements? (Audit, data residency)
```

#### 高層次架構

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA PLANE                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐│
│  │   Connectors │───▶│   Processor  │───▶│       Vector Database        ││
│  │ (SP,GD,Conf) │    │ (chunk,embed)│    │  (Pinecone/Qdrant/Weaviate)  ││
│  └──────────────┘    └──────────────┘    └──────────────────────────────┘│
│                                                      ▲                   │
│                                                      │ sync              │
│  ┌──────────────────────────────────────────────────┼───────────────────┐│
│  │                    Permission Service            │                   ││
│  └──────────────────────────────────────────────────┼───────────────────┘│
└─────────────────────────────────────────────────────┼───────────────────┘
                                                      │
┌─────────────────────────────────────────────────────┼───────────────────┐
│                          QUERY PLANE                │                   │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────┴──────┐             │
│  │    User      │───▶│  Query API   │───▶│   Retriever    │             │
│  │  Interface   │    │              │    │ (+ perm filter)│             │
│  └──────────────┘    └──────────────┘    └────────┬───────┘             │
│                             │                      │                     │
│                             ▼                      ▼                     │
│                      ┌──────────────┐    ┌──────────────┐               │
│                      │   Reranker   │◀───│   Chunks     │               │
│                      └──────┬───────┘    └──────────────┘               │
│                             │                                            │
│                             ▼                                            │
│                      ┌──────────────┐    ┌──────────────┐               │
│                      │  Generator   │───▶│   Response   │               │
│                      │    (LLM)     │    │  + Citations │               │
│                      └──────────────┘    └──────────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 資料流程深入剖析

**1. 連接器（Connectors）：**
```
Each source has a dedicated connector:
- SharePoint: Graph API with delta sync
- Confluence: REST API with webhooks
- Google Drive: Drive API with push notifications

Connector responsibilities:
- Fetch document content and metadata
- Track change events (create, update, delete)
- Extract permissions from source system
- Normalize to common document schema
```

**2. 文件結構描述（Document Schema）：**
```json
{
  "doc_id": "uuid",
  "source": "sharepoint|confluence|gdrive",
  "source_id": "original_id_in_source",
  "title": "string",
  "content": "string",
  "content_type": "pdf|html|docx|md",
  "language": "en|es|zh",
  "permissions": {
    "users": ["user_id_1", "user_id_2"],
    "groups": ["group_id_1"],
    "visibility": "private|internal|public"
  },
  "metadata": {
    "author": "string",
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "path": "folder/path"
  }
}
```

**3. 分塊策略（Chunking Strategy）：**
```
Given mixed document types, use adaptive chunking:

- Markdown/HTML: Semantic chunking by headers
- PDFs: Layout-aware chunking using document AI
- Wiki pages: Section-based chunking

Chunk parameters:
- Target size: 512 tokens
- Overlap: 50 tokens
- Preserve: headers, tables, code blocks

Each chunk inherits parent document permissions.
```

**4. Embedding：**
```
Multilingual requirement suggests:
- Model: Cohere embed-v3 (multilingual, good quality)
- Alternative: OpenAI text-embedding-3-large

Batch embedding:
- Process in batches of 100 chunks
- Rate limit handling with exponential backoff
- Store embedding with chunk in vector DB
```

**5. 向量資料庫的選擇：**
```
Pinecone or Qdrant for this scale.

Selection criteria:
- Metadata filtering: Critical for permissions
- Scale: 10M docs × 5 chunks = 50M vectors
- Hybrid search: Needed for keyword queries

Schema:
- Vector: embedding
- Metadata: doc_id, chunk_id, language, permissions, source
```

#### 查詢流程深入剖析

**1. 權限解析（Permission Resolution）：**
```python
def get_user_permissions(user_id: str) -> PermissionSet:
    """
    Resolve all documents user can access.
    Returns set of:
    - Direct user grants
    - Group memberships expanded
    - Public document access
    
    CACHED with 5-minute TTL since permissions change infrequently.
    """
    cache_key = f"permissions:{user_id}"
    if cached := cache.get(cache_key):
        return cached
    
    perms = permission_service.resolve(user_id)
    cache.set(cache_key, perms, ttl=300)
    return perms
```

**2. 帶過濾的檢索（Retrieval with Filtering）：**
```python
def retrieve(query: str, user_id: str, top_k: int = 20) -> List[Chunk]:
    perms = get_user_permissions(user_id)
    
    # Detect language for query
    lang = detect_language(query)
    
    # Build permission filter
    # User can see: public docs, their own, or groups they belong to
    filter = {
        "$or": [
            {"visibility": "public"},
            {"users": {"$in": [user_id]}},
            {"groups": {"$in": perms.groups}}
        ]
    }
    
    # Optional: boost same-language content
    if lang != "en":
        filter["language"] = lang
    
    results = vector_db.search(
        query_embedding=embed(query),
        top_k=top_k,
        filter=filter
    )
    return results
```

**3. 重新排序（Reranking）：**
```
Rerank top-20 to get top-5 with cross-encoder.
Model: bge-reranker-v2-m3 (multilingual)
Latency budget: ~100ms
```

**4. 生成（Generation）：**
```python
def generate(query: str, chunks: List[Chunk], user_id: str) -> Response:
    context = format_chunks_with_citations(chunks)
    
    prompt = f"""You are a knowledge assistant for [Company].
Answer the question using ONLY the provided context.
If the context does not contain the answer, say "I could not find information about that in our knowledge base."
Always cite sources using [1], [2] format.

CONTEXT:
{context}

QUESTION: {query}
"""
    
    response = llm.generate(
        prompt=prompt,
        model="gpt-4o",
        temperature=0.1
    )
    
    return format_with_source_links(response, chunks)
```

#### 擴展性與可靠性

**延遲預算（p95 < 3s）：**
```
Permission resolution:   50ms  (cached)
Embedding:              100ms
Vector search:          100ms
Reranking:              150ms
LLM generation:        1500ms
Network/overhead:       100ms
─────────────────────────────
Total:                 2000ms (buffer for P95)
```

**擴展考量：**
```
- Vector DB: Sharded by source or hash
- Embedding service: Horizontal scale, stateless
- LLM calls: Multiple providers for redundancy
- Cache: Redis cluster for permissions and responses
```

**故障處理：**
```
- Vector DB down: Return cached results + degraded warning
- LLM down: Fallback to secondary provider
- Rate limiting: Queue with backpressure
- Embedding service: Batch retries with circuit breaker
```

#### 評估方法

**離線指標：**
```
- Retrieval: Precision@5, Recall@5, MRR
- Generation: RAGAS (faithfulness, relevance)
- End-to-end: Answer correctness on test set
```

**線上指標：**
```
- User feedback: Thumbs up/down
- Query reformulation rate: User rephrasing indicates failure
- Citation click-through: Are sources useful?
```

**監控：**
```
- Latency dashboards by percentile
- Permission filter hit rate
- Empty result rate by source
- Cost per query
```

---

## 演練 2：客戶支援聊天機器人

### 問題陳述

為一家電子商務公司設計一套由 AI 驅動的客戶支援系統：

- 每天處理 10,000 次對話
- 可存取產品目錄（100 萬項產品）、訂單歷史與 FAQ
- 目標：在不轉接真人的情況下解決 70% 的工單
- 支援訂單查詢、退貨、產品問題
- 多語言支援（3 種語言）
- 與既有的 Zendesk 工單系統整合

### 解題重點

**關鍵架構決策：**

1. **具流程控制的 Agent 架構：**
```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   ┌─────────┐     ┌─────────────┐     ┌─────────────┐   │
│   │ Intake  │────▶│  Classify   │────▶│   Router    │   │
│   └─────────┘     └─────────────┘     └──────┬──────┘   │
│                                              │           │
│         ┌────────────────┬──────────────────┼───────┐   │
│         ▼                ▼                  ▼       ▼   │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐ ┌─────┐ │
│   │Order Flow │   │Product Q&A│   │ Returns   │ │Human│ │
│   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘ └─────┘ │
│         │               │               │               │
│         └───────────────┴───────────────┘               │
│                         │                               │
│                   ┌─────▼─────┐                         │
│                   │  Response │                         │
│                   │ Generator │                         │
│                   └───────────┘                         │
└─────────────────────────────────────────────────────────┘
```

2. **工具設計（Tool Design）：**
```python
tools = [
    {
        "name": "lookup_order",
        "description": "Look up order details by order ID or customer email",
        "parameters": {
            "order_id": "optional string",
            "email": "optional string"
        }
    },
    {
        "name": "search_products",
        "description": "Search product catalog",
        "parameters": {
            "query": "string",
            "category": "optional string",
            "price_range": "optional tuple"
        }
    },
    {
        "name": "create_return",
        "description": "Initiate a return for an order",
        "parameters": {
            "order_id": "string",
            "reason": "string",
            "items": "list of item IDs"
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Transfer to human agent",
        "parameters": {
            "reason": "string",
            "priority": "low|medium|high"
        }
    }
]
```

3. **升級標準（Escalation Criteria）：**
```
Escalate to human when:
- Customer explicitly requests human
- Sentiment is highly negative (detected by classifier)
- Issue involves payment disputes
- Agent confidence is low after 2 attempts
- Complex multi-order issues
- Refund above threshold amount
```

4. **整合模式（Integration Pattern）：**
```
Zendesk integration:
- Webhook receives new tickets
- AI handles via API
- Resolution → close ticket
- Escalation → assign to queue with context summary
- All interactions logged to ticket timeline
```

---

## 演練 3：程式碼審查助理

### 問題陳述

為一個開發平台設計一套程式碼審查助理：

- 自動審查 pull request
- 提供具體、可執行的回饋
- 遵守 repository 的風格指南與慣例
- 能夠建議程式碼修正
- 與 GitHub/GitLab 整合
- 每天處理 50,000 個 PR

### 解題重點

**關鍵技術選擇：**

1. **脈絡組裝（Context Assembly）：**
```
For each changed file, assemble context:
- The diff (changed lines)
- Full file content (for understanding)
- Related files (imports, tests, types)
- Repository conventions (.eslintrc, .editorconfig)
- Previous review comments (learn from feedback)
```

2. **審查類別（Review Categories）：**
```python
review_types = [
    "bug_risk",           # Potential bugs
    "security",           # Security issues
    "performance",        # Performance concerns
    "maintainability",    # Code quality
    "style",              # Style guide violations
    "test_coverage"       # Missing tests
]
```

3. **模型選擇（Model Selection）：**
```
Primary: Claude 3.5 Sonnet (best for code understanding)
Fallback: GPT-4o

Specialized models:
- Security scanning: CodeQL + LLM review
- Style: Linters + LLM explanation
```

4. **輸出格式（Output Format）：**
```markdown
## Review Summary

### Critical Issues (must fix)
- **Line 45**: SQL injection vulnerability in user query
  ```python
  # Instead of:
  query = f"SELECT * FROM users WHERE id = {user_id}"
  # Use:
  query = "SELECT * FROM users WHERE id = ?"
  cursor.execute(query, (user_id,))
  ```

### Suggestions (consider fixing)
- **Line 78-82**: This loop could be simplified using list comprehension
...
```

5. **延遲策略（Latency Strategy）：**
```
Target: Review ready within 2 minutes of PR creation

Strategy:
- Queue PR for processing
- Parallel processing of files
- Stream results as available
- Cache repository conventions
```

---

## 演練 4：文件處理流程

### 問題陳述

為金融服務業設計一套文件處理流程：

- 每天處理 100,000 份文件（發票、合約、表單）
- 以 99% 的準確率擷取結構化資料
- 處理 PDF、掃描文件、手寫筆記
- 符合 HIPAA/SOC2 規範
- 對低信心度的擷取結果進行人工審查

### 解題重點

**流程架構：**

```
┌────────┐   ┌───────────┐   ┌────────────┐   ┌────────────┐
│ Ingest │──▶│ Classify  │──▶│  Extract   │──▶│  Validate  │
└────────┘   └───────────┘   └────────────┘   └────────────┘
                                                     │
                                     ┌───────────────┼───────────────┐
                                     ▼               ▼               ▼
                              ┌──────────┐   ┌──────────┐   ┌──────────┐
                              │ Auto-pass│   │  Review  │   │  Reject  │
                              └──────────┘   └──────────┘   └──────────┘
```

**關鍵元件：**

1. **文件分類（Document Classification）：**
```
Fine-tuned classifier on document types:
- Invoice, Contract, Receipt, Form, ID, Other

Model: LayoutLMv3 or fine-tuned ViT
Confidence threshold: 0.95 for auto-routing
```

2. **擷取策略（Extraction Strategy）：**
```
Tiered extraction based on document type:

Tier 1: Document AI (Textract/Azure)
- Good for structured forms
- Fast and cheap
- Returns confidence scores

Tier 2: Vision LLM (GPT-4V/Claude)
- Fallback for complex layouts
- Better for unstructured text
- More expensive

Combine outputs and cross-validate.
```

3. **驗證規則（Validation Rules）：**
```python
validation_rules = {
    "invoice": [
        ("total", lambda x: x > 0, "Total must be positive"),
        ("date", lambda x: parse_date(x), "Invalid date format"),
        ("vendor_id", lambda x: regex_match(x, TAX_ID_PATTERN), "Invalid tax ID"),
        ("line_items", lambda x: sum(i.amount for i in x) == total, "Line items must sum to total")
    ],
    "contract": [
        ("parties", lambda x: len(x) >= 2, "Contract must have at least 2 parties"),
        ("effective_date", lambda x: parse_date(x), "Invalid date"),
        ("signature_present", lambda x: x == True, "Signature required")
    ]
}
```

4. **人工審查介面（Human Review Interface）：**
```
Reviewer sees:
- Original document image
- Extracted fields with confidence scores
- Validation errors highlighted
- Suggested corrections from LLM
- One-click approval or field-level corrections
```

5. **合規措施（Compliance Measures）：**
```
HIPAA/SOC2 requirements:
- All documents encrypted at rest (AES-256)
- TLS 1.3 in transit
- Audit log for all access and changes
- PHI detection and masking
- Retention policies enforced
- Access controls with MFA
```

---

## 演練 5：即時內容審核

### 問題陳述

為一個社群平台設計一套內容審核系統：

- 每天 100 萬則貼文（文字、圖片、影片）
- 延遲需求：貼文在 500ms 內可見
- 偵測：仇恨言論、暴力、成人內容、垃圾訊息
- 針對誤判提供申訴流程
- 支援 10 種語言

### 解題重點

**架構模式：多階段串接（Multi-Stage Cascade）**

```
         ┌───────────────────────────────────────────┐
         │              Fast Filters                 │
         │   (regex, blocklist, hash matching)       │
         └─────────────────┬─────────────────────────┘
                           │ Pass 95%
                           ▼
         ┌───────────────────────────────────────────┐
         │            ML Classifiers                 │
         │   (text: BERT, image: CLIP, video: X3D)   │
         └─────────────────┬─────────────────────────┘
                           │ Uncertain 5%
                           ▼
         ┌───────────────────────────────────────────┐
         │            LLM Analysis                   │
         │   (context-aware, nuanced decisions)      │
         └─────────────────┬─────────────────────────┘
                           │ Still uncertain 0.5%
                           ▼
         ┌───────────────────────────────────────────┐
         │            Human Review                   │
         └───────────────────────────────────────────┘
```

**關鍵設計決策：**

1. **延遲優化（Latency Optimization）：**
```
Target: 500ms total

Stage 1 (Fast): 20ms
- Regex patterns
- Known hash matching (PhotoDNA)
- Blocklist lookup

Stage 2 (ML): 80ms
- Batched inference on GPU
- Small specialized models
- Parallel text/image processing

Stage 3 (LLM): 400ms (async for borderline)
- Only 5% of content reaches here
- Used for nuanced decisions
```

2. **門檻策略（Threshold Strategy）：**
```python
class ModerationDecision:
    BLOCK = "block"          # High confidence violation
    ALLOW = "allow"          # High confidence safe
    LIMIT = "limit"          # Reduce distribution
    REVIEW = "human_review"  # Queue for human

thresholds = {
    "hate_speech": {
        "block": 0.95,
        "limit": 0.80,
        "review": 0.60
    },
    "adult_content": {
        "block": 0.98,  # Higher threshold, legal implications
        "limit": 0.90,
        "review": 0.70
    }
}
```

3. **申訴流程（Appeal Workflow）：**
```
1. User submits appeal
2. Content queued for human review
3. Different reviewer than original (blind review)
4. Decision logged with reasoning
5. If overturned:
   - Content restored
   - Original decision added to training data as negative
   - Model retrained periodically
```

---

## 演練 6：多租戶 AI 平台

### 問題陳述

設計一個多租戶 AI 平台（AI-as-a-Service）：

- 服務 500+ 家企業客戶
- 每家客戶擁有自己的文件與模型
- 租戶之間完全的資料隔離
- 各租戶的用量追蹤與計費
- 不同定價方案具備不同的功能
- 必須符合 SOC2 規範

### 解題重點

**租戶隔離架構：**

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │   Auth → Tenant Context → Rate Limit → Route             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Tenant-Aware Service Layer                    │
│                                                                  │
│  All operations scoped to tenant_id from context                │
│  - Retrieval filters by tenant                                  │
│  - Cache keys prefixed by tenant                                │
│  - Audit logs include tenant                                    │
└─────────────────────────────────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Shared Vector  │ │  Shared LLM     │ │  Shared Object  │
│  DB (filtered)  │ │  (no tenant     │ │  Storage        │
│                 │ │   data in prompt│ │  (tenant paths) │
│  tenant_id in   │ │   history)      │ │                 │
│  all metadata   │ │                 │ │  s3://bucket/   │
└─────────────────┘ └─────────────────┘ │  {tenant_id}/   │
                                        └─────────────────┘
```

**關鍵隔離點：**

```python
class TenantContext:
    tenant_id: str
    user_id: str
    tier: str  # "starter" | "pro" | "enterprise"
    
    def __enter__(self):
        # Set tenant context for all downstream calls
        _tenant_context.set(self)
        
    def __exit__(self, *args):
        _tenant_context.set(None)

# Middleware ensures tenant context on every request
@middleware
def enforce_tenant_context(request, call_next):
    tenant_id = extract_tenant_from_token(request.headers["Authorization"])
    with TenantContext(tenant_id=tenant_id, ...):
        verify_tenant_access(tenant_id, request.path)
        response = call_next(request)
        add_tenant_to_audit_log(tenant_id, request, response)
    return response
```

**計費與用量追蹤：**

```python
usage_schema = {
    "tenant_id": "string",
    "timestamp": "datetime",
    "operation": "embed|retrieve|generate",
    "model": "string",
    "tokens_in": "int",
    "tokens_out": "int",
    "latency_ms": "int",
    "cost_cents": "decimal"
}

# Real-time usage aggregation
async def track_usage(tenant_id: str, operation: Usage):
    # Append to time-series DB
    await timeseries.write("usage", {
        "tenant_id": tenant_id,
        **operation.dict()
    })
    
    # Update real-time counter for rate limiting
    await redis.incr(f"usage:{tenant_id}:{today()}", operation.tokens)
```

---

## 演練 7：大規模語意搜尋

### 問題陳述

為一個電子商務網站設計一套語意搜尋系統：

- 5,000 萬項產品
- 每天 1 億次查詢
- P99 延遲低於 100ms
- 支援過濾條件（價格、類別、品牌、評分）
- 根據使用者歷史進行個人化
- 即時庫存更新

### 解題重點

**關鍵挑戰：在每天 1 億次查詢下達到 100ms**

```
100M queries/day = 1,157 QPS average
Peak: 5,000-10,000 QPS

At 100ms latency, need:
- Edge caching
- Pre-computed embeddings
- Optimized retrieval
- Minimal LLM involvement
```

**架構：**

```
┌────────────────────────────────────────────────────────────┐
│                         CDN/Edge                            │
│              (Cache popular queries: ~30% hit)              │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                      Query Service                          │
│  1. Embed query (cached embeddings for common queries)      │
│  2. Retrieve candidates (ANN search)                        │
│  3. Apply filters (post-filter or hybrid)                   │
│  4. Personalize ranking                                     │
│  5. Return results                                          │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                    Vector Database Cluster                  │
│  - Sharded by category (reduce search space)                │
│  - HNSW index with ef_search tuned for speed                │
│  - Metadata filtering with roaring bitmaps                  │
└────────────────────────────────────────────────────────────┘
```

**延遲預算：**

```
Edge cache check:    5ms
Embedding lookup:   10ms (cached) or 30ms (compute)
Vector search:      30ms
Filtering:          10ms
Personalization:    10ms
Serialization:      10ms
Network overhead:   25ms
─────────────────────
Total:              100ms target (with cache hit)
```

**混合搜尋策略（Hybrid Search Strategy）：**

```python
def search(query: str, filters: dict, user_id: str) -> List[Product]:
    # Determine search strategy based on query
    if is_keyword_heavy(query):
        # "nike air max 90 size 10"
        sparse_weight = 0.7
        dense_weight = 0.3
    else:
        # "comfortable running shoes for flat feet"
        sparse_weight = 0.3
        dense_weight = 0.7
    
    # Parallel retrieval
    dense_results = vector_db.search(embed(query), top_k=100, filter=filters)
    sparse_results = elastic.search(query, top_k=100, filter=filters)
    
    # Reciprocal rank fusion
    combined = rrf_merge(
        [dense_results, sparse_results],
        weights=[dense_weight, sparse_weight]
    )
    
    # Personalization boost
    personalized = apply_user_preferences(combined, user_id)
    
    return personalized[:20]
```

**即時更新：**

```
Product updates (price, inventory) flow:
1. Change event published to Kafka
2. Consumer updates vector DB metadata
3. Search reflects change within seconds

Reindexing (description changes):
1. Full re-embed required
2. Run as async job
3. Swap index when complete
```

---

## 白板演練技巧

### 繪圖技巧

1. **先畫出方塊與標籤**，再用箭頭連接
2. **使用一致的標記法**：以矩形代表服務、以圓柱代表資料庫、以箭頭代表資料流
3. **在箭頭上標註資料**：說明各元件之間流動的內容
4. **預留空間**，以便在討論時補充內容

### 應掌握的常見模式

| 模式 | 適用時機 | 畫法 |
|---------|-------------|---------|
| 負載平衡器 + 服務叢集 | 任何需要擴展的服務 | LB → 多個方塊 |
| 佇列 + worker | 非同步處理 | 佇列 → worker pool |
| 快取層 | 讀取密集、對延遲敏感 | 在服務前放一個菱形 |
| CDC/串流 | 即時更新 | Kafka/串流圖示 |
| Sidecar | 橫切關注點 | 附加在服務旁的小方塊 |

### 顯示候選人實力的用語

- 「在我設計這個之前，先讓我了解一下規模……」
- 「這裡的取捨是……」
- 「在正式環境中，我們還需要……」
- 「一個需要考量的故障模式是……」
- 「讓我帶你走過一遍延遲預算……」
- 「在評估方面，我會衡量……」

### 時間管理

- 釐清問題不要花超過 5 分鐘
- 在深入細節之前，先畫出完整的高層次全貌
- 預留時間給可靠性與評估
- 與面試官確認重點關注的領域

---

*另見：[題庫](01-question-bank.md) | [解題框架](02-answer-frameworks.md) | [常見陷阱](03-common-pitfalls.md)*
