# 成本最佳化實戰手冊

AI 成本不再是「魔法」。它們是可量測、可預測，而且高度可最佳化的。隨著 API 定價在過去一年下降了 30-60%，成本槓桿如今主要關乎*路由（routing）*與*快取（caching）*，而不只是挑選一個更便宜的供應商。本章涵蓋在不犧牲品質的前提下，將推論成本降低 10 倍的各種策略。

## 目錄

- [AI 的單位經濟學](#unit-economics)
- [模型階梯（效率分層）](#model-cascading)
- [小型語言模型（SLM）](#slms)
- [Spot 執行個體策略](#spot-instances)
- [「Token 稅」最佳化](#token-tax)
- [面試題](#interview-questions)
- [參考資料](#references)

---

## AI 的單位經濟學

我們以**每美元能換得的 Token 數（Tokens per Dollar，$）**來衡量成功與否。

| 元件 | 成本驅動因子 | 最佳化方式 |
|-----------|-------------|--------------|
| **運算** | GPU 時間（$/hr） | 提升使用率（Batching）。 |
| **VRAM** | KV Cache 大小 | GQA、量化（Quantization）。 |
| **網路** | 酬載大小 | 壓縮、本地化服務。 |
| **API** | 按 token 計價 | 快取、模型選擇。 |

---

## 模型階梯（效率分層）

最有效的節省成本策略，就是使用**能勝任該任務的最便宜模型。**

**階梯模式：**
1. **分類器（Classifier）**：一個極小的模型（0.5B）判斷查詢的複雜度（$0.00）。
2. **Tier 1（SLM）**：90% 的查詢（問候語、簡單問答）交給 8B 模型處理（$）。
3. **Tier 2（前沿模型）**：9% 的查詢（複雜推理）交給 405B/Claude Sonnet 4.6/GPT-5.5/Gemini 3.1 Pro 等級的模型（$$$）。
4. **Tier 3（推理模型）**：1% 的查詢（專家級）交給如 Claude Opus 4.7 或啟用延伸思考（extended thinking）的 GPT-5.5 等思考型模型（$$$$$）。

**最終結果**：相較於將所有流量都送往 Tier 2，可降低 80% 的成本。

---

## 用於生產環境的小型語言模型（SLM）

3B-8B 的模型（Llama 4 8B、Gemini 3.1 Flash、Claude Haiku 4.5）如今在多數基準測試上，已能匹敵甚至勝過 2023 年最初的 GPT-4。
- **使用情境**：實體抽取、情感分析、簡單的 RAG。
- **成本**：執行成本比前沿模型便宜 100 倍。
- **延遲**：回應時間 < 100ms。

### DeepSeek V4 底價

DeepSeek V4 Flash（2026 年 4 月 24 日發布）以**每 1M tokens $0.14 / $0.28** 的價格，搭配 1M 的 context window，以及每 M $0.0028 的 cache-hit 輸入，重新訂下了便宜的前沿級推論的底價。在 75% 折扣於 2026 年 5 月 22 日轉為永久之後，DeepSeek V4 Pro 大約比 Claude Opus 4.7 便宜 10 倍（每 1M $0.435 / $0.87，相對於 $5 / $25）。對於前綴經常被重複使用的快取密集型、高流量工作負載（具備共享知識庫的 RAG、批次分類、程式碼庫代理），V4 Flash 或 V4 Pro 如今在你開始做階梯化之前，就已成為主導性的成本最佳化槓桿。在投入之前，請先到 [DeepSeek 定價頁面](https://api-docs.deepseek.com/quick_start/pricing) 確認。

---

## Spot 執行個體策略

對於非即時的工作負載（批次處理、資料抽取），請使用 **GPU Spot 執行個體**（AWS Spot、Azure Spot、Lambda Labs）。

- **風險**：GPU 可能在 30 秒通知後被收回。
- **緩解措施**：**即時 KV-Cache 遷移（Live KV-Cache Migration）**。一旦收到「收回訊號（Reclamation Signal）」，服務框架可以立即將進行中請求的 KV cache 串流到另一個節點，確保不會有任何工作遺失。

---

## 「Token 稅」最佳化

- **系統提示快取（System Prompt Caching）**：把常見的前綴寫死，以獲得 90% 的折扣。
- **輸出截斷（Output Truncation）**：嚴格限制 `max_tokens`。
- **負向提示（Negative Prompting）**：「別太囉嗦」可節省約 15% 的輸出 token（因而降低成本）。

---

## 面試題

### Q：你如何向 CFO 證明一套 AI 系統的成本是合理的？

**有力的回答：**
我著重在**效率的投資報酬率（ROI of Efficiency）。** 首先，我會實作「模型階梯（Model Cascading）」，確保我們 90% 的流量都由每百萬 token 不到一美分的模型來處理。其次，我會實作「語意快取（Semantic Caching）」，避免為同一個答案付兩次費用。第三，我會建立「推論配額（Inference Quotas）」與「成本回攤模型（Chargeback Models）」，讓每個業務單位都對自己的用量負責。藉由把 AI 當成一種具備分層定價的「商品化資源（Commodity Resource）」，我們便能從「無邊界的實驗」過渡到「可預測的 OpEx」模式。

### Q：自架的個人 GPU 叢集在什麼情況下會比 API 便宜？

**有力的回答：**
「交叉點（Crossover Point）」通常出現在**持續的高吞吐量**時。如果你的應用程式有著每秒 5-10 個請求、全年無休（24/7）的基線，那麼一台 H100 預留執行個體的固定成本，就會比 API 的變動性 token 成本更便宜。然而，如果你的流量是「尖峰型」的，或明顯偏重於上班時段，那麼 API 供應商通常會更便宜，因為它們讓你能在離峰時段「為沉默付費（pay for the silence）」。對多數企業而言，以一個 70B 等級的模型來說，損益兩平點大約落在每月 5 億個 token。

---

## 參考資料
- Google Cloud. "Cost Optimization for Generative AI" (2024)
- Anyscale. "LLM Inference: API vs. Self-Hosted Costs" (2024)

---

*下一篇：[Prompt 工程基礎](../05-prompting-and-context/01-prompt-engineering-fundamentals.md)*
