# Prompt Engineering 基礎

Prompt engineering 是設計輸入以引導 LLM 行為的技藝。它已從「試誤法」演進為一套有紀律的架構實踐，像 DSPy 這樣的框架更將它視為一個編譯問題，而非寫作練習。

## 目錄

- [核心理念（意圖 + 限制）](#core-philosophy)
- [指令階層](#instruction-hierarchy)
- [角色 Prompting](#role-prompting)
- [指令清晰度與分隔符](#clarity)
- [Zero-Shot 與 Few-Shot 的效率比較](#zero-vs-few)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 核心理念：意圖 + 限制

有效的 prompting 關鍵在於最大化**意圖揭露（Intent Disclosure）**，同時最小化**輸出變異（Output Variance）**。

1. **意圖（Intent）**：精確地說明模型應該做什麼。
2. **限制（Constraint）**：明確指出模型應該*避免*什麼（安全性、語氣、格式）。

**原則**：「Prompting 就是用自然語言寫程式。」請把你的 prompt 當作程式碼對待（版本控制、單元測試）。

---

## 指令階層

正式環境（production）的系統會使用分層的訊息結構：

| 角色 | 職責 | 細節考量 |
|------|----------------|--------|
| **System** | 高階規則、人格設定、安全性。 | 對前沿模型最具黏著力（H-rank）。 |
| **Developer** | 技術性覆寫（例如格式）。 | 針對「無預設立場」模型的較新角色。 |
| **User** | 具體、動態的查詢。 | 易受注入攻擊；必須加以隔離。 |
| **Assistant**| 先前回合的歷史紀錄。 | 「近因偏誤（recency bias）」的來源。 |

---

## 角色 Prompting

指派人格不再只是「你是一位老師」。它是一個**能力錨點（Capabilities Anchor）**。

- **弱**：「你是一位程式設計師。」
- **強**：「你是一家一線科技公司的 Staff Software Engineer，專精於高併發的 Rust 系統。你重視記憶體安全（memory safety）與零成本抽象（zero-cost abstractions）。」

**為什麼有效**：它讓模型的注意力集中在與該高階專業相關的特定訓練資料子集上，從而減少不相關的幻覺。

---

## 指令清晰度與分隔符

當前的前沿模型能處理極為龐大的 context。分隔符（delimiters）能幫助模型區分指令與資料。

```markdown
# Instructions
Analyze the following text for PII.

# Data to Analyze
--- START OF USER DATA ---
$USER_INPUT_HERE
--- END OF USER DATA ---

# Output Schema
{ "pii_found": boolean, "types": [] }
```

**可使用的分隔符**：XML 標籤（`<context>`、`</context>`）、Markdown 標頭（`#`），或三引號（`"""`）。

---

## Zero-Shot 與 Few-Shot 的效率比較

| 面向 | Zero-Shot | Few-Shot |
|--------|-----------|----------|
| **延遲（Latency）** | 最低（prompt 較短） | 較高（範例佔用 token） |
| **準確度（Accuracy）**| 不穩定 | 高（格式穩定） |
| **使用情境（Use Case）**| 簡單對話、摘要 | 特定格式、細微邏輯 |

**策略**：如果模型屬於「前沿推理（Frontier Reasoning）」模型（Claude Opus 4.7、開啟 extended thinking 的 GPT-5.5、DeepSeek-R2），請使用 **Zero-Shot + 清晰的 Chain-of-Thought**。如果是小型模型（8B），則使用 **Few-Shot** 來為它建立基準。

---

## 面試問題

### Q：為什麼在現代 LLM 中，system prompt 比 user prompt 具有更高的權重？

**優秀回答：**
System prompt 通常會在模型的架構訓練（RLHF）中被優先處理，在某些架構中甚至可能被注入到一個專屬於「僅限指令」的 embedding 空間。從設計角度來看，system prompt 定義了這場互動的「憲法」。如果 user prompt 與 system prompt 相牴觸（例如要求製作炸彈的配方），一個對齊（aligned）良好的模型會被訓練成優先遵循 system 的「安全限制」，而非 user 的「任務意圖」。

### Q：什麼是「Step-by-Step」prompt 最佳化？

**優秀回答：**
在 2022 年，「Think step by step」是一句觸發 Chain-of-Thought（CoT）的魔法咒語。現代的做法是 **Programmatic CoT**。我們不再使用含糊的字句，而是提供明確的推理里程碑：「1. 找出核心問題。2. 列出限制條件。3. 提出 3 個解決方案。4. 選出最佳方案並說明理由。」這為模型內部的注意力提供了一條「確定性路徑」，使得針對正式環境 agent 的輸出可靠得多。

---

## 參考資料
- OpenAI. "Prompt Engineering Guide" (2024-2025)
- Anthropic. "Claude Prompt Engineering Documentation" (2024)
- Google DeepMind. "The Power of Prompting" (2023)

---

*下一篇：[Few-Shot 與 In-Context Learning](02-few-shot-and-icl.md)*
