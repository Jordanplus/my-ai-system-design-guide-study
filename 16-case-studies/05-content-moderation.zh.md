# 案例研究：大規模內容審核

本案例研究探討如何為一個每日處理數百萬則貼文的社群平台，設計一套由 AI 驅動的內容審核系統。

## 目錄

- [問題陳述](#problem-statement)
- [需求分析](#requirements-analysis)
- [架構設計](#architecture-design)
- [分類流程](#classification-pipeline)
- [人機協作（Human-in-the-Loop）](#human-in-the-loop)
- [對抗式穩健性](#adversarial-robustness)
- [成果與指標](#results-and-metrics)
- [面試演練](#interview-walkthrough)

---

## 問題陳述

**公司：** 擁有 5,000 萬每日活躍使用者的社群媒體平台

**目前狀態：**
- 每天 1,000 萬則貼文
- 500 名人工審核員
- 平均審核時間：4 小時
- 誤判率（false positive）：15%
- 觸及使用者的有害內容：2%

**目標：**
- 將有害內容的曝光降至 < 0.1%
- 在 < 15 分鐘內審核優先內容
- 將誤判率降至 < 5%
- 在不需線性增加審核員的情況下擴展規模

---

## 需求分析

### 內容類別

| 類別 | 嚴重程度 | 處置 | 延遲 |
|----------|----------|--------|---------|
| CSAM | 極嚴重 | 封鎖 + 通報 | 立即 |
| 暴力／血腥 | 高 | 封鎖 + 審核 | < 1 min |
| 仇恨言論 | 高 | 封鎖 + 審核 | < 5 min |
| 騷擾 | 中 | 審核 + 警告 | < 15 min |
| 垃圾訊息 | 中 | 降低優先序 | < 1 hour |
| 不實資訊 | 中 | 標註 + 審核 | < 1 hour |
| 成人內容 | 低 | 年齡分級 | < 1 hour |

### 準確度需求

| 指標 | 目標 | 理由 |
|--------|--------|-----------|
| 召回率（有害內容） | > 99% | 將有害曝光降到最低 |
| 精確率 | > 95% | 將誤判降到最低 |
| 延遲（極嚴重） | < 1 min | 防止擴散 |
| 延遲（標準） | < 15 min | 平衡資源 |

---

## 架構設計

### 高階架構

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONTENT MODERATION PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                                │
│  │   Content   │                                                │
│  │   Ingestion │                                                │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   TIER 1: FAST FILTERS                   │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │    │
│  │  │  Hash    │  │ Keyword  │  │  Known   │              │    │
│  │  │ Matching │  │ Blocklist│  │ Patterns │              │    │
│  │  └──────────┘  └──────────┘  └──────────┘              │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         │ Blocked           │ Pass              │ Elevated      │
│         ▼                   ▼                   ▼               │
│  ┌─────────────┐    ┌─────────────────────────────────────┐    │
│  │   Block +   │    │          TIER 2: ML MODELS          │    │
│  │   Report    │    │  ┌────────┐  ┌────────┐  ┌────────┐│    │
│  └─────────────┘    │  │ Vision │  │  Text  │  │ Multi- ││    │
│                     │  │ Model  │  │ Model  │  │ modal  ││    │
│                     │  └────────┘  └────────┘  └────────┘│    │
│                     └──────────────────┬──────────────────┘    │
│                                        │                        │
│         ┌──────────────────────────────┼──────────────────┐    │
│         │ High Confidence              │ Low Confidence   │    │
│         ▼                              ▼                   │    │
│  ┌─────────────┐              ┌─────────────────────────┐ │    │
│  │ Auto Action │              │    TIER 3: LLM REVIEW   │ │    │
│  └─────────────┘              │  (nuanced cases)        │ │    │
│                               └────────────┬────────────┘ │    │
│                                            │               │    │
│                        ┌───────────────────┼──────────────┐│    │
│                        │ Confident         │ Uncertain    ││    │
│                        ▼                   ▼              ││    │
│                 ┌─────────────┐    ┌─────────────┐       ││    │
│                 │ Auto Action │    │   Human     │       ││    │
│                 └─────────────┘    │   Review    │       ││    │
│                                    └─────────────┘       ││    │
│                                                          ││    │
└──────────────────────────────────────────────────────────┘│    │
```

此分層流程就像一棵決策樹。每一層只把它無法以低成本判定的部分往上升級。Tier 1 與 Tier 4 之間的每次決策成本比約為 1:5000，因此把路由做對是單位經濟效益的主要槓桿：

```mermaid
flowchart TD
    IN[Content Ingestion] --> T1{Tier 1: Fast Filters<br/>hash + keyword + pattern<br/>under 10ms, $0.0001}
    T1 -->|blocked: 5%| B1[Block + Report]
    T1 -->|elevated: pattern hit| T2
    T1 -->|pass clean: 85%| T2
    T2{Tier 2: ML Models<br/>vision + text + multimodal<br/>under 100ms, $0.001}
    T2 -->|high confidence: 85% of T2| AA1[Auto Action]
    T2 -->|low confidence: 15% of T2| T3
    T3{Tier 3: LLM Review<br/>nuanced reasoning<br/>under 3s, $0.01}
    T3 -->|confident| AA2[Auto Action]
    T3 -->|uncertain: 2%| HR[Human Review<br/>minutes, $0.50]
```

### 處理層級

| 層級 | 方法 | 延遲 | 成本 | 覆蓋率 |
|------|--------|---------|------|----------|
| 1 | Hash／keyword | < 10ms | $0.0001 | 5% 被封鎖 |
| 2 | ML 分類器 | < 100ms | $0.001 | 85% 自動判定 |
| 3 | LLM 審核 | < 3s | $0.01 | 8% 細膩案例 |
| 4 | 人工審核 | 數分鐘 | $0.50 | 2% 升級處理 |

---

## 分類流程

### Tier 1：快速過濾器

```python
class FastFilters:
    """
    Immediate blocking for known harmful content.
    No false positives for matches.
    """
    
    def __init__(self):
        self.hash_db = PhotoDNADatabase()  # CSAM detection
        self.keyword_filter = KeywordBlocklist()
        self.pattern_matcher = RegexPatterns()
    
    async def filter(self, content: Content) -> FilterResult:
        # CSAM hash matching (highest priority)
        if content.has_media:
            hash_match = await self.hash_db.check(content.media_hashes)
            if hash_match:
                return FilterResult(
                    action="block_report",
                    reason="csam_hash_match",
                    confidence=1.0,
                    tier=1
                )
        
        # Keyword blocklist
        if content.text:
            keyword_match = self.keyword_filter.check(content.text)
            if keyword_match and keyword_match.severity == "critical":
                return FilterResult(
                    action="block_review",
                    reason=f"keyword_{keyword_match.category}",
                    confidence=0.99,
                    tier=1
                )
        
        # Pattern matching (phone numbers in suspicious context, etc)
        pattern_match = self.pattern_matcher.check(content.text)
        if pattern_match:
            return FilterResult(
                action="elevate",
                reason=f"pattern_{pattern_match.type}",
                confidence=pattern_match.confidence,
                tier=1
            )
        
        return FilterResult(action="continue", tier=1)
```

### Tier 2：ML 分類

```python
### Tier 2: Native Multimodal Classification (Gemini 3 Flash)

```python
class MultimodalSafety:
    """
    Dec 2025 Shift: No separate OCR/Vision models.
    Gemini 3 Flash handles interleaved text/images natively for <$0.10 / 1M posts.
    """
    async def classify(self, content: Content) -> dict:
        # Native multimodal understanding catches context (e.g., text on a protest sign)
        response = await genai.submit(
            model="gemini-3-flash",
            content=[content.text, content.image_bytes],
            schema=SafetySchema
        )
        return response
```

### Tier 3: Nuanced LLM Review (GPT-5.2-mini)

```python
class NuanceReviewer:
    """
    Using GPT-5.2-mini for nuanced context (sarcasm, regional slang).
    Reasoning capabilities of 2025-mini models exceed 2024-frontier models.
    """
    async def review(self, content: Content, context: dict) -> dict:
        result = await client.chat.completions.create(
            model="gpt-5.2-mini",
            messages=[
                {"role": "system", "content": "Analyze for regional hate speech slang."},
                {"role": "user", "content": content.text}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(result)
```
```

---

## 人機協作（Human-in-the-Loop）

### 審核佇列管理

每一則內容都會經歷從提交到終止狀態的生命週期。以狀態機呈現生命週期，可讓 SLO 變得具體：每條優先序通道都有不同的目標「抵達終止狀態時間」，而申訴可以讓狀態轉回 pending：

```mermaid
stateDiagram-v2
    [*] --> Submitted : new post
    Submitted --> Tier1 : enter pipeline
    Tier1 --> Blocked : hash or keyword hit
    Tier1 --> Tier2 : pass or elevate
    Tier2 --> AutoAction : high confidence
    Tier2 --> Tier3 : low confidence
    Tier3 --> AutoAction : confident
    Tier3 --> CriticalQueue : CSAM or violence
    Tier3 --> HighQueue : hate speech
    Tier3 --> StandardQueue : other violation
    CriticalQueue --> HumanReview : SLO 15 min
    HighQueue --> HumanReview : SLO 1 hr
    StandardQueue --> HumanReview : SLO 24 hr
    HumanReview --> AutoAction : decision logged
    AutoAction --> [*]
    Blocked --> Appealed : user appeals
    AutoAction --> Appealed : user appeals
    Appealed --> AppealQueue
    AppealQueue --> HumanReview : SLO 7 days
```

```python
class ReviewQueueManager:
    """
    Prioritize and route content to human moderators.
    """
    
    def __init__(self):
        self.queues = {
            "critical": PriorityQueue(),  # CSAM, violence - immediate
            "high": PriorityQueue(),      # Hate speech - < 15 min
            "standard": PriorityQueue(),  # Other violations - < 1 hour
            "appeals": PriorityQueue()    # User appeals
        }
    
    async def enqueue(self, content: Content, result: ReviewResult):
        priority = self.calculate_priority(content, result)
        
        item = ReviewItem(
            content_id=content.id,
            content=content,
            ai_analysis=result,
            priority=priority,
            enqueued_at=datetime.now()
        )
        
        queue_name = self.get_queue(result.severity)
        await self.queues[queue_name].put(item)
        
        # Alert if critical
        if queue_name == "critical":
            await self.alert_moderators(item)
    
    def calculate_priority(self, content: Content, result: ReviewResult) -> float:
        priority = 0.0
        
        # Severity weight
        severity_weights = {"critical": 100, "high": 50, "medium": 20, "low": 5}
        priority += severity_weights.get(result.severity, 0)
        
        # Reach weight (viral content prioritized)
        priority += min(content.reach_score * 10, 50)
        
        # Confidence inverse (less confident = higher priority)
        priority += (1 - result.confidence) * 30
        
        return priority
```

### 審核員介面

```python
class ModeratorDecision:
    async def submit(
        self,
        moderator_id: str,
        content_id: str,
        decision: str,
        reason: str,
        notes: str = None
    ):
        # Record decision
        await self.store_decision({
            "content_id": content_id,
            "moderator_id": moderator_id,
            "decision": decision,
            "reason": reason,
            "notes": notes,
            "ai_recommendation": await self.get_ai_result(content_id),
            "decided_at": datetime.now()
        })
        
        # Execute action
        await self.execute_action(content_id, decision)
        
        # Update ML models with feedback
        await self.feedback_loop.record(
            content_id=content_id,
            ai_prediction=await self.get_ai_result(content_id),
            human_decision=decision
        )
```

---

## 對抗式穩健性

### 規避手法與防禦措施

| 規避手法 | 防禦措施 |
|-------------------|---------|
| 字元替換（h@te） | 正規化 + 同形異義字（homoglyph）對應 |
| 圖片文字（將文字放進圖片） | OCR 流程 |
| 隱形字元 | Unicode 正規化 |
| 上下文操弄 | 多輪（multi-turn）分析 |
| 編碼內容 | 解碼流程 |
| 對抗式圖片 | 穩健的視覺模型 |

### 防禦流程

```python
class AdversarialDefense:
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.ocr = OCRPipeline()
        self.decoder = ContentDecoder()
    
    def preprocess(self, content: Content) -> Content:
        processed = content.copy()
        
        # Normalize text
        if processed.text:
            processed.text = self.normalizer.normalize(processed.text)
            processed.text = self.decoder.decode_obfuscation(processed.text)
        
        # Extract text from images
        if processed.has_images:
            for image in processed.images:
                extracted_text = self.ocr.extract(image)
                if extracted_text:
                    processed.text = f"{processed.text}\n[IMAGE TEXT]: {extracted_text}"
        
        return processed
    
    def normalize(self, text: str) -> str:
        # Homoglyph normalization
        text = self.homoglyph_map(text)
        
        # Unicode normalization
        text = unicodedata.normalize("NFKC", text)
        
        # Remove zero-width characters
        text = re.sub(r"[\u200b-\u200f\u2028-\u202f]", "", text)
        
        # Leetspeak normalization
        text = self.leetspeak_decode(text)
        
        return text
```

---

## 成果與指標

### 效能比較

| 指標 | 之前 | 之後 | 改善幅度 |
|--------|--------|-------|-------------|
| 有害內容曝光 | 2% | 0.08% | 減少 96% |
| 審核延遲（極嚴重） | 4 小時 | 8 分鐘 | 快 30 倍 |
| 誤判率 | 15% | 4.2% | 減少 72% |
| 審核員效率 | 50/day | 200/day | 提升 4 倍 |

### 成本分析（Dec 2025）

| 元件 | 每 1,000 萬則貼文 | 備註 |
|-----------|---------------|-------|
| Tier 1 過濾器 | $0.10 | 可忽略不計 |
| Tier 2 多模態 | $0.50 | Gemini 3 Flash（$0.05/1M） |
| Tier 3 LLM（GPT-5.2） | $0.20 | 對 10% 流量做細膩度檢查 |
| 人工審核 | $15.00 | 僅聚焦於 1% 的量 |
| **總計** | **$15.80** | **相較 2024 年減少 40%** |

> [!TIP]
> **生產實務智慧：** 將繁重工作從「Tier 2 Vision/OCR」移到 **原生多模態（Gemini 3 Flash）**，讓流程複雜度降低了 70%，延遲降低了 400ms。

*人工審核仍占成本大宗，但已聚焦於困難案例*

---

## 面試演練

**面試官：**「為一個社群媒體平台設計一套內容審核系統。」

**優秀的回答：**

1. **釐清規模與需求**（1 min）
   - 「流量有多大？有哪些內容類型？可接受的誤判率是多少？」
   - 「是否有任何法規要求（CSAM 通報、GDPR）？」

2. **多層架構**（3 min）
   - 「我會採用一個複雜度逐層遞增的串接（cascade）架構：」
   - 「Tier 1：Hash 比對、關鍵字過濾——即時、確定」
   - 「Tier 2：ML 分類器——快速、專門化」
   - 「Tier 3：LLM 審核——細膩、具上下文感知能力」
   - 「Tier 4：人工審核——最終裁決者」
   - 「每一層處理前一層無法處理的部分」

3. **優先排序是關鍵**（2 min）
   - 「並非所有有害內容都同等重要。CSAM 與暴力需要立即處置。仇恨言論是優先處理，但不必即時。垃圾訊息可以等。」
   - 「依據嚴重程度、觸及範圍與信心水準的優先佇列」

4. **人機協作設計**（2 min）
   - 「以人工處理低信心決策與申訴」
   - 「AI 自動處理 95% 以上，使人工審核在經濟上可行」
   - 「回饋迴路：人工決策改善 ML 模型」

5. **對抗式穩健性**（2 min）
   - 「使用者會試圖規避偵測。防禦措施包括：」
   - 「針對混淆內容做文字正規化」
   - 「以 OCR 處理圖片中的文字」
   - 「隨著規避手法演進而持續更新模型」

6. **指標**（1 min）
   - 「主要指標：有害內容曝光率（目標 < 0.1%）」
   - 「次要指標：誤判率（使用者體驗）」
   - 「營運指標：審核延遲、審核員吞吐量」

---

## 參考資料

- Meta 內容審核：https://transparency.fb.com/
- Google Perspective API：https://perspectiveapi.com/
- OpenAI Moderation：https://platform.openai.com/docs/guides/moderation

---

*下一篇：[附錄 A：LLM 定價參考](../appendices/a-pricing-reference.md)*
