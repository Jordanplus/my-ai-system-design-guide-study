# Few-Shot 與情境學習（ICL）

情境學習（In-Context Learning，ICL）是 LLM 僅憑 prompt 中的範例就能學會新任務、而無需任何權重更新的能力。最大化 ICL 的效率是維持 prompt 穩定性的關鍵槓桿。

## 目錄

- [Few-Shot 範例的剖析](#anatomy)
- [需要幾個範例？](#how-many)
- [動態範例選取](#dynamic-selection)
- [標註細膩度的重要性](#labelling)
- [進階 ICL：類比與 Retraining-lite](#advanced-icl)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## Few-Shot 範例的剖析

一個高品質的範例由三個部分組成：
1. **輸入（Input）**：一份貼近真實的潛在使用者資料樣本。
2. **推理（Reasoning，選用）**：簡短說明輸出之所以如此的*原因*。
3. **輸出（Output）**：「黃金標準（Gold Standard）」結果。

```markdown
User: "The weather is okay, but the flight was late."
Reasoning: The user is neutral about the weather but negative about the service.
Sentiment: Mixed
```

---

## 需要幾個範例？

| 模型規模 | 最佳區間 | 擴展行為 |
|------------|------------|------------------|
| **小型（8B）** | 5 - 10 | 收益會持續到約 20 個範例為止。 |
| **中型（70B）**| 3 - 5 | 很早就趨於飽和；範例越多，延遲越高。 |
| **前沿（405B）**| 1 - 2 | 能力極強；通常「指令遵循（Instruction Following）」就足夠。 |

**經驗法則**：如果你需要超過 20 個範例才能得到穩定的輸出，那麼這個任務對該模型而言很可能太複雜，或者你應該考慮 **Fine-tuning**。

---

## 動態範例選取

在正式環境的 RAG 或分類任務中，不要對每位使用者都使用同一組靜態範例。
**動態模式：**
1. 使用者提供一個查詢。
2. 在「黃金範例的 Vector DB」中搜尋 3 個語意上最**相似**的案例。
3. 將那 3 個特定案例注入 prompt 中。

**結果**：準確率大幅提升，因為模型看到的是與當前使用者相關的「在地（local）」模式。

---

## 標註細膩度的重要性

前沿模型對範例中的**分佈偏差（Distribution Bias）**很敏感。
- 如果你提供 5 個「正面」範例與 1 個「負面」範例，模型就會偏向「正面」。
- **修正方法**：務必使用**標籤平衡（Label Balancing）**。確保你的 few-shot 範例大致反映預期的輸出分佈，或是達到完美平衡（1:1）。

---

## 進階 ICL：類比與「Few-Shot CoT」

**類比式 prompting（Analogy Prompting）**：與其說「做 X」，不如提供一個類比。
「翻譯這段程式碼時，要像譯者把一首詩從法文移譯成英文那樣——保留靈魂（邏輯）但改變語法。」

**Few-Shot CoT**：提供 2 個推理過程明確寫出來的範例。這會「引導（prime）」模型的注意力，使其聚焦於邏輯，而不只是模仿輸出字串。

---

## 面試題

### Q：為什麼不乾脆把我們手上全部 50 個範例都放進 prompt？

**有力的回答：**
主要有三個原因：
1. **情境窗延遲（Context Window Latency）**：每個範例都會增加 token，拉長「Prefill」時間並提高每次請求的成本。
2. **注意力稀釋（Attention Dilution）**：即使有 128k 的 context，當特定限制被埋沒在過多無關資料底下時，模型仍可能「弄丟」這些限制（即「lost-in-the-middle」效應）。
3. **過度擬合（Overfitting）**：提供過多狹隘的範例，可能導致模型過於嚴格地模仿範例的*格式*，反而喪失處理這組範例之外邊緣案例的通用能力。

### Q：情境學習中的「標籤偏差（Label Bias）」是什麼？

**有力的回答：**
標籤偏差是指：模型之所以更頻繁地預測某個特定標籤，僅僅是因為該標籤在 few-shot 範例中出現得較多，或是因為它出現在清單的尾端。標準的緩解方法有：
1. 針對不同請求打亂範例的順序。
2. 確保正面／負面／中性樣本的數量相等。
3. 在 prompt 開發階段使用「排列測試（Permutation Testing）」，以確保模型是回應內容、而非順序。

---

## 參考資料
- Brown et al. "Language Models are Few-Shot Learners" (2020)
- Min et al. "Rethinking the Role of Demonstrations: What Makes In-Context Learning Work?" (2022)

---

*下一篇：[Chain-of-Thought](03-chain-of-thought.md)*
