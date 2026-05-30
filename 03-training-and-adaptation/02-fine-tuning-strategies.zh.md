# Fine-Tuning 策略

Fine-tuning 讓預訓練模型能適應特定任務、領域或風格。如今，fine-tuning 比較不是在「教導事實」，而更像是在「教導格式與行為」。

## 目錄

- [何時該做 Fine-Tuning](#when-to-fine-tune)
- [Supervised Fine-Tuning (SFT)](#supervised-fine-tuning)
- [Continued Pretraining（領域適應）](#continued-pretraining)
- [Instruction Tuning](#instruction-tuning)
- [PEFT 與全參數比較](#peft-vs-full-parameter)
- [超參數調校](#hyperparameter-tuning)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 何時該做 Fine-Tuning

在進行 fine-tuning 之前，先問自己：**這個問題能否用 Prompt Engineering 或 RAG 解決？**

| 需求 | 較佳解法 | 原因 |
|-------------|-----------------|-----|
| 新的事實／知識 | **RAG** | LLM 不擅長透過 FT 記憶事實；RAG 更容易更新。 |
| 特定輸出格式 | **Fine-Tuning** | 讓模型在不需要複雜 prompt 的情況下，穩定輸出 JSON/XML。 |
| 語氣／人格 | **Fine-Tuning** | 比 system prompt 一致性高得多。 |
| 降低延遲 | **Fine-Tuning** | 減少對長 few-shot prompt 的需求。 |
| 私有領域語言| **Continued Pretraining** | 教導專業詞彙（醫療、法律、自訂程式碼）。 |

---

## Supervised Fine-Tuning (SFT)

預訓練之後的第一步。模型會以 `(Prompt, Response)` 配對進行訓練。

### 品質的階層
**1,000 筆「完美」範例勝過 1,000,000 筆充滿雜訊的範例。**
- **Golden Sets：** 由領域專家手工精選（技術任務需要博士等級的專業）。
- **Negative Constraint Training：** 納入模型**不應**做什麼的範例（例如「不要道歉」、「不要提到你是 AI」）。

---

## Continued Pretraining（領域適應）

也稱為「第二階段預訓練（Second-stage Pretraining）」。
- **作法**：以特定領域的原始文字進行訓練（例如，為金融模型訓練所有的 SEC filing）。
- **目標**：學習該領域語言的統計分佈。
- **細節**：需要遠低於原始的 learning rate（約為原本的 1/10），以避免「災難性遺忘（catastrophic forgetting）」。

---

## PEFT 與全參數比較

| 特性 | 全參數 FT | PEFT (LoRA, QLoRA) |
|---------|-------------------|--------------------|
| GPU VRAM | 非常高（模型大小 * 4-12） | 低（模型大小 * 1.5） |
| 速度 | 基準 | 快 2x-3x |
| 風險 | 高（災難性遺忘） | 低 |
| 部署 | 每個任務一個模型 | 一個 base model + 多個 adapter |
| **結論**| 保留給基礎模型訓練使用 | **正式環境的標準作法** |

---

## 超參數調校

### 1. Learning Rate (LR)
- **SFT**：標準範圍為 `1e-5` 到 `5e-5`。
- **過高**：模型會「崩潰」，開始重複輸出或胡言亂語。

### 2. LoRA 的 Rank (r)
- 複雜的推理任務使用較高的 rank（`r=64` 到 `r=256`）。
- 簡單的風格／語氣調整使用較低的 rank（`r=8`）。

### 3. 打包訓練 (Packing)
為了最大化吞吐量，我們會把多筆短範例「打包」進單一的 4k 或 8k 序列中，並以 EOS token 分隔。
- **挑戰**：self-attention 可能會在不同範例之間洩漏。
- **解法**：使用 **FlashAttention 搭配 block-masking**，避免跨範例的 attention。

---

## 面試問題

### Q：為什麼要用 Continued Pretraining，而不是直接把領域資料放進 SFT 資料集？

**出色的回答：**
就資料製作而言，SFT 是「昂貴」的——你需要 prompt/answer 配對。Continued Pretraining 則讓你能利用大量的原始、未標註領域文字，去教導模型的內部表徵理解專業詞彙與風格。一旦模型「會說這種語言」，你就能用一小組 SFT 資料集，教它在這種語言下執行「任務」（例如分類、摘要）。

### Q：你如何避免模型在 fine-tuning 過程中「遺忘」通用能力？

**出色的回答：**
這就是「災難性遺忘（Catastrophic Forgetting）」。主要有兩種緩解方式：
1. **Rehearsal：** 在你的 fine-tuning 資料集中混入 5-10% 的原始預訓練資料。
2. **PEFT (LoRA)：** 由於我們只訓練一小部分的權重，原始的「知識」仍凍結在 base model 的權重中，能大幅降低遺忘的風險。

---

## 參考資料
- Hu et al. "LoRA: Low-Rank Adaptation of Large Language Models" (2021)
- Ouyang et al. "Training language models to follow instructions" (InstructGPT, 2022)
- Dettmers et al. "QLoRA: Efficient Finetuning of Quantized LLMs" (2023)

---

*下一篇：[LoRA, QLoRA, and PEFT](03-lora-qlora-peft.md)*
