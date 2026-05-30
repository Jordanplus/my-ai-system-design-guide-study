# RLHF 與 DPO（對齊）

對齊（Alignment）是確保 LLM 的行為符合人類價值觀與指令的過程。這個領域已從傳統的 RLHF 轉向更高效、更具擴展性的方法，例如 DPO 與 Online RL。

## 目錄

- [對齊問題](#the-alignment-problem)
- [RLHF：基礎](#rlhf-foundation)
- [DPO：Direct Preference Optimization](#dpo)
- [線上對齊](#online-alignment)
- [推理模型的對齊](#alignment-for-reasoning)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 對齊問題

預訓練模型「知識豐富但不受控制」。它們可能會：
1. 產生有害內容（安全性）。
2. 無法遵循指令（指令遵循）。
3. 嚴重產生幻覺（事實性）。

對齊會建立「Reward Model」與「Policy Update」來引導模型的行為。

---

## RLHF：基礎

從人類回饋中進行強化學習（Reinforcement Learning from Human Feedback，RLHF）包含三個步驟：
1. **SFT**：監督式微調（Supervised Fine-Tuning）。
2. **Reward Model（RM）**：在 `(Prompt, Winning_Response, Losing_Response)` 上訓練一個模型，以預測人類給出的分數。
3. **PPO（Proximal Policy Optimization）**：透過強化學習，利用 RM 為 LLM 提供「reward signal」。

**細微之處**：由於需要訓練獨立的 Reward Model 的額外開銷，加上 PPO 的不穩定性，傳統 RLHF 現在對大多數團隊而言被認為過於複雜／不穩定。

---

## DPO：Direct Preference Optimization

DPO 是業界標準。它消除了 Reward Model。

### 運作方式：
DPO 透過從偏好資料中直接以數學方式推導出最佳 policy，將 LLM 本身當作 Reward Model 來使用。
- **目標**：相對於一個固定的「reference model」，最大化「winning」回應的機率，並最小化「losing」回應的機率。

### 多階段對齊模式：
1. **Base SFT**：5k-10k 筆高品質樣本。
2. **DPO Step 1**：針對指令遵循進行對齊。
3. **DPO Step 2**：針對安全性與特定語氣進行對齊。

---

## 線上對齊

**Offline DPO 的問題**：它只能從靜態資料中學習。如果模型的能力超越了該資料的範圍，就會碰到天花板。

**解決方案：Online DPO（或 RLOO）**：
1. 模型針對一個 prompt 產生 4-8 個回應。
2. 一個 **Judge Model**（例如 GPT-5.5、Claude Opus 4.7）或一個 **Rule-based Reward**（例如程式碼執行）即時對這些回應排序。
3. 模型根據這個「Online」回饋立即更新其 policy。

---

## 推理模型的對齊（o1／DeepSeek-R1 風格）

對齊「思考型」模型需要從 **Response Preference** 轉向 **Process Preference**。

| 特性 | 標準對齊 | 推理對齊 |
|---------|-------------------|---------------------|
| Reward 目標 | 最終答案 | **思維鏈（Chain of Thought, CoT）** |
| Reward Signal | 有幫助／安全 | **正確性 + 簡潔性** |
| 方法 | 人類排序 | Rule-based（例如「這段程式碼有跑起來嗎？」） |

**Principal 等級的細微之處**：「Verification-based RL」是當今前沿模型的秘訣。我們不再由人類來說明哪個比較好，而是使用可硬性驗證的結果（數學答案、程式碼測試案例）作為 reward signal。

---

## 面試問題

### Q：為什麼 DPO 經常比 RLHF／PPO 更受青睞？

**有力的回答：**
DPO 之所以受青睞，主要是因為它的簡單性與穩定性。PPO 需要在記憶體中同時維護四個模型（Policy、Reference、Value 與 Reward），這對 VRAM 的需求極高。此外，PPO 對超參數出了名地敏感，且經常出現「reward hacking」或突然崩潰的情況。DPO 將對齊視為在偏好配對（preference pairs）上的一個簡單分類問題，使其更為穩健、更容易調校，且執行成本顯著更低。

### Q：「Alignment Tax」的風險是什麼？

**有力的回答：**
「Alignment Tax」指的是模型在針對安全性或特定人格進行對齊之後，其原始能力（例如程式設計、創意寫作或邏輯推理）出現的衰退。由於模型被迫優先考量安全性或對特定風格的遵循，它可能會變得「過於謹慎」，或失去在預訓練期間學到的細膩之處。**Steerable Alignment** 與 **DPO-with-KL-penalty** 等現代技術，其目標便是透過確保模型的 policy 不會偏離原始預訓練分布太遠，來將這種影響降到最低。

---

## 參考資料
- Rafailov et al. "Direct Preference Optimization: Your Language Model is Secretly a Reward Model" (2023)
- Schulman et al. "Proximal Policy Optimization Algorithms" (2017)
- OpenAI. "Learning to Reason with LLMs" (2024)

---

*下一篇：[Knowledge Distillation](05-knowledge-distillation.md)*
