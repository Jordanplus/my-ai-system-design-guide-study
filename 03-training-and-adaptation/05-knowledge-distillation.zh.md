# 知識蒸餾（Knowledge Distillation）

知識蒸餾是將智慧從一個龐大、複雜的模型（「老師」）轉移到一個更小、更高效的模型（「學生」）的過程。這正是當今小型 open-weight 模型能展現出遠超其參數量的高效能背後的秘訣。

## 目錄

- [老師－學生範式](#teacher-student-paradigm)
- [蒸餾如何運作](#how-distillation-works)
- [特徵蒸餾 vs. 輸出蒸餾](#feature-vs-output)
- [從證明進行自我蒸餾（SDP）](#self-distillation-proof)
- [量化感知蒸餾](#quantization-aware-distillation)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 老師－學生範式

小型模型（例如 Llama 4 8B、Gemini 3.1 Flash、Claude Haiku 4.5）並不是單純在原始網路資料上訓練出來的。它們是在由一個更大型的模型（例如 GPT-5.5、Claude Opus 4.7 或 Llama 4 405B）所生成或精選的 **合成資料（Synthetic Data）** 上訓練的。

| 模型 | 角色 | 智慧來源 |
|-------|------|---------------------|
| **老師（Teacher）** | 大型（100B+ 參數） | 在 50T+ tokens 上進行預訓練 |
| **學生（Student）** | 小型（1B - 8B 參數） | 老師經過過濾的邏輯／輸出 |

---

## 蒸餾如何運作

### 1. 硬標籤蒸餾（Hard Label Distillation）
學生從老師的最終預測（例如某個問題的答案）中學習。

### 2. 軟標籤蒸餾（Soft Label Distillation，溫度縮放）
學生從老師的 **機率分布**（Logits）中學習。這蘊含豐富得多的資訊，因為它不只告訴學生正確答案，還告訴它哪些錯誤答案「差一點」就是對的。

```python
# Distillation Loss (KL Divergence):
Loss = KL_Div(Teacher_Logits / T, Student_Logits / T)
```
*其中 T 是溫度（Temperature，通常為 2.0 - 5.0）。*

---

## 特徵蒸餾 vs. 輸出蒸餾

### 輸出蒸餾（標準做法）
學生去匹配老師的文字回應。
- **優點**：可透過 API 輕鬆實作。
- **缺點**：只學到行為上的表層模式。

### 特徵／隱藏狀態蒸餾（Feature/Hidden State Distillation）
學生去匹配老師內部的 **隱藏狀態（Hidden States）**（向量表示）。
- **要求**：你需要能存取老師的權重（Open Weights）。
- **優點**：學生學到的是老師的「內部概念地圖」，從而帶來深得多的推理能力。

---

## 從證明進行自我蒸餾（SDP）

**推理能力的重大突破。**
像 o1、DeepSeek-R1 與 Claude Opus 4.7 這類模型都使用 SDP 來在沒有新的人類資料下持續進步。

1. **生成（Generation）**：模型針對一道困難的數學／程式問題生成 100 個可能的解法。
2. **驗證（Verification）**：一套以規則為基礎的系統（編譯器／計算機）找出其中 1 個正確的解法。
3. **蒸餾（Distillation）**：模型針對導向該正確解法的「思維鏈」（Chain of Thought, CoT）進行 fine-tuning。

**結果**：模型透過只保留高品質的推理路徑來「對自己進行蒸餾」。

---

## 量化感知蒸餾

標準量化（例如 16-bit 轉 4-bit）會造成準確度的小幅下降。
**解法**：在量化過程 *當中* 使用知識蒸餾。16-bit 模型扮演老師的角色，引導 4-bit 模型將其誤差降到最低。這正是現代 4-bit 模型能達到 16-bit 效能的方法。

---

## 面試問題

### Q：為什麼蒸餾出來的 8B 模型，會比在相同 tokens 上從零開始訓練的 8B 模型更好？

**優秀回答：**
在原始網路資料上從零開始訓練（預訓練）充滿雜訊；模型會耗費大量容量去學習如何在這些雜訊中找出方向。然而，蒸餾過的模型是在一套「純化過」的課程上訓練的。老師模型扮演高品質的過濾器，提供結構化的邏輯、清楚的解釋，以及更乾淨的語言分布。本質上，老師透過它的 logit 分布提供「提示」，明確告訴學生語言中哪些特徵是最重要、最該學習的。

### Q：使用 GPT-4o 作為老師來蒸餾一個 Llama 學生，會有哪些風險？

**優秀回答：**
1. **模型崩塌（Model Collapse）**：如果學生只看到老師的輸出，它可能會失去創意或多元知識的「長尾」，只學到老師那狹隘的偏誤。
2. **授權違規（License Violations）**：大多數專有模型（OpenAI、Anthropic）都有條款，禁止使用其輸出來訓練「競爭」模型。對於想從 API 輸出蒸餾出自家模型的企業來說，這是重大的法律風險。
3. **語言模仿（Linguistic Mimicry）**：學生可能學會「聽起來」很自信（像老師一樣），卻不具備同等程度的邏輯深度，導致雖然自信但卻是錯誤的幻覺（hallucinations）。

---

## 參考資料
- Hinton et al. "Distilling the Knowledge in a Neural Network" (2015)
- Gou et al. "Knowledge Distillation: A Survey" (2021)
- DeepSeek. "DeepSeek-R1: Incentivizing Reasoning Capability" (2025)

---

*下一篇：[合成資料生成](06-synthetic-data-generation.md)*
