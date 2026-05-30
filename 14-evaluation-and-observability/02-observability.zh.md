# LLM 可觀測性

LLM 系統的可觀測性需要針對 AI 應用的獨特特性，調整 logs、metrics、traces 這三大支柱。

## 目錄

- [為什麼 LLM 可觀測性與眾不同](#why-llm-observability-is-different)
- [三大支柱](#the-three-pillars)
- [關鍵指標](#key-metrics)
- [追蹤 LLM Pipeline](#tracing-llm-pipelines)
- [品質監控](#quality-monitoring)
- [成本追蹤](#cost-tracking)
- [告警策略](#alerting-strategy)
- [可觀測性工具](#observability-tools)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 為什麼 LLM 可觀測性與眾不同

傳統可觀測性聚焦於：
- 請求/回應模式
- 延遲與吞吐量
- 錯誤率
- 資源使用率

LLM 系統額外加入了：
- **品質是第一級指標**：一個快速、高可用卻產出糟糕輸出的系統，就是失敗的
- **非決定性**：相同輸入可能產生不同輸出
- **Token 經濟學**：成本會以複雜的方式隨使用量擴增
- **多元件 pipeline**：RAG 有檢索、重排序、生成等步驟
- **主觀正確性**：往往沒有 ground truth 可供比對

---

## 三大支柱

### Logging（記錄）

```python
class LLMLogger:
    def log_request(
        self,
        request_id: str,
        model: str,
        messages: list[dict],
        parameters: dict
    ):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "type": "llm_request",
            "model": model,
            "parameters": parameters,
            "input_tokens": self.count_tokens(messages),
            # Hash for privacy, full content in secure store
            "content_hash": self.hash_content(messages)
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_response(
        self,
        request_id: str,
        response: str,
        latency_ms: float,
        tokens: dict
    ):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "type": "llm_response",
            "latency_ms": latency_ms,
            "input_tokens": tokens["input"],
            "output_tokens": tokens["output"],
            "ttft_ms": tokens.get("ttft_ms"),
            "content_hash": self.hash_content(response)
        }
        self.logger.info(json.dumps(log_entry))
```

**該記錄什麼：**
- 用於關聯的 Request ID
- 模型與參數
- Token 數量
- 延遲（TTFT 與總計）
- 內容（若涉及隱私則經過 hash）

### Metrics（指標）

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM requests",
    ["model", "status"]
)

llm_latency_seconds = Histogram(
    "llm_latency_seconds",
    "LLM request latency",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

llm_ttft_seconds = Histogram(
    "llm_ttft_seconds",
    "Time to first token",
    ["model"],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
)

# Token metrics
tokens_used_total = Counter(
    "tokens_used_total",
    "Total tokens consumed",
    ["model", "direction"]  # direction: input/output
)

# Cost metrics
llm_cost_dollars = Counter(
    "llm_cost_dollars",
    "LLM cost in dollars",
    ["model"]
)

# Quality metrics (sampled)
quality_score = Gauge(
    "llm_quality_score",
    "Sampled quality score",
    ["model", "task_type"]
)
```

### Traces（追蹤）

針對 RAG pipeline 的端對端追蹤：

```python
from opentelemetry import trace

tracer = trace.get_tracer("rag_pipeline")

async def rag_query(query: str) -> str:
    with tracer.start_as_current_span("rag_query") as span:
        span.set_attribute("query", query)
        
        # Embedding step
        with tracer.start_as_current_span("embed_query") as embed_span:
            query_embedding = await embed(query)
            embed_span.set_attribute("embedding_dim", len(query_embedding))
        
        # Retrieval step
        with tracer.start_as_current_span("vector_search") as search_span:
            results = await vector_db.search(query_embedding, top_k=10)
            search_span.set_attribute("results_count", len(results))
            search_span.set_attribute("top_score", results[0].score if results else 0)
        
        # Reranking step
        with tracer.start_as_current_span("rerank") as rerank_span:
            reranked = await reranker.rerank(query, results)
            rerank_span.set_attribute("reranked_count", len(reranked))
        
        # Generation step
        with tracer.start_as_current_span("generate") as gen_span:
            response = await llm.generate(query, context=reranked[:5])
            gen_span.set_attribute("model", llm.model)
            gen_span.set_attribute("output_tokens", count_tokens(response))
        
        return response
```

---

## 關鍵指標

### 維運指標

| 指標 | 說明 | 典型告警門檻 |
|--------|-------------|------------------------|
| 請求速率 | 每秒請求數 | 異常偵測 |
| 錯誤率 | 失敗請求數 / 總數 | > 5% |
| 延遲 p50 | 回應時間中位數 | > 2s |
| 延遲 p95 | 第 95 百分位 | > 5s |
| 延遲 p99 | 第 99 百分位 | > 10s |
| TTFT | Time to first token | > 1s |
| Token 吞吐量 | 每秒 token 數 | < baseline |

### 品質指標

| 指標 | 說明 | 蒐集方式 |
|--------|-------------|-------------------|
| 品質分數 | LLM-as-judge 評分 | 抽樣（1-5%） |
| Faithfulness | RAG 答案是否紮根於 context | 抽樣 |
| Relevance | 答案是否切合問題 | 抽樣 |
| 使用者滿意度 | 讚/倒讚、評分 | 使用者回饋 |
| 任務完成度 | 使用者是否達成目標？ | 隱含訊號 |

### 成本指標

| 指標 | 說明 | 粒度 |
|--------|-------------|-------------|
| 每次請求成本 | 平均成本 | 依模型 |
| 每日成本 | 每日總花費 | 整體 + 依模型 |
| 每次使用者行為成本 | 完成使用者目標的成本 | 依任務類型 |
| Token 效率 | 每個 token 帶來的價值 | 依使用情境 |

---

## 品質監控

### 抽樣策略

```python
class QualitySampler:
    def __init__(self, sample_rate: float = 0.05):
        self.sample_rate = sample_rate
        self.judge = LLMJudge()
    
    async def maybe_evaluate(
        self,
        request_id: str,
        query: str,
        context: list[str],
        response: str
    ):
        # Sample randomly
        if random.random() > self.sample_rate:
            return
        
        # Evaluate quality
        scores = await self.judge.evaluate(
            query=query,
            context=context,
            response=response,
            criteria=["relevance", "faithfulness", "helpfulness"]
        )
        
        # Record metrics
        for criterion, score in scores.items():
            quality_score.labels(
                model=self.model,
                criterion=criterion
            ).set(score)
        
        # Store for analysis
        await self.store_evaluation(request_id, scores)
```

### 漂移偵測

```python
class QualityDriftDetector:
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.baseline_scores = []
        self.current_scores = []
    
    def add_score(self, score: float):
        self.current_scores.append(score)
        
        if len(self.current_scores) >= self.window_size:
            self.check_drift()
            self.current_scores = []
    
    def check_drift(self):
        if not self.baseline_scores:
            self.baseline_scores = self.current_scores.copy()
            return
        
        # Statistical test for drift
        baseline_mean = np.mean(self.baseline_scores)
        current_mean = np.mean(self.current_scores)
        
        # Simple threshold-based detection
        drift_threshold = 0.1  # 10% degradation
        if (baseline_mean - current_mean) / baseline_mean > drift_threshold:
            self.alert_drift(baseline_mean, current_mean)
    
    def alert_drift(self, baseline: float, current: float):
        alert = {
            "type": "quality_drift",
            "baseline_score": baseline,
            "current_score": current,
            "degradation_pct": (baseline - current) / baseline * 100
        }
        self.send_alert(alert)
```

---

## 成本追蹤

### 即時成本計算

```python
class CostTracker:
    # Pricing per 1M tokens (verify current rates)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3.5-haiku": {"input": 0.25, "output": 1.25},
    }
    
    def track(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        request_id: str
    ) -> float:
        pricing = self.PRICING.get(model, {"input": 0, "output": 0})
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Record metrics
        llm_cost_dollars.labels(model=model).inc(total_cost)
        tokens_used_total.labels(model=model, direction="input").inc(input_tokens)
        tokens_used_total.labels(model=model, direction="output").inc(output_tokens)
        
        # Log for analysis
        self.log_cost(request_id, model, input_tokens, output_tokens, total_cost)
        
        return total_cost
```

### 成本歸因

```python
class CostAttributor:
    def attribute_cost(
        self,
        request_id: str,
        user_id: str,
        team: str,
        use_case: str,
        cost: float
    ):
        # Store for billing and analysis
        attribution = {
            "request_id": request_id,
            "user_id": user_id,
            "team": team,
            "use_case": use_case,
            "cost": cost,
            "timestamp": datetime.utcnow()
        }
        
        self.store(attribution)
        
        # Update running totals
        self.update_user_total(user_id, cost)
        self.update_team_total(team, cost)
        
        # Check budgets
        if self.exceeds_budget(team):
            self.alert_budget_exceeded(team)
```

---

## 告警策略

### 告警設定

```yaml
alerts:
  # Availability
  - name: high_error_rate
    condition: error_rate > 0.05
    for: 5m
    severity: critical
    runbook: "Check provider status, verify API keys, review recent changes"
    
  # Latency
  - name: high_latency_p95
    condition: latency_p95 > 10s
    for: 5m
    severity: warning
    runbook: "Check model, reduce context size, verify provider status"
    
  # Cost
  - name: cost_spike
    condition: hourly_cost > 2 * rolling_avg_hourly_cost
    for: 1h
    severity: warning
    runbook: "Check for traffic spike, review recent deployments, verify caching"
    
  # Quality
  - name: quality_degradation
    condition: avg_quality_score < 3.5 over 1h
    for: 30m
    severity: warning
    runbook: "Review recent changes, check model performance, sample responses"
    
  # Resource
  - name: rate_limit_approaching
    condition: rate_limit_usage > 0.8
    for: 15m
    severity: warning
    runbook: "Consider model routing, implement backpressure"
```

### 告警分級

| 嚴重程度 | 回應時間 | 範例 |
|----------|---------------|----------|
| Critical | < 15 min | 服務中斷、錯誤率 > 50% |
| High | < 1 hour | 錯誤率 > 10%、P99 > 30s |
| Warning | < 4 hours | 品質劣化、成本暴增 |
| Info | 下一個工作天 | 趨勢變化、容量規劃 |

---

## 可觀測性工具

### LLM 專用工具

| 工具 | 焦點 | 最適用於 |
|------|-------|----------|
| LangSmith | LangChain 追蹤 | 以 LangChain 為基礎的應用 |
| Langfuse | 開源追蹤 | 自架、隱私需求 |
| Weights & Biases | 實驗追蹤 | ML 團隊 |
| Arize Phoenix | LLM 監控 | 生產環境監控 |
| Helicone | API proxy 記錄 | 簡易整合 |

### 整合範例：Langfuse

```python
from langfuse import Langfuse

langfuse = Langfuse()

async def traced_rag_query(query: str) -> str:
    # Start trace
    trace = langfuse.trace(name="rag_query", input=query)
    
    # Embedding span
    embed_span = trace.span(name="embed")
    embedding = await embed(query)
    embed_span.end()
    
    # Retrieval span
    retrieve_span = trace.span(name="retrieve")
    results = await vector_db.search(embedding)
    retrieve_span.end(output={"count": len(results)})
    
    # Generation span
    gen_span = trace.generation(
        name="generate",
        model="gpt-4o",
        input={"query": query, "context": results}
    )
    response = await llm.generate(query, context=results)
    gen_span.end(output=response)
    
    # End trace
    trace.update(output=response)
    
    return response
```

---

## 面試問題

### Q：你會為生產環境的 LLM 系統追蹤哪些指標？

**有力的回答：**

「我將指標分為三大類：

**維運指標：** 這些是任何服務的基本門檻。
- 請求速率與錯誤率
- 延遲百分位：p50、p95、p99
- 串流的 time to first token（TTFT）
- 可用性

**品質指標：** 這正是 LLM 可觀測性獨特之處。
- 使用 LLM-as-judge 的抽樣品質分數（1-5% 抽樣率）
- 對 RAG：faithfulness 與 relevance 分數
- 使用者回饋：讚/倒讚、明確評分
- 在可衡量處的任務完成率

**成本指標：**
- 依模型的每次請求成本
- 每日/每週成本趨勢
- 每次成功使用者行為的成本
- Token 效率

我會為維運問題（錯誤率 > 5%、P95 > SLA）與品質漂移（平均分數較 baseline 下降 10%）設定告警。針對暴增的成本告警有助於及早抓出失控的使用量。

關鍵洞察在於：一個快速、高可用卻產出糟糕輸出的 LLM 系統，仍然是失敗的。品質必須是第一級指標。」

### Q：你如何偵測生產環境中的品質劣化？

**有力的回答：**

「我會採用多種做法：

**持續抽樣：** 我使用 LLM-as-judge 評估 1-5% 的請求。這讓我在不評估全部的情況下取得品質訊號。

**漂移偵測：** 我維護一份 baseline 品質分布，並用統計檢定來偵測目前分數何時出現顯著漂移。劣化 10% 就會觸發警告。

**使用者回饋：** 讚/倒讚、若有的話包含明確評分。這是使用者滿意度的 ground truth。

**隱含訊號：** 任務完成、重試率、升級率、工作階段時長。若使用者更加掙扎，品質可能已經下滑。

**當我偵測到劣化時該怎麼做：**
1. 檢查近期的部署或 prompt 變更
2. 抽樣特定回應以診斷問題
3. 確認問題是模型特定（供應商問題）還是普遍存在
4. 必要時回滾，然後再調查

我也維護一份黃金測試集（golden test set），涵蓋帶有預期行為的查詢，並在每次部署時執行，以在進入生產環境前抓出迴歸。」

---

## 參考資料

- OpenTelemetry: https://opentelemetry.io/
- Langfuse: https://langfuse.com/docs
- LangSmith: https://docs.smith.langchain.com/

---

*下一篇：[LLM 應用的 CI/CD](../11-infrastructure-and-mlops/02-cicd.md)*
