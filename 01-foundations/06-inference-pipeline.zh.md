# 推論管線（Inference Pipeline）

本章介紹 LLM 在推論階段如何生成文字、過程中涉及的運算階段，以及生產環境服務的關鍵指標。

## 目錄

- [生成基礎](#generation-basics)
- [Prefill 與 Decode 階段](#prefill-and-decode-phases)
- [取樣策略](#sampling-strategies)
- [停止條件](#stopping-conditions)
- [延遲優化：Speculative Decoding](#speculative-decoding)
- [延遲指標與 TTFT vs. TPS](#latency-metrics)
- [記憶體與運算需求](#memory-and-compute-requirements)
- [Continuous Batching 與 Prefix Caching](#continuous-batching-and-prefix-caching)
- [Multi-LoRA Serving](#multi-lora-serving)
- [串流（Streaming）](#streaming)
- [生產環境考量](#production-considerations)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 生成基礎

LLM 以自迴歸（autoregressive）方式生成文字：一次產生一個 token，並以先前所有的 token 作為 context。

```
Input: "The quick brown"
Step 1: Generate "fox" -> "The quick brown fox"
Step 2: Generate "jumps" -> "The quick brown fox jumps"
Step 3: Generate "over" -> "The quick brown fox jumps over"
...
```

### 生成迴圈

```python
def generate(prompt: str, max_tokens: int, model) -> str:
    tokens = tokenize(prompt)
    
    for _ in range(max_tokens):
        # Forward pass: get logits for next token
        logits = model.forward(tokens)
        
        # Sample next token from probability distribution
        next_token = sample(logits[-1])
        
        # Check for stop condition
        if next_token == EOS_TOKEN:
            break
        
        tokens.append(next_token)
    
    return detokenize(tokens)
```

---

## Prefill 與 Decode 階段

推論有兩個特性各異的階段：

### Prefill 階段

平行處理整段輸入 prompt。

```
Input: "The quick brown fox" (4 tokens)

Prefill:
- Process all 4 tokens simultaneously
- Compute attention across all pairs
- Populate KV cache for all positions
- Output: logits for next token
```

**特性：**
- 運算密集（compute-bound，大量矩陣運算）
- 可在 token 之間平行化
- 時間隨 prompt 長度而增加
- 每次生成只發生一次

### Decode 階段

一次生成一個 token。

```
Decode step 1:
- Input: new token position only
- Attend to all KV cache (prompt + previously generated)
- Generate one token

Decode step 2:
- Append new K, V to cache
- Input: newest token position
- Generate next token

...repeat until done
```

**特性：**
- 記憶體密集（memory-bound，需從 HBM 載入 KV cache）
- 序列化（必須完成每一步才能開始下一步）
- 每個 token 的時間大致固定
- 重複進行直到滿足停止條件

### 為何重要

| 階段 | 瓶頸 | 優化方式 |
|-------|------------|--------------|
| Prefill | 運算（GPU cores） | Flash Attention、更好的 GPU |
| Decode | 記憶體頻寬 | GQA、batching、quantization |

**對服務的影響：**
- 長 prompt 會增加 prefill 時間（影響 TTFT）
- 長生成會增加 decode 時間（影響整體延遲）
- Batching 對 decode 效率的幫助大於 prefill

---

## 取樣策略

計算出 logits 後，我們需要選出下一個 token。不同策略會產生不同的輸出。

### Greedy Decoding

永遠挑選機率最高的 token：

```python
def greedy_sample(logits):
    return torch.argmax(logits)
```

**特性：**
- 具決定性（deterministic）
- 長生成時經常重複
- 適合事實性／結構化輸出

### Temperature Sampling

在 softmax 之前縮放 logits 以控制隨機性：

```python
def temperature_sample(logits, temperature=1.0):
    scaled_logits = logits / temperature
    probs = torch.softmax(scaled_logits, dim=-1)
    return torch.multinomial(probs, num_samples=1)
```

**Temperature 的影響：**

| Temperature | 行為 | 使用情境 |
|-------------|----------|----------|
| 0 | Greedy（決定性） | 事實性問答、程式碼 |
| 0.3-0.7 | 低隨機性 | 一般任務 |
| 1.0 | 基準 | 創意寫作 |
| 1.5+ | 高隨機性 | 腦力激盪 |

### Top-K Sampling

只考慮機率最高的 K 個 token：

```python
def top_k_sample(logits, k=50):
    values, indices = torch.topk(logits, k)
    probs = torch.softmax(values, dim=-1)
    sampled_idx = torch.multinomial(probs, num_samples=1)
    return indices[sampled_idx]
```

**效果：** 過濾掉可能不合理的低機率 token。

### Top-P（Nucleus）Sampling

納入 token 直到累積機率超過 P：

```python
def top_p_sample(logits, p=0.9):
    sorted_probs, sorted_indices = torch.sort(
        torch.softmax(logits, dim=-1), descending=True
    )
    cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
    
    # Find cutoff
    cutoff_idx = torch.searchsorted(cumulative_probs, p)
    
    # Sample from truncated distribution
    selected_probs = sorted_probs[:cutoff_idx + 1]
    selected_probs = selected_probs / selected_probs.sum()
    sampled_idx = torch.multinomial(selected_probs, num_samples=1)
    
    return sorted_indices[sampled_idx]
```

**相較 Top-K 的優勢：** 會依機率分布動態調整。高信心的預測納入較少的 token；不確定的預測則納入較多。

### 常見組態

| 使用情境 | Temperature | Top-P | Top-K |
|----------|-------------|-------|-------|
| 程式碼生成 | 0-0.2 | 0.95 | - |
| 事實性問答 | 0.1-0.3 | 1.0 | - |
| 一般對話 | 0.7 | 0.9 | - |
| 創意寫作 | 1.0 | 0.95 | - |
| 腦力激盪 | 1.2 | 1.0 | - |

### Repetition Penalty（重複懲罰）

降低近期已生成 token 的機率：

```python
def apply_repetition_penalty(logits, generated_tokens, penalty=1.2):
    for token_id in set(generated_tokens):
        logits[token_id] /= penalty
    return logits
```

**變體：**
- Presence penalty：懲罰所有出現過的 token
- Frequency penalty：依出現次數成比例懲罰

---

## 停止條件

生成會持續進行，直到滿足某個停止條件：

### EOS Token

模型生成序列結尾（end-of-sequence）token：

```python
if next_token == tokenizer.eos_token_id:
    break
```

### Max Tokens

生成長度的硬性上限：

```python
for i in range(max_tokens):
    # generate...
```

### Stop Sequences

用來終止生成的自訂字串：

```python
stop_sequences = ["###", "\n\n", "Human:"]

for seq in stop_sequences:
    if output.endswith(seq):
        output = output[:-len(seq)]
        break
```

## 延遲優化：Speculative Decoding

**目前高頻寬服務的標準做法。**

Speculative decoding 使用一個較小的「draft model」在單一步驟中預測多個未來 token，接著由較大的「target model」平行驗證這些 token。

```
Draft Model (Small): Predicts 5 tokens -> "The", "quick", "brown", "fox", "jumps"
Target Model (Large): Verifies all 5 tokens in ONE forward pass.
Result: If target agrees on 4 tokens, we've generated 4 tokens for the cost of 1 large forward pass.
```

| 方法 | 做法 | 加速比 | 範例 |
|--------|----------|---------|---------|
| Draft Model | 小模型（如 1B）+ 大模型（70B） | 2x-3x | vLLM、TGI |
| **Medusa Heads** | 在同一模型上加多個 LM head | 1.5x-2x | Medusa、Eagle |
| Prompt Lookup | 以 prompt 中的子字串作為推測 | 1.2x | RAG／程式碼補全 |

---

## 延遲指標

### Time to First Token（TTFT）

從發出請求到產生第一個 token 的時間。

```
TTFT = network_latency + queue_time + prefill_time
```

**影響 TTFT 的因素：**
- Prompt 長度（prefill 為 O(n)）
- 模型大小
- GPU 速度
- 佇列深度

**目標值：**
- 互動式對話：< 500ms
- 即時：< 200ms
- 批次：較不關鍵

### Tokens Per Second（TPS）

第一個 token 之後的 token 生成速率。

```
TPS = (total_tokens - 1) / (total_time - TTFT)
```

**影響 TPS 的因素：**
- 模型大小
- Batch size
- GPU 記憶體頻寬
- KV cache 大小

**典型數值：**
- Llama 70B 在 H100 上：每個請求 30-50 tokens/sec
- 透過 API 使用 GPT-4：20-80 tokens/sec（會變動）
- 小模型（7B）：100+ tokens/sec

### 整體延遲

```
Total = TTFT + (output_tokens / TPS)
```

**範例：**
- TTFT：200ms
- TPS：50 tokens/sec
- 輸出：100 tokens
- 總計：200ms + 2000ms = 2.2s

### 吞吐量（Throughput）

單位時間內完成的請求數：

```
Throughput = concurrent_requests * TPS / average_output_tokens
```

更大的 batch size 會提高吞吐量，但可能增加單一請求的延遲。

---

## 記憶體與運算需求

### 模型權重

```
Memory = parameters * bytes_per_parameter

70B model in FP16:
= 70B * 2 bytes
= 140 GB

70B model in INT4:
= 70B * 0.5 bytes
= 35 GB
```

### KV Cache

```
Per token: 2 * layers * heads * head_dim * bytes
Per request: per_token * sequence_length

Llama 70B (80 layers, 64 heads, 128 dim, FP16):
= 2 * 80 * 64 * 128 * 2 bytes
= 2.6 MB per token

At 4K context: 10.5 GB per request
At 8K context: 21 GB per request
```

### GPU 記憶體總量

```
Total = model_weights + kv_cache * batch_size + activations

Example: Llama 70B serving
- Weights (INT4): 35 GB
- KV cache (8K, batch 4): 84 GB
- Activations: ~5 GB
- Total: ~124 GB (fits on 2x H100 80GB)
```

### 每個 Token 的 FLOPs

```
Forward pass FLOPs ≈ 2 * parameters

70B model:
≈ 140 TFLOPs per token

At 40 tokens/sec:
≈ 5.6 PFLOPs sustained
```

---

## 串流（Streaming）

對於互動式應用，應在 token 生成的同時即時串流：

### Server-Side Events（SSE）

```python
# Server
async def generate_stream(prompt: str):
    for token in model.generate_iter(prompt):
        yield f"data: {json.dumps({'token': token})}\n\n"
    yield "data: [DONE]\n\n"

# Client
async for event in sse_client.stream("/generate"):
    token = json.loads(event.data)["token"]
    display(token)
```

### 優點

| 面向 | 串流 | 非串流 |
|--------|-----------|---------------|
| 感知延遲 | 僅 TTFT | 完整生成時間 |
| 使用者體驗 | 漸進式 | 先等待，再一次完成 |
| 提前終止 | 使用者可中止 | 必須等待 |
| 記憶體 | 較低 | 較高（緩衝回應） |

### 實作細節

- 每個 token 後 flush
- 妥善處理連線中斷
- 對非常快速的生成可考慮緩衝
- 部分框架預設會緩衝；串流時請關閉

---

## 生產環境考量

### 為吞吐量做 Batching

合併多個請求以最大化 GPU 使用率：

```python
# Without batching: GPU underutilized
for request in requests:
    response = model.generate(request)

# With batching: parallel processing
batch = collect_requests(timeout=10ms, max_batch=32)
responses = model.generate_batch(batch)
```

### Continuous Batching 與 Prefix Caching

**Continuous Batching（迭代層級排程）：**
不同於靜態 batching，continuous batching 會在 batch 中任一請求觸發 EOS token 時立即注入新請求。這可將吞吐量提升至多 20 倍。

**Prefix Caching（RAD-O）：**
快取常見前綴（如 system prompt、few-shot 範例）的 KV tensors。
- **TTFT 降低幅度**：90%
- **機制**：以前綴的 hash 在 GPU 記憶體的 LRU cache 中查找 KV tensors。

### Multi-LoRA Serving

**情境：** 在同一個 base model 上服務 1000 個不同的 fine-tuned 模型（adapters）。
**挑戰：** 載入 1000 個獨立模型會耗用數 TB 的 VRAM。

**解法（LoRAX／S-LoRA）：**
1. 在 VRAM 中載入一個 base model。
2. 將 LoRA adapters（數 MB）存放在主機 RAM 或 SSD 中。
3. 在 forward pass 期間，依請求 ID 動態切換 adapters。
4. **實作**：使用專門的 kernel（S-LoRA），在同一個 batch 中為多個不同 adapters 執行 matrix-vector 乘法。

### 請求優先排序

```python
class RequestQueue:
    def __init__(self):
        self.high_priority = asyncio.Queue()
        self.low_priority = asyncio.Queue()
    
    async def get_next(self):
        if not self.high_priority.empty():
            return await self.high_priority.get()
        return await self.low_priority.get()
```

**優先排序的判斷標準：**
- 客戶層級
- 請求類型
- 等待時間
- 預估運算成本

### Timeout 處理

```python
async def generate_with_timeout(prompt: str, timeout: float):
    try:
        result = await asyncio.wait_for(
            model.generate(prompt),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        return {"error": "timeout", "partial": partial_output}
```

### Graceful Degradation（優雅降級）

```python
async def generate_with_fallback(prompt: str):
    try:
        return await primary_model.generate(prompt)
    except RateLimitError:
        return await fallback_model.generate(prompt)
    except TimeoutError:
        return await small_fast_model.generate(prompt)
```

### 成本追蹤

```python
@dataclass
class RequestMetrics:
    input_tokens: int
    output_tokens: int
    model: str
    latency_ms: float
    cost_usd: float

def calculate_cost(metrics: RequestMetrics) -> float:
    pricing = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }
    rates = pricing[metrics.model]
    return (
        (metrics.input_tokens / 1_000_000) * rates["input"] +
        (metrics.output_tokens / 1_000_000) * rates["output"]
    )
```

---

## 面試問題

### Q：請說明 prefill 與 decode 階段的差異。

**理想回答：**
LLM 推論有兩個特性各異的階段：

**Prefill：**
- 一次處理整段輸入 prompt
- 所有 token 平行地彼此進行 attention
- 為所有 prompt 位置填入 KV cache
- 運算密集：能有效利用 GPU cores
- 時間隨 prompt 長度而增加

**Decode：**
- 一次生成一個 token
- 新 token 對所有 KV cache 條目進行 attention
- 將新的 K、V 附加到 cache
- 記憶體密集：瓶頸在於載入 KV cache
- 每個 token 的時間大致固定

這對系統設計之所以重要，是因為：
- 長 prompt 會增加 TTFT（prefill 密集）
- Batching 對 decode 的幫助大於 prefill
- 兩個階段適用不同的優化策略

### Q：temperature 與 top-p 如何影響生成？

**理想回答：**
兩者都用來控制 token 選取的隨機性：

**Temperature：**
- 在 softmax 之前縮放 logits
- 低（0-0.3）：較具決定性，偏好高機率 token
- 高（1.0+）：較隨機，使機率分布趨於平坦
- 零：等同 greedy decoding

**Top-p（nucleus sampling）：**
- 篩選出累積機率 > p 的最小 token 集合
- 依分布動態調整截斷點
- 高信心：納入較少 token
- 低信心：納入較多 token

典型的生產環境設定：
- 事實性問答：temperature 0.1、top-p 0.95
- 一般對話：temperature 0.7、top-p 0.9
- 創意：temperature 1.0+、top-p 0.95

關鍵洞見在於兩者協同運作：temperature 重塑分布，top-p 則截斷分布。

### Q：是什麼決定了 TTFT 與 TPS？

**理想回答：**
**TTFT（Time to First Token）：**
- 抵達伺服器的網路延遲
- 佇列等待時間
- Prefill 運算時間
- 主要由：prompt 長度、GPU 運算速度決定

**TPS（Tokens Per Second）：**
- Decode 階段效率
- 載入 KV cache 的記憶體頻寬
- 主要由：記憶體頻寬、batch size、模型大小決定

優化策略各不相同：
- TTFT：盡量縮短 prompt、使用更快的網路、降低佇列時間
- TPS：增加 batch size、採用 GQA/MQA 模型、優化記憶體存取

權衡取捨：batching 能改善 TPS（吞吐量），但若請求需等待 batch 組成，可能增加 TTFT（延遲）。

### Q：你會如何估算服務某個模型所需的 GPU 資源？

**理想回答：**
有三大記憶體消耗來源：

1. **模型權重：**
   - FP16：parameters * 2 bytes
   - INT8：parameters * 1 byte
   - INT4：parameters * 0.5 bytes

2. **KV cache：**
   - 每個 token：2 * layers * kv_heads * head_dim * 2 bytes（FP16）
   - 每個請求：per_token * sequence_length
   - 總計：per_request * batch_size

3. **Activations：** 通常為 5-10% 的額外開銷

以 Llama 70B 服務為例：
- 權重（INT4）：35 GB
- KV cache（8K context，batch 8）：168 GB
- 需求：總計約 200 GB

硬體選項：
- 3x A100 80GB 搭配 tensor parallelism
- 2x H100 80GB 搭配 tensor parallelism
- 8x A100 40GB 搭配更多平行化

接著透過 benchmarking 驗證吞吐量是否滿足需求。

---

## 參考資料

- Holtzman et al. "The Curious Case of Neural Text Degeneration"（nucleus sampling, 2020）
- Kwon et al. "Efficient Memory Management for Large Language Model Serving with PagedAttention"（vLLM, 2023）
- [vLLM Documentation](https://docs.vllm.ai/)
- [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)

---

*上一篇：[Embeddings 與向量空間](05-embeddings-and-vector-spaces.md) | 下一篇：[模型分類法](../02-model-landscape/01-model-taxonomy.md)*
