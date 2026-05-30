# Tokenization 深入解析

Tokenization 是將文字轉換為模型可處理的離散單元（token）的過程。它直接影響模型的能力、成本與效能。

## 目錄

- [為什麼 Tokenization 很重要](#why-tokenization-matters)
- [Tokenization 演算法](#tokenization-algorithms)
- [詞彙表設計取捨](#vocabulary-design-tradeoffs)
- [特殊 Token](#special-tokens)
- [多語言 Tokenization](#multilingual-tokenization)
- [用於成本估算的 Token 計數](#token-counting-for-cost-estimation)
- [常見的 Tokenization 問題](#common-tokenization-issues)
- [實務 Tokenization 模式](#practical-tokenization-patterns)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 為什麼 Tokenization 很重要

### 對系統設計而言

1. **成本**：LLM API 是按 token 計費的。Tokenization 的效率直接影響成本。
2. **Context 限制**：決定什麼能放進 context 的是 token 數量，而非字數。
3. **能力**：某些任務（字元計數、易位構詞）之所以困難，是因為 tokenization 的緣故。
4. **一致性**：同一段文字在不同模型上會以不同方式被 tokenize。

### 對理解 LLM 行為而言

**經典面試題**：為什麼 GPT 很難數出 "strawberry" 中的字母數量？

因為 "strawberry" 會被 tokenize 成多個 subword。模型從來沒有看到個別的字元；它看到的是 subword 單元。要數出字母數量，需要對 token 的內部結構進行推理。

---

## Tokenization 演算法

### Byte Pair Encoding (BPE)

最常見的演算法。被 GPT 系列、Llama、Claude 所使用。

**訓練演算法：**
1. 從個別位元組組成的詞彙表開始（256 個 token）
2. 計算訓練語料庫中所有相鄰的 token 配對
3. 將出現頻率最高的配對合併成一個新的 token
4. 重複直到達到詞彙表大小為止

**範例：**
```
Corpus: "low lower lowest"
Initial: ['l', 'o', 'w', ' ', 'l', 'o', 'w', 'e', 'r', ' ', 'l', 'o', 'w', 'e', 's', 't']

Step 1: Most frequent pair is ('l', 'o'). Merge to 'lo'.
['lo', 'w', ' ', 'lo', 'w', 'e', 'r', ' ', 'lo', 'w', 'e', 's', 't']

Step 2: Most frequent pair is ('lo', 'w'). Merge to 'low'.
['low', ' ', 'low', 'e', 'r', ' ', 'low', 'e', 's', 't']

Step 3: Most frequent pair is ('low', 'e'). Merge to 'lowe'.
['low', ' ', 'lowe', 'r', ' ', 'lowe', 's', 't']

Continue until vocabulary size target...
```

**特性：**
- 在給定訓練好的詞彙表下，tokenization 是確定性的
- 常見的詞往往是單一 token
- 罕見的詞會被拆分成 subword

### WordPiece

被 BERT 系列模型所使用。

**與 BPE 的關鍵差異：**
- BPE：根據頻率進行合併
- WordPiece：根據概似度（likelihood）的提升進行合併

```
Score = freq(AB) / (freq(A) * freq(B))
```

這會傾向於選擇比隨機共現更有意義的合併。

**視覺標記：** WordPiece 對接續的 token 使用 ## 前綴：
```
"embedding" becomes ["em", "##bed", "##ding"]
```

### Unigram (SentencePiece)

被 T5、ALBERT 以及部分多語言模型所使用。

**訓練演算法：**
1. 從一個龐大的候選詞彙表開始
2. 計算移除每個 token 後的 loss
3. 移除那些使 loss 增加最少的 token
4. 重複直到達到詞彙表大小為止

**關鍵差異：** 它以機率（而非頻率）來運作。能夠從次佳的早期合併中恢復過來。

### 比較

| 演算法 | 合併準則 | Tokenization | 使用者 |
|-----------|-----------------|--------------|---------|
| BPE | 頻率 | 確定性 | GPT, Llama, Claude |
| WordPiece | 概似度 | 確定性 | BERT, DistilBERT |
| Unigram | 機率 | 機率性 | T5, mT5, XLNet |

---

## 詞彙表設計取捨

### 詞彙表大小

| 大小 | 範例 | 優點 | 缺點 |
|------|---------|------|------|
| 小型 (10K) | 部分早期模型 | embedding 較小 | token 序列很長 |
| 中型 (32K) | Llama 2 | 平衡良好 | 多語言效率不彰 |
| 大型 (128K) | Llama 3/4、Claude Sonnet 4.6、Mistral Medium 3.5 | **當前的標準。** 高壓縮比。 | embedding 表較大 |
| 巨型 (200K+) | GPT-5.5 (o200k)、Claude Opus 4.7 | 原生多模態與多語言效率 | LM Head 的記憶體壓力 |

**詞彙表擴展深入解析：**
- **Llama 3/4 (128k)**：透過從 32k 移動到 128k，Meta 將英文的壓縮率提升了約 15%，並將像印地語這類非英語語言提升了 3-4 倍。
- **GPT-4o/5.2 (o200k_base)**：Tiktoken 最新的編碼為程式碼與多語言文字提供了更佳的壓縮，藉由對相同語意使用更少的 token，間接降低了 API 成本。

### 字元 vs Subword vs 詞

| 粒度 | 範例 | "running" 的 token | 取捨 |
|-------------|---------|---------------------|-----------|
| 字元 | ByT5 | ['r','u','n','n','i','n','g'] | 能處理任何文字，但序列非常長 |
| Subword | GPT | ['running'] 或 ['run','ning'] | 平衡良好 |
| 詞 | 早期 NLP | ['running'] | 序列短，但無法處理 OOV |

現代 LLM 普遍採用 subword tokenization，以在詞彙表大小與序列長度之間取得平衡。

### Byte-Level BPE

GPT-2 引入了 byte-level BPE：
- 基礎詞彙表是 256 個位元組，而非字元
- 能夠表示任何文字，而不需要 UNK token
- Unicode 自然地以位元組序列處理

```python
# Character-level: Needs explicit handling of characters
text = "cafe"  # Unknown character might become [UNK]

# Byte-level: Works with any text (no UNK needed)
text = "cafe"  # Becomes bytes, then BPE operates on bytes
```

---

## 特殊 Token

特殊 token 用於處理正常文字以外的結構性資訊：

| Token | 用途 | 範例 |
|-------|---------|---------|
| BOS | 序列的開始 | 標示生成的起點 |
| EOS | 序列的結束 | 標示完成 |
| PAD | 填充 | 將批次補齊到相同長度 |
| UNK | 未知 token | OOV 的後備方案（在 byte BPE 下很少見） |
| SEP | 分隔符 | 切分區段（BERT 風格） |

### Chat 範本

現代的 chat 模型使用特殊 token 來表示對話結構：

**Llama 2 格式：**
```
[INST] <<SYS>>
You are a helpful assistant.
<</SYS>>

User message here [/INST] Assistant response here
```

**ChatML（OpenAI 風格）：**
```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
Hello!<|im_end|>
<|im_start|>assistant
Hi there!<|im_end|>
```

**為什麼這很重要：**
- 錯誤的格式會導致糟糕的結果
- 特殊 token 並不存在於預訓練資料中
- 像 transformers 這類函式庫使用 chat_template 來進行自動格式化

---

## 多語言 Tokenization

### 挑戰

主要在英文上訓練的 tokenizer，對其他語言的效率不佳：

| 語言 | "Hello" 的 token | 對應問候語的 token |
|----------|-------------------|-------------------------------|
| 英文 | 1 ("Hello") | - |
| 中文 | - | 對應詞需要 2-3 個以上 |
| 日文 | - | 對應詞需要 3-5 個以上 |
| 韓文 | - | 對應詞需要 2-4 個以上 |

**成本影響：** 非英語使用者每個語意單元要多付 2-3 倍的費用。

### 解決方案

1. **多語言訓練語料庫：** 在平衡的多語言資料上訓練 tokenizer
2. **更大的詞彙表：** 為非英語的 token 留出更多空間
3. **特定語言的 tokenizer：** 每個語系使用各自獨立的 tokenizer

**具備良好多語言支援的模型：**
- mT5、XLM-R：在 100 多種語言上訓練
- GPT-4、Claude 3.5：擁有具多語言涵蓋範圍的大型詞彙表
- Gemini：從一開始就為多語言而設計

| 模型 | 中文 | 日文 | 韓文 | 印地語 |
|-------|---------|----------|--------|--------|
| GPT-2 | 2.5x | 3.0x | 2.8x | 6.0x |
| GPT-4 (cl100k) | 1.4x | 1.6x | 1.5x | 3.2x |
| GPT-5.2 (o200k) | 1.1x | 1.2x | 1.1x | 1.4x |
| Llama 3/4 (128k)| 1.2x | 1.3x | 1.2x | 1.5x |

---

## 多模態 Tokenization（pixels-to-tokens）

現代的原生多模態模型不只是「看見」影像；它們會將影像 tokenize。

### 影像 Tokenization（Vision Transformers）
影像會被切分成 patch（例如 14x14 像素）。每個 patch 經過一個 vision encoder（如 SigLIP）處理，產生單一個視覺 token。
- **固定的 Token 成本**：大多數模型在特定解析度下，對每張影像使用固定數量的 token（例如每張影像 256 或 729 個 token）。
- **動態解析度**：某些模型（Gemini 3）會依據影像的長寬比與細節層級，使用可變數量的 token。

### 音訊/影片 Tokenization
- **音訊**：使用像 EnCodec 這類編解碼器壓縮成離散單元，接著表示為一串音訊 token 的序列。
- **影片**：被視為一連串的影像影格（時間性 tokenization）。一段 1 秒、@ 1FPS 的影片，其成本可能相當於 1 張高解析度影像。

---

## 用於成本估算的 Token 計數

### 快速估算規則

對於英文文字：
- **詞數換算 token：** 每個詞約 1.3 個 token
- **字元數換算 token：** 每個 token 約 4 個字元
- **頁數換算 token：** 每頁約 500-800 個 token

```python
def estimate_tokens(text: str) -> int:
    # Rough estimation for English
    word_count = len(text.split())
    return int(word_count * 1.3)
```

### 精確計數

使用特定模型的 tokenizer：

```python
import tiktoken

# For OpenAI models
encoding = tiktoken.encoding_for_model("gpt-4")
tokens = encoding.encode("Your text here")
token_count = len(tokens)

# For Llama/Anthropic, use transformers
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b")
tokens = tokenizer.encode("Your text here")
token_count = len(tokens)
```

### 成本計算

```python
def calculate_cost(input_text: str, output_text: str, model: str) -> float:
    pricing = {
        "gpt-4o": {"input": 2.50, "output": 10.00},  # per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    }
    
    encoding = tiktoken.encoding_for_model(model)
    input_tokens = len(encoding.encode(input_text))
    output_tokens = len(encoding.encode(output_text))
    
    cost = (
        (input_tokens / 1_000_000) * pricing[model]["input"] +
        (output_tokens / 1_000_000) * pricing[model]["output"]
    )
    return cost
```

---

## 常見的 Tokenization 問題

### 問題 1：Token 邊界錯位

**問題：** 文字操作可能不會對齊到 token 邊界。

```python
text = "Hello world"
# Tokens: ["Hello", " world"]  # Note: space is part of second token

# Truncating at character 6 ("Hello ") splits a token
```

**解決方案：** 在管理 context 時，務必在 token 邊界處進行截斷。

### 問題 2：不一致的 Tokenization

**問題：** 同一段文字會依據 context 而以不同方式被 tokenize。

```python
# GPT tokenizer example
"New York"     # Might be ["New", " York"]
"NewYork"      # Might be ["New", "York"]
" New York"    # Might be [" New", " York"]
```

**影響：** Token 數量可能會依據周圍的文字而變化。務必對完整的 context 進行 tokenize。

### 問題 3：程式碼與結構化資料

**問題：** 程式碼與 JSON 往往被低效率地 tokenize。

```python
# Python code often tokenizes poorly
"def calculate_average(numbers):"
# Becomes many tokens: ["def", " calculate", "_", "average", "(", "numbers", "):", ...]

# JSON keys tokenize individually
'{"firstName": "John"}'
# Many tokens for structure
```

**緩解方式：**
- 某些模型具備為程式碼最佳化的 tokenizer
- 考慮在傳送前壓縮 JSON
- 在可行時使用結構化輸出模式

### 問題 4：空白字元的處理

**問題：** tokenizer 對空白字元的處理方式各不相同。

```python
# Leading spaces often become separate tokens
" Hello"  # [" ", "Hello"] or [" Hello"]

# Multiple spaces may merge or stay separate
"Hello  world"  # Behavior varies by tokenizer
```

**最佳實務：** 在 tokenize 之前先將空白字元正規化。

---

## 實務 Tokenization 模式

### 模式 1：Context 視窗管理

```python
def fit_to_context(
    system_prompt: str,
    user_message: str,
    history: list[str],
    max_tokens: int = 8000,
    reserve_for_output: int = 2000
) -> str:
    encoding = tiktoken.encoding_for_model("gpt-4")
    
    available = max_tokens - reserve_for_output
    
    # System prompt always included
    tokens_used = len(encoding.encode(system_prompt))
    available -= tokens_used
    
    # User message always included
    tokens_used = len(encoding.encode(user_message))
    available -= tokens_used
    
    # Add history from most recent, drop oldest if needed
    included_history = []
    for msg in reversed(history):
        msg_tokens = len(encoding.encode(msg))
        if msg_tokens <= available:
            included_history.insert(0, msg)
            available -= msg_tokens
        else:
            break
    
    return format_prompt(system_prompt, included_history, user_message)
```

### 模式 2：在 Token 邊界處進行分塊

```python
def chunk_at_token_boundaries(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:
    encoding = tiktoken.encoding_for_model("gpt-4")
    tokens = encoding.encode(text)
    
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        start = end - overlap
    
    return chunks
```

### 模式 3：Token 預算分配

```python
class TokenBudget:
    def __init__(self, total: int):
        self.total = total
        self.allocated = {}
    
    def allocate(self, component: str, tokens: int) -> bool:
        used = sum(self.allocated.values())
        if used + tokens > self.total:
            return False
        self.allocated[component] = tokens
        return True
    
    def remaining(self) -> int:
        return self.total - sum(self.allocated.values())

# Usage
budget = TokenBudget(total=8000)
budget.allocate("system_prompt", 500)
budget.allocate("retrieved_context", 2000)
budget.allocate("user_message", 200)
budget.allocate("output_reserve", 2000)
# Remaining: 3300 tokens for conversation history
```

---

## 面試問題

### Q：為什麼 GPT-4 在簡單的字元計數上會有困難？

**有力的回答：**
Tokenization 將文字轉換成 subword 單元，而非字元。當被問到「strawberry 裡有幾個 'r'？」時，模型看到的是像 ["str", "aw", "berry"] 這樣的 token，而非個別的字母。

模型必須對它並未直接觀察到的 token 內部結構進行推理。這需要記住或計算 token 的字元組成，而這是一種並不總是可靠的湧現能力（emergent capability）。

解決方法是先提示模型逐字元拼出該詞，然後再計數。這會強制建立字元層級的 token。

### Q：你會如何估算 token 數量以進行成本規劃？

**有力的回答：**
粗略估算：對於英文文字，將字數乘以 1.3。

精確計數：使用特定模型的 tokenizer。
- OpenAI：tiktoken 函式庫
- 其他：transformers AutoTokenizer

重要考量：
- 非英語文字會多用 1.5-3 倍的 token
- 程式碼與結構化資料的 tokenize 效率不彰
- 務必為輸出 token 預留額外預算（通常定價較高）
- 將 system prompt 與格式化 token 納入計算

對於正式環境的成本估算，我會抽樣實際的請求並測量真實的 token 使用量，然後套用安全邊際。

### Q：在不同模型之間切換 tokenizer 時會發生什麼事？

**有力的回答：**
每個模型家族都有自己的 tokenizer。你無法跨模型重複使用 token，因為：

1. **詞彙表不同：** Token ID 代表不同的字串
2. **合併規則不同：** 同一段文字會以不同方式拆分
3. **特殊 token 不同：** chat 格式各異

實務上的影響：
- 進行 token 計數時，務必使用正確的 tokenizer
- 快取的 embedding 是特定於模型的
- prompt 範本需要針對各模型進行調整
- 經過 fine-tune 的模型會繼承其 base 模型的 tokenizer

### Q：你會如何處理 RAG 分塊的 tokenization？

**有力的回答：**
關鍵考量：

1. **在 token 邊界處分塊：** 在 token 中途切分，會在解碼時破壞文字
2. **將範本 token 納入計算：** system prompt、格式化都會消耗 token
3. **預留緩衝空間：** 檢索到的 chunk 加上問題必須能放進 context

實作方法：
```python
# Determine available tokens for chunks
available = max_context - system_prompt_tokens - question_tokens - output_reserve

# Chunk with overlap at token boundaries
chunks = chunk_at_token_boundaries(document, chunk_size=500, overlap=50)

# Select chunks until budget exhausted
selected = []
tokens_used = 0
for chunk in ranked_chunks:
    chunk_tokens = count_tokens(chunk)
    if tokens_used + chunk_tokens <= available:
        selected.append(chunk)
        tokens_used += chunk_tokens
```

---

## 參考資料

- Sennrich et al. "Neural Machine Translation of Rare Words with Subword Units" (BPE, 2016)
- Wu et al. "Google's Neural Machine Translation System" (WordPiece, 2016)
- Kudo and Richardson "SentencePiece: A simple and language independent subword tokenizer" (2018)
- OpenAI tiktoken library: https://github.com/openai/tiktoken
- HuggingFace tokenizers: https://github.com/huggingface/tokenizers

---

*上一篇：[LLM Internals](01-llm-internals.md) | 下一篇：[Attention Mechanisms](03-attention-mechanisms.md)*
