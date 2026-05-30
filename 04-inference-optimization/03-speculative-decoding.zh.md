# Speculative Decoding

Speculative decoding 是一項如今已成為標準的技術，它讓大型模型（LLMs）能在單次 forward pass 中產生多個 token，有效突破了循序解碼（sequential decoding）所受的記憶體頻寬瓶頸。

## 目錄

- [核心概念](#the-core-concept)
- [Draft-Verify 範式](#draft-verify)
- [Medusa 與多 Token Heads](#medusa)
- [Lookahead Decoding](#lookahead-decoding)
- [硬體感知的推測](#hardware-aware)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 核心概念

LLM 解碼受限於記憶體（memory-bound）：為了產生單一個 2-byte 的 token 而載入 140GB 的權重（70B 模型）是非常沒有效率的。
**Speculative Decoding** 使用一種較廉價的方法來「猜測」接下來的 $N$ 個 token，再用大型模型在單次平行的「Prefill 式」pass 中一次驗證全部。

---

## Draft-Verify 範式

1. **草擬（Drafting）**：一個小而快的「Draft Model」（例如 1B 或 7B）產生 $K$ 個候選 token。
2. **驗證（Verification）**：大型的「Target Model」一次處理全部 $K$ 個 token。
3. **接受（Acceptance）**：利用 target model 的 logits 來接受或拒絕候選 token。若 token $i$ 被拒絕，則其後的所有 token 都會被丟棄。

| 模型 | 大小 | 速度 | 每個 token 的延遲 |
|-------|------|-------|-------------------|
| **Draft** | 1B | 快 | 5ms |
| **Target**| 70B| 慢 | 50ms |
| **Speculative**| - | **快**| **15ms - 25ms** |

**最終結果**：在實際耗用時間（wall-clock time）上達到 2x 至 3x 的加速，且**品質完全沒有損失**。

---

## Medusa 與多 Token Heads

業界已逐漸捨棄獨立的 draft model（會增加 VRAM 負擔），轉而採用 **Medusa Heads**。

- **它是什麼**：附加在 target model 最後一層上的額外「heads」（小型線性層）。
- **運作方式**：它不只預測 token $t+1$，而是由 Head 1 預測 $t+1$、Head 2 預測 $t+2$，依此類推。
- **效益**：不需要第二個模型；以極小的 VRAM 增加換取 2.5x 的加速。

---

## Lookahead Decoding

另一種替代做法，它利用模型自身過去的 hidden states 來尋找重複出現的模式（n-grams），藉此「向前看」並預測未來的 token。
- **最適用於**：結構化資料、程式碼，以及高度重複的技術寫作。

---

## 硬體感知的推測

前沿的服務框架（vLLM、TensorRT-LLM）如今會使用**動態草擬長度（Dynamic Draft Lengths）**。
- 若 GPU 使用率偏低（小 batch），系統會增加草擬 token 的數量（$K$）。
- 若 GPU 已飽和（大 batch），則會減少 $K$，以優先確保吞吐量而非個別請求的延遲。

---

## 面試問題

### Q：為什麼 Speculative Decoding 對高溫度（high-temperature）的創意寫作效果不佳？

**有力的回答：**
Speculative decoding 依賴「Draft Model」能準確預測「Target Model」會說出什麼。在高溫度的創意寫作中，機率分布較為「平坦」，模型也被鼓勵去挑選較不可能的 token。這會導致非常低的**接受率（Acceptance Rate）**（draft model 的猜測經常被拒絕）。當猜測被拒絕時，target model 的平行 pass 就成了浪費掉的運算，系統會退回標準的循序解碼，反而增加了 draft model 延遲所帶來的額外開銷。

### Q：Medusa 與傳統的 Speculative Decoding 有何不同？

**有力的回答：**
傳統的 speculative decoding 需要一個獨立、較小的模型（Draft Model），它會佔用額外的 VRAM，並需要自己的 KV cache 管理。相對地，Medusa 是在基礎模型的最終 hidden state 上加上多個「heads」。每個 head 都被訓練去預測不同的偏移量（例如：下一個 token、next+1、next+2）。這消除了對第二個模型的需求，並將步驟之間的通訊開銷降到最低，因為所有「猜測」都是在同一個基礎模型架構中、於單次 forward pass 內產生的。

---

## 參考資料
- Chen et al. "Accelerating Transformer Decoding via Speculative Decoding" (2023)
- Cai et al. "Medusa: Simple LLM Acceleration via Multiple Decoding Heads" (2024)
- Fu et al. "Lookahead Decoding" (2024)

---

*下一篇：[Batching Strategies](04-batching-strategies.md)*
