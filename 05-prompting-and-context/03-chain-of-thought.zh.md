# Chain-of-Thought (CoT)

Chain-of-Thought (CoT) 是一種促使 LLM 在給出最終答案前先產生中間推理步驟的技術。它已從一句簡單的 prompt 用語，演進為推理模型的核心架構特徵（o1、DeepSeek-R2、具備 extended thinking 的 Claude Opus 4.7、具備 extended thinking 的 GPT-5.5）。

## 目錄

- [CoT 革命](#cot-revolution)
- [Zero-Shot 與程式化 CoT 的比較](#zero-vs-programmatic)
- [「思考型」模型的興起（o1、DeepSeek-R1）](#thinking-models)
- [自我修正與驗證](#self-correction)
- [CoT 何時會失效（過度思考）](#over-thinking)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## CoT 革命

標準的 LLM 是「下一個 token 的預測器」。對於複雜的數學或邏輯問題，單次推理往往不足。CoT 為模型提供了一塊「草稿紙」（工作記憶），讓它得以逐步解決各個子問題。

**公式**：`Input -> Reasoning (Chain) -> Output`

---

## Zero-Shot 與程式化 CoT 的比較

| 技術 | 觸發語句 | 效率 | 使用情境 |
|-----------|----------------|------------|----------|
| **Zero-Shot CoT** | 「Let's think step by step.」 | 高 | 臨時性查詢。 |
| **Few-Shot CoT** | （提供帶有邏輯的範例） | 穩定性更高 | 正式環境的 pipeline。 |
| **程式化 CoT** | 「1. Analyze X. 2. Verify Y. 3. Resolve Z.」 | **最適合 Agent** | 複雜的多工具任務。 |

---

## 「思考型」模型的興起

像 **OpenAI o1/GPT-5.5 extended thinking**、**DeepSeek-R2** 以及 **Claude Opus 4.7** 這類模型，已透過強化學習（RL）將 CoT「內建」於模型之中。

1. **系統層級的 CoT**：模型不只是「印出」推理過程，而是擁有一個專屬的「思考視窗」。
2. **隱藏式 CoT**：在許多企業版中，推理鏈會對使用者隱藏，但系統仍可加以驗證，以防止 prompt injection 或「思路外洩」。
3. **Scaling Law**：這些模型遵循 **Inference Scaling Law**——它們「思考」得越久，就越能解決困難的問題（只要時間足夠，$o1$ 能解出 IMO 金牌等級的數學題）。

---

## 自我修正與驗證

正式環境的 pipeline 不再信任單一的 Chain-of-Thought。它們會加入一層 **Self-Verification（自我驗證）**。

```markdown
# Process
1. Generate Answer A via CoT.
2. Critique: "Are there any errors in the logic above?"
3. If errors: "Correct the logic and provide Answer B."
```

**細節**：這項做法如今已整合進用於編碼的 **Execution-Verified CoT**，模型會撰寫邏輯、執行程式碼，並在程式碼失敗時進行自我修正。

---

## CoT 何時會失效（過度思考）

CoT 並非萬靈丹。對於簡單的任務，它會帶來：
1. **延遲**：更多的 token = 更慢的回應。
2. **成本**：你要為每一個「思考」token 付費。
3. **過度思考**：模型可能會在根本不存在複雜性的地方臆造出複雜性（例如用三大段文字解釋為什麼 2+2=4）。

---

## 面試問題

### Q：為什麼 CoT 能提升模型在數學文字題上的表現？

**理想回答：**
CoT 之所以能提升表現，是因為它讓模型的運算複雜度與任務的邏輯複雜度相互對齊。在標準的單次生成中，模型必須根據有限的局部資訊去預測最終的答案 token。有了 CoT，模型會把問題「拆解」成一連串較小的自迴歸（auto-regressive）步驟。每一步都以前一步的輸出作為 context，讓模型的 attention 機制得以一次專注於一個子問題（例如先把蘋果相加，再把橘子相減），從而減輕單次預測所承受的「認知負擔」。

### Q：在延遲至關重要的正式環境中，你如何處理 CoT？

**理想回答：**
我們採用 **混合推理架構（Hybrid Reasoning Architecture）**：
1. **第一層（快速）**：用一個分類器判斷查詢是否需要深度推理。
2. **第二層（精簡版 CoT）**：我們以「Be concise in your reasoning」提示模型，或採用「Knowledge Distillation（知識蒸餾）」——訓練一個較小的模型，使其在受益於教師模型 CoT 式預訓練的同時，*只*產出最終答案。
3. **第三層（串流）**：我們把 CoT 串流給使用者（若採透明做法）或串流給某個背景程序，讓系統能在結果逐步出現時就開始對最終結果進行「預處理」。

---

## 參考資料
- Wei et al. "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" (2022)
- Wang et al. "Self-Consistency Improves Chain of Thought Reasoning in Language Models" (2023)
- OpenAI. "Learning to Reason with LLMs" (2024)

---

*下一篇：[Tree-of-Thought](04-tree-of-thought.md)*
