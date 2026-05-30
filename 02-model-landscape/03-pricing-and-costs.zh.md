# 定價與成本

理解 LLM 系統的成本結構，是生產環境規劃的關鍵。本章涵蓋定價模型、成本最佳化策略，以及總體擁有成本分析。

## 目錄

- [定價模型](#pricing-models)
- [目前的 API 定價](#current-api-pricing)
- [成本計算](#cost-calculation)
- [成本最佳化策略](#cost-optimization-strategies)
- [Context Caching 經濟學](#context-caching-economics)
- [自架與 GPU 雲端套利](#self-hosting-economics)
- [總體擁有成本](#total-cost-of-ownership)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 定價模型

### 以 Token 計價

大多數 LLM API 是按 token 收費：

```
Cost = (input_tokens × input_rate) + (output_tokens × output_rate)
```

**重點觀察：**
- Output token 的成本比 input token 高出 2-5 倍
- 定價會因模型等級而有顯著差異
- 部分供應商提供批次折扣

### 分級定價

部分供應商提供量大折扣：

| 等級 | 每月支出 | 折扣 |
|------|---------------|----------|
| Standard | $0 - $5K | 0% |
| Growth | $5K - $50K | 10-20% |
| Enterprise | $50K+ | 客製化議價 |

### 承諾型定價

以折扣價預先購買 token：

```
Standard: $2.50 / 1M input tokens
Committed (1-year): $2.00 / 1M input tokens (20% savings)
```

---

## 目前的 API 定價

### 2026 年 5 月定價

> **最後查核：2026 年 5 月 29 日。** 價格經常變動，請務必重新查核：[OpenAI](https://developers.openai.com/api/docs/pricing)、[Anthropic](https://platform.claude.com/docs/en/about-claude/pricing)、[Google](https://ai.google.dev/gemini-api/docs/pricing)、[xAI](https://docs.x.ai/developers/models)、[DeepSeek](https://api-docs.deepseek.com/quick_start/pricing)
>
> **2026 年生效的淘汰項目：** OpenAI 於 2026 年 2 月 13 日將 GPT-4o、GPT-4.1、GPT-4.1-mini、o4-mini 從 ChatGPT 中下架；gpt-5.2-chat-latest 與 gpt-5.3-chat-latest 於 2026 年 5 月 8 日棄用；Realtime API Beta 於 2026 年 5 月 12 日移除；Sora app 於 2026 年 4 月 26 日關閉（API 於 2026 年 9 月 24 日 EOL）。Google Vertex 於 2026 年 3 月 26 日淘汰 `gemini-3-pro-preview`；Project Mariner 於 2026 年 5 月 4 日關閉。Gemini 2.5 Pro/Flash 於 2026 年 6 月 17 日棄用。
>
> **價格異動：** Anthropic 於 2026 年 5 月 28 日發布 **Claude Opus 4.8**，價格與 Opus 4.7 相同，為每 1M $5 / $25，另提供可選的 fast mode，每 1M $10 / $50（比 Opus 4.7 的 fast mode 約快 2.5 倍、便宜 3 倍，後者為 $30 / $150）。DeepSeek 於 2026 年 5 月 22 日將其 75% 的 V4 Pro 折扣**永久化**：自 2026 年 6 月 1 日起，新的牌價降至原價的 25%（每 1M input/output 為 $0.435 / $0.87），且所有 DeepSeek 模型的 cache-hit input 價格已於 2026 年 4 月 26 日調降為發布價的 1/10。DeepSeek V4 Flash（每 1M $0.14 / $0.28，1M context）以極大差距成為最便宜的前沿等級 API。

#### OpenAI（GPT-5.x 世代）
| 模型 | Input / 1M | Output / 1M | 備註 |
|-------|------------|-------------|-------|
| **GPT-5.5** ⭐ NEW | $5.00 | $30.00 | 2026 年 4 月 23 日發布。1M context。全新等級的多模態旗艦。 |
| **GPT-5.5 Instant** ⭐ NEW | check latest | check latest | 自 2026 年 5 月 5 日起為 ChatGPT 與 `chat-latest` 的預設。在高風險 prompt 上幻覺減少 52.5%。 |
| **GPT-Realtime-2** ⭐ NEW | $32.00 (audio) | $64.00 (audio) | 2026 年 5 月 7 日發布。GPT-5 等級的即時語音。 |
| **GPT-Realtime-Translate** ⭐ NEW | (audio pricing) | (audio pricing) | 70+ 種輸入 → 13 種輸出語言。 |
| **GPT-5.4 Pro** | $30.00 | $180.00 | 最強推理；長 context 加倍為 $60/$270 |
| **GPT-5.4** | $2.50 | $15.00 | 旗艦；原生 computer use；cached input $1.25 |
| **GPT-5.4-mini** | $0.75 | $4.50 | GPT-5 等級中最佳的成本/效能比 |
| **GPT-5.4-nano** | check latest | check latest | 最小的 GPT-5.4 變體；2026 年 3 月發布 |
| **GPT-4o** | $2.50 | $10.00 | 2026 年 2 月 13 日從 ChatGPT 下架；API 存取狀況不一 |
| **GPT-4o-mini** | $0.15 | $0.60 | 舊版；請查核 API 可用性 |

#### Anthropic（Claude 4.x 世代）
| 模型 | Input / 1M | Output / 1M | Context | 備註 |
|-------|------------|-------------|---------|-------|
| **Claude Opus 4.8** ⭐ NEW | $5.00 | $25.00 | 1M | 2026 年 5 月 28 日於 API、Bedrock、Vertex AI 發布。Dynamic Workflows 研究預覽，支援平行 subagent。可選 fast mode，每 1M $10 / $50（比 Opus 4.7 的 fast mode 約快 2.5 倍、便宜 3 倍）。SWE-bench Verified 88.6%；SWE-Bench Pro 69.2%；OSWorld-Verified 82.3%。 |
| **Claude Opus 4.7** | $5.00 | $25.00 | 1M | 2026 年 4 月 16 日於 API、Bedrock、Vertex、Microsoft Foundry 發布。更高解析度的視覺、改進的 SWE。Fast mode：每 1M $30 / $150。 |
| **Claude Opus 4.6** | $5.00 | $25.00 | 1M | 128K 最大 output；標準費率下的 adaptive thinking。 |
| **Claude Sonnet 4.6** | $3.00 | $15.00 | 1M | 以較低成本涵蓋大多數 Opus 等級的任務。**截至 2026 年 5 月 29 日尚未發布 Sonnet 4.8。** |
| **Claude Haiku 4.5** | $1.00 | $5.00 | 200K | 最快的 Anthropic 模型；cache hit input 每 1M $0.10。 |
| **Claude Mythos Preview** | n/a | n/a | - | 限 ~11 家 Project Glasswing 合作夥伴使用；未開放一般使用。 |

> [!NOTE]
> **Claude 在標準定價下的 1M context**：Opus 4.8、Opus 4.7、Opus 4.6 與 Sonnet 4.6 在標準費率下即包含完整的 1M token context window，長 context 無需另付高階費率。Batch API 提供 50% 折扣。Cache hit 的成本為標準 input 價格的 10%。Opus 4.8（每 1M $10 / $50）與 Opus 4.7 / 4.6（每 1M $30 / $150）的 fast mode 定價會與 caching 倍率疊加，但無法用於 Batch API 或 AWS 上的 Claude Platform。

#### Google（Gemini 3.x 世代）
| 模型 | Input / 1M | Output / 1M | Context | 備註 |
|-------|------------|-------------|---------|-------|
| **Gemini 3.1 Pro** | $2.00 | $12.00 | 1M | 200K+ context：$4.00/$18.00 |
| **Gemini 3.1 Flash** | $0.10 | $3.00 | 1M | 最佳價格/效能比；高流量 |
| **Gemini 2.5 Flash-Lite** | $0.10 | $0.40 | 1M | 2026 年 6 月棄用 |

> [!WARNING]
> **Gemini 2.5 棄用**：Gemini 2.5 Pro 與 2.5 Flash 排定於 2026 年 6 月 17 日棄用。請遷移至 Gemini 3.x 模型。

#### xAI（Grok）
| 模型 | Input / 1M | Output / 1M | Context | 備註 |
|-------|------------|-------------|---------|-------|
| **Grok 4** | $3.00 | $15.00 | 256K | 原生 tool use；即時搜尋 |
| **Grok 4.1 Fast** | $0.20 | $0.50 | 2M | 高流量、低成本 |
| **Grok 3 mini** | check latest | check latest | - | 更快，但準確度較低 |

#### 透過 API 提供的 Open-Weight 模型（2026 年 5 月）
| 模型 | Input / 1M | Output / 1M | Context | 供應商範例 |
|-------|------------|-------------|---------|-------------------|
| **DeepSeek-V3.2** | $0.28 | $0.42 | 128K | DeepSeek API。98% cache-hit 折扣。透過路由，有效費率可降低 10–30×。 |
| **DeepSeek V4 Pro** ⭐ NEW | $0.435 | $0.87 | 1M | DeepSeek API。75% 的促銷折扣已**永久化**：自 2026 年 6 月 1 日起，新牌價為原價的 25%（$1.74 / $3.48）。Cache-hit input：$0.003625/M。在 1M token 下約為 V3.2 的 27% 算力 / 10% 記憶體。 |
| **DeepSeek V4 Flash** ⭐ NEW | $0.14 | $0.28 | 1M | DeepSeek API。Cache-hit input：$0.0028/M（98% 折扣）。13B-active MoE。目前最便宜的前沿等級 1M-context API。 |
| **Mistral Medium 3.5** ⭐ NEW | $1.50 | check latest | 256K | Mistral API。統一的 chat/reasoning/coding/vision；SWE-Bench Verified 77.6%。 |
| **Kimi K2.6** ⭐ NEW | check latest | check latest | - | Moonshot API。1T MoE / 32B active；agent swarm 可達 300 個 sub-agent。 |
| **Qwen 3.6-35B-A3B** ⭐ NEW | check latest | check latest | - | Apache 2.0 權重；可自架或透過 API 供應商使用。 |
| **Llama 4 Scout** | $0.11 | $0.34 | 10M | Together AI、Groq、Fireworks。注意：超過 32K 後有效 context 會迅速衰退。 |
| **Llama 4 Maverick** | $0.27 | $0.85 | 1M | Together AI、Groq、Fireworks。需具備 MoE-aware 的服務架構。 |
| **DeepSeek-V3** | $0.25 | $1.10 | 128K | DeepSeek API、Together AI |
| **DeepSeek-R1** | $0.55 | $2.19 | 128K | DeepSeek API |
| **Mistral Large 3** | $0.50 | $1.50 | 256K | Mistral API、AWS Bedrock |
| **Llama 3.3 70B** | ~$0.10–0.20 | ~$0.30–0.60 | 128K | Groq、Together AI |
| **Qwen2.5-Coder-32B** | ~$0.50 | ~$1.00 | 32K | Together AI |
| **Gemma 4 (31B / 26B-A4B MoE / E4B / E2B)** ⭐ NEW | self-host | self-host | 256K | Apache 2.0。140+ 種語言；原生 vision/audio；function calling。 |

#### Embedding 模型（2026 年 5 月）
| 模型 | 成本 / 1M tokens | 維度 |
|-------|------------------|-----------|
| **Cohere Embed 4** ⭐ NEW | $0.10 | 256 / 512 / 1024 / 1536 (Matryoshka) |
| **text-embedding-3-large** | $0.13 | 3072 |
| **text-embedding-3-small** | $0.02 | 1536 |
| **Voyage-3** | $0.06 | 1024 |
| **Cohere embed-v3** | $0.10 | 1024 |

> [!IMPORTANT]
> **推論時的計算成本：** 對於具備「Extended Thinking」或 reasoning 模式的模型（GPT-5.4 Pro、Claude Opus 4.6），即使未顯示給使用者，你仍需為**內部 thinking token** 付費。對於邏輯密集的任務，這可能使單次請求的總成本增加 2x-10x。在生產環境中請務必設定 `budget_tokens` 上限。

---

## 成本計算

### 基本成本公式

```python
def calculate_request_cost(
    input_tokens: int,
    output_tokens: int,
    model: str
) -> float:
    pricing = {
        "gpt-5.4": {"input": 2.50, "output": 15.00},
        "gpt-5.4-mini": {"input": 0.75, "output": 4.50},
        "claude-sonnet-4.6": {"input": 3.00, "output": 15.00},
        "claude-opus-4.6": {"input": 5.00, "output": 25.00},
        "gemini-3.1-flash": {"input": 0.10, "output": 3.00},
    }
    
    rates = pricing[model]
    cost = (
        (input_tokens / 1_000_000) * rates["input"] +
        (output_tokens / 1_000_000) * rates["output"]
    )
    return cost
```

### 成本計算範例

**情境 1：RAG 聊天機器人**
```
Per request:
- System prompt: 500 tokens
- Retrieved context: 2,000 tokens
- User message: 100 tokens
- Response: 300 tokens

Input: 2,600 tokens, Output: 300 tokens

GPT-5.4 cost: (2600 × $2.50 + 300 × $15) / 1M = $0.0110 per request

At 10,000 requests/day:
Daily: $95
Monthly: $2,850
```

**情境 2：文件摘要**
```
Per document:
- Document: 8,000 tokens
- Summary: 500 tokens

GPT-5.4 cost: (8000 × $2.50 + 500 × $15) / 1M = $0.0275

1,000 documents: $27.50
10,000 documents: $275
```

### 每月成本預估

```python
def project_monthly_cost(
    requests_per_day: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    model: str
) -> dict:
    per_request = calculate_request_cost(
        avg_input_tokens, avg_output_tokens, model
    )
    
    daily = per_request * requests_per_day
    monthly = daily * 30
    yearly = monthly * 12
    
    return {
        "per_request": per_request,
        "daily": daily,
        "monthly": monthly,
        "yearly": yearly
    }

# Example
costs = project_monthly_cost(
    requests_per_day=50000,
    avg_input_tokens=2000,
    avg_output_tokens=400,
    model="gpt-5.4"
)
# Output: ~$18,750/month
```

---

## 成本最佳化策略

### 策略 1：模型路由

將請求路由至適當的模型等級：

```python
class ModelRouter:
    def __init__(self):
        self.classifier = load_complexity_classifier()
    
    def route(self, query: str, context: str) -> str:
        complexity = self.classifier.predict(query)
        
        if complexity < 0.3:
            return "gpt-5.4-mini"  # Simple queries
        elif complexity < 0.7:
            return "gpt-5.4-mini"  # Medium, try cheap first
        else:
            return "gpt-5.4"  # Complex queries

    def route_with_fallback(self, query: str, context: str) -> str:
        # Try cheap model first
        response = self.try_model("gpt-5.4-mini", query, context)

        if self.is_quality_sufficient(response):
            return response

        # Fallback to expensive model
        return self.try_model("gpt-5.4", query, context)
```

**潛在節省：** 50-70%，且對品質影響極小

### 策略 2：Prompt 最佳化

在不損失品質的前提下減少 token 數量：

```python
# Before: 2,500 tokens
system_prompt = """
You are a helpful customer support assistant for Acme Corp. 
You have access to our product documentation and should answer 
questions accurately and helpfully. Always be polite and professional.
If you don't know something, say so rather than making things up.
Format your responses clearly with bullet points when listing items.
[... more verbose instructions ...]
"""

# After: 800 tokens
system_prompt = """
You are Acme Corp's support assistant.
Rules:
- Answer from provided context only
- Admit uncertainty
- Use bullet points for lists
- Be concise
"""

# Savings: 1,700 tokens × $2.50/1M = $0.00425 per request
# At 10K requests/day: $42.50/day = $1,275/month
```

### 策略 3：Caching

為重複或相似的查詢快取回應：

```python
class ResponseCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.exact_cache = TTLCache(maxsize=10000, ttl=ttl_seconds)
        self.semantic_cache = SemanticCache(threshold=0.95)
    
    def get_or_generate(self, query: str, context: str) -> tuple[str, bool]:
        # Check exact cache
        cache_key = self.make_key(query, context)
        if cache_key in self.exact_cache:
            return self.exact_cache[cache_key], True  # Cache hit
        
        # Check semantic cache
        similar = self.semantic_cache.find_similar(query)
        if similar:
            return similar.response, True  # Semantic hit
        
        # Generate new response
        response = self.generate(query, context)
        self.exact_cache[cache_key] = response
        self.semantic_cache.add(query, response)
        
        return response, False  # Cache miss

# With 30% cache hit rate:
# Baseline: $3,000/month
# With caching: $2,100/month
# Savings: $900/month
```

### 策略 4：批次處理

將多個請求一起處理以提升效率：

```python
# Real-time: pay full price
for query in queries:
    response = model.generate(query)

# Batch API (OpenAI offers 50% discount):
batch_responses = model.batch_generate(queries)
# Cost: 50% of real-time pricing
```

### 策略 5：Output 長度控制

適當地限制回應長度：

```python
# Reduce unnecessary output
response = model.generate(
    prompt=prompt,
    max_tokens=300,  # Limit output
    stop=["\n\n"]    # Stop at natural break
)

# Cost impact:
# Before: avg 500 output tokens = $0.0075 per request (GPT-5.4)
# After: avg 250 output tokens = $0.00375 per request
# Savings: 50% on output costs
```

### 成本最佳化總結

| 策略 | 投入心力 | 潛在節省 |
|----------|--------|-------------------|
| 模型路由 | 中 | 50-70% |
| **Context Caching** | 低 | **60-90%（Input）** |
| Prompt 最佳化 | 低 | 20-40% |
| 回應快取 | 中 | 20-40% |
| 批次處理 | 低 | 50%（OpenAI/Anthropic） |

---

## Context Caching 經濟學

**RAG 的「黃金法則」（2026 年依然成立）。**
如果你有固定的 system prompt，或共用的知識庫（prefix）大於 10,000 token，那麼 **Context Caching** 是必備的。

**損益兩平分析（Claude Sonnet 4.6）：**
- **Standard Input**：每 1M token $3.00
- **Cached Input**：每 1M token $0.30（90% 折扣）
- **Cache Write Fee**：每 1M token $3.75（5 分鐘 TTL，1.25x）；$6.00（1 小時 TTL，2x）

`Break-even = (Write Fee) / (Standard Rate - Cached Rate) ≈ 1.4 requests (5-min) or 2.2 requests (1-hour)`

如果你的長 prefix 被**超過 2 位使用者**使用，那麼快取它必定比每次都原樣傳送更便宜。OpenAI 與 Anthropic 現在都提供可與 caching 疊加的 batch API 折扣（5 折）。

---

## 自架與 GPU 雲端套利

**Reserved 與 Serverless 之間的取捨：**

| 模型大小 | Serverless（RunPod/Together） | Reserved（Lambda/AWS） |
|------------|-----------------------------|-----------------------|
| **突發容量** | 無限（有冷啟動） | 固定 |
| **使用率** | 只為運算時間付費 | 24/7 固定成本 |
| **TCO 損益兩平**| **使用率 < 40% 時較划算** | **使用率 > 40% 時較划算** |

**Principal 等級的細微考量：**
「GPU 雲端套利」是指根據 **spot 執行個體的可用性**，在不同供應商之間搬移生產工作負載。像 **Skypilot** 這類工具可將此流程自動化，透過追蹤全球的「低需求」區域，最多可節省 60% 的自架成本。MoE 模型的興起（Llama 4 Scout 可放進單張 H100、Maverick 約需 2 張 H100、DeepSeek V4 Flash 需 4 張 H100），相較於 dense 模型，進一步降低了自架的 GPU 需求。

### 何時適合自架

```
Break-even analysis:

API cost at scale:
- 1M requests/month
- 2,500 tokens average
- GPT-5.4: ~$37,500/month
- Claude Sonnet 4.6: ~$30,000/month

Self-hosted equivalent (Llama 4 Maverick via MoE):
- 2x H100 80GB: ~$6/hour × 730 = $4,380/month
- Engineering time: $5,000/month (0.5 FTE)
- Ops overhead: $2,000/month
- Total: ~$11,380/month

Savings vs GPT-5.4: $26,120/month = 70%
Savings vs Claude Sonnet 4.6: $18,620/month = 62%
```

### 自架成本組成

| 組成項目 | 每月成本 | 備註 |
|-----------|--------------|-------|
| GPU 運算 | $5K-20K | 視模型大小而定 |
| 儲存 | $200-500 | 模型權重、日誌 |
| 網路 | $100-500 | Egress、負載平衡 |
| 工程 | $5K-15K | 部分 FTE 用於營運 |
| 監控 | $100-500 | 可觀測性工具 |

### 依模型大小的 GPU 需求

| 模型大小 | GPU 配置 | 預估每月成本 |
|------------|------------|---------------------|
| 7B (INT4) | 1x A10G | $500-800 |
| 7B (FP16) | 1x A100 40GB | $1,500-2,500 |
| 70B (INT4) | 2x A100 80GB | $5,000-8,000 |
| 70B (FP16) | 4x A100 80GB | $10,000-15,000 |
| 405B (INT4) | 8x H100 | $20,000-30,000 |

### 決策框架

```
Choose API when:
- Volume < 100K requests/month
- No ML ops expertise
- Need highest quality (frontier models)
- Fast iteration needed

Choose self-hosting when:
- Volume > 500K requests/month
- Have ML infrastructure team
- Data privacy requirements
- Predictable, stable workload
- Custom fine-tuning needed
```

---

## 總體擁有成本

### TCO 組成

```python
def calculate_tco(scenario: dict) -> dict:
    # Direct costs
    api_or_compute = scenario["monthly_api_cost"]
    
    # Engineering costs
    development = scenario["dev_hours"] * scenario["engineer_rate"]
    maintenance = scenario["maintenance_hours"] * scenario["engineer_rate"]
    
    # Infrastructure
    vector_db = scenario["vector_db_cost"]
    monitoring = scenario["monitoring_cost"]
    
    # Indirect costs
    downtime_risk = scenario["expected_downtime_hours"] * scenario["revenue_per_hour"]
    
    monthly_tco = (
        api_or_compute +
        development / 12 +  # Amortized over year
        maintenance +
        vector_db +
        monitoring +
        downtime_risk
    )
    
    return {
        "monthly_tco": monthly_tco,
        "yearly_tco": monthly_tco * 12,
        "breakdown": {
            "llm": api_or_compute,
            "engineering": development / 12 + maintenance,
            "infrastructure": vector_db + monitoring,
            "risk": downtime_risk
        }
    }
```

### TCO 比較範例

**情境：客服機器人（每月 50K 請求）**

| 成本組成 | 採用 API | 自架 |
|----------------|-----------|-------------|
| LLM 成本 | $5,000 | $3,000 |
| Vector DB | $70 | $200 |
| 工程（每月） | $500 | $3,000 |
| 監控 | $100 | $200 |
| **每月合計** | **$5,670** | **$6,400** |

*在此規模下，由於工程開銷，採用 API 較便宜。*

**情境：大規模 RAG（每月 2M 請求）**

| 成本組成 | 採用 API | 自架 |
|----------------|-----------|-------------|
| LLM 成本 | $50,000 | $15,000 |
| Vector DB | $500 | $1,000 |
| 工程（每月） | $1,000 | $8,000 |
| 監控 | $200 | $500 |
| **每月合計** | **$51,700** | **$24,500** |

*在此規模下，自架明顯較便宜。*

---

## 面試問題

### Q：你會如何為高流量的 RAG 應用最佳化成本？

**理想回答：**
我會分層處理成本最佳化：

**1. 架構最佳化：**
- 模型路由：對簡單查詢使用便宜的模型
- 快取：30-40% 的查詢可能可快取
- Prompt 壓縮：將 system prompt 的 token 最小化

**2. 模型選擇：**
```
Simple queries (60%): GPT-5.4-mini at $0.003/request
Complex queries (40%): GPT-5.4 at $0.011/request
Weighted avg: $0.0062/request (vs $0.011 all GPT-5.4)
Savings: 44%
```

**3. 基礎設施：**
- 批次更新 embedding（便宜 50%）
- 適當調整 vector DB 規模
- 盡可能使用 spot 執行個體

**4. 監控：**
- 追蹤每種查詢類型的成本
- 對異常發出告警
- 定期進行成本檢視

### Q：你會在什麼情況下建議自架而非使用 API？

**理想回答：**
決策取決於多項因素：

**流量門檻：**
- 低於每月 100K：幾乎都用 API
- 100K-500K：逐案評估
- 高於 500K：通常自架較有利

**團隊能力：**
- 無 ML ops：無論規模都用 API
- 有強大的基礎設施團隊：可更早考慮自架

**品質需求：**
- 需要絕對最佳：API（前沿模型）
- 夠用即可：自架的 open 模型

**其他因素：**
- 資料隱私：可能迫使你必須自架
- 延遲控制：自架可提供更多掌控
- Fine-tuning 需求：自架能進行更多客製化

**我的建議流程：**
1. 先用 API 以求最快的迭代
2. 建立抽象層以便切換模型
3. 當支出超過每月 $10K 時評估自架
4. 在正式投入前，先以 shadow deployment 進行試行

---

## 參考資料

- OpenAI Pricing: https://developers.openai.com/api/docs/pricing
- Anthropic Pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Google AI Pricing: https://ai.google.dev/gemini-api/docs/pricing
- xAI Pricing: https://docs.x.ai/developers/models
- Mistral Pricing: https://docs.mistral.ai/getting-started/changelog
- Lambda Labs GPU Pricing: https://lambdalabs.com/service/gpu-cloud
- RunPod Pricing: https://www.runpod.io/pricing
- LLM Pricing Comparison: https://pricepertoken.com/

---

*上一篇：[能力評估](02-capability-assessment.md) | 下一篇：[模型選擇指南](04-model-selection-guide.md)*
