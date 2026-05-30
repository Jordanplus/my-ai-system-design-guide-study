# LangSmith Observability

在 2023 年，LLM 的可觀測性還只是「記錄字串」。如今它已經演進成 **Full Trajectory Debugging（完整軌跡除錯）** 與 **Automated Evaluation Pipelines（自動化評估流水線）**。LangSmith 是這個競爭激烈的「LLMOps」層中由 LangChain 原生提供的選項，這一層還包括 Langfuse（於 2026 年 1 月被 ClickHouse 收購）、LangWatch、Braintrust 以及 Arize Phoenix。

## 目錄

- [可觀測性金字塔](#pyramid)
- [Tracing 與軌跡](#tracing)
- [LLM 的單元測試（Datasets）](#datasets)
- [自動化 Evaluators（LLM-as-Judge）](#evaluators)
- [管理部署：A/B Testing](#ab-testing)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## 可觀測性金字塔

1. **頂層（價值）**：使用者的任務有沒有被完成？（Success Rate）
2. **中層（流程）**：哪一個 agent node 是瓶頸？（每個 node 的 Latency/Cost）
3. **底層（原始資料）**：實際的 prompt/completion 配對到底是什麼？（Traces）

---

## Tracing 與軌跡

LangSmith 會自動擷取 **LangGraph** 或 **Chain** 中的每一個 node。
- **Metadata Tagging**：為每一筆 trace 標記 `user_id`、`model_tier` 與 `is_canary`。
- **The Debugger**：你可以在 LangSmith UI 中「重播（Play back）」一筆 trace，修改 prompt 並觀察回應如何改變。這個過程不需要重新執行整個應用程式。

---

## LLM 的單元測試（Datasets）

在沒有 **Dataset** 的情況下建構 LLM 應用程式，等於是「憑感覺開發（vibe-based development）」。
- **Gold Standard Datasets**：一組 `(Input, Expected_Output)` 配對的集合。
- **標準工作流程**：每當使用者提供負面回饋時，該次互動就會自動被匯入一個「Correction Dataset」，供未來測試使用。

---

## 自動化 Evaluators

你不可能每天早上手動檢查 1,000 筆 log 紀錄。
- **LLM-as-Judge**：使用更強的模型（Claude Opus 4.7、GPT-5.5 reasoning、DeepSeek-R2）來針對 **Tone（語氣）**、**Accuracy（準確度）** 與 **Safe Action execution（安全動作執行）** 等類別，為 production 模型評分。
- **Custom Evaluators**：用來檢查 regex 樣式、JSON schema 有效性或 Toxicity 分數的 Python 函式。

---

## A/B Testing

LangSmith 支援 **Experiment Branching（實驗分支）**。
- 將 2% 的流量導向新的「System Prompt」版本。
- 即時比較 **Success Rate** 與 **Token Cost**。
- 當失敗率超過門檻時自動回滾（roll back）。

---

## 面試題

### Q：為什麼「Trace Attribution（軌跡歸因）」對 Staff 等級的工程師至關重要？

**好的回答：**
在複雜的 multi-agent 系統中，最終輸出可能很糟，但錯誤其實發生在 10 個步驟之前的某個「Researcher」node。如果沒有 **Trace Attribution**，你只是在猜要去哪裡修改 prompt。歸因讓我能看到 **Line of Reasoning（推理脈絡）**。我可以看到「Researcher」沒有找到正確的 URL，進而導致「Summarizer」產生幻覺。這讓我能進行 **Targeted Optimization（針對性最佳化）**，而不是大範圍地「Prompt Engineering」。

### Q：你如何說服別人接受像 LangSmith 這類可觀測性平台的成本？

**好的回答：**
這個成本會被 **Developer Productivity（開發者生產力）** 與 **Token Efficiency（Token 效率）** 所抵銷。一位工程師花一整天「猜測」模型為何失敗，成本遠高於每月的訂閱費用。此外，透過使用 LangSmith 找出「Meandering（兜圈子）」的 agent（也就是步驟過多的那些），我可以最佳化 graph，把平均步驟數從 8 步降到 5 步，這會直接帶來 **30-40% 的 LLM API 帳單下降**。

---

## 參考資料
- LangChain Team. "LangSmith: The Unified Evaluation Platform" (2025)
- Microsoft. "Tracing and Debugging Multi-Agent Systems" (2025)
- Weights & Biases. "Integrating LLOps into the CI/CD Pipeline" (2024/2025)

---

*下一篇：[LlamaIndex and Data-Centric AI](04-llamaindex.md)*
