# 預訓練基礎

預訓練是建構 LLM 過程中運算成本最高的階段，模型會在此階段從海量資料集中學習通用知識與語言模式。

## 目錄

- [預訓練目標](#the-pretraining-objective)
- [資料課程與品質](#data-curriculum-and-quality)
- [擴展法則（推論最佳化）](#scaling-laws)
- [運算需求](#computational-requirements)
- [訓練穩定性](#training-stability)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 預訓練目標

大多數現代 LLM 屬於 **Decoder-only** 架構，並採用 **Causal Language Modeling (CLM)**：

```python
# Objective: Minimize Cross-Entropy Loss
Loss = -sum(log P(token_i | token_1, ..., token_{i-1}))
```

模型會根據上下文預測下一個 token。這個看似簡單的目標，在足夠大的規模下會帶來湧現的推理能力。

---

## 資料課程與品質

關注焦點已經從「更多資料」轉移到「更好的課程」。

### 100T Token 的視野
前沿模型（Llama 4、GPT-5.5、Claude Opus 4.7、Gemini 3.1 Pro）以 15T 到 100T tokens 進行訓練。在這個規模下，**去重（Deduplication）** 與 **品質篩選（Quality Filtering）** 是主要的差異化因素。

### 資料混合標準
| 組成 | 百分比 | 用途 |
|-----------|------------|---------|
| 網頁（CommonCrawl） | 50-60% | 通用知識、多元風格 |
| 程式碼（Github、StackOverflow）| 15-20% | **對邏輯與推理至關重要** |
| 書籍（Project Gutenberg） | 10% | 敘事連貫性、長上下文 |
| 學術（ArXiv、PubMed） | 10% | 專業技術知識 |
| 合成資料（模型生成） | 5-10% | 數學、邏輯與特定的指令路徑 |

**細節：「程式碼效應」（The "Code Effect"）：**
研究顯示，在預訓練混合資料中增加程式碼比例，能夠透過教導模型結構化思考，提升其在**非程式碼**推理任務（例如數學、邏輯謎題）上的表現。

---

## 擴展法則：訓練最佳化 vs 推論最佳化

### Chinchilla 範式（2022-2024）
`Data Tokens (D) ≈ 20 * Parameters (N)`
以 70B 模型為例，這意味著約需 1.4T tokens。

### 推論最佳化範式
現代模型（Llama 3、Llama 4）相對於 Chinchilla 而言是**嚴重過度訓練（heavily overtrained）** 的。
- **為什麼？**：訓練成本只需支付一次；推論成本則要支付數十億次。
- **結果**：小型模型（8B）如今以 15T+ tokens 進行訓練，使其能力媲美較舊的 70B 模型，但服務成本卻便宜許多。

| 策略 | Token/參數比 | 最適用於 |
|----------|-------------------|----------|
| Chinchilla | 20:1 | 研究／概念驗證 |
| **推論最佳化** | **200:1 到 500:1**| 生產環境部署 |

---

## 訓練穩定性

在「超大」規模（100k+ GPU）下進行訓練會面臨巨大的穩定性問題。

### 1. 損失尖峰（Loss Spikes）
損失突然飆升，可能毀掉整次訓練。
- **標準解法**：**定期建立檢查點（Periodic Checkpointing）** 與**自動回滾（Automatic Rollbacks）**。
- **架構解法**：**Residual Scaling**（以特定方式初始化權重，使殘差分支從接近零的狀態開始）。

### 2. 精度：FP8 vs BF16
- **BF16**：2023-2024 年的穩定性標準。
- **FP8**：當前的生產環境標準。由 H100/B200 原生支援，可將記憶體用量減半並使吞吐量加倍，同時透過 **Stochastic Rounding** 維持訓練穩定性。

---

## 面試問題

### Q：如果 Chinchilla 認為 160B tokens 才是最佳值，為什麼要用 15T tokens 來訓練一個 8B 模型？

**優秀答案：**
Chinchilla 的最佳性著眼於如何最有效地運用固定的**訓練**運算預算。然而，在生產環境中，我們在意的是**總體擁有成本（Total Cost of Ownership, TCO）**，而這主要由推論主導。透過對小型模型進行過度訓練，我們把更多智慧「烘焙」進更少的參數裡。其結果是一個服務效率顯著更高（更高的 TPS、更低的 VRAM）、同時又能維持前沿等級品質的模型。

### Q：LLM 預訓練中的「課程（curriculum）」是什麼？

**優秀答案：**
課程指的是資料的順序與混合方式。一種常見的現代模式是：
1. **通用知識階段：** 80% 的 tokens（網頁、書籍）。
2. **推理聚焦階段：** 15% 的 tokens（程式碼、數學、邏輯）。
3. **高品質「冷卻」階段：** 最後 1-5% 的 tokens 是極高品質、經人工策劃或教科書等級的資料。這個「冷卻」階段有助於讓模型抖動更少，並在任何 fine-tuning 開始之前就能更好地遵循指令。

---

## 參考資料
- Kaplan et al. "Scaling Laws for Neural Language Models" (2020)
- Hoffmann et al. "Training Compute-Optimal Large Language Models" (Chinchilla, 2022)
- Meta AI. "The Llama 3/4 Herd of Models" (2024/2025)

---

*下一篇：[Fine-Tuning 策略](02-fine-tuning-strategies.md)*
