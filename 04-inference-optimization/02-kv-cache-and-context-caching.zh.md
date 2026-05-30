# KV Cache 與 Context Caching

KV Cache 是長 context AI 系統中最主要的記憶體消耗來源。能否有效管理這個 cache，決定了系統是能擴展到 2M token，還是在 10k 就崩潰。

## 目錄

- [KV Cache 的問題](#kv-cache-problem)
- [GQA：Grouped Query Attention](#gqa)
- [Context Caching（自架）](#context-caching-self-hosted)
- [API 層級的 Context Caching（Prompt Caching）](#api-prompt-caching)
- [RAD-O：Retrieval Augmented Decoding](#rad-o)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## KV Cache 的問題

在生成過程中，模型需要先前所有 token 的 Key (K) 與 Value (V) 張量。將這些資料存放在記憶體中相當昂貴。

**VRAM 計算（Llama 4 70B）：**
- **Tokens**：128,000
- **精度**：BF16（2 bytes/param）
- **記憶體**：`2 (KV) * layers (80) * context (128k) * heads (8) * head_dim (128) * 2 bytes`
- **總計**：在 128k context 下，**每位使用者約 42 GB**。

---

## GQA：Grouped Query Attention

GQA 是目前在不損失效能的前提下縮減 KV Cache 大小的標準做法。

| 方法 | 比例 | KV Cache 縮減 | 品質損失 |
|--------|-------|-------------------|--------------|
| **Multi-Head (MHA)** | 1:1 | 1x（基準） | 0% |
| **Grouped Query (GQA)** | 8:1 | **8x** | < 0.2% |
| **Multi-Query (MQA)** | All:1 | 64x-128x | 2-3% |

**細節說明**：GQA 讓模型能從多個「推理」head 共用同一份 KV「記憶」，大幅降低 Decode 階段所需的記憶體頻寬。

---

## Context Caching（自架）

正式環境系統會針對具有共同前綴的 prompt 使用 **Shared KV Caches**（例如一份由 1,000 位使用者共用的 100 頁知識庫）。

### Disk vs. VRAM Caching
- **VRAM Cache**：可即時存取，但容量嚴格受限。
- **Disk/SSD Cache**：存取較慢，但容量幾乎無上限。像 **SGLang** 這類框架採用分層系統：`Most Recent (VRAM) -> Frequent (HBM) -> Occasional (SSD)`。

---

## API 層級的 Context Caching（Prompt Caching）

主要供應商（OpenAI、Anthropic、Google、DeepSeek）現在都提供 **Prompt Caching** 折扣。

| 供應商 | 功能名稱 | 定價（已快取的 input） | 最適合的情境 |
|----------|--------------|------------------------|----------|
| **Anthropic** | Context Caching | 90% 折扣（Sonnet 4.6 cached：$0.30/1M） | 長 system prompt、tool schema |
| **OpenAI** | Prompt Caching | 已快取 input 約 50% 折扣（GPT-5.5 cached：約 $2.50/1M） | 多輪對話 |
| **Google** | Context Caching | Cache 讀取 $0.20/1M（Gemini 3.1 Pro 200K 以下）；另收每小時儲存費 | 長篇共用語料 |
| **DeepSeek** | Context Caching | **$0.003625/M (V4 Pro) / $0.0028/M (V4 Flash)** | 大型 codebase RAG；市場上最便宜的 cache 層級 |

**損益兩平的細節**：如果你的已快取前綴被重複使用超過 **1.1x 到 1.5x**，使用 caching 會比直接用原始 token 更便宜。Anthropic 對 cache 寫入加收 25% 的費用，因此對於較短的前綴，損益兩平點較高（需重複使用 3-5x）。DeepSeek 於 2026 年 4 月 26 日將 cache-hit 價格砍到上線時的 1/10。對於 cache 密集的工作負載，V4 Flash 目前每個已快取 token 的成本約比 GPT-5.5 便宜 30-50x。

---

## RAD-O：Retrieval Augmented Decoding

RAD-O 是一種 context-caching 技術，模型會將長文件的 KV cache **壓縮**成「Latent tokens」。
- **做法**：不再為 1M token 儲存完整的 KV 向量，而是儲存一份小 10x 的壓縮表示。
- **影響**：讓原本只支援 200k 的硬體能處理 2M+ token 的 context。

---

## 面試題

### Q：PagedAttention 如何協助 KV Cache 管理？（簡化版）

**強力回答：**
標準 KV cache 需要連續的記憶體配置（一整塊巨大的 RAM）。這會導致 **External Fragmentation**（記憶體確實存在，卻散落在無法使用的空隙中）。PagedAttention（用於 vLLM）將 KV cache 拆成小型、固定大小的「page」（類似 OS 的虛擬記憶體）。這讓 cache 可以是非連續的，意味著我們能在真正需要時才精確配置記憶體，並在具有相同前綴的不同請求之間共用 page。這通常能將記憶體使用效率從 60% 提升到 96%+。

### Q：對於一份 50k token 的文件，為什麼 Context Caching 比 RAG 更好？

**強力回答：**
有了便宜的 context caching（DeepSeek、Gemini、Anthropic），對中等大小的文件而言，RAG 往往是「殺雞用牛刀」。
1. **Recall**：Context caching 提供 100% recall（整份文件都在 window 中），而 RAG 則取決於檢索的準確度。
2. **連貫性**：模型能看到整份文件中的交叉引用。
3. **成本考量**：在 50k token 時，已快取 input 的成本往往低於維護 vector database 與檢索 pipeline 所帶來的複雜度。

---

## 參考資料
- Kwon et al. "Efficient Memory Management with PagedAttention" (2023)
- Anthropic. "Prompt Caching Documentation" (2024)
- DeepSeek. "Context Caching Technical Report" (2025)

---

*下一篇：[Speculative Decoding](03-speculative-decoding.md)*
