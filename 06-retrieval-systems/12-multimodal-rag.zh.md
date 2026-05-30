# 多模態 RAG

多模態 RAG 將檢索增強生成（retrieval-augmented generation）從純文字延伸出去，用以處理影像、表格、圖表、音訊，以及混合版面配置的文件。如今正式上線的系統經常需要攝取含有示意圖的 PDF、簡報投影片、掃描的發票，以及視覺版面配置「就是」其意義所在的研究論文。三種架構主導了這個領域：caption-and-index（先標註再建立索引）、統一的 vision-text embedding（Cohere Embed v4、Voyage-Multimodal-3.5、Gemini Embedding 001），以及搭配 late interaction 的 page-as-image（將整頁視為影像；ColPali、ColQwen2.5、ColNomic）。

## 目錄

- [為什麼純文字 RAG 會失敗](#why-text-only-rag-fails)
- [架構模式](#architecture-patterns)
- [多模態 embedding 策略](#multi-modal-embedding-strategies)
- [用於文件理解的 Vision-Language Model](#vision-language-models)
- [ColPali 與以視覺為基礎的檢索](#colpali)
- [表格擷取與結構化資料檢索](#table-extraction)
- [圖表與示意圖理解](#chart-understanding)
- [正式環境架構](#production-architecture)
- [實作範例](#implementation-example)
- [系統設計面試切入角度](#system-design-interview-angle)
- [參考資料](#references)

---

## 為什麼純文字 RAG 會失敗

傳統的 RAG pipeline 會把文件解析成文字 chunk、對其做 embedding，再針對文字查詢進行檢索。這在真實世界的文件上會失效：

| 文件元素 | 純文字 RAG 的行為 | 實際遺失的資訊 |
|-----------------|----------------------|------------------------|
| **長條圖** | 只擷取座標軸標籤 | 趨勢、比較、量級大小 |
| **架構示意圖** | 完全漏掉 | 元件關係、資料流 |
| **表格** | 攤平的列失去結構 | 列-欄的對應關係、表頭 |
| **資訊圖表（Infographic）** | 抓到零散的文字片段 | 視覺階層、空間分組 |
| **附說明文字的照片** | 取得說明文字，遺失影像 | 視覺證據、空間脈絡 |

**現實情況**：企業文件中有 40-60% 是非文字內容。財務報告的價值就在它的圖表裡。醫學論文的關鍵發現就在它的圖中。忽略視覺內容，等於忽略大部分的知識。

---

## 架構模式

多模態 RAG 有三種主導的模式，各有不同的取捨：

### 模式 1：統一 embedding 空間

```
                     Shared Vector Space
                    +-------------------+
  Text  --> Encoder |  [0.2, 0.8, ...] |
  Image --> Encoder |  [0.3, 0.7, ...] |  --> Single Index --> Retrieve
  Table --> Encoder |  [0.1, 0.9, ...] |
                    +-------------------+

  Query "show revenue trends" --> encode --> nearest neighbors across ALL modalities
```

- **做法**：使用像 CLIP 或 SigLIP 這類模型，把文字與影像投影到同一個向量空間。
- **優點**：單一索引、單一查詢、簡單的檢索邏輯。
- **缺點**：embedding 品質因模態而異；表格需要序列化。

### 模式 2：各模態各自檢索並融合

```
  Query --> +----> Text Index    --> Top-K text chunks
            |
            +----> Image Index   --> Top-K images
            |
            +----> Table Index   --> Top-K tables
            |
            v
        Fusion / Reranking Layer --> Combined Top-K --> VLM Generator
```

- **做法**：每個模態各自有獨立的 embedding 與索引。由 reranker 或 reciprocal rank fusion（RRF）合併結果。
- **優點**：每個模態都用同類中最佳的 embedding；可獨立調校每個檢索器。
- **缺點**：基礎設施更複雜；融合邏輯並不簡單。

### 模式 3：視覺優先（Page-as-Image，將整頁視為影像）

```
  Document Page --> Screenshot/Render --> Vision Encoder --> Multi-vector Index
                                              |
  Query ---------> Text Encoder --------------+---> Late Interaction Score
                                                    --> Retrieve top pages
```

- **做法**：把每一頁文件都當成一張影像。使用 vision-language model（例如 ColPali）來建立 patch 層級的 embedding。透過 late interaction（MaxSim）來計分。
- **優點**：不需要 OCR、不需要版面解析、不需要表格擷取 pipeline。可端到端訓練。
- **缺點**：建立索引時運算量較高；失去細緻的文字搜尋能力。

**建議**：在以文件為主的使用情境中，模式 3（視覺優先）正快速取得進展。當你需要在視覺檢索之外同時進行精準的文字搜尋時，模式 2 仍是正式環境的主力。

---

## 多模態 embedding 策略

### CLIP（Contrastive Language-Image Pretraining）

最初的 dual-encoder，把文字與影像對應到一個共享的 512/768 維空間。

- **優勢**：龐大的生態系、廣為人知、有許多 fine-tuned 變體。
- **弱點**：相較於自然照片，在文件式影像（圖表、表格）上表現較弱。Contrastive loss 需要很大的 batch size。

### SigLIP / SigLIP 2

把 CLIP 的 softmax cross-entropy 換成 sigmoid loss，讓每一組 image-text pair 都能被獨立評估。

- **SigLIP 2（2025）**：加入了 captioning decoder、self-distillation 與 masked prediction。在跨 109 種語言、超過 10B 張影像上訓練。
- **關鍵勝出點**：在小 batch size（4-8k）下勝過 CLIP，並提供更稠密、更穩健的特徵。
- **正式環境應用**：挪威國家圖書館、電商視覺搜尋、AI 藝術策展。

### 用於 RAG 的比較

| 模型 | 最適合 | Embedding 維度 | 文件品質 | 自然影像品質 |
|-------|----------|--------------|-----------------|----------------------|
| CLIP ViT-L/14 | 通用 | 768 | 中 | 高 |
| SigLIP 2 So400m | 多語言文件 | 1152 | 高 | 高 |
| Nomic Embed Vision | 文字密集型文件 | 768 | 高 | 中 |
| Voyage Multimodal 3 | 混合型文件 | 1024 | 高 | 高 |

### Embedding 策略的決策

```
Is your content mostly natural images (photos, products)?
  YES --> CLIP or SigLIP fine-tuned on your domain
  NO
    |
    v
Is your content document pages (PDFs, slides, reports)?
  YES --> ColPali / ColQwen (vision-first, no OCR needed)
  NO
    |
    v
Is it a mix of text, images, and structured data?
  YES --> Modality-specific encoders + fusion (Pattern 2)
```

---

## 用於文件理解的 Vision-Language Model

VLM 在多模態 RAG 中扮演兩種角色：（1）作為**生成器（generator）**，從檢索到的多模態脈絡中綜合出答案；（2）作為**索引引擎（indexing engine）**，在攝取（ingestion）時擷取結構化資訊。

### VLM 能力比較

| 能力 | Claude Opus 4.7 / Sonnet 4.6 | GPT-5.5 | Gemini 3.1 Pro |
|-----------|------------------------------|---------|----------------|
| **圖表判讀** | 優異 | 優異 | 優異 |
| **表格擷取** | 優異 | 良好 | 優異 |
| **示意圖理解** | 優異 | 良好 | 優異 |
| **手寫 OCR** | 良好 | 良好 | 良好 |
| **多頁推理** | 優異（Sonnet 4.6 具備 1M ctx） | 優異（1M ctx） | 優異（1M ctx） |
| **結構化輸出** | 原生 JSON mode | 原生 JSON mode | 原生 JSON mode |

### VLM 增強的攝取 pipeline

```
  Raw PDF
    |
    v
  Page Renderer (pdf2image, 300 DPI)
    |
    v
  VLM Extraction Pass:
    +-- "Extract all tables as markdown"
    +-- "Describe this chart: axes, trends, key data points"
    +-- "Summarize the diagram: components and relationships"
    |
    v
  Structured Output (JSON)
    |
    +---> Text chunks     --> Text embedding index
    +---> Table markdown  --> Text embedding index (with metadata: "type=table")
    +---> Chart summaries --> Text embedding index (with metadata: "type=chart")
    +---> Page images     --> Image embedding index (CLIP/SigLIP)
```

這種「先描述、再 embedding」（describe-then-embed）的做法，把視覺內容轉換成可搜尋的文字，同時保留原始影像供生成步驟使用。

---

## ColPali 與以視覺為基礎的檢索

ColPali 代表了一種典範轉移：不再建立複雜的 OCR + 版面 + 表格擷取 pipeline，而是把每一頁文件都當成單一影像，讓 vision-language model 來處理一切。

### ColPali 如何運作

```
  Document Page Image
        |
        v
  SigLIP Vision Encoder (So400m)
        |
  Splits image into patches (e.g., 32x32 grid = 1024 patches)
        |
        v
  Gemma 2B Language Model (contextualizes patch embeddings)
        |
        v
  Linear Projection --> 128-dim patch embeddings
        |
  Result: 1024 vectors of dim 128 per page
        |
        v
  Stored in Multi-Vector Index

  At query time:
  Query --> Tokenize --> Embed --> 128-dim token embeddings
        |
        v
  Late Interaction (MaxSim):
    Score = Sum over query tokens of Max similarity to any patch
```

### ColPali 與傳統 pipeline 的比較

| 面向 | 傳統 pipeline | ColPali |
|--------|---------------------|---------|
| **OCR** | 必要（Tesseract、Azure OCR） | 不需要 |
| **版面偵測** | 必要（Detectron2、LayoutLM） | 不需要 |
| **表格解析器** | 必要（Camelot、Tabula） | 不需要 |
| **圖表擷取器** | 必要（ChartOCR） | 不需要 |
| **建立索引速度** | 慢（多階段） | 快（單次 forward pass） |
| **檢索品質** | 文字上高、視覺上差 | 跨所有模態皆高 |
| **儲存** | 文字索引（約小） | Multi-vector 索引（約較大） |

### ColPali 家族

- **ColPali（v1）**：以 PaliGemma-3B 為骨幹。最初的版本。
- **ColQwen 2.5**：以 Qwen2-VL 為骨幹。更佳的多語言支援，在亞洲語言文件上有所改進。
- **ColSmol**：適用於邊緣（edge）部署的較小變體。約 1B 參數。

### ViDoRe Benchmark 結果

ColPali 在視覺上複雜的 benchmark 上表現出色，例如 InfographicVQA、ArxivQA 與 TabFQuAD，它們分別測試資訊圖表、圖，以及表格。即使在以文字為中心的文件上，它也勝過傳統的文字式 pipeline。

---

## 表格擷取與結構化資料檢索

表格是傳統 RAG 最難處理的模態。逐列攤平一個表格會破壞賦予每個儲存格意義的「欄-表頭」關係。

### 策略 1：以 VLM 為基礎的擷取

```python
# Pseudocode: Extract tables using a VLM
def extract_tables_from_page(page_image: bytes) -> list[dict]:
    prompt = """
    Extract ALL tables from this document page.
    For each table, return:
    {
      "title": "table title or caption",
      "headers": ["col1", "col2", ...],
      "rows": [["val1", "val2", ...], ...],
      "markdown": "| col1 | col2 |\\n|---|---|\\n| val1 | val2 |"
    }
    Return JSON array. If no tables, return [].
    """
    response = vlm.generate(image=page_image, prompt=prompt)
    return json.loads(response)
```

### 策略 2：專用的表格解析器

- **Tabula / Camelot**：以規則為基礎的 PDF 表格擷取。快速，但在複雜版面上很脆弱。
- **Table Transformer（以 DETR 為基礎）**：從影像中偵測表格邊界與儲存格結構。
- **Unstructured.io**：結合啟發式規則與 ML 模型，做出能感知版面的解析。

### 策略 3：感知表格的 chunking

```
  Original Table (20 rows x 8 columns)
        |
        v
  Chunk as complete unit (do NOT split tables across chunks)
        |
        v
  Embed the full markdown table as a single chunk
        |
        v
  Add metadata: {"type": "table", "page": 14, "caption": "Q3 Revenue by Region"}
        |
        v
  At generation time: pass the FULL table to the LLM, not a fragment
```

**關鍵原則**：表格必須是不可分割（atomic）的檢索單位。絕對不要把一個表格切割到跨越多個 chunk 的邊界。

---

## 圖表與示意圖理解

### 圖表類型與擷取方法

| 圖表類型 | 要擷取什麼 | 最佳方法 |
|-----------|----------------|---------------|
| **長條圖/折線圖/圓餅圖** | 資料值、趨勢、比較 | VLM 描述 + 資料表格擷取 |
| **流程圖** | 步驟、決策、連接 | VLM 結構化擷取（節點 + 邊） |
| **架構示意圖** | 元件、關係、資料流 | VLM 描述 + 實體擷取 |
| **散佈圖** | 相關性、離群值、群集 | VLM 趨勢描述 + 原始資料（若有的話） |
| **甘特圖** | 時程、相依性、里程碑 | VLM 結構化擷取 |

### 雙重表示法策略

對每一張圖表或示意圖，儲存「兩種」表示法：

```
  Chart Image
    |
    +---> (1) Text Description (for text-based retrieval)
    |         "This bar chart shows Q3 revenue by region.
    |          North America: $4.2M, Europe: $3.1M, APAC: $2.8M.
    |          NA grew 15% QoQ while APAC declined 3%."
    |
    +---> (2) Original Image (for visual retrieval + generation context)
              Stored with CLIP/SigLIP embedding for image-based queries
```

這確保了該圖表既能被文字查詢檢索到（「APAC 的營收是多少？」），也能被視覺查詢檢索到（「給我看那張營收圖表」）。

---

## 正式環境架構

### 完整的多模態 RAG pipeline

```
  INGESTION:
  Raw Docs --> Doc Classifier --+--> Text-Heavy  --> chunking + text embeddings
                                +--> Visual-Heavy --> page render + ColPali
                                +--> Mixed        --> VLM extraction + hybrid
                                         |
                                         v
                          [Text Index] [Image Index] [Table Index]

  RETRIEVAL:
  Query --> Query Analyzer --+--> Text:  BM25 + dense search
                             +--> Image: CLIP/ColPali search
                             +--> Table: metadata-filtered dense
                                    |
                                    v
                             Cross-Modal Reranker --> Context Assembly --> VLM --> Response
```

### 規模化的考量

| 考量點 | 解決方案 |
|---------|----------|
| **索引大小** | ColPali 每頁儲存約 1024 個向量。100 萬頁 = 約 10 億個向量。使用量化（binary、PQ）。 |
| **攝取延遲** | VLM 擷取很慢（約 2-5 秒/頁）。使用搭配 GPU 加速的非同步 worker。 |
| **查詢延遲** | 多索引扇出（fan-out）會增加延遲。使用平行檢索 + 積極的 top-k 修剪。 |
| **成本** | 攝取時的 VLM 呼叫是一次性的。攤提到查詢量上。擷取編列每頁 $0.01-0.05 的預算。 |
| **儲存** | 把頁面影像存在物件儲存（S3）。把 embedding 存在 vector DB。把文字存在搜尋索引。 |

---

## 實作範例

### 以 ColPali + VLM 實作端到端多模態 RAG

```python
# Pseudocode: Production multi-modal RAG pipeline

from colpali_engine import ColPali, ColPaliProcessor
from qdrant_client import QdrantClient
import anthropic

# --- INDEXING ---

def index_document(pdf_path: str, collection: str):
    """Index a PDF document using ColPali for visual retrieval
    and VLM extraction for text-based retrieval."""

    pages = render_pdf_to_images(pdf_path, dpi=300)

    colpali_model = ColPali.from_pretrained("vidore/colpali-v1.3")
    processor = ColPaliProcessor.from_pretrained("vidore/colpali-v1.3")
    vlm_client = anthropic.Anthropic()

    for page_num, page_image in enumerate(pages):
        # 1. Generate ColPali multi-vector embeddings
        inputs = processor(images=[page_image])
        patch_embeddings = colpali_model(**inputs)  # shape: [1, 1024, 128]

        # 2. Extract structured content via VLM
        extraction = vlm_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": encode_image(page_image)},
                    {"type": "text", "text": """Extract from this page:
                    1. All text content (preserve structure)
                    2. Tables as markdown
                    3. Chart descriptions with data points
                    Return as JSON with keys: text, tables, charts"""}
                ]
            }]
        )

        structured = json.loads(extraction.content[0].text)

        # 3. Store in vector DB
        qdrant.upsert(collection, points=[
            # ColPali multi-vector for visual retrieval
            PointStruct(
                id=f"{pdf_path}:page:{page_num}:colpali",
                vector={"colpali": patch_embeddings[0].tolist()},
                payload={
                    "source": pdf_path,
                    "page": page_num,
                    "type": "page_image",
                    "text_preview": structured["text"][:500]
                }
            ),
            # Text embeddings for each extracted element
            *create_text_chunks(structured, pdf_path, page_num)
        ])


# --- RETRIEVAL ---

def retrieve(query: str, collection: str, top_k: int = 5):
    """Hybrid retrieval: ColPali visual + text semantic search."""

    # Visual retrieval via ColPali
    query_inputs = processor(text=[query])
    query_embeddings = colpali_model(**query_inputs)

    visual_results = qdrant.query(
        collection,
        query_vector=("colpali", query_embeddings[0].tolist()),
        limit=top_k,
        query_filter=Filter(must=[FieldCondition(key="type", match="page_image")])
    )

    # Text retrieval via dense embeddings
    text_embedding = text_encoder.encode(query)
    text_results = qdrant.search(
        collection,
        query_vector=("text", text_embedding.tolist()),
        limit=top_k
    )

    # Fuse results using reciprocal rank fusion
    fused = reciprocal_rank_fusion(visual_results, text_results, k=60)
    return fused[:top_k]


# --- GENERATION ---

def generate_answer(query: str, retrieved_context: list) -> str:
    """Generate answer using VLM with multi-modal context."""

    content_blocks = [{"type": "text", "text": f"Question: {query}\n\nContext:"}]

    for ctx in retrieved_context:
        if ctx.payload["type"] == "page_image":
            # Include the actual page image
            content_blocks.append({
                "type": "image",
                "source": load_page_image(ctx.payload["source"], ctx.payload["page"])
            })
        else:
            # Include text/table content
            content_blocks.append({
                "type": "text",
                "text": f"[{ctx.payload['type']}] {ctx.payload['content']}"
            })

    content_blocks.append({
        "type": "text",
        "text": "Answer the question using ONLY the provided context. Cite sources."
    })

    response = vlm_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": content_blocks}]
    )
    return response.content[0].text
```

---

## 系統設計面試切入角度

### 問：為一個金融研究平台設計一套 RAG 系統，它需要回答關於財報的問題，而財報中包含文字、表格與圖表。

**強力的回答：**

核心挑戰在於，財報中有 60% 以上的資訊存在於表格與圖表中，而不是散文裡。純文字 RAG pipeline 會漏掉營收明細、趨勢線與比較資料。

**架構**：我會採用混合做法（模式 2 + 模式 3 的元素）：

1. **攝取**：以 300 DPI render 每一頁 PDF。執行一次 VLM 擷取，把表格轉成 markdown、把圖表轉成結構化描述。同時為每一張頁面影像產生 ColPali multi-vector embedding。

2. **儲存**：三個索引 —— (a) 帶有 dense embedding 的文字 chunk（金融文字），(b) 帶有 dense embedding 並加上表格類型 metadata 過濾條件的表格 markdown，(c) 用於頁面層級視覺檢索的 ColPali multi-vector 索引。

3. **檢索**：query analyzer 會對查詢類型進行分類。「Q3 營收是多少？」會觸發文字 + 表格搜尋。「給我看營收趨勢」會觸發視覺（ColPali）搜尋。結果透過 RRF 融合，並由 cross-encoder 重新排序。

4. **生成**：由一個 VLM（Claude 或 Gemini）接收融合後的脈絡 —— 文字 chunk、表格 markdown，以及相關的頁面影像。它會生成一個有依據（grounded）的答案，並引用到特定的頁面與表格。

**關鍵取捨**：ColPali 在視覺內容上提供優異的 recall，但每頁儲存約 1024 個向量，因此對於 10 萬份文件（50 萬頁），這就是約 5 億個向量。我會使用 binary quantization 把儲存量減少 32 倍，並接受 recall 的小幅下降。對於文字路徑，BM25 + dense 的混合搜尋能妥善處理金融術語。

### 問：你會如何處理一個需要同時用到「位於不同頁面」的一張圖表與一個表格的查詢？

**強力的回答：**

這是跨模態、跨頁面的檢索問題。解法有三個部分：

1. **檢索多樣性**：確保檢索器回傳來自多個模態的結果。設定最低配額 —— 在每一個檢索集合中，至少有 2 筆文字結果、2 筆表格結果與 1 筆視覺結果，無論哪個模態的分數最高。

2. **脈絡組裝**：在組裝 VLM prompt 時，把所有檢索到的內容都納入，並附上明確的來源出處：「[Table from page 14: Q3 Revenue by Region]」與「[Chart from page 22: Revenue Trend 2024-2026]」。如此一來，VLM 就能跨這兩者進行推理。

3. **Agentic 後援機制**：如果初次檢索沒有浮現出足夠的跨模態脈絡，可以由一個 agentic 層發出後續檢索：「表格顯示的是營收數字，但使用者問的是趨勢 —— 讓我也搜尋一下與營收相關的圖表。」

關鍵洞見在於，跨模態的問題本質上就是 multi-hop。系統需要先從一個模態檢索，辨識出缺口，再從另一個模態檢索。

---

## 參考資料

- Faysse et al. "ColPali: Efficient Document Retrieval with Vision Language Models" (ICLR 2025)
- Google. "SigLIP 2: Multilingual Vision-Language Encoders" (2025)
- NVIDIA. "An Easy Introduction to Multimodal Retrieval-Augmented Generation" (2025)
- HKUDS. "RAG-Anything: All-in-One Multimodal RAG Framework" (2025)
- Vespa Blog. "PDF Retrieval with Vision Language Models" (2024)

---

*上一篇：[進階檢索模式](09-advanced-retrieval-patterns.md) | 下一篇：[RAG 評估模式](13-rag-evaluation-patterns.md)*
