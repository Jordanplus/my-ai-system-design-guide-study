# DSPy：對語言模型進行程式設計

**DSPy** 已成為高可靠性 AI 系統的業界標竿。它代表了一種典範轉移：從「Prompt Engineering」(反覆試錯) 轉向 **Prompt Compilation** (自動化最佳化)，而各項基準測試也一致顯示，相較於手動調校的 prompt，品質可提升 10-40%。

## 目錄

- [程式設計典範](#paradigm)
- [Signatures：描述任務](#signatures)
- [Optimizers 與 MIPROv2](#optimizers)
- [Assertions 與約束條件](#assertions)
- [管理模型漂移 (Model Drift)](#model-drift)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 程式設計典範

DSPy 把 LLM 應用視為一個**神經網路 (Neural Network)**。
- **The Module**：一個可重複使用的邏輯區塊 (例如 `ChainOfThought`)。
- **The Signature**：對模組行為的宣告式規格描述 (Input -> Output)。
- **The Optimizer**：一個依據指標，為模組找出最佳「權重 (Weights)」(也就是 Prompts) 的流程。

---

## Signatures：描述任務

你不必撰寫一段 100 行的 prompt，而是撰寫一個 **Signature**：
```python
class ResearchAssistant(dspy.Signature):
    """Answer the question by synthesizing the provided web context."""
    context = dspy.InputField(desc="Scraped web content")
    question = dspy.InputField()
    answer = dspy.OutputField(desc="A technical summary with citations")
```
**致勝的微妙之處**：Signatures 是 **Model-Agnostic (模型無關)** 的。你可以針對 Claude Opus 4.7、Claude Sonnet 4.6、GPT-5.5、Gemini 3.1 Pro 或 Llama 4 8B 進行編譯，而完全不需要更動任何一行程式碼。

---

## Optimizers 與 MIPROv2

**MIPROv2 (Multi-stage Instruction PRoposal Optimizer)** 是 DSPy 的旗艦級 optimizer。
1. **Instruction Proposal**：由一個「Assistant Model」針對該任務提出 10-20 種不同的系統 prompt 撰寫方式。
2. **Bayesian Optimization**：DSPy 將提出的這些 prompt 在一個小型訓練集上執行，並使用指標為其評分。
3. **Selection**：它會挑選出能讓你的指標最大化的 prompt (例如 Factuality 分數)。

---

## Assertions 與約束條件

DSPy 支援 **Hard 與 Soft Assertions**。
- `dspy.Suggest(...)`：若模型未通過某項檢查 (例如「答案必須少於 50 個字」)，DSPy 會**自動以失敗原因重新對模型下 prompt**，讓它自行修正。
- `dspy.Assert(...)`：若某項硬性約束被違反 (例如「不得包含 PII」)，執行便會中止並進入復原狀態。

---

## 管理模型漂移 (Model Drift)

當 OpenAI 或 Anthropic 釋出權重更新時，手工打造的 prompt 往往會失效。
- **2025 年的解法**：有了 DSPy，你只要**重新編譯 (Re-compile)** 即可。Optimizer 會為更新後的模型架構找出新的「最佳」tokens，毋須人力即可維持一致性。

---

## 面試問題

### Q：為什麼 DSPy 被視為「Anti-Prompt Engineering (反 Prompt Engineering)」？

**有力的回答：**
因為它以一個**最佳化迴圈 (Optimization Loop)** 取代了**人工反覆試錯的迴圈**。在 prompt engineering 中，人類就是那個 optimizer；而在 DSPy 中，人類是**老師 (Teacher)**。你定義*目標* (Signature) 與*評估方式* (Metric)，並提供幾個*範例*。框架接著會運用數學最佳化方法 (例如 Bayesian search) 來找出在統計上表現最佳的 tokens。這讓系統相較於一整個寫死字串的程式庫更具**可攜性 (Portable)** 與**可擴展性 (Scalable)**。

### Q：在正式環境 (production) 中使用 DSPy 最大的缺點是什麼？

**有力的回答：**
**Compilation Latency 與成本**。要編譯一條複雜的 DSPy pipeline，你可能需要執行 100-500 次 LLM 呼叫來測試不同的 prompt 變體。這是一筆可觀的前期成本。然而，對於 Staff 級別的工程師而言，這是一種**取捨 (Tradeoff)**：你在開發/編譯時間上付出較多，以換取**有保障的可靠性 (Guaranteed Reliability)** 與更低的**執行期失敗率 (Run-time Failure Rates)**。另一項挑戰則是學習曲線；它要求你像 ML 研究員一樣思考，而非像傳統開發者那樣。

---

## 參考資料
- Khattab et al. "DSPy: Compiling Declarative Language Model Calls" (2024/2025)
- Stanford NLP. "The MIPROv2 Technical Report" (2025)
- Databricks. "Productionizing Programmed Prompts" (2025)

---

*下一篇：[Semantic Kernel：企業級 AI](06-semantic-kernel.md)*
