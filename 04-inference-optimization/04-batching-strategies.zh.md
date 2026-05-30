# 批次處理策略（Batching Strategies）

批次處理（Batching）是提升 LLM 吞吐量並降低成本的主要槓桿。服務框架已從單純的請求層級（request-level）批次處理，演進到子 token、迭代層級（iteration-level）的協調調度。

## 目錄

- [靜態批次 vs. 動態批次](#static-vs-dynamic)
- [連續批次（Continuous Batching）](#continuous-batching)
- [In-Flight Batching（Prefill-Decode 融合）](#in-flight-batching)
- [Chunked Prefill 與 RAD-O](#chunked-prefill)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 靜態批次 vs. 動態批次

在傳統 ML（分類任務）中，我們使用 **靜態批次（Static Batching）**，其中所有請求必須具有相同大小，且一起開始／一起結束。由於 LLM 的回應長度不固定，這種做法對 LLM 而言效率低落。

---

## 連續批次（迭代層級）

連續批次（Continuous batching，由 Orca 與 vLLM 開創）允許在每一個獨立的 token 生成步驟結束時，讓新的請求加入批次、讓已完成的請求離開批次。

| 面向 | 靜態批次 | 連續批次 |
|--------|-----------------|---------------------|
| **加入／離開** | 僅在開始／結束時 | 任何迭代 |
| **GPU 使用率**| 低（等待最長的請求） | 高（始終飽和） |
| **吞吐量** | 1x | **4x - 10x** |
| **延遲** | 對最短請求而言最高 | 平衡 |

---

## In-Flight Batching（Prefill-Decode 融合）

過去，服務引擎處理的是一批「Prefill」（運算密集）*或*一批「Decode」（記憶體密集）。
**In-Flight Batching**（TensorRT-LLM）允許將兩者混合處理：
- 1 個請求處於 Prefill 階段。
- 15 個請求處於 Decode 階段。
- **效益**：Prefill 請求利用 GPU 閒置的運算核心，而 Decode 請求則利用記憶體頻寬。

---

## Chunked Prefill 與 RAD-O

超大型情境提示（1M+ tokens）在 Prefill 階段可能會讓整個批次卡住數秒，造成「停頓（stalls）」。

**解法：Chunked Prefill**
引擎不再一次性 prefill 128k tokens，而是將 prefill 拆成較小的區塊（例如每塊 4k tokens），並與其他使用者正在進行的 Decode 步驟交錯穿插。即使有沉重的請求湧入，這也能維持穩定的 **TPOT**。

---

## 面試問題

### Q：對 LLM 而言，為什麼連續批次優於靜態批次？

**有力的回答：**
靜態批次迫使一個批次中的所有請求都必須等待最長的生成任務完成（即「最長尾部（longest tail）」問題）。如果一位使用者要求 500 個 tokens，而另一位只要求 5 個 tokens，那麼對於那位只要 5 個 token 的使用者而言，GPU 會閒置 495 個週期。連續批次允許這位只要 5 個 token 的使用者的請求在產生最後一個 token 後立即離開 GPU，釋出 VRAM 與運算插槽（compute slots）給佇列中的新請求。這能在整個硬體叢集上最大化「每秒 tokens 數（Tokens per Second）」。

### Q：LLM 服務中的「停頓（stall）」是什麼？Chunked Prefill 如何緩解它？

**有力的回答：**
當一個超大型的新請求湧入，而其 Prefill 階段（運算需求極高）需要 2-3 秒才能完成時，就會發生「停頓（stall）」。在這段時間內，GPU 忙於 prefill，以至於無法為處於「Decode」階段的既有使用者生成 tokens，導致他們的 TPOT 飆升。Chunked Prefill 會將那個 3 秒的 prefill 拆成小的 200ms「區塊」，先處理一個區塊，接著為其他所有人執行一輪 decoding，然後再回頭處理下一個 prefill 區塊。這能確保所有使用者都獲得一致且流暢的體驗。

---

## 參考資料
- Yu et al. "Orca: A Distributed Serving System for [Transformer] Models" (2022)
- NVIDIA. "TensorRT-LLM: In-Flight Batching" (2023)
- vLLM Project. "Iteration-Level Scheduling" (2023)

---

*下一篇：[PagedAttention](05-paged-attention.md)*
