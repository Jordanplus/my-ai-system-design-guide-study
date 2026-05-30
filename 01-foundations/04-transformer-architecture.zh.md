# Transformer 架構

本章提供完整 transformer 架構的全面視角，將前幾章介紹的各個元件整合成一套統一的理解。

## 目錄

- [架構總覽](#architecture-overview)
- [輸入處理](#input-processing)
- [Transformer 區塊](#the-transformer-block)
- [輸出處理](#output-processing)
- [現代架構變體（Hybrid MoE、MLA）](#mixture-of-experts-moe--hybrid-architectures)
- [Untied 與 Tied Embeddings](#untied-vs-tied-embeddings)
- [擴展特性](#scaling-properties)
- [架構比較表](#architecture-comparison-table)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 架構總覽

一個 decoder-only transformer（GPT、Claude、Llama 採用的架構）由以下部分組成：

```
┌─────────────────────────────────────────────────────────────────┐
│                     Token Embeddings                            │
│              + Position Embeddings (or RoPE)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│    ┌─────────────────────────────────────────────────────┐      │
│    │                  Transformer Block                   │      │
│    │  ┌─────────────────────────────────────────────┐    │      │
│    │  │              RMSNorm/LayerNorm              │    │      │
│    │  └───────────────────┬─────────────────────────┘    │      │
│    │                      ▼                              │      │
│    │  ┌─────────────────────────────────────────────┐    │      │
│    │  │         Masked Multi-Head Attention         │    │      │
│    │  │            (with KV Cache)                  │    │      │
│    │  └───────────────────┬─────────────────────────┘    │      │
│    │                      │                              │      │
│    │                  + Residual                         │      │
│    │                      │                              │      │
│    │  ┌─────────────────────────────────────────────┐    │      │
│    │  │              RMSNorm/LayerNorm              │    │      │
│    │  └───────────────────┬─────────────────────────┘    │      │
│    │                      ▼                              │      │
│    │  ┌─────────────────────────────────────────────┐    │      │
│    │  │             Feed-Forward Network            │    │      │
│    │  │               (SwiGLU/GELU)                 │    │      │
│    │  └───────────────────┬─────────────────────────┘    │      │
│    │                      │                              │      │
│    │                  + Residual                         │      │
│    └──────────────────────┴──────────────────────────────┘      │
│                           │                                     │
│                    Repeat × N layers                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Output RMSNorm                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Language Model Head                           │
│              (Linear: hidden_dim → vocab_size)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                         Logits
```

---

## 輸入處理

### Token Embedding

將 token ID 轉換為密集向量：

```python
class TokenEmbedding(nn.Module):
    def __init__(self, vocab_size, d_model):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
    
    def forward(self, token_ids):
        return self.embedding(token_ids)
```

**維度：**
- 輸入：[batch_size, seq_len] token ID
- 輸出：[batch_size, seq_len, d_model] embeddings

### 位置資訊

位置資訊透過下列其中一種方式納入：

**1. Rotary Position Embedding（RoPE）：**
在 attention 內部套用，而非加到 embeddings 上：
```python
def apply_rope(q, k, positions):
    # Rotate q and k vectors based on position
    freqs = compute_frequencies(positions)
    q_rotated = rotate_embeddings(q, freqs)
    k_rotated = rotate_embeddings(k, freqs)
    return q_rotated, k_rotated
```

**2. Learned Position Embeddings：**
直接加到 token embeddings 上：
```python
position_embeddings = nn.Embedding(max_seq_len, d_model)
x = token_embeddings + position_embeddings(positions)
```

**現代模型（Llama、Mistral、GPT-4）採用 RoPE**，以獲得更好的長度泛化能力。

---

## Transformer 區塊

### Pre-Norm 結構

現代 transformer 採用 pre-normalization：

```python
class TransformerBlock(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.attn_norm = RMSNorm(config.d_model)
        self.attn = GroupedQueryAttention(
            d_model=config.d_model,
            n_heads=config.n_heads,
            n_kv_heads=config.n_kv_heads
        )
        self.ff_norm = RMSNorm(config.d_model)
        self.ff = SwiGLUFFN(
            d_model=config.d_model,
            d_ff=config.d_ff
        )
    
    def forward(self, x, mask=None, kv_cache=None):
        # Attention with residual
        h = x + self.attn(self.attn_norm(x), mask, kv_cache)
        
        # FFN with residual
        out = h + self.ff(self.ff_norm(h))
        
        return out
```

### Attention 元件

```python
class GroupedQueryAttention(nn.Module):
    def __init__(self, d_model, n_heads, n_kv_heads):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = d_model // n_heads
        
        self.q_proj = nn.Linear(d_model, n_heads * self.head_dim)
        self.k_proj = nn.Linear(d_model, n_kv_heads * self.head_dim)
        self.v_proj = nn.Linear(d_model, n_kv_heads * self.head_dim)
        self.o_proj = nn.Linear(n_heads * self.head_dim, d_model)
    
    def forward(self, x, mask, kv_cache):
        B, T, D = x.shape
        
        # Project
        q = self.q_proj(x).view(B, T, self.n_heads, self.head_dim)
        k = self.k_proj(x).view(B, T, self.n_kv_heads, self.head_dim)
        v = self.v_proj(x).view(B, T, self.n_kv_heads, self.head_dim)
        
        # Apply RoPE
        q, k = apply_rope(q, k, positions)
        
        # Update KV cache
        if kv_cache is not None:
            k = torch.cat([kv_cache.k, k], dim=1)
            v = torch.cat([kv_cache.v, v], dim=1)
            kv_cache.update(k, v)
        
        # Repeat KV heads for GQA
        k = k.repeat_interleave(self.n_heads // self.n_kv_heads, dim=2)
        v = v.repeat_interleave(self.n_heads // self.n_kv_heads, dim=2)
        
        # Attention (using Flash Attention in practice)
        attn_out = flash_attention(q, k, v, mask)
        
        # Output projection
        out = self.o_proj(attn_out.view(B, T, -1))
        return out
```

### Feed-Forward Network

```python
class SwiGLUFFN(nn.Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        # SwiGLU has 3 projections instead of 2
        self.gate_proj = nn.Linear(d_model, d_ff, bias=False)
        self.up_proj = nn.Linear(d_model, d_ff, bias=False)
        self.down_proj = nn.Linear(d_ff, d_model, bias=False)
    
    def forward(self, x):
        gate = F.silu(self.gate_proj(x))  # SiLU = Swish
        up = self.up_proj(x)
        return self.down_proj(gate * up)
```

**FFN 隱藏維度** 在 SwiGLU 中通常是模型維度的 2.7 倍（相較於使用 GELU 的標準 FFN 為 4 倍）。

### RMSNorm

```python
class RMSNorm(nn.Module):
    def __init__(self, d_model, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d_model))
        self.eps = eps
    
    def forward(self, x):
        rms = torch.sqrt(torch.mean(x ** 2, dim=-1, keepdim=True) + self.eps)
        return self.weight * (x / rms)
```

由於省略了均值置中（mean centering），因此比 LayerNorm 更簡單也更快。

---

## 輸出處理

### 最終正規化

在最後一個 transformer 區塊之後套用 RMSNorm：

```python
hidden_states = self.output_norm(hidden_states)
```

### Language Model Head

投影到詞彙表大小：

```python
class LMHead(nn.Module):
    def __init__(self, d_model, vocab_size):
        super().__init__()
        self.linear = nn.Linear(d_model, vocab_size, bias=False)
    
    def forward(self, x):
        return self.linear(x)  # Returns logits
```

## Untied 與 Tied Embeddings

**標準模式（GPT-3、Llama 2）：** Weight Tying（權重綁定）
- 輸出 head 與輸入 embeddings 共用權重。
- **優點**：節省記憶體（vocab_size * hidden_dim）。
- **缺點**：強制輸入與輸出的 latent 空間完全相同，這可能並非最佳選擇。

**2025 前沿模式（Llama 3/4、GPT-5.2）：** Untied Embeddings（未綁定 embeddings）
- 輸出 head 擁有自己獨立的權重。
- **為什麼？**：更大的詞彙表（128k+）使得 embedding 表佔了模型相當大的比例。解除綁定讓輸出 head 能專注於「預測邏輯」，而輸入 embeddings 則專注於「語意理解」。
- **系統影響**：增加了參數量，但對於多語言與程式碼任務往往能改善 perplexity。

### 取得預測結果

```python
# During generation
logits = lm_head(hidden_states[:, -1, :])  # Last position only
next_token = sample(logits)

# During training
logits = lm_head(hidden_states)  # All positions
loss = cross_entropy(logits, targets)
```

---

## 現代架構變體

### Llama 2/3 架構

| 元件 | 實作方式 |
|-----------|----------------|
| Attention | Grouped Query Attention (GQA) |
| 位置 | Rotary Position Embedding (RoPE) |
| 正規化 | RMSNorm (pre-norm) |
| 激活函數 | SwiGLU |
| Bias | 線性層中不使用 bias |

### Mistral 架構

與 Llama 相同，但額外加入：
- **Sliding Window Attention：** 每一層只關注 4K 個 token
- 仍透過堆疊達成有效的 32K+ context

### Mixture of Experts (MoE) 與混合架構

最先進的模型通常採用 **Hybrid MoE/Dense** 區塊：
- **週期性 Dense 層**：每隔幾個 MoE 層便加入一個 dense 層，以確保「全域」知識能在所有 expert 之間共享。
- **Expert Parallelism**：將不同的 expert 分散到不同的 GPU 上。這使得 **節點間頻寬（inter-node bandwidth）**（NVLink/InfiniBand）成為架構上的主要瓶頸。

### Multi-head Latent Attention (MLA) 整合
[DeepSeek-V3 / V4](file:///Users/om/play/ai-system-design-guide/01-foundations/03-attention-mechanisms.md#multi-head-latent-attention-mla) 與同等現代架構中的標準 attention 區塊，將標準的 Q/K/V 投影替換為低秩 latent 壓縮。
- **架構轉變**：「KV Cache」如今變成一個壓縮後的 latent 表示，改變了整個 transformer 區塊的記憶體／運算比例。

### 選擇的比較

| 選擇 | 舊作法 | 現代作法 | 效益 |
|--------|--------------|-----------------|---------|
| Norm | Post-LN | Pre-LN / RMSNorm | 訓練穩定性、速度 |
| 位置 | Sinusoidal/Learned | RoPE | 更好的外推能力 |
| 激活函數 | GELU | SwiGLU | 品質（在 benchmark 上提升 +1%）|
| Attention | MHA | GQA | KV cache 縮小 8 倍 |
| Bias | 使用 bias | 不使用 bias | 參數更少，品質相近 |

---

## 擴展特性

### 參數量

| 元件 | 參數量 |
|-----------|------------|
| Token embedding | vocab_size * d_model |
| 每層 Q/K/V | 3 * d_model * d_model（針對 MHA）|
| 每層 O proj | d_model * d_model |
| 每層 FFN | 3 * d_model * d_ff（針對 SwiGLU）|
| LM head | d_model * vocab_size（通常為 tied）|

**Decoder-only 的近似估算：**
```
Total ≈ 12 * n_layers * d_model^2 (for d_ff = 4 * d_model, MHA)
```

### 運算需求

**訓練：** 每個 token 的 FLOPs ≈ 6 * parameters（前向 + 反向）

**推論：** 每個 token 的 FLOPs ≈ 2 * parameters（僅前向）

### 擴展定律（Scaling Laws）

Chinchilla scaling law 建議的最佳配置為：

```
D (data tokens) ≈ 20 * N (parameters)
```

對於一個 70B 模型，要達成 compute-optimal 訓練應使用約 1.4T 個 token 進行訓練。

**但是：** 許多現代模型相對於 Chinchilla 都進行了過度訓練（overtrain），以換取更佳的推論效率。Llama 便是以 2T+ 個 token 訓練而成。

---

## 架構比較表

| 模型 | 參數量 | 層數 | d_model | Heads | KV Heads | FFN | Context |
|-------|--------|--------|---------|-------|----------|-----|---------|
| GPT-3 | 175B | 96 | 12288 | 96 | 96 | GELU | 2K |
| Llama 2 70B | 70B | 80 | 8192 | 64 | 8 | SwiGLU | 4K |
| Llama 3 405B| 405B | 126 | 16384 | 128 | 16 | SwiGLU | 128K |
| DeepSeek V3 | 671B | 128 | 7168 | 128 | MLA | MoE | 128K |
| Llama 4 (spec)| 1T+ | 140+ | 18432 | 192 | 24 | MoE/H | 1M+ |

*Mistral 採用 sliding window attention 來達成有效的長 context。

---

## 面試問題

### Q：請帶我走過一遍 transformer 的 forward pass。

**優秀答案：**
以一個生成文字的 decoder-only 模型為例：

1. **Tokenization：** 將輸入文字轉換為 token ID

2. **Embedding：** 從 embedding 表中查找 token embeddings

3. **對每一個 transformer 層：**
   - 對輸入套用 RMSNorm
   - 計算 Q、K、V 投影
   - 對 Q 與 K 套用 RoPE 以納入位置資訊
   - 生成時：將新的 K、V 附加到 KV cache 中
   - 計算 attention（masked，因此每個位置只能看到先前的位置）
   - 投影 attention 輸出並加上 residual
   - 套用 RMSNorm
   - 通過 SwiGLU feed-forward network
   - 加上 residual

4. **輸出 norm：** 套用最終的 RMSNorm

5. **LM head：** 投影到詞彙表大小以取得 logits

6. **取樣：** 使用 temperature/top-p 從 logits 中選出下一個 token

在生成時，對每一個新的 token 重複步驟 3-6，並重複利用先前位置的 KV cache。

### Q：pre-norm 與 post-norm 的差異是什麼？

**優秀答案：**
差異在於 layer normalization 相對於子層（attention、FFN）所套用的位置：

**Post-norm（原始 transformer）：**
```
x = LayerNorm(x + Sublayer(x))
```
在加上 residual 之後才正規化。

**Pre-norm（現代 transformer）：**
```
x = x + Sublayer(LayerNorm(x))
```
在子層之前先正規化。

偏好 pre-norm 的原因：
1. 梯度能更直接地流經 residual 連接
2. 訓練更穩定，對深層模型尤其如此
3. 對初始化與學習率較不敏感
4. 不需要學習率 warmup

代價是在某些 benchmark 上最終效能略低，但對於大型模型而言，這份訓練穩定性是值得的。

### Q：請解釋 GQA，以及它對 serving 為何重要。

**優秀答案：**
Grouped Query Attention（GQA）讓 Key 與 Value head 在多組 Query head 之間共用。

標準 Multi-Head Attention：64 個 query head、64 個 KV head（1:1）
GQA：64 個 query head、8 個 KV head（8:1）

實作方式：每個 KV head 透過重複（repetition）供 8 個 query head 使用。

**為什麼重要：**
KV cache 在生成過程中會儲存所有位置的 K 與 V。以 Llama 70B 在 8K context 下為例：
- MHA：2.6 MB/token * 8K = 每個請求 21 GB
- GQA (8:1)：每個請求約 2.6 GB

縮小 8 倍可帶來：
- 更大的 batch size（更多並行使用者）
- 更長的 context
- 更低的 GPU 記憶體需求

品質影響：極小。研究顯示 GQA 可達成 MHA 品質的 99%+。

### Q：從 GPT-2 到 Llama 2 之間有哪些改變？

**優秀答案：**
主要的架構改進：

| 元件 | GPT-2 | Llama 2 |
|-----------|-------|---------|
| Norm | Post-LayerNorm | Pre-RMSNorm |
| 位置 | Learned absolute | RoPE (rotary) |
| 激活函數 | GELU | SwiGLU |
| Attention | MHA | GQA（針對 70B）|
| Bias | 有 | 移除 |

影響：
- RMSNorm：更快且同樣有效
- RoPE：更好的長度外推能力
- SwiGLU：約 1% 的品質提升
- GQA：serving 時 KV cache 縮小 8 倍
- 不使用 bias：參數更少，且無品質損失

這些改變使得能更穩定地訓練更大的模型，並更有效率地進行 serving。

---

## 參考資料

- Vaswani et al. "Attention Is All You Need" (2017)
- Touvron et al. "Llama: Open and Efficient Foundation Language Models" (2023)
- Touvron et al. "Llama 2: Open Foundation and Fine-Tuned Chat Models" (2023)
- Zhang and Sennrich. "Root Mean Square Layer Normalization" (2019)
- Shazeer. "GLU Variants Improve Transformer" (2020)
- Su et al. "RoFormer: Enhanced Transformer with Rotary Position Embedding" (2021)
- Jiang et al. "Mistral 7B" (2023)

---

*上一篇：[Attention 機制](03-attention-mechanisms.md) | 下一篇：[Embeddings 與向量空間](05-embeddings-and-vector-spaces.md)*
