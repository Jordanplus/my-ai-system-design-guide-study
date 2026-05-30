# 量化深入剖析

量化是降低模型權重精度（例如從 16-bit 降到 4-bit）的過程，目的是節省記憶體並提升推論速度。這是在消費級與單一 GPU 硬體上部署大型模型的主要工具。

## 目錄

- [精度與效能的取捨](#precision-performance)
- [量化方法（NF4、GPTQ、AWQ）](#methods)
- [GGUF vs. EXL2](#formats)
- [KV Cache 量化（VRAM 的節省利器）](#kv-cache)
- [量化感知微調](#qaft)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 精度與效能的取捨

傳統模型使用 **BF16**（16-bit）。量化的目標是把它降低到 **8-bit（FP8）**、**4-bit（Int4/NF4）**，甚至 **1.5-bit（BitNet）**。

| 精度 | Bits | 權重大小（8B 模型） | 品質損失 | GPU 相容性 |
|-----------|------|------------------------|--------------|-------------------|
| **BF16** | 16 | 16 GB | 0%（基準） | 所有現代 GPU |
| **FP8** | 8 | 8 GB | < 1% | H100 / B200 / RTX 4090 |
| **4-bit (NF4)**| 4 | 5 GB | 1-2% | 所有現代 GPU |
| **2-bit** | 2 | 2.5 GB | 10-15% | 研究用 / 特殊用途 |

---

## 量化方法

### 1. NF4 (NormalFloat4)
微調（QLoRA）的黃金標準。它假設權重服從常態分布，並將其對應到一組 16 個數值。

### 2. AWQ (Activation-aware Weight Quantization)
AWQ 不是對所有權重一視同仁地量化，而是辨識出對品質最重要的 **1%「顯著（salient）」權重**，並將它們保留在較高精度。
- **優點**：準確度優於 GPTQ。

### 3. FP8（多節點標準）
由 Nvidia 的 Transformer Engine 支援的硬體原生量化。
- **為何勝出**：它提供 Int8 的速度，卻有 Float16 的動態範圍，使其在訓練與推論上都很穩定。

---

## GGUF vs. EXL2

### GGUF (llama.cpp)
- **部署**：CPU + GPU 卸載（offloading）。
- **優點**：跨平台（Mac、Linux、Windows）、單一檔案、高度可攜。
- **缺點**：比純 GPU 格式慢。

### EXL2 (ExLlamaV2)
- **部署**：僅限 GPU（Nvidia）。
- **優點**：**Nvidia GPU 上最快的 4-bit 格式**。相較於 AutoGPTQ/AWQ 有顯著的效能提升。
- **缺點**：缺乏彈性（僅限 Nvidia）。

---

## KV Cache 量化（VRAM 的節省利器）

在長上下文 RAG（1M+ tokens）中，**KV Cache** 消耗的 VRAM 往往比模型權重本身還多。

- **BF16 KV Cache**：2M tokens ≈ 32GB VRAM（在 8B 模型上）。
- **FP8/Int4 KV Cache**：2M tokens ≈ 8GB - 16GB VRAM。

**細節**：現代服務框架（vLLM、SGLang、TensorRT-LLM）現在支援 **串流量化（Streaming Quantization）**，KV cache 會被即時壓縮，使同一張 GPU 上的並行量提升 4 倍。

---

## 量化感知訓練 (QAT)

QAT 不是在模型訓練*之後*才量化（後訓練量化，Post-training Quantization），而是在訓練過程*中*模擬量化。
- **結果**：模型學會補償損失的精度。
- **現況**：對於小於 3B 參數的模型，這是讓它們在 4-bit 下仍然可用的必要手段。

---

## 面試題

### Q：為什麼 QLoRA 要用 NF4 而不是標準的 Float4？

**好的回答：**
標準 Float4 採用固定的網格，無法妥善對應到 LLM 權重的實際分布，後者通常服從以零為中心的常態分布。NF4 (NormalFloat4) 是一種在數學上經過最佳化的資料型別，讓每個量化區間（bin）都包含來自常態分布、數量相等的數值。這可以避免權重「群聚（clustering）」，並確保模型盡可能保留最多的資訊（熵），從而達到比標準 4-bit 整數明顯更高的準確度。

### Q：AWQ 與 GPTQ 有何不同？

**好的回答：**
GPTQ 是一種「逐層（Layer-wise）」量化方法，會最小化權重的均方誤差。AWQ (Activation-aware Weight Quantization) 則是「輸入感知（input-aware）」的。它會根據一次小型校正（calibration）執行中觀察到的實際 activation 數值，辨識出哪些權重最為「顯著（salient）」。透過僅將這些重要權重（通常為 1%）保留在較高精度、並量化其餘權重，AWQ 達到比 GPTQ 更好的 perplexity，尤其是在較小的模型或更激進的量化（例如 3-bit）情境下。

---

## 參考資料
- Dettmers et al. "QLoRA: Efficient Finetuning of Quantized LLMs" (2023)
- Frantar et al. "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers" (2022)
- Lin et al. "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration" (2023)

---

*下一篇：[推論基礎](../04-inference-optimization/01-inference-fundamentals.md)*
