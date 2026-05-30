# PagedAttention

PagedAttention 是高吞吐量服務引擎（vLLM、SGLang、TensorRT-LLM）背後的基礎演算法。它解決了過去限制 LLM 擴展性的「記憶體碎片化」問題。

## 目錄

- [連續記憶體的問題](#contiguous-memory)
- [PagedAttention 如何運作](#how-it-works)
- [管理虛擬記憶體（Block Manager）](#block-manager)
- [KV Cache 共享（Copy-on-Write）](#sharing)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 連續記憶體的問題

標準的深度學習框架以大塊且連續的方式配置記憶體。
對於一個 LLM 請求，你可能會為 8192 個 token 的 `max_sequence_length` 預先配置記憶體。

**浪費之處：**
1. **內部碎片化（Internal Fragmentation）**：如果使用者只生成 10 個 token，那塊保留區塊有 99.9% 都被浪費掉了。
2. **外部碎片化（External Fragmentation）**：記憶體被切成許多空隙，每個都太小而無法容納一個新的「大區塊」，即使總空閒記憶體量很高也一樣。

---

## PagedAttention 如何運作（vLLM）

PagedAttention 的靈感來自作業系統中的虛擬記憶體（Virtual Memory）。

1. **Token 轉成 Block**：一個請求的 KV cache 會被切分成小的、固定大小的 **Block**（例如每個 block 16 個 token）。
2. **邏輯 vs. 實體**：模型以為自己正在關注（attending）一段連續的序列（邏輯記憶體），但這些 block 其實分散在整個 VRAM 各處（實體記憶體）。
3. **查找表（Lookup Table）**：**Block Table** 負責將邏輯索引對應到實體位址。

**主要效益**：記憶體浪費從約 60-80% 降到 **不到 4%**。

---

## 管理虛擬記憶體（Block Manager）

服務框架（vLLM、SGLang）扮演著 GPU 的「迷你作業系統」角色。

- **配置（Allocation）**：當一個新請求開始時，Block Manager 會指派給它一組空的實體 block。
- **驅逐（Eviction）**：如果 VRAM 滿了，管理器可以將不活躍的 KV block「換出（swap）」到 CPU RAM，並在需要時再把它們取回（Paged Swap）。

---

## KV Cache 共享（Copy-on-Write）

PagedAttention 讓「共同前綴（Common Prefixes）」的共享變得毫不費力。

**情境**：100 位使用者正在和同一個 5,000-token 的 system prompt 對話。
- **傳統做法**：把那份 5,000-token 的 KV cache 儲存 100 次（VRAM 中共 **500k 個 token**）。
- **PagedAttention**：透過 Block Table 只儲存 **一次**，並讓全部 100 位使用者都指向同一組實體 block。
- **Copy-on-Write**：如果某位使用者生成了一個獨有的 token，就會專為他建立一個新的 block，而共享的 block 則保持不變。

---

## 面試問題

### Q：為什麼 PagedAttention 能顯著提升吞吐量？

**理想的回答：**
PagedAttention 透過允許大得多的 **batch size** 來提升吞吐量。由於它消除了內部與外部的記憶體碎片化，我們可以在同一個 GPU VRAM 中塞進多得多的請求。在傳統服務中，我們可能只能容納 4 個請求，因為必須「保留」最大長度的 block；有了 PagedAttention，我們可以容納 20-30 個請求，因為我們只為實際存在的 token 使用記憶體。更大的 batch 帶來更好的 GPU 使用率，以及顯著更高的總體每秒 token 數。

### Q：請在 vLLM 的脈絡下解釋「Block Table」。

**理想的回答：**
Block Table 是一個對應結構，它彌合了模型期望資料是連續的，與記憶體實際上是分散的這兩者之間的落差。表中的每一筆項目對應一個 token 的「邏輯 Block（Logical Block）」。它儲存了該 block 的 key 與 value 張量所在的 GPU 記憶體實體位址。這讓框架能夠以小區塊為單位動態地配置與釋放記憶體，從而支援前綴共享（prefix sharing）與高效的多執行緒等進階功能。

---

## 參考資料
- Kwon et al. "Efficient Memory Management for Large Language Model Serving with PagedAttention" (SOSP 2023)
- vLLM Documentation. "PagedAttention Logic" (2024)

---

*下一篇：[服務基礎設施](06-serving-infrastructure.md)*
