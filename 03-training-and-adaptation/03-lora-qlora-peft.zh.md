# LoRA、QLoRA 與 PEFT

參數高效微調（Parameter-Efficient Fine-Tuning, PEFT）是調整 LLM 的業界標準。本章涵蓋 LoRA 及其他 PEFT 方法的運作機制與進階變體。

## 目錄

- [PEFT 革命](#the-peft-revolution)
- [LoRA 運作機制](#lora-mechanics)
- [QLoRA：4-bit 微調](#qlora)
- [進階變體（DoRA、Vera、RS-LoRA）](#advanced-variants)
- [Multi-LoRA 服務（Adapters）](#multi-lora-serving)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## PEFT 革命

對大多數企業而言，對前沿模型（GPT-5.5、Claude Opus 4.7、Llama 4 405B）進行完整微調在經濟上並不可行。PEFT 帶來：
1. **記憶體效率**：在單張 A100 上訓練 70B 模型。
2. **速度**：僅更新 <1% 的權重，訓練速度提升 2 倍。
3. **模組化**：在共享的基礎模型上抽換「技能」（adapters），無需重新載入權重。

---

## LoRA 運作機制

LoRA（Low-Rank Adaptation，低秩適應）會將可訓練的秩分解矩陣注入 transformer 層中。

```python
# The LoRA Equation for a Weight Matrix W:
h = Wx + (BA)x * (alpha/r)
```
- **W**：預訓練權重（凍結，Gradient = None）
- **A, B**：LoRA adapters（可訓練）
- **r**：秩（rank，例如 8、16、64）
- **alpha**：縮放因子（通常為 2 * rank）

### 關鍵細節：Target Modules
過去我們只針對 query/value 投影（`q_proj`、`v_proj`）。
**現代標準**：針對**所有**線性層（`q, k, v, o, gate, up, down`），即使在較低的秩下也能達到最大的穩定性與效能。

---

## QLoRA：4-bit 微調

QLoRA 透過將基礎模型量化為 4-bit（NF4），同時維持 16-bit 梯度，進一步提升效率。

| 最佳化 | 方法 | 效益 |
|--------------|--------|---------|
| **NF4 量化** | Normalized Float 4 | 比標準 Int4 具有更佳的資訊密度 |
| **Double Quant** | 對量化常數再做量化 | 每個模型節省約 0.5 GB VRAM |
| **Paging** | Unified Memory（Nvidia） | 透過溢寫至 CPU RAM 來避免 OOM |

---

## 進階變體

### 1. DoRA（Weight-Decomposed Low-Rank Adaptation）
DoRA 將權重更新分解為**幅度（Magnitude）**與**方向（Direction）**。
- **結果**：學習速度比 LoRA 快 2 倍，且效能更接近完整微調。
- **致勝之處**：它讓模型能夠獨立地調整「要改變多少」與「要改變什麼」。

### 2. Vera（Vector-based Random Aggregation）
Vera 不使用低秩矩陣 `A` 與 `B`，而是採用固定的隨機投影搭配一個小型的可訓練向量。
- **效率**：相較於 LoRA，adapter 大小縮減 **10 倍**。
- **使用情境**：大規模的 Multi-LoRA 服務。

### 3. RS-LoRA（Rank-Stabilized LoRA）
使用 `alpha / sqrt(r)` 作為縮放因子。
- **效益**：讓你能夠提高秩（至 256+），而不會使模型變得不穩定，也不需要降低學習率。

---

## Multi-LoRA 服務（Adapters）

生產系統如今會服務單一基礎模型（例如 Llama 4 70B），並在同一個 batch 中動態抽換 adapters。

```python
# vLLM/LMCache Multi-LoRA Pattern:
# Request 1 -> Base + Finance_Adapter
# Request 2 -> Base + Legal_Adapter
# Request 3 -> Base + Medical_Adapter
```
**技術**：**Continuous Batching + PagedAttention v3** 讓你能夠服務 100+ 個 adapters，而延遲開銷相較於基礎模型僅增加 5-10%。

---

## 面試問題

### Q：為什麼 LoRA 的 alpha 參數通常設定為秩的 2 倍？

**優秀的回答：**
`alpha` 參數是 LoRA 更新的縮放因子。當我們初始化 LoRA 矩陣時，B 通常會初始化為零，而 A 為隨機值。在訓練過程中，更新的大小取決於秩 `r`。透過設定 `alpha=2r`（或任何常數），我們可以確保即使日後決定改變秩（例如從 8 改為 16），也無需重新調整學習率。縮放因子 `alpha/r` 會將更新幅度相對於學習率做正規化。

### Q：什麼是 DoRA？為什麼你會選擇它而非標準的 LoRA？

**優秀的回答：**
DoRA（Weight-Decomposed Low-Rank Adaptation）是 2024 年的一項技術，它將預訓練權重的更新拆分為幅度與方向兩個分量，類似於 Weight Normalization。標準 LoRA 會同時更新幅度與方向，而 DoRA 則讓它們能夠獨立學習。從實證結果來看，DoRA 展現出明顯更好的收斂性與更高的準確度，即使在低秩下也常能匹敵完整參數微調，因此成為高風險領域適應的首選。

---

## 參考資料
- Hu et al. "LoRA: Low-Rank Adaptation of Large Language Models" (2021)
- Liu et al. "DoRA: Weight-Decomposed Low-Rank Adaptation" (2024)
- Dettmers et al. "QLoRA: Efficient Finetuning of Quantized LLMs" (2023)

---

*下一篇：[RLHF 與 DPO](04-rlhf-and-dpo.md)*
