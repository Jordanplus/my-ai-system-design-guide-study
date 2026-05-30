# 結構化生成（Structured Generation）

結構化生成是強制 LLM 以機器可讀格式（JSON、YAML、CSV）輸出且達到 100% 可靠性的過程。這門技藝已經從「以 prompt 為基礎的請求」演進到「引擎層級的約束」。

## 目錄

- [JSON Mode 革命](#json-mode)
- [Function Calling 與 Tool Use](#function-calling)
- [約束式解碼（CFG 與 Regex）](#constrained-decoding)
- [多階段抽取模式](#multi-stage)
- [驗證與格式錯誤](#validation)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## JSON Mode 革命

在過去，要取得 JSON 是一場「只回傳 JSON，不要其他文字」的苦戰。
**標準做法**：使用原生的 `response_format: { type: "json_schema" }`（OpenAI/Gemini）或 tool-output schema（Anthropic）。

- **好處**：100% 的語法有效性。模型實際上無法輸出一個不是有效 JSON 的字串。
- **幕後原理**：服務引擎會在每一步遮罩（mask）詞彙表，確保下一步只能挑選有效的 JSON 字元（例如 `{`、`"`、`:`、`[`）。

---

## Function Calling 與 Tool Use

Function calling 是一種結構化生成，由 LLM「挑選」一個函式並填入其參數。

```json
// Example Tool Call
{
  "name": "get_stock_price",
  "arguments": { "symbol": "AAPL", "interval": "1d" }
}
```

**細節**：**Parallel Function Calling（平行函式呼叫）** 如今已是標準。模型可以決定同時呼叫 5 個不同的工具（例如查詢帳戶餘額、查詢信用評分、查詢貸款利率）並彙整結果。

---

## 約束式解碼（CFG 與 Regex）

對於自架的模型（Llama-cpp、透過 Outlines 的 vLLM），我們使用 **Context-Free Grammars（CFG，上下文無關文法）** 或 **Regex**。

```python
# Outlines Pattern
model = outlines.models.transformers("meta-llama/Llama-4-8B")
generator = outlines.generate.regex(model, r"(\d{3})-\d{3}-\d{4}")
# Result: The model can ONLY output telephone numbers.
```

---

## 多階段抽取模式

對於複雜的資料抽取（例如從一份病歷中抽出 50 個欄位），不要一次完成。
- **階段 1（Text-to-Text）**：以自然語言抽取一組「凌亂」但完整的事實。
- **階段 2（Text-to-JSON）**：使用一個較小、較便宜的模型，將這些自然語言事實轉換成嚴格的 JSON schema。
- **好處**：減少「壓力下的幻覺」——大型模型在被迫同時進行推理「並」遵循嚴格語法時會很吃力。

---

## 驗證與格式錯誤

即使使用了「JSON mode」，JSON 內部的**邏輯**仍可能出錯（例如某個欄位遺漏，或日期格式錯誤）。

**復原模式**：
1. 以 **Pydantic/Zod** 驗證輸出。
2. 如果驗證失敗，將 **Traceback** 回傳給模型：
   「Error: Field 'age' must be an integer, got 'twenty'. Fix and re-generate.」
3. 大多數模型會在第一次重試時就修正錯誤。

---

## 面試問題

### Q：為什麼「JSON Mode」會比以 prompt 為基礎的 JSON 請求更可靠？

**有力的回答：**
以 prompt 為基礎的請求仰賴模型遵循指令的*意願*；「JSON Mode」（或約束式解碼）則仰賴服務引擎的*無能為力*——它沒辦法做出其他選擇。透過在推論層級套用「Logit Bias」或「Grammar Mask」，引擎會把下一個 token 的選擇限制成只有那些依照 schema 才會有效的選項。這消除了「前言」（例如「當然，這是你的 JSON……」），並確保你絕不會因為高 temperature 或隨機性而得到格式錯誤的字串。

### Q：要求 LLM 一次輸出過多結構化欄位有什麼風險？

**有力的回答：**
在 **Schema 複雜度** 與 **資訊完整性** 之間存在權衡。隨著 schema 變大（例如 20 個以上的階層式欄位），模型的注意力會被維持 JSON 結構（括號、key、引號）所消耗，而非用於驗證資料的正確性。這往往會導致「遺漏型幻覺（Omission Hallucinations）」，模型會跳過欄位，或以佔位資料填入。緩解之道是採用「Chain-of-Density」抽取，或將抽取拆分成多個平行的子任務。

---

## 參考資料
- OpenAI. "Structured Outputs Documentation" (August 2024 update)
- Outlines Project. "Context-Free Grammar Guided Generation" (2024)
- Willard et al. "Efficient Guided Generation for LLMs" (2023)

---

*下一篇：[Prompt 最佳化（DSPy）](07-prompt-optimization-dspy.md)*
