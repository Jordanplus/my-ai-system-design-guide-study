# 短期上下文管理

短期上下文（L1 Memory）是推理發生的高速介面。要把它管理好，已經不再是處理「訊息列表」的問題，而是關於 **KV Cache Optimization** 與 **Dynamic Context Allocation**。

## 目錄

- [上下文生命週期](#lifecycle)
- [KV Cache Tiling 與 PagedAttention](#paged-attention)
- [Prefix Caching（System Prompt 的保留）](#prefix-caching)
- [Sliding Windows 與 Summarization 的比較](#sliding-vs-summary)
- [上下文壓縮（選擇性丟棄）](#compression)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 上下文生命週期

上下文會經歷三個階段：
1. **Intake（攝入）**：使用者查詢 + 近期歷史 + 系統指令。
2. **Processing（處理）**：GPU 為新的 token 計算 KV cache。
3. **Eviction（驅逐）**：一旦達到上限，移除舊的 token 以騰出空間給新的 token。

---

## KV Cache Tiling

現代推理引擎（vLLM、TensorRT-LLM）使用 **PagedAttention**。
- **概念**：不再為上下文配置一整塊連續的 GPU 記憶體，而是將記憶體切分成多個 **Block**（頁）。
- **效率**：將記憶體碎片化降低 **60-80%**，讓相同硬體上能容納顯著更大的 batch size 與更長的 context window。

---

## Prefix Caching

對任何正式環境的 LLM 技術堆疊而言，這是 **延遲的聖杯（Holy Grail of Latency）**。
- **問題**：每當 agent 呼叫 LLM 時，都會送出相同的那 2,000-token System Prompt + 50 個 Tool Schema。這浪費了運算資源。
- **解決方案**：**Persistent Prefix Caching**。伺服器將 prompt 中「靜態」部分（即 prefix）的 KV cache 保留在記憶體中。
- **結果**：你只需為訊息中*新增*部分的運算付費（並等待）。

---

## Sliding Windows 與 Summarization 的比較

| 方法 | 運作機制 | 優點 | 缺點 |
|--------|-----------|-----|-----|
| **Sliding Window** | 完整保留最後 N 個 token。 | 對近期內容有高度保真。 | 「健忘魚（Dory）」效應（忘記開頭）。 |
| **Summarization** | 將舊的對話回合壓縮成文字。 | 保留「關鍵事實」。 | 失去細節／格式。 |
| **Hybrid** | 保留最後 10 個對話回合 + 1 份摘要。 | 兼得兩者之長。 | 複雜度略高。 |

---

## 上下文壓縮

目前的前沿模型支援 **Prompt Hardening**。
- **選擇性丟棄（Selective Dropping）**：自動剝除前幾個對話回合中不相關的「Thought」區塊以節省空間。
- **Token Pruning**：在送進「Reasoning」模型之前，使用較小的模型將冗長的使用者訊息改寫成短 50%、語意等價的 prompt。

---

## 面試題

### Q：「Model Context Window」與「Application Context Window」有什麼差別？

**理想答案：**
**Model Context Window** 是由架構定義的硬性上限（例如 GPT-4o 的 128K）。**Application Context Window** 則是工程師設定的組態（例如 16K 上限），用來管理 **延遲與成本**。在正式環境中，我們很少在每個回合都用滿整個模型視窗，因為 attention 的額外開銷會隨著上下文大小增加，導致生成速度變慢。我們會使用一個 **Buffer Zone（緩衝區）**，為模型的新回應預留空間。

### Q：「Prefix Caching」如何改變你設計 System Prompt 的方式？

**理想答案：**
它促使我把 **靜態內容移到前面**、**動態內容移到後面**。早期 LLM 的常見做法是把使用者名稱或日期放在最頂端，這會破壞 prefix cache。我會把「不可變規則」與「Tool Schema」放在開頭，把（每個回合都會變動的）「使用者上下文」放在結尾。如此可確保前 5,000 個 token 在所有使用者之間都完全相同，將推理伺服器上的快取命中率最大化。

---

## 參考資料
- vLLM Team. "PagedAttention: Software-Defined Memory for LLM Serving" (2024/2025)
- NVIDIA. "Optimizing Inference with TensorRT-LLM" (2025)
- Anthropic. "Prompt Caching: Scale while reducing costs" (2024/2025)

---

*下一篇：[長期記憶](03-long-term-memory.md)*
