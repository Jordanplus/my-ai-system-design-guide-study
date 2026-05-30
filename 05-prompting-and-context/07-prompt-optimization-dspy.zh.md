# Prompt 最佳化（DSPy）

Prompting 已經從「手動調校」的時代邁向「程式化」的時代。**DSPy（Declarative Self-improving Language Programs）** 是建構穩健 LLM pipeline 的事實標準，其中的 prompt 是由演算法自動最佳化的。3.x 系列（DSPy 3.1.3 於 2026 年 2 月 5 日推出，並持續發布修補版本至 2026 年 5 月）導入了與 reasoning-native 模型更緊密的整合，以及更乾淨的 async runtime。

## 目錄

- [DSPy 的理念：Programming 與 Prompting 的對比](#philosophy)
- [Signatures 與 Modules](#signatures-modules)
- [Teleprompters（最佳化器）](#optimizers)
- [「Prompt 即權重」的類比](#prompt-as-weight)
- [Metric 驅動的最佳化](#metrics)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## DSPy 的理念：Programming 與 Prompting 的對比

在傳統的 prompting 中，更換模型（例如從 GPT-5.5 換成 Claude Sonnet 4.6 或 Llama 4）需要重新撰寫你所有的 prompt。
**DSPy 將邏輯（Logic）與格式（Formatting）分離。**

- **Logic（邏輯）**：由 **Modules** 定義（例如 ChainOfThought、ReAct）。
- **Optimization（最佳化）**：系統會自動為*特定*模型找出最佳的 prompt 與範例，以實現該邏輯。

---

## Signatures 與 Modules

你不必撰寫 prompt，而是定義一個 **Signature**：輸入是什麼，以及輸出應該是什麼。

```python
# Signature pattern
class MultiHopQA(dspy.Signature):
    """Answer questions that require multiple context retrievals."""
    context = dspy.InputField()
    question = dspy.InputField()
    answer = dspy.OutputField(desc="A concise 1-sentence answer")

# Logic is handled by a Module
qa_system = dspy.ChainOfThought(MultiHopQA)
```

---

## Teleprompters（最佳化器）

Teleprompters 是會反覆迭代你的程式以提升準確度的演算法。
1. **BootstrapFewShot**：自動為你的 prompt 找出高品質的範例。
2. **MIPROv2**：一種 Bayesian 最佳化器，它會嘗試不同的指令措辭，並挑選出能讓你的分數最大化的那一個。它仍是 3.x 系列中的旗艦最佳化器。

**為什麼這很重要**：你不再需要猜測「Be helpful」還是「Think carefully」哪個比較好。最佳化器會用資料來證明它。

---

## 「Prompt 即權重」的類比

在 DSPy 中，你的 prompt 就像是神經網路裡的權重。你不會「寫死」權重，而是去訓練它們。
- 如果你更換模型，你只需要**重新編譯（Re-compile，重新訓練）**你的程式即可。最佳化器會找出新模型更能理解的全新 few-shot 範例。

---

## Metric 驅動的最佳化

最佳化需要一個 **Metric**（一個會回傳分數的函式）。
- **Exact Match（完全比對）**：`prediction.answer == target.answer`
- **LLM-as-Judge**：使用較大的模型（Claude Opus 4.7、GPT-5.5 reasoning）來為較小模型（Llama 4 8B、Claude Haiku 4.5）的輸出評分。

---

## 面試問題

### Q：DSPy 如何解決 prompt engineering 的「脆弱性」問題？

**好的回答：**
DSPy 把「格式化」與「grounding」的複雜性從人身上移開，交給編譯器處理。當我們手寫 prompt 時，我們實際上是在「寫死」某種行為，而這種行為僅適用於某個特定模型、某個特定時間點（point-in-time tuning，特定時間點的調校）。一旦該模型被更新或被替換，prompt 就會失效。DSPy 把 prompt 視為一個可學習的參數。透過定義清楚的 **Signature** 與 **Metric**，我們讓系統能夠透過數千次模擬迭代去「搜尋」最有效的 prompt，使最終的系統對模型變動更具韌性。

### Q：在 DSPy 的脈絡下，「Teleprompter」是什麼？

**好的回答：**
Teleprompter 是一種程式化的最佳化器。它的工作是接收一個 DSPy 程式（可能是由多個 module 組成的複雜串接）以及一小組訓練範例，然後把它們「編譯」成最佳化後的版本。它的做法是產生候選的「thinking patterns（思考模式）」與範例，對照某個 metric 進行測試，並挑選出最有效的那些。簡而言之，Teleprompter 就是 prompt engineering 世界裡的「Gradient Descent（梯度下降）」。

---

## 參考資料
- Khattab et al. "DSPy: Compiling Declarative Language Models" (2023/2024)
- Stanford NLP. "DSPy Documentation and Tutorials" (2025)

---

*下一篇：[Prompt Injection 與防禦](08-prompt-injection-defense.md)*
