# Tree-of-Thought (ToT)

Tree-of-Thought (ToT) 是一種進階的 prompting 架構，模型會探索多條推理路徑、評估它們，並在某條路徑走入死胡同時「回溯 (backtrack)」。它是現代自主研究代理 (autonomous research agents) 背後的藍圖。

## 目錄

- [樹 vs. 鏈](#tree-vs-chain)
- [ToT 迴圈：提議、評估、搜尋](#tot-loop)
- [自我修正與回溯](#self-correction)
- [MCTS 與 Search-as-Service](#mcts)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 樹 vs. 鏈

**Chain-of-Thought** 是線性的（單一路徑），而 **Tree-of-Thought** 則允許分支。

| 特性 | Chain-of-Thought | Tree-of-Thought |
|---------|------------------|-----------------|
| **拓撲結構** | 線性（1 條路徑） | 分支（多條路徑） |
| **邏輯** | 循序 | 平行 + 可評估 |
| **自我修正**| 低（承諾偏誤 commitment bias） | 高（回溯） |
| **使用情境** | 數學、簡單邏輯 | 解謎、程式架構、策略規劃 |

---

## ToT 迴圈：提議、評估、搜尋

一個 ToT 系統由三個模組組成：
1. **Thought Proposer（思路提議器）**：為某個問題生成 3-5 個潛在的「下一步」。
2. **State Evaluator（狀態評估器）**：為每一步評分（例如「Good」、「Maybe」、「Impossible」）。
3. **Search Algorithm（搜尋演算法）**：（BFS 或 DFS）用以決定接下來要探索哪條分支。

```python
# The ToT logic (Simplified):
For each branch:
   Score = Evaluate(branch)
   If Score < Threshold:
      Prune branch (Backtrack)
   Else:
      Continue exploring
```

---

## 自我修正與回溯

ToT 是專門設計用來克服**幻覺串連 (Hallucination Cascades)** 的。
在一條線性的鏈中，如果模型在第 1 步犯了錯，後續每一步都很可能跟著出錯。在 ToT 中，「Evaluator」（可以是另一個模型，或是基於規則的檢查）會在第 1 步就抓到錯誤，並強迫模型嘗試不同的起點。

---

## MCTS 與 Search-as-Service

ToT 已演化為適用於 LLM 的 **Monte Carlo Tree Search (MCTS)**。
- **搜尋時運算擴展 (Search-time Compute Scaling)**：我們不使用單一的大型 prompt，而是用 100 個小型 prompt 來「搜尋」最佳答案。
- **RAD-T (Reasoning-as-Data-Tree)**：專門的「Searcher」模型（Gemini 3.1 Pro Deep Think、GPT-5.5 extended thinking、Claude Opus 4.7）原生就被訓練來管理這些分支。

---

## 面試問題

### Q：ToT 在什麼情況下會明顯優於單純的 CoT？

**強力回答：**
當問題具有「龐大的搜尋空間」且需要「全域一致性 (global consistency)」時，ToT 就更為出色。舉例來說，在一次複雜的軟體重構中，單一的 Chain-of-Thought 可能一開始進展順利，卻在 10 步之後撞上約束衝突。有了 ToT，模型可以提議 3 種不同的重構模式，評估每一種對程式庫的影響，並在動手寫任何程式碼之前就捨棄那些會導致循環相依 (circular dependencies) 的模式。

### Q：Tree-of-Thought 在面向消費者的應用中，主要的缺點是什麼？

**強力回答：**
主要缺點是**指數級的成本與延遲 (Exponential Cost and Latency)**。探索 3 條分支至深度 5，可能需要 15-20 次個別的 LLM 呼叫。在消費者應用中，這對單一查詢可能造成 30 秒的延遲與 $0.50 的成本。標準的緩解作法是採用「混合模型 (Hybrid Model)」：將 ToT 用於高風險的離線任務（例如生成黃金資料集或安全稽核），並將那些結果蒸餾 (distill) 成一個快速、線性的模型，供即時互動使用。

---

## 參考資料
- Yao et al. "Tree of Thoughts: Deliberate Problem Solving with Large Language Models" (2023)
- Silver et al. "Mastering the Game of Go without Human Knowledge" (MCTS inspiration)

---

*下一篇：[Context Engineering](05-context-engineering.md)*
