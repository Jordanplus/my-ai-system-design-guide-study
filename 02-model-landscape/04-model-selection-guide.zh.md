# 模型選型指南

一套用於為你的使用情境挑選合適 LLM 的實務框架，涵蓋能力、成本、延遲與營運面向的考量。

## 目錄

- [選型框架](#selection-framework)
- [能力比較](#capability-comparison)
- [使用情境對應](#use-case-mapping)
- [成本分析](#cost-analysis)
- [營運考量](#operational-considerations)
- [多模型策略](#multi-model-strategies)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 選型框架

### 決策樹（2025 年 12 月）

```
Start Here
    │
    ├── Need autonomous agents / long-horizon planning?
    │   └── Yes ─────────────────────────────────────────┐
    │   └── No ──┐                                       │
    │            │                                       ▼
    │            │                              ┌─────────────────┐
    │            │                              │ Claude Opus 4.8 │
    │            │                              │ GPT-5.5 reason. │
    │            │                              └─────────────────┘
    │            │
    ├── Need best software engineering / coding?
    │   └── Yes ─────────────────────────────────────────┐
    │   └── No ──┐                                       │
    │            │                                       ▼
    │            │                              ┌─────────────────┐
    │            │                              │ GPT-5.5 88.7% / │
    │            │                              │ Opus 4.8 88.6%  │
    │            │                              │ Sonnet 4.6 cheap│
    │            │                              └─────────────────┘
    │            │
    ├── Need to process massive context (>1M)?
    │   └── Yes ─────────────────────────────────────────┐
    │   └── No ──┐                                       │
    │            │                                       ▼
    │            │                              ┌─────────────────┐
    │            │                              │ Gemini 3.0 Pro  │
    │            │                              │ (2.5M context)  │
    │            │                              └─────────────────┘
    │            │
    ├── Cost-sensitive high volume?
    │   └── Yes ─────────────────────────────────────────┐
    │   └── No ──┐                                       │
    │            │                                       ▼
    │            │                              ┌─────────────────┐
    │            │                              │ Gemini 3 Flash /│
    │            │                              │ o4-mini         │
    │            │                              └─────────────────┘
    │            │
    └── Default: Production Choice
                 ▼
        ┌─────────────────┐
        │ Claude Sonnet 4.6│
        │ GPT-5.5-mini    │
        └─────────────────┘
```

### 關鍵選型因素

| 因素 | 權重 | 考量 |
|--------|--------|----------------|
| **Agentic 可靠性** | 高 | 工具呼叫（tool-calling）準確度、多步驟規劃 |
| **長文脈召回** | 高 | 在 1M+ 文脈下的大海撈針（needle-in-a-haystack）表現 |
| **速率上限** | 高 | **（資深要點）**：供應商能否在不出現 429 錯誤的情況下承載你的 P99 吞吐量？ |
| **生態系成熟度** | 高 | 正式環境實績、SDK 支援，以及 Enterprise SLA |
| **成本 / 輸出 Token** | 中 | Agentic 迴圈會消耗多 5x-10x 的 token |

---

## 能力比較

### 前沿模型比較（2026 年 5 月）

| 模型 | 優勢 | 缺點 | 文脈 | 最適用於 |
|-------|-----------|------|---------|----------|
| **Claude Opus 4.8** | 長時間執行的 agentic coding（SWE-bench 88.6%）、可搭配平行 subagent 的 Dynamic Workflows、$10/$50 fast mode | 標準定價與 4.7 相同為 $5/$25；GPT-5.5 在單次（single-shot）SWE-bench 上些微領先 | 1M | 程式庫規模的遷移、自主編碼迴圈 |
| **GPT-5.5** | SWE-bench Verified 領先者（88.7%）、Terminal-Bench 領先者（78.2%）、原生 omni 多模態 | 成本高（$5/$30） | 1M | 多代理（multi-agent）系統、單次編碼 |
| **Claude Opus 4.7** | 前一代旗艦（SWE-bench 87.6%、SWE-Bench Pro 64.3%） | 已被同價的 4.8 取代 | 1M | 沒有遷移壓力的既有 4.7 部署 |
| **Claude Sonnet 4.6** | 強勁的成本／品質平衡、標準價即享完整 1M | 尚未推出 Sonnet 4.8 | 1M | 通用正式環境主力 |
| **Gemini 3.1 Pro** | GPQA Diamond 領先者（94.3%）、1M 多模態、Deep Think 模式 | Deep Think 會出現延遲尖峰 | 1M | 科學推理、多模態 |
| **DeepSeek-R1** | 開源推理、具競爭力的數學能力 | 僅限推理；通用用途非前沿水準 | 128K | 數學、複雜除錯、開放權重推理 |

### 平價模型比較

| 模型 | 成本（每 1M 輸入/輸出） | 品質 | 文脈 | 最適用於 |
|-------|----------------------------|---------|---------|----------|
| **Gemini 3 Flash** | $0.05 / $0.20 | 前沿等級 | 1M | 高流量 RAG |
| **o4-mini** | $0.10 / $0.40 | 優異 | 128K | 快速推理任務 |
| **Llama 4 8B** | 自架（H100/L40） | 強勁 | 128K | 裝置端、私有部署 |

### 開源模型

| 模型 | 參數量 | 品質 | 最適用於 |
|-------|------------|---------|----------|
| **Llama 4 70B** | 70B | 具前沿競爭力 | 通用開源首選 |
| **Nemotron 3 Ultra** | 500B MoE | Agentic 精通 | 可擴展的開源代理 |
| **DeepSeek V3.2** | 671B MoE | 極致效能 | 達到前沿品質的最低 TCO |

---

## 使用情境對應

### 依應用類型（2026 年 5 月）

| 使用情境 | 推薦模型 | 理由 |
|----------|-------------------|-----------|
| **自主開發** | 搭配 Dynamic Workflows 的 Claude Opus 4.8、Claude Sonnet 4.6 | 在 Claude Code 中執行平行 subagent；SWE-Bench Pro 居冠達 69.2% |
| **企業級 RAG** | Gemini 3.1 Pro、Gemini 3.1 Flash、DeepSeek V4 Flash | 1M 文脈與積極的快取折扣消除了檢索的複雜度 |
| **客服支援** | Gemini 3.1 Flash、GPT-5.5-mini、Claude Haiku 4.5 | 近乎零延遲且推理能力強 |
| **推理 / 除錯** | GPT-5.5 reasoning、Claude Opus 4.8（thinking）、DeepSeek-R1 | 在程式碼與邏輯的隱藏式 CoT 表現最佳 |
| **影片 / 多模態** | Gemini 3.1 Pro、GPT-5.5、Claude Opus 4.8 | 原生交錯式（interleaved）多模態處理 |
| **私有代理** | Llama 4 Maverick、DeepSeek V4 Pro（開放權重） | 最強的開放權重 agentic 規劃能力 |

### 依限制條件

| 限制條件 | 做法 |
|------------|----------|
| **最大延遲 < 100ms** | Gemini 3.1 Flash、GPT-5.5-mini、Claude Haiku 4.5，或自架的 Nano 模型 |
| **文脈 > 1M tokens** | Claude Opus 4.8 / Opus 4.7 / Sonnet 4.6、Gemini 3.1 Pro、GPT-5.5、Llama 4 Scout（10M） |
| **零資料外洩** | 在內部 VPC 上運行的 Llama 4 70B、DeepSeek V4 Pro |
| **複雜工具使用** | Claude Opus 4.8 或 GPT-5.5（最佳規劃準確度） |

---

## 成本分析

### 成本建模（2026 年 5 月）

| 模型 | 輸入 / 1M | 輸出 / 1M | 備註 |
|-------|------------|-------------|-------|
| **Claude Opus 4.8** | $5.00 | $25.00 | 前沿編碼與 agentic；選用 fast mode $10 / $50 |
| **Claude Opus 4.7** | $5.00 | $25.00 | 標準價相同；fast mode 較貴，為 $30 / $150 |
| **GPT-5.5** | $5.00 | $30.00 | 單次 SWE-bench 領先者 |
| **Claude Sonnet 4.6** | $3.00 | $15.00 | 均衡選擇；尚未推出 Sonnet 4.8 |
| **Gemini 3.1 Pro** | $2.00 | $12.00 | 最佳性價比前沿；多模態 |
| **DeepSeek V4 Pro** | $0.435 | $0.87 | 5 月 22 日起 75% 折扣永久化 |
| **Gemini 3.1 Flash** | $0.10 | $3.00 | 大規模 RAG；快取折扣 |
| **DeepSeek V4 Flash** | $0.14 | $0.28 | 最便宜的前沿等級 1M 文脈 |

### 成本比較範例

假設每月 1M 次查詢，每次查詢 1K 輸入 token + 500 輸出 token：

| 用量 | GPT-5.5 | Claude Sonnet | Gemini 3 Pro | Gemini 3 Flash |
|--------|---------|---------------|--------------|----------------|
| 每月 10K 次查詢 | $150 | $105 | $37.50 | $1.50 |
| 每月 1M 次查詢 | $15,000 | $10,500 | $3,750 | $150 |

*洞察：DeepSeek V4 Flash（$0.14 / $0.28）與 Gemini 3.1 Flash（$0.10 / $3.00）已實質上將 RAG 商品化，使得大規模的長文脈處理比傳統向量搜尋基礎設施更便宜。*

---

## 營運考量

### 速率限制與配額

| 供應商 | 級別 | RPM | TPM |
|----------|------|-----|-----|
| OpenAI (Tier 1) | Basic | 500 | 30K |
| OpenAI (Tier 5) | Enterprise | 10K | 10M |
| Anthropic (Tier 1) | Basic | 50 | 40K |
| Anthropic (Tier 4) | Enterprise | 4K | 400K |

### 可靠性模式

```python
class ReliableModelClient:
    def __init__(self):
        self.providers = {
            "primary": OpenAIClient(),
            "fallback1": AnthropicClient(),
            "fallback2": GoogleClient()
        }
    
    async def generate(self, prompt: str) -> str:
        for name, client in self.providers.items():
            try:
                return await client.generate(prompt)
            except RateLimitError:
                continue
            except ServiceError:
                continue
        
        raise AllProvidersUnavailable()
```

### 抽象層

```python
class LLMClient:
    """Unified interface for multiple providers."""
    
    def __init__(self, config: dict):
        self.default_model = config["default_model"]
        self.clients = self._init_clients(config)
    
    async def generate(
        self,
        messages: list[dict],
        model: str = None,
        **kwargs
    ) -> str:
        model = model or self.default_model
        client = self._get_client(model)
        
        # Normalize request format
        normalized = self._normalize_request(messages, kwargs)
        
        # Call provider
        response = await client.generate(**normalized)
        
        # Normalize response
        return self._normalize_response(response)
    
    def _normalize_request(self, messages: list[dict], kwargs: dict) -> dict:
        # Handle differences between providers
        # OpenAI uses 'messages', Anthropic uses 'messages' with different format
        pass
```

---

## 多模型策略

### 模型路由

```python
class ModelRouter:
    def __init__(self):
        self.classifier = QueryClassifier()
        self.models = {
            "simple": "gpt-4o-mini",
            "complex": "claude-3.5-sonnet",
            "code": "claude-3.5-sonnet",
            "long_context": "gemini-1.5-pro",
            "reasoning": "o1-mini"
        }
    
    async def route(self, query: str, context_length: int) -> str:
        # Classify query complexity
        query_type = await self.classifier.classify(query)
        
        # Override for long context
        if context_length > 100_000:
            return self.models["long_context"]
        
        return self.models[query_type]
```

### 級聯模式（Cascade Pattern，2025 年精修版）

**核心邏輯**：絕不用 70B 模型去做 1B 模型就能完成的任務。使用「Router」來為信心度評分。

```python
class ModelCascade:
    """The 'Efficiency First' Pattern."""
    
    async def generate_optimized(self, query: str):
        # 1. Draft check (SLM / Classifier)
        if is_simple_intent(query):
            return await gpt4o_mini.generate(query)
            
        # 2. Main Generation (Efficient model)
        response = await claude_sonnet.generate(query)
        
        # 3. Validation / Escalate
        if needs_verification(response):
            return await o3.generate(f"Verify this: {response}")
            
        return response
```

**資深層級提示：** 實作「語意化備援（Semantic Fallback）」，亦即在出錯時不只是對同一個模型重試，而是立即跳轉到更大的模型或不同的供應商（OpenAI -> Anthropic），以避免相關聯（correlated）的故障。

---

## 面試題

### Q：在正式環境應用中，你如何在 GPT-4o、Claude 與 Gemini 之間做選擇？

**優秀回答：**

「我的選擇取決於具體需求：

**對大多數正式環境工作負載**，我預設選用 Claude 3.5 Sonnet 或 GPT-4o。兩者都是出色的通用模型。Sonnet 在編碼上略勝一籌，GPT-4o 則有更好的生態系整合。

**對長文脈應用**，Gemini 1.5 Pro 以 1-2 百萬 token 的文脈成為明顯贏家。如果我需要處理整個程式庫或非常長的文件，Gemini 就是我的選擇。

**對成本敏感的高流量場景**，選 GPT-4o-mini 或 Claude Haiku。它們便宜 10-20 倍，且能妥善處理單純的任務。

**我的實務做法：**
1. 先用 Sonnet 或 GPT-4o 做原型以驗證使用情境
2. 在「我自己」的具體任務上評估，而非僅看 benchmark
3. 建立抽象層，讓我能輕易切換
4. 透過將較簡單的請求路由到更便宜的模型來優化成本

我從不只依賴 benchmark 分數。在 MMLU 上排名較低的模型，可能在我的領域中表現出色。」

### Q：什麼情況下你會選擇自架（self-host）而非使用 API 供應商？

**優秀回答：**

「這是控制權與營運負擔之間的取捨。

**在以下情況使用 API：**
- 用量低於每月 1M 次查詢（成本交叉點）
- 需要立即取得最新模型
- 團隊缺乏 GPU 基礎設施專業
- 工作負載變動大、難以做容量規劃
- 上市時間（time-to-market）至關重要

**在以下情況自架：**
- 資料不能離開自有基礎設施（合規）
- 用量超過每月 10M 次查詢（成本節省）
- 需要 P99 延遲低於 100ms
- 需要自訂模型權重或 fine-tuning
- 對模型行為有完全控制權

**混合（Hybrid）做法通常最佳：**
- 對高流量、可預測的工作負載採自架
- 對流量尖峰與特殊模型採用 API
- 以 API 作為自架失效時的備援

自架的隱藏成本：GPU 採購、工程時間、模型更新、監控。要把 1-2 名專責基礎設施的工程師納入考量。」

---

## 參考資料

- OpenAI API: https://platform.openai.com/
- Anthropic API: https://docs.anthropic.com/
- Google AI: https://ai.google.dev/
- LMSys Leaderboard: https://chat.lmsys.org/

---

*下一篇：[Fine-Tuning 指南](../03-fine-tuning/01-when-to-fine-tune.md)*
