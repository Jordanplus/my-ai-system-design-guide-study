# RAG 評估模式

評估是 RAG 中最難、尚未解決的問題。你可以在一天內建好一條 retrieval pipeline；但要知道它是否真的有效卻需要數週。業界已收斂到一套分層的評估策略：以 RAG Triad 衡量正確性、以元件層級的指標做除錯、以及以自動化迴歸測試確保生產環境的安全性。Langfuse、LangWatch、Braintrust 與 Arize Phoenix 都內建了 RAG 評估範本；請依部署模式（自架 vs SaaS）以及你是否需要由評估把關（eval-gated）的 CI/CD 阻擋機制來選擇。

## 目錄

- [RAG Triad](#the-rag-triad)
- [RAGAS 框架與指標](#ragas-framework)
- [元件層級評估](#component-level-evaluation)
- [用於 RAG 的 LLM-as-Judge](#llm-as-judge)
- [建立黃金測試集](#golden-test-sets)
- [自動化迴歸測試](#regression-testing)
- [生產環境監控](#production-monitoring)
- [大規模評估的成本](#cost-at-scale)
- [工具比較](#tools-comparison)
- [系統設計面試切角](#system-design-interview-angle)
- [參考資料](#references)

---

## RAG Triad

RAG Triad 是評估 RAG 系統的基礎框架。它把正確性拆解成三個獨立的面向，每一個都能捕捉到不同的失敗模式。

```
                          User Query
                              |
                              v
                    +-------------------+
                    |    RETRIEVER      |
                    +-------------------+
                              |
                   (1) Context Relevance
                    "Did we retrieve the
                     right documents?"
                              |
                              v
                    +-------------------+
                    |    GENERATOR      |
                    +-------------------+
                         /         \
            (2) Groundedness      (3) Answer Relevance
            "Is the answer         "Does the answer
             supported by           address the actual
             the context?"          question?"
                  |                       |
                  v                       v
             No hallucination       No tangential answers
```

### 面向 1：Context Relevance（脈絡相關性）

**問題**：每個被檢索到的 chunk 是否真的與使用者查詢相關？

**能捕捉到什麼**：糟糕的 retrieval——向量搜尋回傳了關於錯誤主題的文件，或是查詢本身曖昧不清而 retriever 猜錯了。

**如何衡量**：
- 對每個被檢索到的 chunk 問：「這個 chunk 與回答查詢相關嗎？」
- 分數：（相關 chunk 數量）/（被檢索到的 chunk 總數）
- 分數 0.3 代表 70% 的檢索脈絡都是雜訊，迫使 LLM 在一堆不相關的草堆裡找針。

**為什麼重要**：低 context relevance 是多數 RAG 失敗的根本原因。即使是完美的 generator，也無法從不相關的脈絡中產出好答案。

### 面向 2：Groundedness（忠實度，Faithfulness）

**問題**：生成答案中的每一項主張，是否都有被檢索到的脈絡所支持？

**能捕捉到什麼**：幻覺（hallucination）——LLM 產生了聽起來合理、但並未出現在被檢索文件中的主張。

**如何衡量**：
- 把答案拆解成個別的主張／陳述。
- 對每個主張，在被檢索到的脈絡中搜尋支持證據。
- 分數：（被支持的主張數量）/（主張總數）
- 分數 0.7 代表答案中有 30% 是幻覺。

**為什麼重要**：這是企業客戶最在意的指標。一個不忠實的 RAG 系統比完全沒有 RAG 還糟，因為它會產出聽起來很有把握、卻是錯誤、還附上假引用的答案。

### 面向 3：Answer Relevance（答案相關性）

**問題**：最終答案是否真的回應了使用者所問的問題？

**能捕捉到什麼**：離題的答案——retrieval 不錯、答案有依據（grounded），但卻沒有回答問題。這在 retriever 找到相關但不完全吻合的內容時很常見。

**如何衡量**：
- 產生 N 個假設性問題，使該答案會是這些問題的好回應。
- 衡量這些假設性問題與原始查詢之間的語意相似度。
- 高相似度代表答案切題。

**為什麼重要**：一個系統可以檢索到相關脈絡並忠實地加以摘要，卻仍然沒抓到問題的重點。Answer relevance 能捕捉到這種情況。

### Triad 的失敗模式

| 失敗型態 | Context Relevance | Groundedness | Answer Relevance | 根本原因 |
|----------------|-------------------|-------------|-----------------|------------|
| 良好的 RAG | 高 | 高 | 高 | 系統正常運作 |
| 糟糕的 Retrieval | **低** | 高 | 低 | Embeddings 或搜尋設定錯誤 |
| 幻覺 | 高 | **低** | 高 | LLM 忽略脈絡、prompt 問題 |
| 離題的答案 | 高 | 高 | **低** | 查詢曖昧、索引錯誤 |
| 全面失敗 | **低** | **低** | **低** | pipeline 的根本性問題 |

---

## RAGAS 框架與指標

RAGAS（Retrieval Augmented Generation Assessment）是 RAG 領域最被廣泛採用的開源評估框架，提供不需要 ground-truth 答案的 reference-free（無參考）指標。

### 核心 RAGAS 指標

```
  RAGAS Metric Suite (v0.2+)
  |
  +-- Retrieval Metrics
  |     +-- Context Precision: Are relevant docs ranked higher?
  |     +-- Context Recall: Did we find all relevant docs?
  |     +-- Context Entities Recall: Did we capture key entities?
  |     +-- Context Relevance: Is retrieved context pertinent?
  |
  +-- Generation Metrics
  |     +-- Faithfulness: Are claims supported by context?
  |     +-- Answer Relevance: Does the answer address the query?
  |     +-- Answer Correctness: Does the answer match ground truth?
  |     +-- Answer Similarity: Semantic overlap with reference answer
  |
  +-- Noise & Robustness
  |     +-- Noise Sensitivity: How much does irrelevant context hurt?
  |
  +-- Multi-Modal (2025+)
        +-- Multimodal Faithfulness: Claims supported by images + text?
        +-- Multimodal Relevance: Are retrieved images relevant?
```

### RAGAS Faithfulness 如何運作（底層機制）

```
Step 1: Claim Extraction
  Answer: "Revenue grew 15% in Q3, driven by APAC expansion
           and the new enterprise tier launched in July."

  Claims:
    c1: "Revenue grew 15% in Q3"
    c2: "Growth was driven by APAC expansion"
    c3: "Growth was driven by the new enterprise tier"
    c4: "The enterprise tier was launched in July"

Step 2: Evidence Matching (per claim)
  c1: Found in Context chunk 3 --> SUPPORTED
  c2: Found in Context chunk 1 --> SUPPORTED
  c3: Not found in any context --> UNSUPPORTED
  c4: Context says "August" not "July" --> CONTRADICTED

Step 3: Score Calculation
  Faithfulness = supported / total = 2/4 = 0.50
```

### RAGAS Context Precision 如何運作

```
  Retrieved chunks ranked by retriever score:
    Rank 1: Chunk about Q3 revenue    --> Relevant (v_1 = 1)
    Rank 2: Chunk about company history --> Not relevant (v_2 = 0)
    Rank 3: Chunk about Q3 expenses   --> Relevant (v_3 = 1)
    Rank 4: Chunk about office locations --> Not relevant (v_4 = 0)

  Context Precision@K:
    Precision@1 = 1/1 = 1.0
    Precision@2 = 1/2 = 0.5
    Precision@3 = 2/3 = 0.67
    Precision@4 = 2/4 = 0.5

  Average Precision = (1.0*1 + 0.5*0 + 0.67*1 + 0.5*0) / 2
                    = (1.0 + 0.67) / 2 = 0.835
```

### RAGAS vs. 需要 Ground-Truth 的指標

| 指標 | 需要 Ground Truth？ | 它衡量什麼 |
|--------|-------------------|------------------|
| Faithfulness | 否 | 主張是否被脈絡支持 |
| Context Relevance | 否 | 被檢索 chunk 的相關性 |
| Answer Relevance | 否 | 答案是否回應查詢 |
| Context Recall | **是** | 對參考答案的涵蓋程度 |
| Answer Correctness | **是** | 與參考答案的吻合程度 |
| Answer Similarity | **是** | 與參考答案的語意重疊 |

**洞見**：先從 reference-free 指標（faithfulness、context relevance、answer relevance）開始，以利快速迭代。等你有了用於迴歸測試的黃金測試集後，再加入需要 ground-truth 的指標。

---

## 元件層級評估

RAG Triad 是端對端地評估整個系統。元件層級評估則是把每個階段隔離出來，以精準定位失敗點。

### Retriever 評估

```
  Query Set (100+ queries with known relevant documents)
        |
        v
  Run Retriever --> Retrieved docs per query
        |
        v
  Compare against ground truth relevance labels
        |
        v
  Metrics:
    +-- Recall@K: What fraction of relevant docs are in the top K?
    +-- MRR (Mean Reciprocal Rank): How high is the first relevant doc?
    +-- NDCG@K: Quality-weighted ranking metric
    +-- Precision@K: What fraction of top K are relevant?
```

**關鍵的 Retriever 基準**：

| 指標 | 最低門檻 | 良好 | 優異 |
|--------|------------------|------|-----------|
| Recall@10 | 0.70 | 0.85 | 0.95+ |
| MRR | 0.50 | 0.70 | 0.85+ |
| NDCG@10 | 0.50 | 0.70 | 0.85+ |
| Precision@5 | 0.40 | 0.60 | 0.80+ |

### Generator 評估

藉由固定 retrieval 脈絡、只改變生成部分，來隔離 generator。

```
  Fixed Context (known relevant chunks)
  + Query
        |
        v
  Run Generator --> Answer
        |
        v
  Metrics:
    +-- Faithfulness (RAGAS): Does it stay grounded?
    +-- Completeness: Does it cover all relevant info in context?
    +-- Conciseness: Is it appropriately brief?
    +-- Format Compliance: Does it follow the expected output format?
    +-- Citation Accuracy: Do citations point to the right chunks?
```

### Reranker 評估

```
  Query + Initial retrieval results (e.g., top 100 from BM25)
        |
        v
  Run Reranker --> Reranked results
        |
        v
  Metrics:
    +-- NDCG improvement: Did reranking move relevant docs up?
    +-- Recall preservation: Did reranking lose any relevant docs?
    +-- Latency: What did reranking add to query time?
```

---

## 用於 RAG 的 LLM-as-Judge

用一個 LLM 來評估另一個 LLM 的輸出，是當前主流的評估典範。它能在人工評估無法觸及的規模上擴展，但有已知的偏誤。

### 運作方式

```
  Evaluation Prompt Template:
  +------------------------------------------------------------------+
  | You are evaluating a RAG system. Given:                           |
  | - User Query: {query}                                             |
  | - Retrieved Context: {context}                                    |
  | - Generated Answer: {answer}                                      |
  |                                                                    |
  | Rate the following on a scale of 1-5:                             |
  | 1. Faithfulness: Are all claims in the answer supported by        |
  |    the context? (1=hallucinated, 5=fully grounded)                |
  | 2. Relevance: Does the answer address the user's question?        |
  |    (1=off-topic, 5=directly answers)                              |
  | 3. Completeness: Does the answer cover all relevant info?         |
  |    (1=missing key info, 5=comprehensive)                          |
  |                                                                    |
  | Provide scores and brief justifications in JSON.                  |
  +------------------------------------------------------------------+
```

### 已知的偏誤與緩解方式

| 偏誤 | 說明 | 緩解方式 |
|------|-------------|------------|
| **冗長性（Verbosity）** | LLM 評判者偏好較長的答案 | 依答案長度將分數正規化；加入簡潔度懲罰 |
| **自我偏好（Self-preference）** | GPT-4 給 GPT-4 的答案較高分 | 使用與 generator 不同的評判模型 |
| **位置（Position）** | A/B 比較中第一個選項被給較高分 | 隨機化呈現順序 |
| **諂媚（Sycophancy）** | 評判者同意正在被評估的系統 | 使用帶有具體標準的結構化評分標準（rubric） |
| **寬鬆（Leniency）** | LLM 很少給出低於 3/5 的分數 | 使用二元判定（pass/fail）而非 Likert 量表 |

### LLM-as-Judge 的最佳實務

1. **以二元判定取代量表**：「這項主張有被支持嗎？YES/NO」比「請以 1-5 評估支持程度」更可靠。
2. **拆解成原子化的評估**：一次只評估一項主張或一個面向。
3. **要求證據**：強制評判者引用支持／反駁每項主張的具體脈絡段落。
4. **以人類一致性校準**：讓 100 個以上的範例同時通過 LLM 與人類評判者。衡量 Cohen's Kappa。目標 > 0.7。
5. **使用可取得的最強模型**：以 Claude Opus 或 GPT-4o 作為評判者；絕不要使用與產生答案相同的模型。

---

## 建立黃金測試集

黃金測試集（golden test set）是一份經過策展、有版本控管的 (query, expected_context, expected_answer) 三元組集合，作為迴歸測試的 ground truth。

### 建立流程

```
  Step 1: Seed Collection
  +-------------------------------------------------------+
  | Source production queries (logs, support tickets)       |
  | Target: 200-500 diverse queries                        |
  | Coverage: all topics, question types, difficulty levels |
  +-------------------------------------------------------+
            |
            v
  Step 2: Synthetic Augmentation
  +-------------------------------------------------------+
  | Use RAGAS or DataMorgana to generate additional queries |
  | from your corpus:                                       |
  |   - Simple factual questions (40%)                     |
  |   - Multi-hop reasoning questions (25%)                |
  |   - Conditional/comparative questions (20%)            |
  |   - Adversarial/edge cases (15%)                       |
  +-------------------------------------------------------+
            |
            v
  Step 3: Human Annotation
  +-------------------------------------------------------+
  | For each query, annotate:                               |
  |   - Expected relevant document IDs (for retrieval eval) |
  |   - Reference answer (for generation eval)              |
  |   - Difficulty label (easy / medium / hard)             |
  |   - Category tags (topic, question type)                |
  +-------------------------------------------------------+
            |
            v
  Step 4: Versioning and Freezing
  +-------------------------------------------------------+
  | Store in version control (golden_set_v3.json)           |
  | FREEZE the set for each evaluation cycle                |
  | Never modify a frozen set -- create a new version       |
  +-------------------------------------------------------+
```

### 黃金測試集組成指引

| 問題類型 | 比例 | 用途 |
|--------------|-----------|---------|
| 簡單事實型 | 40% | 基準線：應該永遠通過 |
| 多跳推理（Multi-hop reasoning） | 25% | 測試跨文件的 retrieval |
| 比較型 | 15% | 測試對多份相關文件的 retrieval |
| 時序型（Temporal） | 10% | 測試對有版本／日期內容的處理 |
| 對抗型（Adversarial） | 10% | 測試穩健性（無解、超出範圍） |

### 使用 RAGAS 產生合成測試

```python
# Pseudocode: Generate synthetic test queries from your corpus
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context

generator = TestsetGenerator.from_langchain(
    generator_llm=ChatOpenAI(model="gpt-4o"),
    critic_llm=ChatOpenAI(model="gpt-4o"),
)
testset = generator.generate_with_langchain_docs(
    documents=load_documents("./knowledge_base/"),
    test_size=200,
    distributions={simple: 0.4, reasoning: 0.35, multi_context: 0.25}
)
# CRITICAL: Always human-review synthetic data before using as ground truth
testset.to_pandas().to_csv("golden_set_draft_v4.csv")
```

**警告**：合成測試集是起點，不是終點。務必以人工審查驗證，以免變成在對抗生成模型的產物（artifacts）做測試。

---

## 自動化迴歸測試

每一次 RAG pipeline 的變更（新的 embeddings、chunk 大小、prompt 編輯、reranker 抽換）都需要在部署前進行自動化迴歸測試。

### CI/CD 整合

```
  PR (RAG change) --> CI: Load golden set --> Run pipeline --> Compute metrics
                          --> Compare vs. baseline --> FAIL if drop > 5%, WARN if > 2%
                          --> Post metrics table as PR comment
```

### 品質關卡（Quality Gates）

| 指標 | 絕對最低值 | 迴歸門檻 |
|--------|-----------------|---------------------|
| Recall@10 | 0.85 | 較基準線下降 5% |
| MRR | 0.70 | 下降 5% |
| Faithfulness | 0.80 | 下降 3% |
| Answer Relevance | 0.75 | 下降 5% |
| Answer Correctness | 0.70 | 下降 5% |

任何低於其絕對最低值的指標都會阻擋該 PR。任何超過門檻的迴歸都會觸發警告，並標示出退化的特定查詢。

---

## 生產環境監控

離線評估有其必要，但並不足夠。生產環境的查詢與測試集不同，且 retrieval 品質會隨著語料庫變動而隨時間退化。

### 關鍵的生產環境訊號

| 訊號 | 它偵測什麼 | 如何衡量 |
|--------|----------------|----------------|
| **空檢索率（Empty Retrieval Rate）** | 沒有相關結果的查詢 | top-1 相似度 < 門檻的查詢百分比 |
| **相似度分數漂移（Similarity Score Drift）** | Embedding 或語料庫退化 | 追蹤平均相似度隨時間的變化；下降時告警 |
| **Faithfulness 抽樣** | 生產環境的幻覺率 | 對 5-10% 的隨機樣本執行 LLM-as-judge |
| **使用者回饋相關性** | 指標是否符合真實品質 | 比對讚／倒讚與自動化分數 |
| **延遲 P99（Latency P99）** | 效能退化 | 追蹤 retrieval + 生成的延遲 |
| **Token 使用量** | 成本漂移 | 監控每次查詢的平均脈絡 token 數 |

### Retrieval 品質漂移

當語料庫變動、但 embeddings、chunks 或 prompts 沒有跟上時，就會發生漂移。四種常見情境：(1) 帶有不同詞彙的新文件造成 embedding 空間不匹配——透過重新 embedding 受影響的 collection 來修正；(2) 使用者查詢型態轉向沒有內容的主題——透過監控空檢索率來偵測；(3) 過時的內容回傳了陳舊的答案——加入新鮮度（freshness）metadata 並優先採用較新的文件；(4) embedding 模型更新改變了相似度分布——在模型變更後重新校準所有門檻。

---

## 大規模評估的成本

LLM-as-judge 評估很強大，但很昂貴。理解其成本結構對編列預算至關重要。

### 每次查詢的成本（完整 RAG Triad）

| 指標 | LLM 呼叫次數 | Tokens | GPT-4o 成本 | Claude Haiku 成本 |
|--------|-----------|--------|-------------|-------------------|
| Faithfulness | ~3（extract + verify） | ~3k | $0.0075 | $0.00075 |
| Context Relevance | ~5（per chunk） | ~2.5k | $0.00625 | $0.000625 |
| Answer Relevance | ~2（question gen） | ~1.6k | $0.004 | $0.0004 |
| **完整 Triad** | **~10** | **~7k** | **~$0.018** | **~$0.002** |

### 擴展策略

| 評估類型 | 頻率 | 量 | 評判模型 | 每月成本（10k 查詢／天） |
|----------------|-----------|--------|-------------|-------------------------------|
| **CI 迴歸** | 每個 PR | 黃金測試集（500 個查詢） | GPT-4o | ~$9/run |
| **每夜批次（Nightly Batch）** | 每日 | 隨機 1k 個生產查詢 | Claude Haiku | ~$60/month |
| **生產抽樣** | 即時 | 5% 的流量 | Claude Haiku | ~$300/month |
| **深度稽核（Deep Audit）** | 每週 | 完整黃金測試集 + 分析 | GPT-4o | ~$36/month |

**洞見**：高量的生產抽樣請使用 Claude Haiku 4.5 或 GPT-5.5-mini。把 Claude Opus 4.7 或 GPT-5.5 保留給準確性比成本更重要的 CI 迴歸測試與深度稽核。

---

## 工具比較

### 框架總覽

| 工具 | 最適用於 | 開源 | 主要強項 | 主要弱項 |
|------|----------|------------|--------------|--------------|
| **RAGAS** | 快速 RAG 評估、合成資料 | 是 | Reference-free 指標、社群強大 | 指標結果缺乏解釋 |
| **DeepEval** | CI/CD 整合、為 LLM 做 TDD | 是 | 相容 pytest、分數能自我解釋 | 設置較繁重 |
| **TruLens** | RAG Triad 評估、可觀測性 | 是 | 創造了 RAG Triad 一詞、tracing 良好 | 開發較不活躍 |
| **UpTrain** | 生產環境監控、漂移偵測 | 是 | 混合式評估（LLM + 啟發式）、漂移告警 | 排名準確性較低 |
| **Braintrust** | 團隊協作、實驗追蹤 | 商業 | 最佳 UI/UX、實驗比較 | 進階功能需付費 |
| **LangSmith** | LangChain 生態系、tracing | 商業 | 深度整合 LangChain、tracing | 綁定於 LangChain 生態系 |

### 何時用什麼

```
  Starting a new RAG project?
    --> RAGAS for quick baseline metrics + synthetic test generation

  Adding RAG eval to CI/CD?
    --> DeepEval (pytest integration, quality gates as assertions)

  Need production monitoring?
    --> UpTrain or Braintrust (drift detection, alerting)

  Want end-to-end observability?
    --> LangSmith (if LangChain) or Braintrust (if framework-agnostic)

  Building custom eval pipeline?
    --> Roll your own with LLM-as-judge + the RAG Triad structure
```

### 自訂評估器模式

自訂評估器的核心模式很簡單：對每個 triad 面向，使用二元的 LLM-as-judge 呼叫並加以彙總。

```python
# Pseudocode: Core faithfulness evaluator (other dimensions follow the same pattern)

def evaluate_faithfulness(answer: str, context: str, judge) -> float:
    # Step 1: Extract atomic claims from the answer
    claims = judge.generate(f"List every factual claim as a JSON array:\n{answer}")

    # Step 2: Verify each claim against context (binary YES/NO)
    supported = sum(
        1 for claim in json.loads(claims)
        if "YES" in judge.generate(
            f"Is this claim supported by the context? YES or NO.\n"
            f"Claim: {claim}\nContext: {context}"
        ).upper()
    )
    return supported / max(len(json.loads(claims)), 1)
```

對 context relevance（逐 chunk：「這與查詢相關嗎？」）以及 answer relevance（產生假設性問題、衡量與原始查詢的相似度）套用相同的「先拆解再評判」模式。

---

## 系統設計面試切角

### Q：你部署了一套 RAG 系統，使用者回報答案有時是錯的。你會如何有系統地診斷並修復這個問題？

**好的回答：**

我會用 RAG Triad 來隔離失敗模式：

1. **抽樣失敗的查詢**：蒐集 50-100 個使用者標記答案不佳的查詢。依失敗類型分類。

2. **執行 triad**：
   - **Context Relevance 低？** --> retrieval 問題。系統抓到了錯誤的文件。修正方式：檢視 embedding 相似度分數、確認查詢語言是否與文件語言相符、嘗試 hybrid search（BM25 + dense）、加入 reranker。
   - **Groundedness 低？** --> 幻覺問題。即使有良好脈絡，LLM 仍在編造。修正方式：強化 system prompt（「只能根據提供的脈絡作答」）、降低 temperature、改用更聽從指令的模型，或加上引用要求。
   - **Answer Relevance 低？** --> 系統檢索到相關內容並忠實摘要，卻沒抓到實際問題。修正方式：改善查詢理解（query rewriting、HyDE）、加入查詢分類以路由到正確的索引。

3. **建立迴歸測試**：取那 50 個失敗查詢，標註其預期答案，並把它們加入黃金測試集。未來每一次 pipeline 變更都必須通過這些案例。

4. **建立持續監控**：抽樣 5% 的生產流量做自動化評估。當 faithfulness 低於 0.80 或 context relevance 低於 0.60 時告警。

關鍵洞見在於：「答案是錯的」並不是診斷——它是一個症狀。RAG Triad 能把模糊的抱怨轉化為具體、可採取行動的根本原因。

### Q：當你沒有 ground-truth 答案時，要如何評估一套 RAG 系統？

**好的回答：**

這是最常見的真實世界情境。我採用三層做法：

**第 1 層：Reference-free 指標（第 1 天）**。RAGAS 的 faithfulness 與 context relevance 不需要 ground truth。它們會告訴你系統是否在產生幻覺、以及 retrieval 是否運作正常。你可以立即在任何查詢上執行這些指標。

**第 2 層：合成黃金測試集（第 1 週）**。使用 RAGAS TestsetGenerator 從你的語料庫產生合成的 (query, answer) 配對。這能為 answer correctness 與 context recall 提供近似的 ground truth。以人工審查一份樣本來驗證品質。

**第 3 層：源自生產的黃金測試集（第 1 個月）**。從生產記錄中挖掘使用者滿意度高（按讚、無後續追問）的查詢。讓標註者為這些查詢標上參考答案。這會建立出一個反映真實使用型態、而非合成分布的黃金測試集。

權衡在於準確性 vs. 速度。第 1 層能在數小時內給你訊號，但較為近似。第 3 層能給你 ground truth，但需要數週。三者並行執行，先以第 1 層取得即時回饋。

### Q：你的 RAG 評估 pipeline 每天花費 $500 在 LLM 評判呼叫上。你會如何降低它？

**好的回答：**

四種策略，依影響力排序：

1. **分層評判模型**：對生產抽樣（90% 的量）使用 Claude Haiku（$0.002/query）。把 GPT-4o（$0.018/query）保留給 CI 迴歸測試與每週深度稽核。光是這一點就能砍掉 80% 的成本。

2. **聰明抽樣**：不要評估每一個查詢。抽樣 5% 的生產流量，依查詢類型與使用者區隔分層。對 CI，只跑黃金測試集（500 個查詢），而非完整的合成集。

3. **快取（Caching）**：許多生產查詢都很相似。對 (query, context, answer) 元組做雜湊並快取評估結果。相同或近乎相同的輸入即沿用快取的分數。

4. **啟發式預過濾（Heuristic pre-filters）**：在呼叫 LLM 評判者之前，先跑廉價的啟發式檢查。如果答案包含「我不知道」或與脈絡完全沒有重疊（ROUGE-L < 0.1），就跳過昂貴的 faithfulness 評估並直接給定分數。

目標是把評估預算花在能提供最多訊號之處：那些曖昧、模稜兩可、需要 LLM 評判者細膩推理的邊界案例。

---

## 參考資料

- Es et al. "RAGAS: Automated Evaluation of Retrieval Augmented Generation" (2023, arXiv:2309.15217)
- TruLens. "The RAG Triad" (2024)
- DeepEval. "Using the RAG Triad for RAG Evaluation" (2025)
- Confident AI. "RAG Evaluation Metrics" (2025)
- Microsoft. "The Path to a Golden Dataset" (2025)
- Prem AI. "RAG Evaluation: Metrics, Frameworks & Testing" (2026)

---

*Previous: [Multi-Modal RAG](12-multimodal-rag.md) | Next: Coming Soon*
