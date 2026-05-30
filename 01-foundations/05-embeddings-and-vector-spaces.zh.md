# Embeddings 與向量空間

Embeddings 是文字的密集向量表示，能夠捕捉語意意義。它們是 RAG 系統、語意搜尋以及許多 AI 應用的基礎。

## 目錄

- [什麼是 Embeddings](#what-are-embeddings)
- [Embedding 模型架構](#embedding-model-architectures)
- [訓練目標](#training-objectives)
- [距離度量](#distance-metrics)
- [Embedding 模型比較](#embedding-model-comparison)
- [Matryoshka 與自適應維度](#matryoshka-and-adaptive-dimensions)
- [Late Interaction 與 Late Chunking 比較](#late-chunking-and-interaction)
- [Binary 與 Scalar 量化](#quantization-for-scale)
- [實務考量（批次處理、快取）](#practical-considerations)
- [Embedding 漂移與版本管理](#embedding-drift-and-versioning)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 什麼是 Embeddings

Embeddings 將離散的文字（詞、句子、文件）映射到連續的向量空間，使得語意相似度對應到幾何上的鄰近程度。

**關鍵特性：**
- 意義相近者在空間中彼此靠近
- 關係可以被編碼為向量運算（king - man + woman = queen）
- 透過近似最近鄰（approximate nearest neighbor）演算法實現高效的相似度搜尋

**心智模型：**
可以把 embeddings 想成一個非常高維度空間中的座標。維度（512 到 4096）提供了表達能力。每個維度都捕捉了意義的某個面向，雖然個別維度本身並不具可解釋性。

---

## Embedding 模型架構

### 詞 Embeddings（歷史）

早期的方法是對個別的詞進行 embedding：

| 模型 | 年份 | 方法 | 限制 |
|-------|------|----------|------------|
| Word2Vec | 2013 | Skip-gram, CBOW | 靜態：「bank」在所有語境中都相同 |
| GloVe | 2014 | 共現矩陣 | 靜態 |
| FastText | 2017 | 子詞 embeddings | 靜態，但能處理 OOV |

**關鍵限制：** 相同的詞無論語境如何，都會得到相同的 embedding。

### 語境化 Embeddings

以 Transformer 為基礎的模型會產生與語境相關的 embeddings：

```python
# Static embedding (Word2Vec)
embed("bank") = [0.1, 0.3, ...]  # Same vector always

# Contextual embedding (BERT)
embed("river bank") = [0.1, 0.3, ...]   # Geography sense
embed("bank account") = [0.5, 0.2, ...]  # Finance sense
```

### 句子／文件 Embeddings

在檢索場景中，我們需要對整段文字進行 embedding：

| 方法 | 做法 | 優點 | 缺點 |
|----------|--------|------|------|
| Mean pooling | 對 token embeddings 取平均 | 簡單 | 會遺失資訊 |
| CLS token | 使用 [CLS] token 的 embedding | BERT 的標準做法 | 可能無法捕捉完整文字 |
| Last token | 使用最後一個 token | 適用於 decoder 模型 | 有位置偏差 |
| Trained pooling | 學習 pooling 權重 | 品質較佳 | 需要訓練 |

現代的 embedding 模型是專門針對句子／文件 embedding 進行訓練的，而不只是從語言模型改造而來。

### Bi-Encoder 架構

標準的檢索 embedding 架構：

```
Document -> Encoder -> Document Embedding
Query    -> Encoder -> Query Embedding

Similarity = cosine(doc_embedding, query_embedding)
```

**特性：**
- 文件可以事先計算並建立索引
- Query embedding 在查詢時才計算
- 每份文件的相似度計算為 O(1)（搭配 ANN）

### Cross-Encoder 架構

另一種做法是將 query 與文件一起處理：

```
[Query, Document] -> Encoder -> Relevance Score
```

**特性：**
- 更準確（同時看到兩者）
- 無法事先計算：對 n 份文件需做 O(n) 次推論
- 用於 reranking，而非檢索

---

## 訓練目標

### 對比學習（Contrastive Learning）

大多數現代 embedding 模型都採用對比學習：

```python
# Simplified contrastive loss
def contrastive_loss(anchor, positive, negatives):
    pos_sim = cosine_similarity(anchor, positive)
    neg_sims = [cosine_similarity(anchor, neg) for neg in negatives]
    
    # Push positive close, negatives far
    loss = -log(exp(pos_sim / tau) / 
                (exp(pos_sim / tau) + sum(exp(neg_sim / tau) for neg_sim in neg_sims)))
    return loss
```

**關鍵因素：**
- **正樣本對（Positive pairs）：** 語意相似的文字（平行句、query-document 配對）
- **困難負樣本（Hard negatives）：** 相似但不匹配的文字（由 BM25 檢索到的非相關內容）
- **批內負樣本（In-batch negatives）：** 將同批次中的其他項目作為負樣本（高效）

### 訓練資料來源

| 來源 | 正樣本對 | 品質 | 規模 |
|--------|---------------|---------|-------|
| 平行句 | 翻譯配對 | 高 | 中 |
| Query-document | 搜尋日誌 | 高 | 中 |
| Title-body | 文件結構 | 中 | 大 |
| Paraphrase | NLI 資料集 | 高 | 小 |
| Generated | 由 LLM 生成配對 | 不定 | 大 |

### Instruction-Tuned Embeddings

近期的模型可接受任務指令：

```python
# Instruction-tuned (e.g., E5, BGE)
query_embedding = embed("Represent this query for retrieval: What is RAG?")
doc_embedding = embed("Represent this document for retrieval: RAG combines...")
```

透過指定預期用途，能提升效能。

---

## 距離度量

### 餘弦相似度（Cosine Similarity）

文字 embeddings 最常用的度量：

```python
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

**特性：**
- 範圍：[-1, 1]（對於正規化向量；若為正值則為 [0, 1]）
- 衡量角度，而非大小
- 不受向量長度影響

**何時使用：** 文字 embeddings 的預設選擇。

### 內積（Dot Product）

```python
def dot_product(a, b):
    return np.dot(a, b)
```

**特性：**
- 大小（magnitude）會影響結果
- 範圍無界
- 對於正規化向量，等同於餘弦相似度

**何時使用：** 當 embeddings 已經正規化，或大小本身具有意義時。

### 歐幾里得距離（Euclidean Distance）

```python
def euclidean_distance(a, b):
    return np.linalg.norm(a - b)
```

**特性：**
- 衡量絕對差異
- 受大小影響
- 對於正規化向量：sqrt(2 - 2 * cosine)

**何時使用：** 在文字上很少使用；較常用於影像 embeddings。

### 度量的選擇

| 度量 | 向量資料庫 | 常見用途 |
|--------|------------------|------------|
| Cosine | Pinecone, Qdrant, Weaviate | 文字 embeddings |
| Dot Product | 所有主流資料庫 | 正規化的 embeddings |
| Euclidean | 所有主流資料庫 | 影像、多模態 |

---

## Embedding 模型比較

### 目前的頂尖模型（2025 年 12 月）

| 模型 | 維度 | 最大 Tokens | MTEB Retrieval | 每 1M tokens 成本 |
|-------|------------|------------|----------------|------------------|
| OpenAI text-embedding-4 | 3072 | 16k | 68.2 | $0.10 |
| Voyage-4 | 1024 | 128k | 70.1 | $0.05 |
| Cohere embed-v3.5 | 1024 | 512 | 67.5 | $0.10 |
| Google text-embedding-005 | 768 | 8k | 67.2 | $0.02 |

*MTEB 分數為近似值，會隨基準測試子集而有所不同。請務必查證當前數值。英文排行榜目前由 Gemini Embedding 001（68.32）領先；多語言排行榜則由 Qwen3-Embedding-8B（70.58）與 Llama-Embed-Nemotron-8B 領先。*

### 開源模型

| 模型 | 維度 | 最大 Tokens | MTEB Retrieval | 備註 |
|-------|------------|------------|----------------|-------|
| BGE-large-en-v1.5 | 1024 | 512 | 63.9 | 強大的開源模型 |
| E5-large-v2 | 1024 | 512 | 62.4 | Instruction-tuned |
| GTE-large | 1024 | 512 | 63.1 | 阿里巴巴 |
| Nomic-embed-text-v1.5 | 768 | 8192 | 62.3 | 長語境、開源 |

### 選擇準則

| 因素 | 考量 |
|--------|----------------|
| 品質（MTEB） | 越高越好，但針對特定任務的評估更為重要 |
| 維度 | 越高 = 表達能力越強，但儲存／運算成本也越高 |
| 最大 Tokens | 必須能容納你的文件大小 |
| 成本 | API 與自行託管之間的取捨 |
| 延遲 | Embedding 生成所需時間 |
| 多語言 | 若需服務非英文內容 |

---

## Matryoshka 與自適應維度

### 概念

Matryoshka Representation Learning（MRL）以一種方式訓練 embeddings，使得完整 embedding 的前綴部分也同樣具有意義：

```python
full_embedding = model.encode(text)  # 1024 dimensions

# All these are valid embeddings with decreasing quality
dim_512 = full_embedding[:512]  
dim_256 = full_embedding[:256]
dim_128 = full_embedding[:128]
dim_64 = full_embedding[:64]
```

### 為什麼重要

| 使用情境 | 維度 | 取捨 |
|----------|-----------|----------|
| 完整檢索 | 1024-3072 | 最高準確度 |
| **兩階段檢索**| 128 -> 1024 | **生產環境標準做法**：以 128 維檢索出 1000 筆，再以 1024 維精修前 100 筆。 |
| 成本敏感 | 256 | 節省 12 倍儲存空間，MRR 損失 <2% |
| 邊緣／行動裝置 | 64 | 最高速度，可處理簡單意圖 |

### 支援 Matryoshka 的模型

- OpenAI text-embedding-3-*（原生支援）
- Nomic-embed-text-v1.5
- 數個經過 fine-tune 的模型

### 使用 Matryoshka Embeddings

```python
from openai import OpenAI
client = OpenAI()

# Request smaller dimensions
response = client.embeddings.create(
    model="text-embedding-3-large",
    input="Your text here",
    dimensions=256  # Request 256 instead of full 3072
)
```

---

### Late Chunking（2025 年的轉變）

**傳統 Chunking：**
`Document -> Split into chunks -> Embed chunks individually`
- **問題**：Chunk 2 會遺失來自 Chunk 1 的語境。

**Late Chunking（由 Jina AI／Voyage 提出）：**
`Full Document -> Model Encoder -> Token-level Embeddings -> Pool into chunk boundaries`
- **效益**：每個 chunk 的 embedding 都包含來自**整份文件**的資訊，因為在進行 pooling 之前，transformer 的 self-attention 已套用到完整序列上。
- **要求**：需要支援長語境的模型（至少 8k+ tokens）。

---

## 為規模而生的量化

為了處理數十億個向量，**Binary** 與 **Scalar（Int8）** 量化如今已成為標準做法。

| 類型 | 資料大小 | 記憶體節省 | 品質損失 | 支援者 |
|------|-----------|----------------|--------------|--------------|
| Float32 | 4 bytes/dim | 基準 | 0% | 全部 |
| Int8 | 1 byte/dim | 4x | <1% | Cohere, BGE |
| **Binary** | **1 bit/dim** | **32x** | ~5-10% | Cohere v3, v4 |

**Binary 量化模式：**
1. 使用 Binary embeddings 檢索出前 1000 筆（極致速度）。
2. 使用 Float32 或 Cross-Encoder 對前 50 筆進行 rerank（最高準確度）。

### 何時使用 ColBERT

- 檢索精準度至關重要
- 能夠負擔儲存開銷
- 查詢延遲預算 > 50ms

### 實作

```python
# Using RAGatouille
from ragatouille import RAGPretrainedModel

model = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

# Index documents
model.index(
    collection=documents,
    index_name="my_index"
)

# Search
results = model.search(query="What is RAG?", k=10)
```

---

## 實務考量

### 批次處理

```python
# Inefficient: one API call per document
embeddings = [embed(doc) for doc in documents]

# Efficient: batch API calls
batch_size = 100
embeddings = []
for i in range(0, len(documents), batch_size):
    batch = documents[i:i + batch_size]
    batch_embeddings = embed_batch(batch)
    embeddings.extend(batch_embeddings)
```

### 為 Embedding 進行 Chunking

長文件必須先切分（chunk）再進行 embedding：

```python
def embed_document(document: str, max_tokens: int = 512) -> list[np.array]:
    chunks = chunk_document(document, max_tokens=max_tokens)
    embeddings = []
    for chunk in chunks:
        embedding = embed(chunk)
        embeddings.append(embedding)
    return embeddings
```

**考量事項：**
- Chunk 大小應小於模型的最大 tokens 數
- 重疊（overlap）有助於在 chunk 邊界之間保留語境
- 儲存 chunk 對應到 document 的映射關係，以供檢索使用

### 正規化

許多系統預期使用正規化後的 embeddings：

```python
def normalize(embedding):
    norm = np.linalg.norm(embedding)
    return embedding / norm

# Cosine similarity of normalized vectors = dot product
similarity = np.dot(normalize(a), normalize(b))
```

大多數向量資料庫與 embedding API 都會處理正規化，但請務必確認。

### 快取

Embedding 運算成本高昂，應積極使用快取：

```python
import hashlib

def get_embedding(text: str, cache: dict) -> np.array:
    key = hashlib.sha256(text.encode()).hexdigest()
    
    if key in cache:
        return cache[key]
    
    embedding = compute_embedding(text)
    cache[key] = embedding
    return embedding
```

---

## Embedding 漂移與版本管理

### 問題

Embeddings 在以下情況之間並不具可比性：
- 不同的模型
- 同一模型的不同版本
- 有時甚至是不同的 API 呼叫（某些 API 具有非確定性）

### 後果

如果你更新了 embedding 模型：
- 所有既有的 embeddings 都會變得不相容
- 必須對整個語料庫重新進行 embedding
- 在遷移期間搜尋結果會不一致

### 緩解策略

**1. 為你的 embeddings 加上版本：**
```python
embedding_metadata = {
    "model": "text-embedding-3-large",
    "model_version": "2024-01",
    "dimensions": 3072,
    "created_at": "2025-12-16"
}
```

**2. 為重新 embedding 預做規劃：**
- 估算完整重新 embedding 的成本與時間
- 建立能在背景執行的管線
- 在切換前先測試新的 embeddings

**3. 藍綠部署（Blue-green deployment）：**
```
Index A: Current embeddings
Index B: New embeddings (building)

Query -> Both indexes -> Merge or switch
```

**4. 追蹤 embedding 品質：**
- 持續監控檢索指標
- 偵測 embedding 分布的漂移
- 在品質劣化時發出警報

---

## 面試問題

### Q：embedding 模型如何學習語意相似度？

**理想答案：**
Embedding 模型是以對比學習（contrastive learning）來訓練的。其目標是讓語意相似的文字 embeddings 彼此靠近，並讓不相似的文字彼此遠離。

訓練流程：
1. 正樣本對：應當相似的文字（query-document 配對、paraphrase、翻譯）
2. 負樣本對：應當不相似的文字（通常來自同一批次，或來自 BM25 的困難負樣本）
3. 損失函數：將正樣本對推近、將負樣本對推遠

模型學會將文字放置在一個高維空間中，使得距離與語意相似度相關。這便能實現檢索：對 query 進行 embedding，再在文件 embedding 空間中尋找最近鄰。

像 E5 與 BGE 這類現代模型也經過 instruction-tuned，你會在前面加上任務指令，使 embedding 專門化。

### Q：什麼時候你會選用 ColBERT 而非 bi-encoder？

**理想答案：**
ColBERT 採用 late interaction：它不是為每份文件產生單一 embedding，而是保留每個 token 的 embedding。在查詢時，它會計算 token 層級的相似度。

選擇 ColBERT 的時機：
- 檢索精準度至關重要（法律、醫療、高風險場景）
- 你能負擔每份文件 10-100 倍的儲存開銷
- 查詢延遲預算為 50ms 以上（略慢於 bi-encoder）
- 你的查詢能受益於詞彙匹配（lexical matching，例如技術術語）

選擇 bi-encoder 的時機：
- 儲存空間受限
- 需要低於 20ms 的延遲
- bi-encoder 的檢索精準度已足夠
- 需要頻繁重新建立索引（ColBERT 的重新索引成本高昂）

實務上，常見的模式是：以 bi-encoder 進行第一階段檢索（前 100 筆），再以 cross-encoder 或 ColBERT 進行 reranking。

### Q：更新模型時，你如何處理 embedding 漂移？

**理想答案：**
Embedding 模型所產生的向量，只有相對於同一個模型時才具有意義。如果你更新了模型，所有舊的 embeddings 都會變得不相容。

我的做法：
1. **絕不就地更新。** 建立一個帶有新 embeddings 的平行索引。
2. **切換前先測試。** 在一個測試集上，比較舊與新 embeddings 的檢索品質。
3. **背景重建。** 在背景中以新模型對整個語料庫重新進行 embedding。
4. **原子化切換。** 一旦新索引完成並通過驗證，就以原子化方式切換流量。
5. **回滾計畫。** 保留舊索引以便快速回滾。

成本估算：假設你有 1000 萬份文件、平均 500 tokens，而 text-embedding-3-large 的成本為 $0.13/1M tokens，重新 embedding 的成本約為 $650。在考慮更新模型時，請將此成本納入規劃。

### Q：你如何為 embeddings 選擇維度？

**理想答案：**
較高的維度能捕捉更多資訊，但會帶來更高的儲存與運算成本。

考量事項：
- **儲存：** 1024 維的 float32 = 每個 embedding 4 KB。在 1000 萬份文件下 = 光是 embeddings 就要 40 GB。
- **搜尋速度：** 維度越高 = 最近鄰搜尋越慢。
- **品質：** 對大多數任務而言，超過某個維度後便會出現邊際效益遞減。

實務做法：
1. 從模型建議的維度開始。
2. 若使用 Matryoshka 模型（如 text-embedding-3），在你的任務上試驗較低的維度。
3. 在不同維度下對品質進行基準測試：通常 256-512 即可達到完整品質的 95%。
4. 對於兩階段檢索：第一階段使用低維度，reranking 時使用完整維度。

對大多數應用而言，768-1024 維能提供良好的平衡。例外情況是對精準度要求極高的場景，此時 2048-4096 維可能有所助益。

---

## 參考資料

- Reimers and Gurevych. "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks" (2019)
- Khattab and Zaharia. "ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT" (2020)
- Wang et al. "Text Embeddings by Weakly-Supervised Contrastive Pre-training" (E5, 2022)
- Xiao et al. "C-Pack: Packaged Resources To Advance General Chinese Embedding" (BGE, 2023)
- Kusupati et al. "Matryoshka Representation Learning" (MRL, 2022)
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- OpenAI Embeddings Guide: https://platform.openai.com/docs/guides/embeddings

---

*上一篇：[Transformer 架構](04-transformer-architecture.md) | 下一篇：[推論管線](06-inference-pipeline.md)*
