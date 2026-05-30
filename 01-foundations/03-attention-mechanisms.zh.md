# 注意力機制（Attention Mechanisms）

注意力是讓 transformer 得以成立的核心創新。本章涵蓋對系統設計與面試而言不可或缺的數學基礎、各種變體與優化技術。

## 目錄

- [注意力基礎](#attention-fundamentals)
- [縮放點積注意力](#scaled-dot-product-attention)
- [多頭注意力](#multi-head-attention)
- [注意力模式](#attention-patterns)
- [高效注意力變體](#efficient-attention-variants)
- [Flash Attention（v2 與 v3）](#flash-attention)
- [多頭潛在注意力（MLA）](#multi-head-latent-attention-mla)
- [KV cache 優化與 Context Caching](#kv-cache-optimizations)
- [實務影響](#practical-implications)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 注意力基礎

### 核心概念

注意力讓序列中的每個位置都能從所有其他位置蒐集資訊。不同於遞迴（一步一步傳遞資訊），注意力建立的是直接連結。

**給分散式系統工程師的心智模型：**
- RNN：沿著鏈條的訊息傳遞（message passing）
- 注意力：pub/sub，每個節點都能查詢其他任一節點

### Query、Key、Value 框架

注意力會使用輸入的三種投影：

| 元件 | 角色 | 類比 |
|-----------|------|---------|
| Query (Q) | 我在尋找什麼？ | 搜尋查詢 |
| Key (K) | 我包含什麼？ | 文件索引 |
| Value (V) | 我貢獻什麼？ | 文件內容 |

```python
# Input: x of shape [batch, seq_len, d_model]

Q = x @ W_q  # [batch, seq_len, d_k]
K = x @ W_k  # [batch, seq_len, d_k]
V = x @ W_v  # [batch, seq_len, d_v]
```

---

## 縮放點積注意力

最基本的注意力運算：

```python
def scaled_dot_product_attention(Q, K, V, mask=None):
    d_k = Q.shape[-1]
    
    # Compute attention scores
    scores = Q @ K.transpose(-2, -1)  # [batch, seq_len, seq_len]
    scores = scores / math.sqrt(d_k)  # Scale
    
    # Apply mask (for causal attention)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))
    
    # Convert to probabilities
    attention_weights = F.softmax(scores, dim=-1)
    
    # Weighted sum of values
    output = attention_weights @ V
    
    return output, attention_weights
```

### 為什麼要除以 d_k 的平方根來縮放？

**面試常考**：這題考驗的是對數值的直覺。

若不縮放，點積會隨維度增長：
- 對於維度為 d 的隨機單位向量 q 與 k
- E[q . k] = 0，但 Var[q . k] = d
- 標準差 = sqrt(d)

當 d 很大時（512 或更大），點積可能會非常大或非常小。在大數值上做 softmax 會趨近 one-hot，導致梯度消失。

```python
# Demonstration
import numpy as np

d = 512
q = np.random.randn(d)
k = np.random.randn(d)

unscaled = np.dot(q, k)      # Magnitude ~ sqrt(512) ~ 22
scaled = unscaled / np.sqrt(d)  # Magnitude ~ 1
```

### 因果遮罩（Causal Masking）

對於自迴歸生成，每個位置只能注意到先前的位置：

```python
def create_causal_mask(seq_len):
    # Lower triangular matrix
    mask = torch.tril(torch.ones(seq_len, seq_len))
    return mask

# Example for seq_len=4:
# [[1, 0, 0, 0],
#  [1, 1, 0, 0],
#  [1, 1, 1, 0],
#  [1, 1, 1, 1]]
```

mask=0 的位置會得到負無限大的分數，在 softmax 之後變為 0。

---

## 多頭注意力

不採用單一注意力函數，而是使用多個「頭（head）」來關注不同面向：

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
    
    def forward(self, x, mask=None):
        batch_size, seq_len, d_model = x.shape
        
        # Project to Q, K, V
        Q = self.W_q(x)  # [batch, seq_len, d_model]
        K = self.W_k(x)
        V = self.W_v(x)
        
        # Reshape to multiple heads
        Q = Q.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        # Now: [batch, num_heads, seq_len, d_k]
        
        # Attention per head
        attn_output, _ = scaled_dot_product_attention(Q, K, V, mask)
        
        # Concatenate heads
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, d_model)
        
        # Final projection
        output = self.W_o(attn_output)
        return output
```

**為什麼要用多個頭？**
1. 不同的頭學習不同的模式（語法、語意、共指）
2. 提供表徵上的多樣性（ensemble 效果）
3. 讓多個頭之間能夠平行運算

### 頭數的常見配置

| 模型 | d_model | 頭數 | 每個頭的 d_k |
|-------|---------|-------|--------------|
| BERT-base | 768 | 12 | 64 |
| GPT-2 | 768 | 12 | 64 |
| GPT-3 175B | 12288 | 96 | 128 |
| Llama 2 70B | 8192 | 64 | 128 |

64 或 128 的 d_k 在各種模型規模間出奇地一致。

---

## 注意力模式

### 注意力學到了什麼

不同的頭會專精於不同的模式：

| 模式類型 | 它捕捉了什麼 | 範例 |
|--------------|------------------|---------|
| 位置型 | 相鄰 token | 下一個／上一個字 |
| 語法型 | 文法關係 | 主詞—動詞 |
| 語意型 | 意義關係 | 共指（coreference） |
| 分隔型 | 標點、結構 | 段落邊界 |
| 罕見型 | 不常見的模式 | 罕見字的複製 |

### 視覺化注意力

注意力權重可以用熱圖（heatmap）視覺化，呈現哪些位置注意到哪些位置：

```
Query positions (rows) vs Key positions (columns)

"The cat sat on the mat"

         The  cat  sat  on   the  mat
The     [□    ○    ○    ○    ○    ○ ]
cat     [●    □    ○    ○    ○    ○ ]
sat     [○    ●    □    ○    ○    ○ ]
on      [○    ○    ●    □    ○    ○ ]
the     [○    ○    ○    ○    □    ○ ]
mat     [○    ●    ○    ●    ●    □ ]

● = high attention, ○ = low attention
```

「mat」強烈地注意到「cat」（語意）、「on」（語法）以及「the」（限定詞）。

---

## 高效注意力變體

標準注意力對序列長度而言是 O(n^2)。許多變體可降低這個複雜度：

### 稀疏注意力（Sparse Attention）

只注意到位置的一個子集，而非全部：

| 變體 | 模式 | 複雜度 | 範例 |
|---------|---------|------------|---------|
| Local | 每個位置周圍的視窗 | O(n * w) | Longformer |
| Strided | 每隔 k 個位置 | O(n^2 / k) | Sparse Transformer |
| Global | 特殊 token 注意到所有位置 | O(n * g) | Longformer、BigBird |
| Block | 區塊對角注意力 | O(n * b) | BigBird |

**Longformer 模式：**
```
Local window + Global tokens

[G] [L] [L] [L] [L] [G] [L] [L] [L] [L]

G: Global tokens (attend to/from all)
L: Local tokens (attend within window)
```

### 線性注意力（Linear Attention）

以可線性化的方案取代 softmax：

```python
# Standard attention (quadratic)
attention = softmax(Q @ K.T) @ V

# Linear attention approximation
attention = (Q @ (K.T @ V))  # Associativity trick
```

**變體：**
- Performer：隨機特徵近似
- Linear Transformer：elu(Q) @ (elu(K).T @ V)

**取捨：** 速度更快，但品質會下降，尤其是在需要精確注意力的任務上。

### 複雜度比較

| 方法 | 時間 | 空間 | 品質 | 備註 |
|--------|------|-------|---------|-------|
| Standard | O(n^2) | O(n^2) | 最佳 | 基準 |
| Sparse (Longformer) | O(n) | O(n) | 接近最佳 | 適用於長文件 |
| Linear (Performer) | O(n) | O(n) | 下降 | 最適合極長序列 |
| Flash Attention | O(n^2) | O(n) | 最佳 | 兼具兩者之長 |

---

## Flash Attention

Flash Attention 是目前最先進的實作，能在計算精確注意力的同時達到 O(n) 記憶體用量。

### 它解決的問題

標準注意力需要實際具現出 n x n 的注意力矩陣：
- 對於 8K context：64M 個浮點數 = 每層每頭 256 MB
- 對於 100K context：10B 個浮點數 = 每層每頭 40 GB

這項記憶體需求會限制批次大小（batch size）與 context 長度。

### 運作原理

Flash Attention 透過分塊（tiling）與重算（recomputation）來避免儲存完整的注意力矩陣：

```
Standard: Q, K -> Attention Matrix (n x n) -> Output
Flash:    Q, K -> Tiles (block_size x block_size) -> Incremental Output
```

**關鍵想法：**
1. 以能放進 SRAM 的區塊為單位來處理注意力
2. 絕不在 HBM 中實際具現完整的注意力矩陣
3. 在反向傳播時重算注意力（比從 HBM 載入更快）

### 效能影響

### FlashAttention-2（工作分割，Work Partitioning）
針對 A100/H100 進行優化，改善了跨頭與跨序列長度的平行度。

### FlashAttention-3（FP8 與 H100 優化）
**目前 H100/B200 叢集的標準作法：**
- **非同步執行（Asynchronous Execution）**：在 H100 上利用 TMA（Tensor Memory Accelerator）讓 GEMM（矩陣乘法）與 softmax 運算重疊執行。
- **FP8 支援**：原生支援 FP8 精度，相較 FP16 可將吞吐量翻倍，同時透過隨機捨入（stochastic rounding）維持注意力的準確度。
- **加速**：在長 context 的 prefill 階段，較 FlashAttention-2 快約 1.5x-2.0x。

---

## 多頭潛在注意力（MLA）

由 DeepSeek（V2/V3）提出，**在 KV cache 壓力極大時，MLA 是 GQA 的現代替代方案**。

MLA 不只是分組各個頭，而是在將 Key 與 Value 向量存入 cache 之前，先把它們壓縮到一個**低維潛在空間（low-dimensional latent space）**。

```
Query (Up-projected) ────────┐
                             ▼
Key, Value (Down-projected) ─▶ [Low-dim Latent Cache] ─▶ [Output]
                             ▲
                             └─ Projection Matrices
```

| 指標 | MHA | GQA | MLA（2025 年 12 月） |
|--------|-----|-----|----------------|
| KV Cache 大小 | 100% | 12.5% | **~5%** |
| 品質 | 基準 | 接近基準 | **優於 GQA** |
| 延遲 | 基準 | 較快 | **最快（減少 I/O）** |

**MLA 為何勝出**：它採用「解耦旋轉位置編碼（Decoupled Rotary Positional Embeddings）」，讓壓縮後的潛在 KV 無需解碼即可重複使用，在長 context 生成期間節省了大量記憶體頻寬。

---

## KV cache 優化與 Context Caching

### Context Caching（系統層級）
API 供應商（OpenAI、Gemini、Anthropic）如今都提供 **Context Caching**。
- **運作方式**：預先計算並儲存某個長「前綴（prefix）」的 KV 張量（例如一本 100k token 的法律書）。
- **效益**：對於重複的前綴，可將 TTFT（首個 token 的時間）降低 90%、成本降低 50-90%。

### 滑動視窗注意力（Sliding Window Attention，SWA）
用於 Mistral/Gemma 模型，將注意力深度限制在一個固定視窗內（例如 4096 個 token），避免 KV cache 無限增長。

### 多查詢注意力（Multi-Query Attention，MQA）

讓所有 query 頭共用單一的 K 與 V：

```python
# Standard MHA
Q: [batch, num_heads, seq, d_k]  # 32 heads
K: [batch, num_heads, seq, d_k]  # 32 separate K
V: [batch, num_heads, seq, d_k]  # 32 separate V

# MQA
Q: [batch, num_heads, seq, d_k]  # 32 heads
K: [batch, 1, seq, d_k]          # 1 shared K
V: [batch, 1, seq, d_k]          # 1 shared V
```

**效果：** KV cache 大小縮減 32 倍，伴隨一些品質損失。

### 分組查詢注意力（Grouped-Query Attention，GQA）

讓 K 與 V 在數組 query 頭之間共用：

```python
# GQA with 8 KV heads for 64 query heads (8:1 ratio)
Q: [batch, 64, seq, d_k]  # 64 query heads
K: [batch, 8, seq, d_k]   # 8 KV heads
V: [batch, 8, seq, d_k]   # 8 KV heads

# Each KV head serves 8 query heads
```

**效果：** KV cache 縮減 8 倍，品質損失極小。

**採用 GQA 的模型：**
- Llama 2 70B：64 個 query 頭配 8 個 KV 頭
- Mistral 7B：32 個 query 頭配 8 個 KV 頭
- Gemma：多種配置

### 比較

| 注意力 | KV Cache | 品質 | 模型 |
|-----------|----------|---------|--------|
| MHA | 完整 | 最佳 | GPT-3 |
| GQA | 通常 1/8 | 接近最佳 | Llama 2、Mistral |
| MQA | 1/n_heads | 下降 | PaLM、Falcon |

---

## 實務影響

### 對系統設計而言

1. **批次大小與 context 的取捨：**
   - 總 GPU 記憶體 = 模型 + KV cache * batch_size
   - context 越長，批次就越小
   - GQA 模型能服務更多並行請求

2. **延遲預算分配：**
   - 注意力的計算是 O(n^2)，採用 Flash 後為 O(n)
   - Prefill（處理 prompt）隨 prompt 長度增長
   - Decode（生成）隨已生成長度加上 prompt 長度而增長

3. **記憶體頻寬瓶頸：**
   - 生成階段往往受記憶體限制（memory-bound）
   - 為每個 token 載入 KV cache 是主要開銷
   - 較大的批次能攤平這項成本

### Prefill 與 Decode

| 階段 | 計算模式 | 瓶頸 |
|-------|-----------------|------------|
| Prefill | 處理所有輸入 token | 計算（GPU 核心） |
| Decode | 一次生成一個 token | 記憶體（頻寬） |

這就是為什麼 TTFT（首個 token 的時間）與 TPS（每秒 token 數）要分開衡量。

### Context 長度的擴展

| Context | 注意力計算量 | KV Cache（Llama 70B） |
|---------|-------------------|---------------------|
| 4K | 基準 | 10.7 GB |
| 8K | 4x | 21.5 GB |
| 32K | 64x | 86 GB |
| 128K | 1024x | 344 GB |

長 context 需要：
- Flash Attention（節省記憶體）
- GQA 或 MQA（較小的 KV cache）
- 可能還需要模型平行（model parallelism）

---

## 面試題

### 問：解釋注意力機制，以及它為何呈二次方擴展。

**好的回答：**
注意力會計算所有位置之間的兩兩交互。對於 n 個位置：

1. Q @ K^T 產生一個 n x n 的分數矩陣
2. 每個注意力分數都是一個 query 與一個 key 的點積
3. 總計：n^2 次點積

這對序列長度而言是二次方的。對於 8K token，等於每層每頭有 6,400 萬個兩兩分數。對於 128K token，則是 160 億個。

二次方的擴展限制了 context 長度。解決方案包括：
- Flash Attention：計算為 O(n^2) 但記憶體為 O(n)
- 稀疏注意力：透過只注意子集達到 O(n)
- 線性注意力：O(n) 的近似

### 問：什麼是 KV cache，為什麼它對服務（serving）至關重要？

**好的回答：**
在自迴歸生成期間，我們一次產生一個 token。若沒有快取，每產生一個新 token 都需要為所有先前位置重新計算 K 與 V。

KV cache 會儲存先前位置的 K 與 V 張量。每產生一個新 token 時：
1. 只為新位置計算 Q、K、V
2. 將新的 K、V 附加到 cache
3. 對完整的已快取 K、V 做注意力

這讓投影計算的每 token 複雜度從 O(n) 降到 O(1)。

代價是記憶體：KV cache 隨序列長度線性增長。以 Llama 70B 在 8K context 為例，每個請求約需 21 GB。這會直接限制批次大小與吞吐量。

GQA 與 MQA 透過讓 K、V 在 query 頭之間共用來降低這項開銷。

### 問：比較 MHA、GQA 與 MQA。

**好的回答：**
| 變體 | K、V 頭數 | KV Cache | 品質 | 適用情境 |
|---------|-----------|----------|---------|----------|
| MHA | 等同 Q 頭數 | 完整 | 最佳 | 訓練、品質關鍵 |
| GQA | 少於 Q 頭數 | 減少 | 接近 MHA | 正式環境服務 |
| MQA | 1 | 最少 | 下降 | 記憶體受限 |

MHA：每個 query 頭都有自己的 K 與 V。品質最佳，但 KV cache 最大。

GQA：數組 query 頭共用 K 與 V。Llama 2 使用 64 個 query 頭配 8 個 KV 頭（8:1 比例）。cache 小 8 倍，品質損失極小。

MQA：所有 query 頭共用一組 K 與 V。記憶體節省最大，但品質會有可量測的下降。PaLM 採用此法。

對於服務而言，GQA 是最佳取捨。它能支援更大的批次（更高吞吐量），品質又與 MHA 幾乎相同。

### 問：Flash Attention 如何達到 O(n) 記憶體？

**好的回答：**
標準注意力會在 GPU 記憶體中實際具現出完整的 n x n 注意力矩陣。Flash Attention 透過以下方式避免這點：

1. **分塊（Tiling）：** 以能放進晶片內 SRAM 的 Q、K 區塊為單位處理
2. **線上 softmax（Online softmax）：** 以增量方式計算 softmax，而不儲存所有分數
3. **重算（Recomputation）：** 在反向傳播時重算注意力，而非載入已存的數值

關鍵洞見是：GPU SRAM（每個 SM 20 MB）比 HBM（80 GB）快 10 倍。透過在 SRAM 中做更多算術、減少 HBM 的讀寫，Flash Attention 既更快又更省記憶體。

結果是精確的注意力（並非近似），達到 O(n) 記憶體並有 2-4x 加速。

---

## 參考資料

- Vaswani et al. "Attention Is All You Need" (2017)
- Dao et al. "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness" (2022)
- Dao "FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning" (2023)
- Beltagy et al. "Longformer: The Long-Document Transformer" (2020)
- Ainslie et al. "GQA: Training Generalized Multi-Query Transformer Models" (2023)
- Shazeer "Fast Transformer Decoding: One Write-Head is All You Need" (MQA, 2019)
- [Flash Attention 程式庫](https://github.com/Dao-AILab/flash-attention)

---

*上一篇：[Tokenization 深入剖析](02-tokenization-deep-dive.md) | 下一篇：[Transformer 架構](04-transformer-architecture.md)*
