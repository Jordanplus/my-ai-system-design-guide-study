# 推論基礎

推論（Inference）是從訓練好的模型產生預測結果的過程。為了在 Hopper（H100）與 Blackwell（B200）等級的硬體上處理重度推理（reasoning）工作負載，推論優化的重心已經從「單純的加速」轉移到「架構層級的效率」。

## 目錄

- [推論的兩個階段](#two-phases)
- [瓶頸：Compute-Bound 與 Memory-Bound](#bottlenecks)
- [效能指標：TTFT 與 TPOT](#metrics)
- [硬體驅動的優化（FP8）](#hardware-optimizations)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 推論的兩個階段

LLM 推論並非單一操作；它由兩個截然不同的運算階段所組成。

### 1. Prefill 階段（Prompt 處理）
模型在單次傳遞中處理整段輸入 prompt。
- **運算特性**：高度平行化的矩陣乘法。
- **瓶頸**：**Compute-bound**（受限於 GPU 的 TFLOPS）。
- **時間複雜度**：$O(N)$，其中 $N$ 為輸入長度（但可平行化處理）。

### 2. Decode 階段（Token 生成）
模型逐一產生 token，其中每個 token 都取決於前面的 token。
- **運算特性**：循序處理，一次處理權重矩陣的一列。
- **瓶頸**：**Memory-bound**（受限於記憶體頻寬）。
- **時間複雜度**：$O(M)$，其中 $M$ 為輸出長度（循序進行）。

---

## 瓶頸：Compute-Bound 與 Memory-Bound

了解系統的瓶頸所在，對於選擇正確的優化方式至關重要。

| 階段 | 瓶頸 | 原因？ | 主要優化手段 |
|-------|------------|------|----------------------|
| **Prefill** | 運算量（FLOPs） | 平行處理使 GPU 的算術運算單元達到飽和。 | FlashAttention、FP8/FP16 精度。 |
| **Decode** | 記憶體頻寬 | *每產生一個 token* 都必須從 VRAM 載入權重。 | 量化（4-bit）、GQA、批次處理（Batching）。 |

**記憶體牆（Memory Wall）的洞見**
隨著模型越來越大，記憶體頻寬（HBM3/HBM3e）的成長速度並未跟上運算能力（TFLOPS）。這使得 Decode 階段成為生產環境優化的首要目標。

---

## 效能指標

| 指標 | 全名 | 目標 | 重要性 |
|--------|-----------|------|------------|
| **TTFT** | Time To First Token（首個 token 時間） | < 200ms | 使用者感知到的回應速度。 |
| **TPOT** | Time Per Output Token（每個輸出 token 時間） | < 30ms | 閱讀速度與對話流暢度。 |
| **Throughput** | Tokens/Second（總和） | 最大化 | 決定每次查詢的成本。 |
| **Latency** | 端對端時間 | < 2.0s | agent 的整體往返時間。 |

---

## 硬體驅動的優化（FP8）

**FP8（8-bit 浮點數）** 是 H100 與 B200 GPU 上進行推論的原生精度。

- **效益**：比 FP16/BF16 快 2 倍，且準確度損失可忽略不計（<0.1%）。
- **運作原理**：相較於 Int8，它使用較小的尾數（mantissa）與較大的指數（exponent），讓它能更精確地表示 LLM activation 的動態範圍，而不需要複雜的校正（calibration）。

**Principal 等級的細節**：serving 框架現在會使用 **Dynamic FP8 Scaling（動態 FP8 縮放）**，逐層調整量化的縮放比例，以避免離群值（outliers）破壞整個模型的邏輯。

---

## 面試題

### Q：為什麼 LLM 生成比分類（classification）還慢？

**強力的回答：**
分類是一種「僅 Prefill」的任務；它在單次平行傳遞中處理整段輸入並產生單一輸出，因此達到運算最佳化（compute-optimal）。然而，LLM 生成是 **auto-regressive（自迴歸）** 的。每個 token 都取決於前一個 token，因而被迫進入循序的「Decode」迴圈。由於這個迴圈中的每一步都是 memory-bound（為了產生極微量的資料而載入數 GB 的權重），系統大部分時間都花在等待記憶體傳輸上，而非進行運算。

### Q：你如何分別優化 TTFT 與 TPOT？

**強力的回答：**
要優化 **TTFT**，你必須優化 Prefill 階段：使用 FlashAttention-3、提高運算平行度（Tensor Parallelism），或使用 Prefix Caching 來針對常見 prompt 完全略過 prefill。
要優化 **TPOT**，你必須優化 Decode 期間的記憶體頻寬：使用量化（4-bit 權重）以減少從 VRAM 搬移的資料量、使用 Grouped Query Attention（GQA）來縮小 KV cache 的大小，或使用 Speculative Decoding 在每次記憶體載入時產生多個 token。

---

## 參考資料
- Pope et al. "Efficiently Scaling Transformer Inference" (2022)
- NVIDIA. "Transformer Engine Documentation" (2024)
- vLLM Blog. "Understanding LLM Inference Latency" (2023)

---

*下一篇：[KV Cache 與 Context Caching](02-kv-cache-and-context-caching.md)*
