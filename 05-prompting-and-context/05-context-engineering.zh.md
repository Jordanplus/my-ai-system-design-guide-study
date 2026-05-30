# Context Engineering

Context engineering 是一門將 LLM 有限的「工作記憶」填入最有價值 token 的科學。隨著 context window 如今已達到 1M+ token（Claude Sonnet 4.6、Gemini 3.1 Pro、GPT-5.5），加上模型獲得 Extended Thinking 能力，重心已從「塞入資料」轉移到「排序相關性」與「管理運算預算」。

## 目錄

- [長 Context 典範（1M+ Token）](#long-context)
- [Extended Thinking 與 Budget Token](#extended-thinking)
- [Lost-in-the-Middle](#lost-in-the-middle)
- [Context 預算編列與 Token 意識](#budgeting)
- [Prompt Caching 經濟學](#prompt-caching)
- [Contextual Compression（RAD-L）](#compression)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 長 Context 典範（1M+ Token）

像 Gemini 3.1 Pro（1M）、Claude Sonnet 4.6（1M）、Claude Opus 4.7（1M）以及 GPT-5.5（1M）這類模型，都擁有龐大的 context window。

**洞見**：「Context 就是新的 RAG。」
對於少於 100,000 份文件的資料集而言，將整個資料集放入 context window，通常比使用外部向量資料庫更準確也更快速。這稱為 **「In-Context RAG。」**

---

## Extended Thinking 與 Budget Token

多款前沿模型現在都提供在產生回應前的**可控內部推理**：

### Claude（Sonnet 4.6、Opus 4.7）：Extended Thinking

```python
response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000  # max internal reasoning tokens
    },
    messages=[{"role": "user", "content": "Refactor this codebase to be async..."}]
)

# Response has two blocks:
# 1. thinking block (visible for debug, not shown to user)
# 2. text block (the actual answer)
for block in response.content:
    if block.type == "thinking":
        print("[THINKING]", block.thinking)
    elif block.type == "text":
        print("[ANSWER]", block.text)
```

**關鍵參數：**
- `budget_tokens`：1,024 → 100,000。越高 = 準確度越好，成本也越高。
- Thinking token 以標準費率計費。10K 的 thinking budget = 每次請求 +$0.15。
- 支援串流 —— thinking block 會在 text 之前串流輸出。

### o3（OpenAI）—— Reasoning Effort

```python
response = client.chat.completions.create(
    model="o3",
    reasoning_effort="medium",  # "low" | "medium" | "high"
    messages=[{"role": "user", "content": "Prove P=NP or disprove it."}]
)
# Reasoning tokens are invisible — o3 never exposes its internal chain
```

**Effort 等級與成本（約略）：**
| Effort | 速度 | 成本倍數 | 最適用於 |
|--------|-------|-----------------|----------|
| low | 快 | 1x | 簡單邏輯、快速查詢 |
| medium | 中等 | 3-5x | 寫程式、分析 |
| high | 慢 | 8-20x | 博士等級問題、ARC-AGI |

### 何時啟用 Thinking / Reasoning

| 條件 | 建議 |
|-----------|----------------|
| 複雜的多步驟程式碼重構 | ✅ 啟用（budget：8K-20K） |
| 簡單問答 / 抽取 | ❌ 停用 —— 會增加成本與延遲 |
| STEM / 數學問題 | ✅ 啟用（o3-mini medium） |
| 高流量聊天機器人 | ❌ 停用 —— 使用標準模式 |
| 安全關鍵的決策 | ✅ 啟用 —— 額外推理能捕捉邊界情況 |

**生產環境模式**：使用一個複雜度分類器來控制 Extended Thinking 的開關。若查詢的複雜度分數 < 0.5，就完全跳過 thinking 模式（在推理密集的工作負載上可節省 60-80% 成本）。

```python
def smart_generate(query: str) -> str:
    complexity = classifier.predict(query)  # 0-1 score
    
    if complexity > 0.7:
        # Enable Extended Thinking for hard problems
        return claude_with_thinking(query, budget_tokens=8000)
    else:
        # Standard fast mode for simple tasks
        return claude_standard(query)
```

---

## Lost-in-the-Middle

在 2023 年，模型對於 prompt 中段的資訊會出現準確度下降的情形。
**現況**：前沿模型（Claude Sonnet 4.6、Claude Opus 4.7、Gemini 3.1 Pro、GPT-5.5）的表現已大幅改善，但 **Attention Gradient（注意力梯度）** 依然存在。
- **最佳實務**：將關鍵指令與黃金標準範例放在 prompt 的**最開頭**與**最結尾**。中段 = 原始資料/知識區塊。
- **善用區塊排序**：對檢索回來的文件重新排序，讓最相關的排在最前與最後。

---

## Context 預算編列與 Token 意識

每個 token 都要花錢，並會增加 TTFT（Time to First Token，首個 token 時間）。

| 元件 | 預算（Token） | 為什麼？ |
|-----------|-----------------|------|
| **System Prompt** | 500 - 1,000 | 核心邏輯與人格設定。 |
| **History** | 2,000 - 5,000 | 對話的「狀態」。 |
| **Data/Search** | 10k - 1M | 取決於任務深度。 |
| **Output Reserve**| 1,000 - 4,000 | 必須為推理保留空間。 |

---

## Prompt Caching 經濟學

幾乎所有主要供應商（OpenAI、DeepSeek、Anthropic、Google）都支援 **Prefix Caching（前綴快取）**。

- **交叉點**：如果你重複使用一份 100k token 的 context（例如一個程式碼庫）超過 2 次請求，快取折扣實際上會讓它比 RAG 更便宜。
- **Cache Hits（快取命中）**：$0.05 / 1M tokens。
- **Cache Misses（快取未命中）**：$5.00 / 1M tokens。

**架構抉擇**：設計你的系統，讓「System Prompt + 基礎知識」保持靜態，以維持 100% 的快取命中率。

---

## Contextual Compression（RAD-L）

對於極長的 context（10M+），我們會使用 **Reasoning-Aware Deletion（RAD-L，推理感知刪除）**。
- **作法**：一個微型輔助模型（0.1B）會掃描文字，在 prompt 送往龐大的前沿模型*之前*，移除「填充」字詞、常見的語言模式以及不相關的段落。
- **效益**：將 prompt 大小縮減 20-50%，準確度下降不到 <1%。

---

## 面試問題

### Q：你會在什麼情況下選擇 Long Context 而非 RAG？

**強力回答：**
當高保真檢索與跨文件推理至關重要時，我會選擇 Long Context。RAG 會受到「Retrieval Gap（檢索缺口）」之苦 —— 如果你的向量搜尋漏掉了相關的區塊，模型就永遠看不到它。Long Context（最高 2M token）提供 100% 的召回率。具體而言，我會將它用於程式碼庫分析、法律文件審閱以及多檔案財務稽核。對於動態的網路規模資料，或是超出任何 context window 的十億級文件資料集，我則會堅持使用 RAG。

### Q：你如何處理百萬級 token prompt 所伴隨的高 TTFT？

**強力回答：**
主要的解決方案是 **Context Caching（Context 快取）**。透過將龐大的文件快取在 GPU 叢集上，模型就不必為了每一輪對話而「重新讀取」（prefill）整整 1M 個 token。已快取 prompt 的 TTFT 幾乎和 1k token prompt 一樣。此外，對於未快取的請求，我會使用 **Streaming Prefill（串流預填）**，讓模型在仍在處理這份龐大 context 的後半部時，就先產生初步的摘要或「Thought（想法）」。

---

## 參考資料
- Liu et al. "Lost in the Middle" (2023/2024 update)
- Anthropic. "Extended Thinking: Technical Guide" (2025) — https://docs.anthropic.com/
- OpenAI. "o3 and o3-mini System Card" (2025)
- Google. "Gemini 2.0 Flash: Technical Report" (2024)

---

*下一篇：[Structured Generation](06-structured-generation.md)*
