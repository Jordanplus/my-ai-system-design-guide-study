# Contextual Retrieval

Contextual Retrieval 是一種在資料匯入階段（ingestion-time）使用的技術，用來解決 RAG 失敗的頭號成因：**chunk 一旦脫離原始文件就失去語意**。這項技術由 Anthropic 於 2024 年底率先提出，如今已成為高精準度檢索的生產環境標準。Anthropic 自家的量測顯示，單靠 hybrid search 就能讓檢索失敗率降低 49%，搭配 reranking 後更可降低 67%。

## Table of Contents

- [問題所在：語境稀釋（Context Dilution）](#context-dilution)
- [Contextual Retrieval 的運作方式](#how-it-works)
- [Contextual Embeddings](#contextual-embeddings)
- [Contextual BM25](#contextual-bm25)
- [完整管線：Hybrid + Reranking](#full-pipeline)
- [實作模式](#implementation)
- [成本考量](#cost)
- [Contextual Retrieval 與其他做法的比較](#comparison)
- [生產環境架構](#production)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 問題所在：語境稀釋（Context Dilution）

當我們為了 RAG 而把文件切成 chunk 時，個別 chunk 會失去賦予它意義的周遭語境。

**語境稀釋的範例：**

```
Original Document: "Acme Corp Q3 2025 Financial Report"
  Section 4: Product Pricing

  "The Standard plan costs $200/month. The Enterprise
   plan includes SSO and audit logs for $800/month."

-------- After Chunking --------

Chunk 17: "It costs $200/month."
Chunk 18: "The Enterprise plan includes SSO and audit
           logs for $800/month."
```

**Chunk 17 的問題**：當使用者搜尋「How much does Acme Standard plan cost?」時，很可能會錯過這個 chunk，因為它完全沒有提到「Acme」、「Standard」或「plan」。「It costs $200/month」這個 embedding 在語意上與查詢相距甚遠。

**洞察**：Anthropic 的研究顯示，傳統切塊方式在前 20 個檢索 chunk 上會造成 **5.7% 的檢索失敗率**。這代表每約 18 次查詢就有 1 次無法檢索到相關資訊，即使該資訊確實存在於知識庫中。

---

## Contextual Retrieval 的運作方式

核心概念很簡單：**在對 chunk 進行 embedding 之前，先在前面加上一段簡短的語境字串，說明這個 chunk 在整份文件中是在講什麼**。

```
┌──────────────────────────────────────────────────┐
│              TRADITIONAL CHUNKING                │
│                                                  │
│  Document ──► Split ──► Chunks ──► Embed ──► DB  │
│                                                  │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              CONTEXTUAL RETRIEVAL                            │
│                                                              │
│  Document ──► Split ──► Chunks ──┐                           │
│                                  ├──► Contextualize ──►      │
│  Document (full) ───────────────┘    (LLM call per chunk)    │
│                                                              │
│  ──► Contextual Chunks ──► Embed ──► DB                      │
│                            + BM25 Index                      │
└──────────────────────────────────────────────────────────────┘
```

**這個語境化步驟（contextualization step）** 會把完整文件 + 個別 chunk 送進 LLM，並使用以下 prompt：

```
<document>
{{WHOLE_DOCUMENT}}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{{CHUNK_CONTENT}}
</chunk>

Please give a short succinct context to situate this chunk
within the overall document for the purposes of improving
search retrieval of the chunk. Answer only with the succinct
context and nothing else.
```

**Chunk 17 的結果**：

```
Before: "It costs $200/month."

After:  "This chunk is from the Acme Corp Q3 2025 Financial
         Report, Section 4 on Product Pricing. It describes
         the cost of the Standard plan.
         It costs $200/month."
```

現在這個 chunk 的 embedding 就包含了「Acme」、「Standard plan」與「Product Pricing」——也就是使用者自然會去搜尋的所有詞彙。

---

## Contextual Embeddings

Contextual Embeddings 是第一個子技術：對語境化後的 chunk 進行 embedding，而不是對原始 chunk 進行 embedding。

### 它如何改善檢索

| 情境 | 原始 Chunk Embedding | Contextual Embedding |
|----------|--------------------|-----------------------|
| 使用者詢問「Acme pricing」 | 錯過「It costs $200」 | 命中「Acme...Standard plan...costs $200」 |
| 使用者詢問「SSO features」 | 命中「SSO and audit logs」 | 在加上「Enterprise plan」語境後命中 |
| 使用者詢問「Q3 financials」 | 無命中（沒有提到 Q3） | 透過前置的「Q3 2025 Financial Report」而命中 |

**效能**：單靠 Contextual Embeddings 就能把前 20 名的檢索失敗率從 **5.7% 降到 3.7%**——也就是檢索失敗減少了 **35%**。

### 向量空間位移

```
                    ▲ Dimension 2
                    │
                    │    ● "Acme pricing" (query)
                    │         \
                    │          \  close (contextual)
                    │           \
                    │            ● Contextualized chunk
                    │
                    │                          ● Raw chunk "It costs $200"
                    │                            (far from query)
                    │
                    └─────────────────────────────► Dimension 1
```

---

## Contextual BM25

第二個子技術是把相同的語境化做法套用在這些經過擴充的 chunk 上，建立一個 **BM25 關鍵字索引**。

### 為什麼 BM25 依然重要

Dense embeddings 擅長語意相似度，但在以下情況會失效：
- **精確詞彙**：產品 ID、版本號、縮寫
- **罕見 token**：embedding 模型未充分學習的領域專有術語
- **專有名詞**：公司名稱、人名、地名

**範例**：使用者搜尋「Widget-X pricing」時，對原始 chunk「It costs $200/month」的 BM25 命中數會是零，因為「Widget-X」根本沒有出現。有了 contextual BM25，前置的語境裡會把「Widget-X」當作關鍵字納入，使 BM25 得以命中。

### 效能提升（累積）

| 設定 | 失敗率 | 相較基準的降幅 |
|---------------|-------------|----------------------|
| Traditional embeddings（基準） | 5.7% | -- |
| 僅使用 Contextual Embeddings | 3.7% | 35% |
| Contextual Embeddings + Contextual BM25 | 2.9% | **49%** |
| Contextual Embeddings + Contextual BM25 + Reranking | 1.9% | **67%** |

**重點**：contextual embeddings + contextual BM25 的組合，是你能對 RAG 管線做出的單一、槓桿效益最高的變更。在其上再加一個 reranker，可讓你達到失敗減少 67%。

---

## 完整管線：Hybrid + Reranking

生產等級的 Contextual Retrieval 管線有四個階段：

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                          │
│                                                                 │
│  1. Chunk documents (recursive, 300-500 tokens)                 │
│  2. For each chunk:                                             │
│     a. Send (full_doc + chunk) to LLM                           │
│     b. Get context string (50-100 tokens)                       │
│     c. Prepend context to chunk                                 │
│  3. Embed contextualized chunks ──► Vector DB                   │
│  4. Index contextualized chunks ──► BM25 Index                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     QUERY PIPELINE                              │
│                                                                 │
│  User Query                                                     │
│      │                                                          │
│      ├──► Vector Search (Top 50) ──┐                            │
│      │                             ├──► RRF Fusion (Top 25)     │
│      └──► BM25 Search (Top 50)  ──┘         │                   │
│                                             ▼                   │
│                                      Reranker (Top 5)           │
│                                             │                   │
│                                             ▼                   │
│                                     LLM Generation              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 用於合併結果的 Reciprocal Rank Fusion（RRF）

標準 hybrid search 所用的同一套 RRF 技術，在這裡同樣適用：

```
RRF_Score(doc) = sum( 1 / (k + rank_in_list) )
                 for each list where doc appears

k = 60 (standard smoothing constant)
```

---

## 實作模式

### 模式 1：基本的 Contextual Retrieval（Python）

```python
import anthropic
from typing import List

client = anthropic.Anthropic()

CONTEXT_PROMPT = """<document>
{document}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{chunk}
</chunk>

Please give a short succinct context to situate this chunk
within the overall document for the purposes of improving
search retrieval of the chunk. Answer only with the succinct
context and nothing else."""


def contextualize_chunk(
    full_document: str,
    chunk: str,
    model: str = "claude-sonnet-4-20250514"
) -> str:
    """Generate context for a single chunk."""
    response = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": CONTEXT_PROMPT.format(
                document=full_document,
                chunk=chunk
            )
        }]
    )
    context = response.content[0].text
    return f"{context}\n\n{chunk}"


def process_document(document: str, chunks: List[str]) -> List[str]:
    """Contextualize all chunks in a document."""
    contextualized = []
    for chunk in chunks:
        ctx_chunk = contextualize_chunk(document, chunk)
        contextualized.append(ctx_chunk)
    return contextualized
```

### 模式 2：以 Prompt Caching 進行成本最佳化

最大的成本來源是每個 chunk 都要附帶完整文件一起送出。**Prompt Caching** 可以解決這個問題：

```python
def contextualize_with_caching(
    full_document: str,
    chunks: List[str],
    model: str = "claude-sonnet-4-20250514"
) -> List[str]:
    """
    Use prompt caching so the full document is only
    processed once across all chunks.
    """
    results = []

    for chunk in chunks:
        response = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"<document>\n{full_document}\n</document>",
                        "cache_control": {"type": "ephemeral"}
                    },
                    {
                        "type": "text",
                        "text": (
                            f"<chunk>\n{chunk}\n</chunk>\n\n"
                            "Please give a short succinct context to "
                            "situate this chunk within the overall "
                            "document for the purposes of improving "
                            "search retrieval of the chunk. Answer "
                            "only with the succinct context and "
                            "nothing else."
                        )
                    }
                ]
            }]
        )
        context = response.content[0].text
        results.append(f"{context}\n\n{chunk}")

    return results
```

**Prompt Caching 的成本影響**：以一份 10,000-token 的文件、切成 30 個 chunk 為例，prompt caching 最高可讓語境化成本降低 **90%**，因為文件前綴在第一次呼叫之後就被快取下來。

### 模式 3：Contextual Chunk Headers（輕量級替代方案）

如果以 LLM 為基礎的語境化太貴，可以改用 **Contextual Chunk Headers（CCH）** 作為決定性（deterministic）的替代方案：

```python
def add_chunk_headers(
    document_title: str,
    section_hierarchy: List[str],
    chunk: str
) -> str:
    """
    Prepend document and section metadata to the chunk.
    No LLM call required -- purely structural.
    """
    header_parts = [f"Document: {document_title}"]

    for i, section in enumerate(section_hierarchy):
        prefix = "  " * i
        header_parts.append(f"{prefix}Section: {section}")

    header = "\n".join(header_parts)
    return f"{header}\n\n{chunk}"


# Example usage:
contextualized = add_chunk_headers(
    document_title="Acme Corp Q3 2025 Financial Report",
    section_hierarchy=["Finance", "Product Pricing", "Standard Plan"],
    chunk="It costs $200/month."
)

# Result:
# Document: Acme Corp Q3 2025 Financial Report
#   Section: Finance
#     Section: Product Pricing
#       Section: Standard Plan
#
# It costs $200/month.
```

**何時使用 CCH 對比 LLM 語境化：**

| 因素 | Chunk Headers（CCH） | LLM 語境化 |
|--------|--------------------|-----------------------|
| **成本** | 免費（無 LLM 呼叫） | 每 1M tokens 約 $1-5 |
| **品質** | 對結構化文件良好 | 對所有文件都極佳 |
| **速度** | 即時 | 每個 chunk 50-200ms |
| **最適合** | Markdown、HTML、含清楚標題的 PDF | 非結構化文字、法律、醫療 |

---

## 成本考量

### 語境化成本

以一個包含 10,000 個 chunk（平均每個 400 tokens）的知識庫為例：

| 模型 | 每 Chunk 成本 | 總成本 | 品質 |
|-------|---------------|------------|---------|
| Claude Haiku（快速、便宜） | ~$0.0003 | ~$3 | 良好 |
| Claude Sonnet（平衡） | ~$0.002 | ~$20 | 非常好 |
| Claude Opus（最高品質） | ~$0.01 | ~$100 | 極佳 |

**最佳實務**：使用 Haiku（或其他快速、便宜的模型）來做語境化。這些語境字串既短又屬於事實陳述，所以你不需要前沿（frontier）模型。再搭配 prompt caching，可讓那份被反覆傳入的文件本體成本降低約 90%。

### 何時該使用 Contextual Retrieval

**在以下情況使用：**
- 你的語料中有破碎的文件，chunk 在孤立狀態下會失去意義
- 你有 embedding 模型難以處理的領域專有術語
- 你的檢索失敗率超過 3-5%
- 你能負擔這筆一次性的匯入成本

**在以下情況略過：**
- 你的 chunk 本身已自成一體（例如 FAQ 配對、產品描述）
- 你的語料極小（< 100 個 chunk）——直接改用 long-context 即可
- 你需要即時匯入（每份文件 < 1 秒），且無法批次處理

---

## Contextual Retrieval 與其他做法的比較

| 做法 | 運作方式 | 檢索改善幅度 | 成本 | 複雜度 |
|----------|-------------|----------------------|------|------------|
| **Naive Chunking** | 固定大小切塊、對原始內容做 embedding | 基準 | 無 | 低 |
| **Chunk Headers（CCH）** | 前置文件／章節標題 | 10-20% | 無 | 低 |
| **Contextual Retrieval** | 由 LLM 為每個 chunk 產生語境 | 35-49% | 每 1 萬 chunk $3-20 | 中 |
| **Contextual + Reranking** | 上述做法 + cross-encoder rerank | 67% | 每 1 萬 chunk $5-30 | 中高 |
| **HyDE** | 在查詢時產生假設性文件 | 20-40% | 每次查詢的 LLM 成本 | 中 |
| **Parent-Child Chunking** | 對子塊做 embedding、檢索父塊 | 15-30% | 無 | 中 |

**關鍵差異**：Contextual Retrieval 是一種 **匯入階段（ingestion-time）** 技術（付費一次），而 HyDE 是一種 **查詢階段（query-time）** 技術（每次查詢付費）。對於高流量系統，Contextual Retrieval 的成本攤提（amortize）效果好得多。

### Contextual Retrieval 與 Late Chunking

**Late Chunking**（Jina，2024）是一種相關但截然不同的做法：

```
Contextual Retrieval:
  Chunk ──► LLM adds context ──► Embed enriched chunk

Late Chunking:
  Full doc ──► Long-context embed model ──► Token embeddings
  ──► THEN chunk the token embeddings (preserving context)
```

Late Chunking 需要一個 long-context embedding 模型（例如 Jina v3），並且完全避開 LLM 呼叫。它透過 embedding 模型的 attention 機制來保留語境，而不是顯式地在文字前面附加內容。其取捨在於：Late Chunking 對 BM25 搜尋沒有幫助，只對 dense retrieval 有效。

---

## 生產環境架構

### 參考架構：規模化的 Contextual RAG

```
┌─────────────────────────────────────────────────────────────────────┐
│                     INGESTION SERVICE                               │
│                                                                     │
│  Document Store ──► Chunker ──► Contextualization Queue             │
│                       │              │                              │
│                       │         ┌────┴────┐                         │
│                       │         │ Workers  │ (N parallel LLM calls) │
│                       │         │ + Cache  │                        │
│                       │         └────┬────┘                         │
│                       │              │                              │
│                       ▼              ▼                              │
│                  Raw Chunks    Contextualized Chunks                 │
│                       │              │                              │
│                       │         ┌────┴────┐                         │
│                       │         │ Embed + │                         │
│                       │         │ BM25    │                         │
│                       │         └────┬────┘                         │
│                       │              │                              │
│                       ▼              ▼                              │
│                  Metadata DB    Vector DB + BM25 Index               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     QUERY SERVICE                                   │
│                                                                     │
│  Query ──► [Vector Search] + [BM25 Search]                          │
│                    │               │                                │
│                    └───── RRF ─────┘                                │
│                           │                                         │
│                      Top 25 chunks                                  │
│                           │                                         │
│                      Reranker (Cohere, Cross-Encoder)               │
│                           │                                         │
│                      Top 5 chunks                                   │
│                           │                                         │
│                      LLM Generation                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 規模化考量

| 關注點 | 解法 |
|---------|----------|
| **匯入吞吐量** | 以非同步 worker 平行處理 LLM 呼叫（50-100 個並行） |
| **文件更新** | 只重新語境化有變動的 chunk；將原始內容與語境分開儲存 |
| **規模化下的成本** | 使用 Haiku + prompt caching；依大小批次處理文件 |
| **品質監控** | 抽樣 1% 的 chunk，由人工評估語境品質 |
| **索引一致性** | 以文件為單位，原子性（atomically）地更新 vector DB + BM25 索引 |

---

## 面試問題

### Q：請解釋 Anthropic 的 Contextual Retrieval。你會在什麼情況使用它，又會在什麼情況略過它？

**優秀的回答：**
Contextual Retrieval 解決了 RAG 中的「語境稀釋」問題。當文件被切成 chunk 時，個別 chunk 會失去賦予它意義的周遭語境——一個寫著「It costs $200」的 chunk，在不知道「什麼」要 $200 的情況下毫無用處。這項技術在匯入階段使用 LLM 為每個 chunk 產生一段簡短的語境字串（50-100 tokens），說明該 chunk 在文件中是在講什麼。這段語境會在 embedding 與 BM25 索引之前被前置到 chunk 上。

關鍵結果：單靠 Contextual Embeddings 就能讓檢索失敗減少 35%。加上 Contextual BM25 可達到 49% 的降幅。再加上 reranker 則達到 67% 的降幅。

當 chunk 經常在孤立狀態下失去意義時——法律合約、財務報告、技術手冊——我就會使用它。而當 chunk 本身已自成一體（FAQ、產品卡片），或當語料小到可以用 long-context RAG 處理時，我就會略過它。

### Q：一個包含 50,000 份文件的知識庫需要 Contextual Retrieval。你會如何管理匯入成本？

**優秀的回答：**
三項策略：
1. **模型選擇**：使用一個小型、快速的模型（Claude Haiku 等級）來做語境化。輸出是簡短的事實性文字，而非創意寫作——前沿模型只會增加成本卻不會帶來品質提升。
2. **Prompt caching**：在所有 chunk 的語境化呼叫之間快取完整文件文字。以一份 10,000-token、30 個 chunk 的文件為例，這能讓輸入的 token 成本降低約 90%。
3. **分層做法**：並非每份文件都需要 LLM 語境化。對於結構良好的文件（Markdown、含標題的 HTML），使用決定性的 Contextual Chunk Headers（前置文件標題 + 章節階層），這是免費的。把 LLM 語境化保留給非結構化或語意含糊的文件。

### Q：在提升檢索品質方面，Contextual Retrieval 與 HyDE 相比如何？

**優秀的回答：**
它們解決的是同一個問題的不同面向。Contextual Retrieval 在匯入階段豐富 **文件**（付費一次），而 HyDE 在搜尋階段豐富 **查詢**（每次查詢付費）。對於一個每天處理 10,000 次查詢、面對 50,000 個 chunk 語料的系統來說，Contextual Retrieval 便宜得多，因為匯入成本被攤提掉了。HyDE 還有幻覺（hallucination）風險——那份假設性文件可能會引入錯誤資料。實務上，最強的系統會兩者並用：以 Contextual Retrieval 做匯入端的豐富化，並以 HyDE（或 multi-query expansion）來協助那些需要查詢端幫助的複雜查詢。

---

## 參考資料
- Anthropic. "Contextual Retrieval" (September 2024)
- Jina AI. "Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models" (2024)
- Voyage AI. "voyage-context-3: Contextualized Chunk Embeddings" (2025)
- NirDiamant. "RAG Techniques: Contextual Chunk Headers" (GitHub, 2024)

---

*上一篇：[Advanced Retrieval Patterns](09-advanced-retrieval-patterns.md) | 下一篇：[Late Interaction & ColBERT](11-late-interaction-colbert.md)*
