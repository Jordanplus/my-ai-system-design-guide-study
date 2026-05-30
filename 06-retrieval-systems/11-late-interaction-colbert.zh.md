# Late Interaction 與 ColBERT

Late Interaction 是一種檢索範式，介於快速但不精確的 **bi-encoder** 與精確但緩慢的 **cross-encoder** 之間。ColBERT（Contextualized Late Interaction over BERT）是這個領域的代表性模型，能以 bi-encoder 等級的速度達到 cross-encoder 等級的準確度。late-interaction 這一系列已經成熟為高精度搜尋的正式生產級替代方案，並擁有多模態的延伸版本（ColPali、ColQwen2.5、ColNomic，以及像 Wholembed v3 這類統一檢索器），如今都納入同一套工具組之中。

## 目錄

- [檢索架構光譜](#spectrum)
- [ColBERT 架構](#colbert-architecture)
- [MaxSim：核心評分機制](#maxsim)
- [ColBERTv2 與 PLAID 索引](#colbertv2)
- [Late Interaction 與其他方案的比較](#comparison)
- [使用 RAGatouille 實作](#ragatouille)
- [生產環境部署模式](#production)
- [何時該選擇 ColBERT](#when-to-choose)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 檢索架構光譜

神經檢索有三種基本架構。理解 late interaction 落在何處，正是貫穿整個章節的關鍵。

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   SPEED ◄──────────────────────────────────────────────► ACCURACY   │
│                                                                     │
│   Bi-Encoder          Late Interaction          Cross-Encoder       │
│   (Single Vector)     (Multi-Vector)            (Full Attention)    │
│                                                                     │
│   ● Fast (< 10ms)     ● Balanced (10-50ms)      ● Slow (100ms+)   │
│   ● Low accuracy       ● High accuracy           ● Highest accuracy│
│   ● Scales to 1B+     ● Scales to 100M+         ● Scales to 10K   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 每種架構如何處理一組查詢-文件配對

```
BI-ENCODER (e.g., E5, BGE):
  Query  ──► Encoder ──► [1 vector]  ─┐
                                      ├──► dot product ──► score
  Doc    ──► Encoder ──► [1 vector]  ─┘

  Total interaction: 1 comparison

─────────────────────────────────────────────

LATE INTERACTION (ColBERT):
  Query  ──► Encoder ──► [N vectors] ─┐
                (one per token)       ├──► MaxSim ──► score
  Doc    ──► Encoder ──► [M vectors] ─┘
                (one per token)

  Total interaction: N x M comparisons (but decomposable)

─────────────────────────────────────────────

CROSS-ENCODER (e.g., ms-marco-MiniLM):
  [Query + Doc] ──► Encoder ──► score

  Total interaction: Full self-attention across
                     all query AND document tokens
```

**洞察**：關鍵差異在於查詢與文件「何時」進行互動。Bi-encoder 從不互動（各自獨立編碼）。Cross-encoder 完全互動（聯合編碼）。Late interaction 則是折衷地帶：各自獨立編碼，再以低成本在 token 層級進行互動。

---

## ColBERT 架構

ColBERT 將查詢與文件編碼成 **token 層級 embedding 的矩陣**（而非單一向量），並透過細粒度的 token 互動來評分。

### 編碼階段

```
Query: "What is the price of Widget-X?"

Token Embeddings (each 128-dim):
  q1 = Embed("What")     = [0.12, -0.34, ..., 0.08]
  q2 = Embed("is")       = [0.05, -0.11, ..., 0.22]
  q3 = Embed("the")      = [0.01, -0.02, ..., 0.15]
  q4 = Embed("price")    = [0.45,  0.67, ..., 0.91]  ◄── high signal
  q5 = Embed("of")       = [0.03, -0.05, ..., 0.11]
  q6 = Embed("Widget-X") = [0.88,  0.21, ..., 0.73]  ◄── high signal

Document: "Widget-X costs $200 per month for the Standard plan"

Token Embeddings:
  d1 = Embed("Widget-X")  = [0.85,  0.19, ..., 0.71]
  d2 = Embed("costs")     = [0.42,  0.63, ..., 0.88]
  d3 = Embed("$200")      = [0.31,  0.55, ..., 0.79]
  d4 = Embed("per")       = [0.02, -0.01, ..., 0.09]
  d5 = Embed("month")     = [0.11,  0.08, ..., 0.14]
  d6 = Embed("Standard")  = [0.38,  0.44, ..., 0.62]
  d7 = Embed("plan")      = [0.29,  0.37, ..., 0.51]
```

**關鍵設計選擇**：ColBERT 採用 **128 維** 的 token embedding（相較於標準 bi-encoder 的 768-1024 維）。這個較小的維度對儲存效率至關重要，因為我們為每份文件儲存的是 N 個向量，而非 1 個。

### 離線運算與線上運算

| 元件 | 何時進行 | 成本 |
|-----------|------|------|
| 文件編碼 | 離線（建立索引時） | 一次性、可平行化 |
| 查詢編碼 | 線上（每次查詢） | 快速（在 GPU 上約 5-10ms） |
| MaxSim 評分 | 線上（每次查詢） | token 層級運算，由 PLAID 最佳化 |

**正是這種拆解讓 ColBERT 變得快速**：文件只需預先編碼一次。在查詢時，只有查詢需要編碼，而評分則是針對預先計算好的向量進行的簡單算術運算。

---

## MaxSim：核心評分機制

MaxSim（Maximum Similarity，最大相似度）是讓 late interaction 得以運作的運算子。它在概念上很簡單，威力卻出乎意料地強大。

### MaxSim 如何運作

```
For each query token qi:
  1. Compute dot product with EVERY document token dj
  2. Keep only the MAXIMUM score

Score(Q, D) = SUM over all qi of MAX over all dj of (qi . dj)
```

### 範例演算

```
            d1        d2       d3       d4       d5
          Widget-X   costs    $200     per     month
  q4       0.41      0.89*    0.73     0.01     0.05
  price
  q6       0.95*     0.38     0.27     0.01     0.03
  Widget-X

  * = maximum for that query token

  MaxSim contribution from q4 ("price"): 0.89 (matched "costs")
  MaxSim contribution from q6 ("Widget-X"): 0.95 (matched "Widget-X")

  Total Score = sum of all max values across all query tokens
```

### 為何 MaxSim 勝過單一向量相似度

| 特性 | 單一向量（內積） | MaxSim（Late Interaction） |
|----------|----------------------------|--------------------------|
| **粒度** | 文件層級 | token 層級 |
| **部分匹配** | 全有或全無 | 各 token 獨立匹配 |
| **詞彙重要性** | 壓縮進 1 個向量 | 每個 token 各自貢獻 |
| **罕見詞** | 被平均稀釋 | 以獨立向量保留 |

**直覺**：在 bi-encoder 中，「Widget-X」的語意會與「costs」、「$200」以及其他所有 token 一起被平均成單一向量。如果「Widget-X」很罕見，它的訊號就會被稀釋。而在 ColBERT 中，「Widget-X」保留了自己專屬的向量，因此 MaxSim 運算子能夠獨立地為它找到強而有力的匹配。

---

## ColBERTv2 與 PLAID 索引

最初的 ColBERT（2020）有一個關鍵限制：**儲存**。為每份文件中的每個 token 都儲存 128 維向量的成本相當高昂。一個包含 1,000 萬份文件、每份各 200 個 token 的語料庫，將需要約 256 GB 的向量儲存空間。

### ColBERTv2 的改進（2021）

ColBERTv2 引入了兩項關鍵創新：

**1. 殘差壓縮（Residual Compression）**：

```
Original ColBERT:
  Each token vector: 128 dims x 32-bit float = 512 bytes

ColBERTv2 Residual Compression:
  1. Cluster all token vectors into centroids (k-means)
  2. Store only the centroid ID + residual (difference)
  3. Quantize the residual to 1-2 bits per dimension

  Each token vector: ~16-32 bytes (16-32x compression)
```

**2. 去噪監督（Denoised Supervision）**：
- 在從 cross-encoder teacher 挖掘出的 hard negative 上進行訓練
- cross-encoder 標籤可「清理」帶有雜訊的訓練資料
- 結果：儘管經過壓縮，仍能得到品質更佳的 embedding

**ColBERTv2 儲存空間比較**：

| 系統 | 每 token 儲存量 | 1,000 萬份文件（每份 200 token） |
|--------|------------------|---------------------------|
| ColBERT v1 | 512 bytes | ~1 TB |
| ColBERTv2（壓縮後） | 32 bytes | ~64 GB |
| Bi-encoder（每份文件 1 向量） | 3 KB | ~30 GB |

### PLAID：索引引擎

PLAID（Performance-optimized Late Interaction Driver）是讓 ColBERT 能在大規模下實用化的索引與檢索引擎。

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLAID RETRIEVAL PIPELINE                     │
│                                                                 │
│  Stage 1: CENTROID PRUNING                                      │
│  ─────────────────────────                                      │
│  For each query token, find nearest centroids                   │
│  Collect candidate passages that contain those centroids        │
│  Result: ~10,000 candidates from millions                       │
│                                                                 │
│  Stage 2: CENTROID INTERACTION                                  │
│  ─────────────────────────────                                  │
│  Approximate MaxSim using centroid-level scores only            │
│  Filter candidates to top ~1,000                                │
│                                                                 │
│  Stage 3: CENTROID PRUNING (Fine)                               │
│  ──────────────────────────────                                 │
│  Decompress residuals for remaining candidates                  │
│  Compute approximate MaxSim with residual vectors               │
│  Filter to top ~100                                             │
│                                                                 │
│  Stage 4: FULL DECOMPRESSION                                    │
│  ────────────────────────────                                   │
│  Fully decompress token vectors for top candidates              │
│  Compute exact MaxSim                                           │
│  Return final ranked results                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**關鍵洞察**：PLAID 避免為所有文件解壓縮所有向量。每個階段都以低成本篩選候選集合，使得昂貴的精確評分只會在語料庫中極小的一部分上進行。

**PLAID 效能**：
- 在單一 GPU 上於 **50-100ms** 內從 1,000 萬份以上文件中完成檢索
- 維持 **精確 MaxSim** 的準確度（而非近似值）
- 利用 centroid pruning，在進行完整評分前略過語料庫的 99% 以上

---

## Late Interaction 與其他方案的比較

### 全面比較

| 面向 | BM25 | Bi-Encoder | ColBERT（Late） | Cross-Encoder |
|-----------|------|-----------|----------------|---------------|
| **編碼方式** | 詞頻 | 每份文件 1 向量 | 每份文件 N 向量 | 聯合（無預先計算） |
| **查詢延遲** | ~5ms | ~10ms | ~30-50ms | 每配對 ~500ms+ |
| **可擴展性** | 數十億 | 數十億 | 1 億以上 | ~10K（僅重新排序） |
| **儲存（100 萬份文件）** | ~2 GB | ~3 GB | ~6-12 GB | 0（無索引） |
| **準確度（NDCG@10）** | 0.30-0.35 | 0.35-0.40 | 0.39-0.44 | 0.42-0.46 |
| **領域遷移** | 強（詞彙層級） | 弱（需要 fine-tuning） | 強（token 層級） | 最強 |
| **建置複雜度** | 低 | 中 | 高 | 低（無索引） |

### ColBERT 何時勝出

```
                  ▲ Accuracy
                  │
             0.45 ┤                     ● Cross-Encoder
                  │                   ●
             0.40 ┤              ● ColBERT
                  │         ●
             0.35 ┤    ● Bi-Encoder
                  │ ●
             0.30 ┤ BM25
                  │
                  └────┬────┬────┬────┬────┬──► Throughput (QPS)
                      10   100  1K   10K  100K
```

**ColBERT 佔據了甜蜜點**：在特定領域的基準測試上，它的準確度是 bi-encoder 的 3-5 倍（在專門資料集上 mAP 最高可達 +13.8%），同時又比 cross-encoder 快上 10-50 倍。

---

## 使用 RAGatouille 實作

RAGatouille（由 Answer.AI 開發）是在 RAG 流程中使用 ColBERT 的標準 Python 函式庫。它以簡潔的高階 API 封裝了 Stanford 的 ColBERT 程式碼庫。

### 基本用法

```python
from ragatouille import RAGPretrainedModel

# Load a pretrained ColBERT model
RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

# Index documents (one-time, creates PLAID index on disk)
documents = [
    "Widget-X costs $200 per month for the Standard plan.",
    "The Enterprise plan includes SSO and audit logs for $800/month.",
    "All plans include 99.9% uptime SLA and 24/7 email support.",
    "Widget-X was launched in 2023 and serves 10,000+ customers.",
]

index_path = RAG.index(
    index_name="products",
    collection=documents,
    split_documents=True  # auto-chunk long docs
)

# Search the index
results = RAG.search(
    query="How much does Widget-X cost?",
    k=3
)

for result in results:
    print(f"Score: {result['score']:.4f}")
    print(f"Text:  {result['content']}\n")
```

### 與 LangChain 整合

```python
from ragatouille import RAGPretrainedModel
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Create ColBERT retriever
RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
retriever = RAG.as_langchain_retriever(k=5)

# Build RAG chain
template = """Answer based on the following context:
{context}

Question: {question}"""

prompt = ChatPromptTemplate.from_template(template)
llm = ChatOpenAI(model="gpt-4o")

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
)

response = chain.invoke("What features does the Enterprise plan include?")
```

### 其他 ColBERT 函式庫與整合方案

| 函式庫 | 使用情境 | 備註 |
|---------|----------|-------|
| **RAGatouille** | Python 優先、API 簡潔 | 最適合原型開發與中小規模 |
| **colbert-ai**（Stanford） | 研究用途、完整掌控 | 較為底層、提供更多設定選項 |
| **Vespa** | 生產級規模部署 | 託管基礎設施，原生支援 ColBERT |
| **PyLate** | 彈性的訓練／fine-tuning | 建構於 Sentence Transformers 之上，適合客製化模型 |
| **Jina ColBERT v2** | 多語言（89 種語言） | 輸出維度可彈性調整，已達生產級 |

---

## 生產環境部署模式

### 模式 1：ColBERT 作為主要檢索器

```
Query ──► ColBERT (PLAID) ──► Top 20 ──► LLM
```

最適合：中等規模語料庫（100 萬至 5,000 萬份文件），準確度至為重要且你能負擔額外的儲存開銷。

### 模式 2：ColBERT 作為重新排序器（最常見）

```
Query ──► BM25 or Bi-Encoder ──► Top 1000 ──► ColBERT Rerank ──► Top 20 ──► LLM
```

最適合：大規模系統，其中第一階段檢索必須低成本，但你又需要高品質的重新排序，且不願承擔 cross-encoder 的成本。

```
┌─────────────────────────────────────────────────────────────────┐
│              COLBERT-AS-RERANKER ARCHITECTURE                   │
│                                                                 │
│  User Query                                                     │
│      │                                                          │
│      ▼                                                          │
│  First Stage: BM25 / Bi-Encoder                                 │
│  (cheap, high recall, Top 1000)                                 │
│      │                                                          │
│      ▼                                                          │
│  Second Stage: ColBERT MaxSim Reranking                         │
│  (pre-computed doc tokens, score Top 1000)                      │
│  Cost: only query encoding + MaxSim arithmetic                  │
│      │                                                          │
│      ▼                                                          │
│  Top 20 Passages ──► LLM Generation                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 模式 3：混合式（ColBERT + BM25 + Dense）

```
Query ──┬──► BM25 (Top 50) ────────┐
        ├──► Dense Bi-Encoder (50) ─┼──► RRF ──► ColBERT Rerank ──► Top 10
        └──► ColBERT (Top 50) ─────┘
```

最適合：在中等規模下追求最高準確度。成本高昂，但涵蓋了所有檢索模態。

### 儲存與基礎設施考量

| 語料庫規模 | Bi-Encoder 儲存量 | ColBERT 儲存量 | GPU 需求 |
|------------|-------------------|-----------------|-----------------|
| 10 萬份文件 | ~300 MB | ~600 MB - 1.2 GB | 純 CPU 即可 |
| 100 萬份文件 | ~3 GB | ~6-12 GB | 建議 1 顆 GPU |
| 1,000 萬份文件 | ~30 GB | ~60-120 GB | 需要 1-2 顆 GPU |
| 1 億份文件 | ~300 GB | ~600 GB - 1.2 TB | 多 GPU／分散式 |

**現實檢視**：ColBERT 的儲存量是 bi-encoder 的 2-4 倍。對多數 RAG 使用情境（1,000 萬份文件以下）而言，這是可控的。但對網路規模的搜尋（數十億頁面）來說，在第一階段檢索上，bi-encoder 或 learned sparse 方法仍然更為實際。

---

## 何時該選擇 ColBERT

### 決策框架

```
Is your corpus < 100M documents?
├── No  ──► Use Bi-Encoder for retrieval + ColBERT for reranking
└── Yes
    │
    Is accuracy more important than infrastructure simplicity?
    ├── No  ──► Use Bi-Encoder (simpler, cheaper)
    └── Yes
        │
        Can you afford 2-4x storage vs. bi-encoder?
        ├── No  ──► Use Bi-Encoder + Cross-Encoder reranker
        └── Yes ──► Use ColBERT (PLAID) as primary retriever
```

### ColBERT、Dense Retrieval 與 Hybrid Search 的比較

| 情境 | 最佳選擇 | 原因 |
|----------|-------------|-----|
| 通用型 RAG（100 萬份文件以下） | 混合式（Dense + BM25） | 最簡單，準確度也夠用 |
| 特定領域搜尋（法律、醫療） | ColBERT | token 層級匹配能保留專業術語 |
| 多語言語料庫 | Jina ColBERT v2 | 原生支援 89 種語言 |
| 對成本敏感、高流量 | Bi-Encoder + BM25 | 儲存與運算成本最低 |
| 中等規模下追求最高準確度 | ColBERT + 重新排序器 | 兼具最佳品質，又無 cross-encoder 的延遲 |
| 網路規模（10 億份以上文件） | Bi-Encoder 第一階段 + ColBERT 重新排序 | ColBERT 索引太大，不適合作為主要檢索 |

---

## 面試問題

### Q：請解釋 bi-encoder、cross-encoder 與 late interaction 模型之間的差異。你會在什麼情況下分別選擇它們？

**理想答案：**
這三種架構的差異在於查詢與文件「何時」進行互動：

**Bi-encoder** 將查詢與文件各自獨立地編碼成單一向量。互動只在最後透過內積發生。這很快速（可預先計算所有文件向量，並在數毫秒內完成搜尋），但會失去細粒度的匹配——整份文件的語意被壓縮成向量空間中的單一點。

**Cross-encoder** 將串接後的查詢 + 文件透過單一 transformer 處理。完整的 self-attention 意味著每個查詢 token 都會關注每個文件 token。這帶來最高的準確度，但無法預先計算任何東西——每組查詢-文件配對都需要一次完整的前向傳遞，使其不適合用於第一階段檢索。Cross-encoder 用於對排名前 10-100 的候選結果進行重新排序。

**Late interaction（ColBERT）** 將查詢與文件各自獨立編碼（如同 bi-encoder），但編碼成「每個 token」的向量矩陣，而非單一向量。評分採用 MaxSim——為每個查詢 token 找出最佳匹配的文件 token。這既保留了 token 層級的粒度，又仍允許文件預先計算。其結果是接近 cross-encoder 的準確度，搭配接近 bi-encoder 的速度。

當看重簡潔性的大規模第一階段檢索時，我會選擇 bi-encoder；對小型候選集合進行高風險重新排序時，我會選擇 cross-encoder；而當我需要 cross-encoder 的準確度卻又無法承受其延遲時，我會選擇 ColBERT——尤其是在詞彙層級匹配很重要的特定領域搜尋中（法律、醫療、技術文件）。

### Q：ColBERT 為每個 token 儲存一個向量。它如何擴展？儲存上的取捨又是什麼？

**理想答案：**
ColBERT 的原始儲存成本相當可觀。一份 200 個 token 的文件需要 200 個各 128 維的向量，相較之下 bi-encoder 只需要 1 個 768-1024 維的向量。這意味著每份文件約需 3-5 倍的儲存空間。

ColBERTv2 以 **殘差壓縮（residual compression）** 解決此問題：token 向量被聚類成 centroid，只儲存 centroid ID 加上量化後的殘差。這達到每個 token 向量 16-32 倍的壓縮率，使實際儲存量降到約為 bi-encoder 的 2-4 倍。

PLAID 索引引擎則透過多階段流程，進一步在查詢時提升效率。它先以 centroid pruning（快速、粗略）剔除 99% 的候選，接著只針對有希望的候選逐步解壓縮殘差。最終的精確 MaxSim 只在不到 100 份文件上計算，即使在 1,000 萬份以上文件的語料庫上，也能將延遲維持在 50-100ms。

對於超過 1 億份文件的規模，我會把 ColBERT 當作重新排序器而非主要檢索器——讓 bi-encoder 或 BM25 負責第一階段檢索，將候選集合縮減到 1,000 份文件，再套用 ColBERT 的 MaxSim 進行高品質的重新排序。

### Q：你正在設計一套擁有 500 萬份文件的法律文件搜尋系統。團隊正在「搭配 cross-encoder 重新排序器的 dense bi-encoder 搜尋」與「ColBERT」之間爭論。你會推薦哪一個？

**理想答案：**
基於以下三個理由，我會為此使用情境推薦 ColBERT：

第一，**法律文本對詞彙高度敏感**。合約條款會引用特定的章節編號、定義過的術語（例如「Force Majeure」）以及確切的措辭。ColBERT 的 token 層級 MaxSim 匹配能保留這些罕見卻關鍵的詞彙，而它們在單一向量的 bi-encoder embedding 中會被稀釋。

第二，**500 萬份文件正好落在 ColBERT 的甜蜜點上**。搭配 ColBERTv2 壓縮，索引大約為 30-60 GB——能輕鬆放進單一 GPU。這個規模小到足以用於主要檢索，無需另設獨立的第一階段檢索器。

第三，**cross-encoder 重新排序會增加延遲**。每組查詢-文件配對都需要一次完整的 transformer 前向傳遞。用 cross-encoder 重新排序 100 個候選可能要花上 500ms-2s。ColBERT 在達到相當準確度的同時，能將總延遲維持在 100ms 以下，因為文件 token 是預先計算好的。

我唯一會為 ColBERT 補強的地方，是搭配一個平行的 BM25 索引，用於關鍵字精確度很重要的精確匹配查詢（法條編號、案例引用）。我會用 RRF 將 ColBERT 與 BM25 的結果結合後，再傳給 LLM。

---

## 參考資料
- Khattab & Zaharia. "ColBERT: Efficient and Effective Passage Search" (SIGIR 2020)
- Santhanam et al. "ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction" (NAACL 2022)
- Santhanam et al. "PLAID: An Efficient Engine for Late Interaction Retrieval" (CIKM 2022)
- Answer.AI. "RAGatouille: State-of-the-art Late Interaction Retrieval" (GitHub, 2024)
- Jina AI. "Jina-ColBERT-v2: General-Purpose Multilingual Late Interaction Retriever" (2024)
- Weaviate. "An Overview of Late Interaction Retrieval Models" (2025)
- ECIR 2026. "Late Interaction Workshop" (2026)

---

*上一篇：[Contextual Retrieval](10-contextual-retrieval.md)*
