# 合成資料生成

整個產業已經撞上了「資料牆」(Data Wall),也就是網路上高品質人類文字已經耗盡。如今,合成資料已成為推動模型改進的主要引擎,坐落於每一套現代前沿模型訓練配方的核心。

## 目錄

- [資料牆與合成資料的轉向](#synthetic-shift)
- [Evol-Instruct 模式](#evol-instruct)
- [Constitutional AI 與自我修正](#constitutional-ai)
- [可驗證的合成資料(數學/程式碼)](#verifiable-data)
- [去偏見與多樣性](#diversity)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 「資料牆」之後:合成資料的轉向

前沿模型(Llama 4、GPT-5.5、Claude Opus 4.7、Gemini 3.1 Pro)是以 100T 以上的 token 訓練而成。人類文字根本不足以支撐這樣的規模擴張。
**現實狀況:** 前沿模型 fine-tuning 的訓練混合資料中,如今已有超過 **50% 是合成資料**(而 pretraining 則有 10%)。

| 來源 | 人類資料 | 合成資料 |
|--------|------------|----------------|
| **數量** | 固定(有限) | 無限 |
| **品質** | 不穩定(含雜訊) | 可控制(已淨化) |
| **成本** | 高(人類標註人員) | 低廉(推論/GPU) |
| **偏見** | 網際網路的鏡像 | 可手動平衡 |

---

## Evol-Instruct 模式

Evol-Instruct 是一種遞迴流程,讓 LLM 接收一條簡單的指令,並將其演化為更複雜的指令。

**演化的方向:**
1. **廣度 (Breadth)**:增加任務的數量。
2. **深度 (Depth)**:加入限制條件、複雜化因素,或多步驟邏輯。
3. **去雜訊 (De-noising)**:整理措辭,去除「AI 味」(AI-isms)。

```python
# Simple Instruction: "Write a function to add two numbers."
# Evolved Instruction: "Write a thread-safe Python class that performs 
# matrix addition with error handling and unit tests, adhering to PEP8."
```

---

## Constitutional AI 與 AI 回饋(RLAIF)

RLAIF 由 Anthropic 開發並在業界廣泛採用,它使用一套「憲法」(Constitution,即一組規則)來引導模型評估並改進它自己的資料。

**這個迴圈:**
1. **提案 (Propose)**:模型 A 產生一則回應。
2. **批判 (Critique)**:模型 B(憲法評審者)根據準則找出缺陷。
3. **修訂 (Revise)**:模型 A 根據批判產生更好的版本。
4. **訓練 (Train)**:最終的(Prompt, Revise)配對被加入 SFT 資料集。

---

## 可驗證的合成資料

合成資料最大的風險是**模型崩潰 (Model Collapse)**(模型學到了自己的錯誤)。
**2025 年的解法**:聚焦於那些不需要 LLM 就能驗證「真相」的領域。

- **數學**:使用形式化驗證(Lean/Isabelle)或 Python 執行來驗證答案。
- **程式碼**:讓產生的程式碼對測試案例執行(單元測試)。
- **RAG**:使用「黃金脈絡」(Gold Context)來產生那些答案明確存在於文字中的問題。

---

## 去偏見與多樣性

合成資料被用來「填補」人類資料中的缺口。
- **語言**:透過翻譯概念性的範本,為低資源語言(例如斯瓦希里語、馬拉地語)產生高品質文字。
- **邏輯**:為某個特定的邏輯謬誤建立 1,000,000 種變體,以「強化」模型抵禦它的能力。

---

## 面試問題

### Q:以合成資料進行訓練時,「模型崩潰」(Model Collapse)的風險是什麼?

**有力的回答:**
當模型以自己較早版本所產生的資料進行訓練時,就會發生模型崩潰。由於模型的分布比真實世界更狹窄(它對某些字詞與模式有偏好/偏見),訓練迴圈便成為一個錯誤與平庸不斷放大的「正回饋迴圈」。到了 2025 年,我們透過以下方式來緩解:
1. 混入 5-20% 的「黃金」(Golden)人類認證資料。
2. 使用「可驗證」(Verifiable)的獎勵(數學/程式碼),讓錯誤永遠不會被學習到。
3. 使用更強大的「教師」(Teacher)模型,為「學生」(Student)模型產生資料。

### Q:你如何確保一個 1000 萬筆資料的合成資料集的*品質*?

**有力的回答:**
我們使用一套**多階段過濾管線 (Multi-Stage Filtering Pipeline)**:
1. **語意去重 (Semantic Deduplication)**:使用 embedding 來移除近乎相同的叢集。
2. **LLM-as-Judge**:抽樣 1% 的資料,並讓一個更強的模型(例如 GPT-5.2)針對邏輯與安全性評分。
3. **困惑度過濾 (Perplexity Filtering)**:使用一個小型模型來計算文字的困惑度。如果太高(無意義)或太低(重複/簡單),就予以丟棄。
4. **可驗證執行 (Verifiable Execution)**:如果資料包含程式碼或數學,它必須通過本機編譯器/直譯器的檢查。

---

## 參考資料
- Xu et al. "WizardLM: Empowering Large Language Models to Follow Complex Instructions" (2023)
- Bai et al. "Constitutional AI: Harmlessness from AI Feedback" (2022)
- OpenAI. "Weak-to-Strong Generalization" (2023)

---

*下一篇:[量化深度解析](07-quantization-deep-dive.md)*
