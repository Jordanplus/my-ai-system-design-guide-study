# 能力評估

本章說明如何針對你的特定使用情境評估與比較模型能力。通用 benchmark 很少能道盡全貌；本指南協助你進行有意義的評估。

## 目錄

- [為什麼 benchmark 還不夠](#why-benchmarks-are-not-enough)
- [評估維度](#evaluation-dimensions)
- [打造自訂評估](#building-custom-evaluations)
- [常見的評估陷阱](#common-evaluation-pitfalls)
- [實務評估流程](#practical-assessment-process)
- [內部 Elo 評估法](#internal-elo-based-evaluation)
- [推理校準與效率](#reasoning-calibration)
- [A/B 測試模型](#ab-testing-models)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 為什麼 benchmark 還不夠

### Benchmark 的問題

公開 benchmark（MMLU、HumanEval、GSM8K）有其侷限：

| 問題 | 影響 |
|-------|--------|
| 訓練資料污染 | 模型可能已看過測試題目 |
| 任務不匹配 | Benchmark 可能無法反映你的使用情境 |
| 彙總分數掩蓋變異 | 模型 A 整體可能贏過 B，但在你的領域卻輸了 |
| 刻意作弊 | 模型為 benchmark 而非真實任務做最佳化 |
| 過時 | Benchmark 落後於模型能力 |

### Benchmark 能告訴你什麼

```
Benchmark results tell you: "Model X scored 88% on MMLU"

What you need to know: "Will Model X correctly answer my 
customers' questions about our product documentation?"
```

**經驗法則：** 用 benchmark 做初步篩選，接著進行你自己的評估。

---

## 評估維度

### 維度一：任務表現

| 任務類型 | 評估方法 | 關鍵指標 |
|-----------|---------------------|------------|
| **自主式編碼（Autonomous Coding）** | CWE/SWE-bench（Verified） | 自主解決的 issue 百分比 |
| **長程規劃（Long-Horizon Planning）** | Agentic Loop 測試 | 10+ 步驟計畫的成功率 |
| **推理深度** | Thinking 模式分析 | 跨 CoT 步驟的邏輯一致性 |
| **長 context RAG** | Needle-in-a-Haystack（2M+） | 大規模下的召回效率 |
| **原生多模態（Native Multimodal）** | 交錯的 Vision/Voice/Text | 跨模態的同步準確度 |

### 維度二：Agentic 精熟度

模型使用工具與遵循多步驟指令的能力有多好？

```python
def evaluate_agentic_flow(agent, task_environment):
    """
    Measure success on 'Autonomous Agent' tasks:
    1. Plan generation
    2. Tool selection accuracy
    3. Error recovery
    4. Feedback loop utilization
    """
    results = []
    for scenario in task_environment.scenarios:
        traj = agent.run(scenario.goal)
        results.append({
            "success": traj.reached_goal,
            "steps": len(traj.steps),
            "tool_errors": traj.count_invalid_tool_calls()
        })
    return aggregate(results)
```

### 維度三：推理可靠度

相較於標準生成，「Thinking」模式是否提升了輸出準確度？

| 模式 | 準確度（數學） | 準確度（程式碼） | 平均延遲 | Tokens／輸出 |
|------|-----------------|-----------------|-------------|-----------------|
| **Standard** | 72% | 68% | 1.2s | 400 |
| **Thinking** | 94% | 89% | 12.5s | 2400 |
| **Hybrid** | 視情況而定 | 視情況而定 | 由使用者定義 | 可設定 |

### 推理校準

**「過度思考（Over-Thinking）」問題：**
模型常在一個只需 10 個 token 就能回答的問題上花費 2000+ 個「thinking」token（例如「What is 2+2?」）。

**Principal 等級的細膩之處：**
以 **邏輯效率（Logic Efficiency）** 來評估模型：`Accuracy / (Inference Tokens)`。
生產系統採用 **模型仲裁（Model Arbitration）**：由一個小模型（Gemini 3.1 Flash、Claude Haiku 4.5、GPT-5.5-mini）偵測查詢是否需要「Thinking」模式。如此可避免簡單查詢承受 10 倍的延遲與成本代價。

---

## 內部 Elo 評估法

**超越靜態評分量表（rubric）。**
評分量表（1-5 分制）容易產生「評審疲勞（judge fatigue）」與「分數漂移（score drifting）」。現代系統對內部黃金集（golden set）採用 **成對 Elo（Pairwise Elo）**。

**工作流程：**
1. **盲測並排（Blind Side-by-Side）：** 模型 A 與模型 B 針對同一查詢生成答案。
2. **評審（The Judge）：** 由一個「Ultra」模型（Claude Opus 4.7、GPT-5.5 reasoning，或人類）選出贏家。
3. **Elo 更新：** 更新內部排行榜。

```python
def update_elo(winner_elo, loser_elo, k=32):
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    new_winner_elo = winner_elo + k * (1 - expected_winner)
    new_loser_elo = loser_elo + k * (0 - (1 - expected_winner))
    return new_winner_elo, new_loser_elo
```

**為什麼它勝出：** 它提供一種 **相對** 排名，對評審個性或模型版本變動的耐受度遠高出許多。

### 維度四：Context 召回

在 2M+ context window 下，單純的「needle-in-a-haystack」已不再足夠。我們如今衡量跨整個 window 的 **情境推理（Contextual Reasoning）**。

| 指標 | 衡量方式 | 目標 |
|--------|-------------|--------|
| **Window 召回** | 在 90% window 深度處的事實召回 | > 98% |
| **跨文件推理** | 連結 Doc A（位置 10k）與 Doc B（位置 1M）的邏輯 | > 90% |
| **情境噪音抵抗力** | 當 90% 的 window 是無關「填充」內容時的準確度 | > 95% |

---

## 打造自訂評估

### 步驟一：定義評估準則

```python
evaluation_criteria = {
    "correctness": {
        "weight": 0.4,
        "description": "Is the answer factually correct?",
        "scale": [1, 2, 3, 4, 5],
        "rubric": {
            5: "Completely correct, no errors",
            4: "Mostly correct, minor issues",
            3: "Partially correct, some errors",
            2: "Mostly incorrect",
            1: "Completely wrong or nonsensical"
        }
    },
    "relevance": {
        "weight": 0.3,
        "description": "Does the answer address the question?",
        "scale": [1, 2, 3, 4, 5]
    },
    "completeness": {
        "weight": 0.2,
        "description": "Are all parts of the question addressed?",
        "scale": [1, 2, 3, 4, 5]
    },
    "conciseness": {
        "weight": 0.1,
        "description": "Is the answer appropriately concise?",
        "scale": [1, 2, 3, 4, 5]
    }
}
```

### 步驟二：建立測試集

```python
test_set = [
    {
        "id": "q001",
        "query": "What is the refund policy for subscription cancellation?",
        "context": "[relevant documentation]",
        "ground_truth": "Full refund within 30 days, prorated after",
        "difficulty": "easy",
        "category": "policy"
    },
    {
        "id": "q002",
        "query": "How do I integrate the API with a Python async application?",
        "context": "[API documentation]",
        "ground_truth": "[expected code pattern]",
        "difficulty": "medium",
        "category": "technical"
    },
    # ... 50-100+ test cases
]
```

**測試集準則：**
- 涵蓋所有主要使用情境
- 納入簡單、中等、困難的範例
- 在各類別之間取得平衡
- 納入邊界案例
- 具備明確的 ground truth 答案

### 步驟三：實作評估

```python
class ModelEvaluator:
    def __init__(self, models: list[str], test_set: list[dict]):
        self.models = models
        self.test_set = test_set
        self.results = {}
    
    def evaluate_all(self):
        for model in self.models:
            self.results[model] = self.evaluate_model(model)
        return self.results
    
    def evaluate_model(self, model: str) -> dict:
        scores = []
        latencies = []
        
        for case in self.test_set:
            start = time.time()
            response = self.generate(model, case)
            latency = time.time() - start
            latencies.append(latency)
            
            # Score using LLM judge or human
            score = self.score_response(case, response)
            scores.append(score)
        
        return {
            "mean_score": mean(scores),
            "score_by_category": self.group_by_category(scores),
            "p50_latency": percentile(latencies, 50),
            "p99_latency": percentile(latencies, 99)
        }
    
    def score_response(self, case: dict, response: str) -> float:
        # Option 1: LLM-as-judge
        return self.llm_judge(case, response)
        
        # Option 2: Exact match
        # return exact_match(response, case["ground_truth"])
        
        # Option 3: Semantic similarity
        # return cosine_sim(embed(response), embed(case["ground_truth"]))
```

### 步驟四：LLM-as-Judge

```python
def llm_judge(case: dict, response: str) -> dict:
    prompt = f"""Evaluate this response to a customer query.

Query: {case['query']}
Expected Answer: {case['ground_truth']}
Model Response: {response}

Rate the response on these criteria (1-5 scale):
1. Correctness: Is it factually accurate?
2. Relevance: Does it answer the question?
3. Completeness: Are all aspects covered?
4. Conciseness: Is it appropriately brief?

Output JSON:
{{"correctness": X, "relevance": X, "completeness": X, "conciseness": X, "reasoning": "..."}}
"""
    
    result = judge_model.generate(prompt)
    return parse_json(result)
```

---

## 常見的評估陷阱

### 陷阱一：測試集太小

**問題：** 20 個測試案例不足以進行可靠的比較。

**解法：** 以 100+ 個案例為目標，並依難度與類別分層。

### 陷阱二：模稜兩可的 ground truth

**問題：** 「合理」的答案被標記為錯誤。

```
Query: "What is the capital of Australia?"
Ground truth: "Canberra"
Model answer: "The capital of Australia is Canberra."
Exact match: FAIL (but clearly correct)
```

**解法：** 使用語意比對或 LLM 評審，而非完全相符（exact match）。

### 陷阱三：評估集洩漏

**問題：** 開發與評估使用相同的案例。

**解法：** 保留一個保留測試集（held-out test set），且絕不用於 prompt 調校。

### 陷阱四：忽略變異

**問題：** 每個測試只跑一次會忽略模型的隨機性。

**解法：** 在 temperature > 0 的情況下多次執行，並回報信賴區間。

### 陷阱五：對成本視而不見

**問題：** 最佳模型貴上 10 倍。

**解法：** 一律回報品質調整後成本（quality-adjusted cost）。

```python
def quality_adjusted_cost(model_results):
    return {
        model: {
            "quality": results["mean_score"],
            "cost_per_1k": results["cost_per_1k_queries"],
            "quality_per_dollar": results["mean_score"] / results["cost_per_1k"]
        }
        for model, results in model_results.items()
    }
```

---

## 實務評估流程

### 第 1 週：建置與初步篩選

```
Day 1-2: Define evaluation criteria and create test set
Day 3-4: Benchmark 4-6 candidate models
Day 5: Analyze results, filter to top 2-3
```

### 第 2 週：深度評估

```
Day 1-2: Expand test set for top candidates
Day 3: Test edge cases and robustness
Day 4: Measure latency and throughput
Day 5: Calculate total cost of ownership
```

### 第 3 週：生產驗證

```
Day 1-2: Shadow mode deployment
Day 3-4: A/B test if traffic allows
Day 5: Final decision and documentation
```

### 決策範本

```markdown
## Model Evaluation Report

### Candidates Evaluated
- Model A: GPT-4o
- Model B: Claude 3.5 Sonnet
- Model C: Llama 3.1 70B

### Evaluation Results

| Metric | Model A | Model B | Model C |
|--------|---------|---------|---------|
| Overall Score | 4.2/5 | 4.3/5 | 3.9/5 |
| Category 1 | ... | ... | ... |
| P50 Latency | 450ms | 520ms | 180ms |
| Cost/1K queries | $0.85 | $1.10 | $0.25 |

### Recommendation
Model B (Claude 3.5 Sonnet) for quality-critical paths
Model C (Llama 3.1 70B) for high-volume, cost-sensitive paths

### Rationale
[Detailed reasoning]
```

---

## A/B 測試模型

### 何時該做 A/B 測試

- 高流量（1000+ 查詢／天）
- 明確的成功指標
- 可接受的品質變異風險
- 需要生產驗證

### A/B 測試設計

```python
class ModelABTest:
    def __init__(self, model_a: str, model_b: str, traffic_split: float = 0.5):
        self.model_a = model_a
        self.model_b = model_b
        self.traffic_split = traffic_split
        self.results = {"a": [], "b": []}
    
    def route_request(self, request_id: str) -> str:
        # Deterministic routing for consistency
        hash_val = hash(request_id) % 100
        if hash_val < self.traffic_split * 100:
            return self.model_a
        return self.model_b
    
    def record_outcome(self, request_id: str, metrics: dict):
        model = self.route_request(request_id)
        bucket = "a" if model == self.model_a else "b"
        self.results[bucket].append(metrics)
    
    def analyze(self):
        return {
            "model_a": {
                "name": self.model_a,
                "mean_score": mean([r["score"] for r in self.results["a"]]),
                "sample_size": len(self.results["a"])
            },
            "model_b": {
                "name": self.model_b,
                "mean_score": mean([r["score"] for r in self.results["b"]]),
                "sample_size": len(self.results["b"])
            },
            "p_value": self.calculate_significance()
        }
```

### 應追蹤的指標

| 指標類型 | 範例 |
|-------------|----------|
| 品質 | 使用者評分、專家審查、LLM 評審 |
| 互動 | 點擊率、停留時間、後續查詢 |
| 商業 | 轉換率、客服升級、解決率 |
| 維運 | 延遲、錯誤、成本 |

---

## 面試題

### Q：你會如何為客服聊天機器人評估模型？

**強答案：**
我會將評估分層進行：

**1. 離線評估（80% 的心力）：**
- 從真實客服工單建立測試集（200+ 案例）
- 涵蓋所有類別：帳務、技術、退貨、一般
- 納入簡單、中等、困難的難度
- 衡量：準確度、有用性、安全性

**2. 評估方法：**
- 對主觀指標使用 LLM-as-judge
- 抽樣（20%）由人類審查
- 追蹤指令遵循（格式、長度）

**3. 指標：**
```python
metrics = {
    "resolution_accuracy": "Does answer solve the problem?",
    "safety": "No harmful/wrong advice?", 
    "tone": "Professional and empathetic?",
    "escalation_appropriate": "Knows when to involve human?"
}
```

**4. 生產驗證：**
- Shadow mode：執行新模型並比較輸出
- A/B 測試：將 10% 流量導向新模型
- 監控：CSAT、升級率、解決時間

### Q：用 MMLU 來為你的使用情境比較模型有什麼問題？

**強答案：**
MMLU 對特定使用情境有幾個問題：

**1. 領域不匹配：** MMLU 測的是學術知識。我的客服機器人需要的是產品知識。

**2. 格式不匹配：** MMLU 是選擇題。我的使用情境是自由生成。

**3. 污染：** 模型可能曾在 MMLU 題目上訓練過。

**4. 彙總掩蓋變異：** 模型 A 在 MMLU 上可能贏過 B，但在我在意的特定類別上卻輸了。

**5. 沒有 context 測試：** MMLU 不測試 RAG 或長 context 能力。

**更好的做法：**
- 用 MMLU 做初步篩選（省時間）
- 為最終決策打造自訂評估
- 在實際使用情境資料上測試
- 納入維運指標（延遲、成本）

---

## 參考資料

- Zheng et al. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (2023)
- LMSYS Chatbot Arena: https://chat.lmsys.org/
- HELM: https://crfm.stanford.edu/helm/
- LMSys Evaluation: https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge
- OpenAI Evals: https://github.com/openai/evals

---

*上一篇： [Model Taxonomy](01-model-taxonomy.md) | 下一篇： [Pricing and Costs](03-pricing-and-costs.md)*
