# 模型分類體系

本章提供一份截至 **2026 年 5 月** 的模型生態完整指南，涵蓋模型家族、能力，以及生產系統的選型準則。

> **最後驗證日期：2026 年 5 月 29 日。** 模型生態演進極為快速，請務必對照各供應商的定價頁面與發行說明再行確認。
>
> **2026 年 5 月——自 4 月更新以來的新進展：** Anthropic Claude Opus 4.8（5 月 28 日，價格與 Opus 4.7 相同，為 $5/$25；Dynamic Workflows 研究預覽，支援數百個並行子代理；快速模式為 $10/$50，比 Opus 4.7 的快速模式便宜 3 倍）；OpenAI GPT-5.5（4 月 23 日）與 GPT-5.5 Instant（5 月 5 日，ChatGPT 中的預設模型）；Claude Opus 4.7（4 月 16 日，於 Bedrock/Vertex/Foundry 正式上線）；Claude Mythos Preview（受限；僅限 Project Glasswing 合作夥伴）；Google Gemma 4（4 月 2 日，Apache 2.0）與 Gemini 3.2 Flash（5 月 5 日低調推出）；DeepSeek V4 Pro 與 V4 Flash（4 月 24 日；75% 的 V4 Pro 折扣於 5 月 22 日**永久化**，自 6 月 1 日起每 1M 的新標價為 $0.435/$0.87）；Moonshot Kimi K2.6（4 月 20 日，1T MoE / 32B 活躍）；Alibaba Qwen 3.6 Plus / 3.6-35B-A3B / 3.6 Max-Preview；Mistral Medium 3.5（4 月 29 日，統一聊天/推理/編碼/視覺）；Meta Muse Spark（4 月 8 日，Meta 首個閉源權重模型）；Llama 4 Behemoth 因能力疑慮，發布暫停至 2026 年秋季。SWE-bench Verified 領先者：Claude Mythos Preview 93.9%、GPT-5.5 88.7%、Claude Opus 4.8 88.6%、Claude Opus 4.7 87.6%；ARC-AGI-2 領先者：GPT-5.5 為 85.0%。

## 目錄

- [模型分類](#model-categories)
- [前沿模型（2026 年 5 月）](#frontier-models)
- [推理模型](#reasoning-models)
- [開源模型](#open-source-models)
- [專用模型](#specialized-models)
- [嵌入模型](#embedding-models)
- [模型選型框架與語意路由](#model-selection-framework)
- [主權 AI 與資料落地](#sovereign-ai-and-data-residency)
- [能力比較](#capability-comparison)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 模型分類

### 依能力層級分類（2026 年 4 月現況）

| 層級 | 特性 | 範例 | 使用情境 |
|------|-----------------|----------|----------|
| **前沿（Frontier）** | 頂尖推理、代理能力精熟 | Claude Opus 4.8, GPT-5.5, Gemini 3.1 Pro, Grok 4.3 | 複雜推理、編碼、生產級代理 |
| **快速/高效（Fast/Efficient）** | 低於 200ms、成本最佳化 | Gemini 3.1 Flash, GPT-5.5-mini, Claude Haiku 4.5, DeepSeek V4 Flash | 高流量串流、UI、即時應用 |
| **久經實戰（Battle-Tested）** | 成熟、廣泛部署、穩定 | Claude Sonnet 4.6, GPT-5.5 Instant, Gemini 3.1 Pro | 企業生產工作負載 |
| **小型/邊緣（Small/Edge）** | 私有、邊緣、專用 | Llama 4 Scout, Mistral Small 4, Phi-4 | 本地隱私、裝置端、MoE 高效 |
| **重推理（Reasoning-Heavy）** | 延伸的內部 CoT | Claude Opus 4.8（thinking）, GPT-5.5 reasoning, Gemini 3.1 Pro Deep Think, DeepSeek-R1 | 數學、程式除錯、多步邏輯 |

### 依推理模式分類（2025–2026）

| 模式 | 能力 | 模型 | 使用情境 |
|------|------------|--------|----------|
| **標準（Standard）** | 快速、直覺式回應 | GPT-5.5-mini, Claude Sonnet 4.6 | 聊天、簡單抽取 |
| **延伸思考（Extended Thinking）** | 輸出前先進行內部草稿 CoT | Claude Opus 4.8, GPT-5.5 reasoning, DeepSeek-R1 | 數學、程式除錯、規劃 |
| **混合（Hybrid）** | 使用者可控的推理深度 | Claude Opus 4.8, GPT-5.5 | 複雜度可變的任務 |

---

## 前沿模型（2026 年 5 月）

### Claude Opus 4.8（Anthropic）- 2026 年 5 月新發布

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 1M tokens（整個視窗皆採標準定價） |
| 輸入成本 | $5.00 / 1M tokens（與 4.7 相同） |
| 輸出成本 | $25.00 / 1M tokens（與 4.7 相同） |
| 快取：5m 寫入 | $6.25 / 1M tokens |
| 快取：1h 寫入 | $10.00 / 1M tokens |
| 快取：命中 / 刷新 | $0.50 / 1M tokens |
| Batch API | 每 1M 為 $2.50 / $12.50（50% 折扣） |
| 快速模式（研究預覽） | 每 1M 為 $10 / $50（約快 2.5 倍；比 $30 / $150 的 Opus 4.7 快速模式便宜 3 倍） |
| 延伸思考 | 原生、自適應模式 |
| 多模態 | 文字 + 更高解析度視覺 |
| SWE-bench Verified | 88.6% |
| SWE-Bench Pro | 69.2%（自 Opus 4.7 的 64.3% 提升） |
| Terminal-Bench 2.1 | 74.6%（GPT-5.5 仍以 78.2% 領先） |
| GDPval-AA | 1890 Elo（自 Opus 4.7 的 1753 提升） |
| OSWorld-Verified | 82.3% |
| Online-Mind2Web | 84% |
| 發布日期 | 2026 年 5 月 28 日（於 Claude API、AWS Bedrock、Vertex AI 正式上線） |

**最適合用於：** 在 Claude Code 中長時間執行的自主編碼工作、程式庫規模的遷移、需要並行子代理的代理工作流，以及對齊與誠實度提升具關鍵意義的工作負載。

**相較於 Opus 4.7 的關鍵特性：**
- **Dynamic Workflows**（研究預覽）：Claude 在單一 Claude Code 工作階段中規劃工作並執行數百個並行子代理、驗證其輸出並回報。適用於跨數十萬行程式碼的程式庫規模遷移。
- **任務中途系統訊息**：Messages API 現在可在對話進行中接受系統訊息，有助於在不結束工作階段的情況下引導長時間的代理執行。
- **可選快速模式**，速度約 2.5 倍，每 1M 為 $10 / $50，價格比 Opus 4.7 的快速模式低 3 倍。
- **努力程度控制開關**：`claude.ai` 與 Cowork 中可讓使用者依每一輪調整推理深度。
- **擴充的 Claude Code 速率限制**。

**考量事項：** 分詞器與 Opus 4.7 所導入的相同（對相同的固定文字，token 數比 4.7 之前的分詞器最多多出 35%）。GPT-5.5 仍以 88.7% 蟬聯 SWE-Bench Verified 排行榜，並以 78.2% 領先 Terminal-Bench 2.1。GPQA Diamond 相較 Opus 4.7 下滑 0.6 分。Anthropic 的分詞器變更意味著相同文字的 token 數與帳單金額無法與 4.7 之前的模型直接比較。截至 2026 年 5 月 29 日**並無 Claude Sonnet 4.8 發布**；Sonnet 4.6 仍是生產主力。

### Claude Opus 4.7（Anthropic）

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 1M tokens |
| 最大輸出 | 128K tokens |
| 輸入成本 | $5.00 / 1M tokens（與 4.6 相同） |
| 輸出成本 | $25.00 / 1M tokens（與 4.6 相同） |
| 延伸思考 | 原生、自適應模式 |
| 多模態 | 文字 + 更高解析度視覺 |
| SWE-bench Verified（Adaptive） | 87.6%（2026 年 5 月 13 日） |
| 發布日期 | 2026 年 4 月 16 日（於 API、Bedrock、Vertex、Microsoft Foundry 正式上線） |

**最適合用於：** 自主編碼代理（為 Claude Code 提供動力）、多檔重構、複雜推理。定價與 4.6 相同——對多數工作負載而言是直接升級。
**考量事項：** 對成本敏感的工作負載請使用 Sonnet 4.6；Opus 4.7 主要用於需要頂尖編碼/代理品質的任務。

### Claude Mythos Preview（Anthropic）- 受限存取

| 屬性 | 數值 |
|-----------|-------|
| 狀態 | 未發布——僅限 Project Glasswing 合作夥伴（約 11 個組織：AWS、Apple、Cisco、Google、Microsoft、NVIDIA、Palo Alto 等） |
| 受限原因 | 雙重用途的網路安全能力 |
| SWE-bench Verified | 93.9%（2026 年 5 月 13 日——當前 SOTA） |
| 發布日期 | 2026 年 4 月 7 日（受限合作夥伴預覽） |

**最適合用於：** 生產環境中不適用。在此追蹤是因為它樹立了 SWE-bench Verified 的公開 SOTA，並反映出前沿在內部的所在位置。

### Claude Opus 4.6（Anthropic）

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 1M tokens |
| 最大輸出 | 128K tokens |
| 輸入成本 | $5.00 / 1M tokens |
| 輸出成本 | $25.00 / 1M tokens |
| 延伸思考 | 原生自適應思考（可設定 budget_tokens） |
| 多模態 | 文字 + 視覺 |
| 亮點 | 最強大的 Anthropic 模型；卓越的編碼與推理能力 |
| 發布日期 | 2026 年 2 月 |

**最適合用於：** 最複雜的推理、自主軟體工程、代理工作流。
**考量事項：** 高階定價；不需頂尖能力的任務請使用 Sonnet 4.6。

### Claude Sonnet 4.6（Anthropic）

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 1M tokens |
| 輸入成本 | $3.00 / 1M tokens |
| 輸出成本 | $15.00 / 1M tokens |
| 延伸思考 | 支援 |
| 多模態 | 文字 + 視覺 |
| 亮點 | 能處理過去需要 Opus 層級的任務；最佳成本/品質平衡 |
| 發布日期 | 2026 年 2 月 |

**最適合用於：** 生產級編碼代理（為 Claude Code 提供動力）、大規模複雜推理。
**考量事項：** 現可以更低成本涵蓋多數 Opus 層級任務。是多數工作負載的強力預設選擇。

### GPT-5.4（OpenAI）

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 272K tokens（標準）；可使用延伸版 |
| 輸入成本 | $2.50 / 1M tokens |
| 輸出成本 | $15.00 / 1M tokens |
| 多模態 | 文字、視覺、原生電腦操作 |
| 亮點 | 內建電腦操作能力；事實性錯誤較 GPT-5.2 減少 33%；結合編碼 + 代理優勢 |
| 發布日期 | 2026 年 3 月 |

**最適合用於：** 結合電腦操作的代理工作流、編碼、專業任務。
**考量事項：** 在 272K+ tokens 時長上下文定價會加倍。

### GPT-5.4-mini（OpenAI）

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 272K tokens |
| 輸入成本 | $0.75 / 1M tokens |
| 輸出成本 | $4.50 / 1M tokens |
| 亮點 | 高流量 GPT-5 層級工作負載的最佳成本/效能比 |
| 發布日期 | 2026 年 3 月 |

**最適合用於：** 高流量 API 呼叫、成本最佳化推理、生產級聊天機器人。

### GPT-5.4 Pro（OpenAI）

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 272K tokens |
| 輸入成本 | $30.00 / 1M tokens |
| 輸出成本 | $180.00 / 1M tokens |
| 亮點 | 最高推理能力；針對最艱難任務的高階層級 |
| 發布日期 | 2026 年 3 月 |

**最適合用於：** 競賽等級數學、複雜的多步推理。
**考量事項：** 非常昂貴；大量使用請選用標準版 GPT-5.4 或 mini。

### GPT-5.5（OpenAI）- 2026 年 5 月新發布

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 1M tokens |
| 輸入成本 | $5.00 / 1M tokens |
| 輸出成本 | $30.00 / 1M tokens |
| 多模態 | 文字、影像、音訊、影片 |
| ARC-AGI-2 | 85.0%（2026 年 5 月 13 日——領先者） |
| 發布日期 | 2026 年 4 月 23 日 |

**最適合用於：** 最高品質的多模態工作負載；當前 ARC-AGI-2 領先者。定位為「面向實際工作的新一類智慧」——在頂尖推理 + 多模態方面取代 GPT-5.4。
**考量事項：** 輸入成本約為 GPT-5.4 的 2 倍（$2.50 → $5.00），輸出約 2 倍（$15 → $30）。價格不划算的聊天工作負載請使用 GPT-5.5 Instant。

### GPT-5.5 Instant（OpenAI）- 2026 年 5 月新發布

| 屬性 | 數值 |
|-----------|-------|
| 狀態 | 自 2026 年 5 月 5 日起為 ChatGPT 中的預設模型與 API 中的 `chat-latest` |
| 幻覺減少 | 在高風險提示（醫療/法律/金融）上相較 GPT-5.3 Instant 減少 52.5% |
| AIME 2025 | 81.2%（自 GPT-5.3 Instant 的 65.4% 提升） |
| 回應長度 | 字數/行數較前代減少約 30% |
| 發布日期 | 2026 年 5 月 5 日 |

**最適合用於：** 預設的 ChatGPT 等效工作負載、即時聊天，以及幻覺減少具關鍵意義的高風險領域。
**考量事項：** 取代 GPT-5.3 Instant 成為聊天預設模型。GPT-5.2-chat-latest 與 GPT-5.3-chat-latest 於 2026 年 5 月 8 日棄用。

### GPT-Realtime-2、Translate、Whisper（OpenAI）- 2026 年 5 月新發布

| 屬性 | 數值 |
|-----------|-------|
| 能力 | 具備 GPT-5 級推理的即時語音 |
| Translate 涵蓋範圍 | 70+ 種輸入 → 13 種輸出語言 |
| 定價 | 每 1M 音訊 tokens 為 $32 / $64（輸入/輸出） |
| 發布日期 | 2026 年 5 月 7 日 |

**最適合用於：** 即時語音代理、多語言翻譯、語音優先產品。Realtime API Beta 已於 2026 年 5 月 12 日移除——Realtime-2 是受支援的途徑。

### Gemini 3.1 Pro（Google）

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 1M tokens |
| 輸入成本 | $2.00 / 1M tokens（標準）；$4.00（200K+） |
| 輸出成本 | $12.00 / 1M tokens（標準）；$18.00（200K+） |
| 多模態 | 原生：文字、視覺、音訊、影片 |
| 亮點 | 頂尖的 Google 推理能力；強大的代理與編碼能力 |
| 發布日期 | 2026 年 2 月 |

**最適合用於：** 複雜推理、多模態分析、長上下文工作負載。
**考量事項：** 取代了 Gemini 3 Pro Preview。Gemini 2.5 Pro/Flash 於 2026 年 6 月棄用。

### Gemini 3.1 Flash（Google）

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 1M tokens |
| 輸入成本 | $0.10 / 1M tokens |
| 輸出成本 | $3.00 / 1M tokens |
| 多模態 | 原生：文字、視覺、音訊、影片 |
| 亮點 | 最快的 Google 模型；高流量場景的最佳性價比 |
| 發布日期 | 2026 年 3 月 |

**最適合用於：** 即時多模態應用、高流量管線、長上下文 RAG。

### Gemini 3.2 Flash（Google）- 2026 年 5 月新發布

| 屬性 | 數值 |
|-----------|-------|
| 狀態 | 於 2026 年 5 月 5 日在 iOS Gemini app 與 Google AI Studio 低調推出（尚無正式公告） |
| 發布日期 | 2026 年 5 月 5 日 |

**最適合用於：** 可能是 3.1 Flash 在高流量工作負載上的後繼者。視為預覽版——定價與完整能力揭露待正式發表。

### Gemini Deep Research / Deep Research Max（Google）- 2026 年 5 月新發布

| 屬性 | 數值 |
|-----------|-------|
| 建構基礎 | Gemini 3.1 Pro |
| 能力 | MCP 支援；原生圖表/資訊圖產生；延伸的測試時計算；非同步背景工作流 |
| 發布日期 | 2026 年 4 月 21 日 |

**最適合用於：** 研究代理、文件綜合、長時間執行的非同步工作流。MCP 支援使其成為首個具備一流工具整合的 Google 研究代理產品。

### Gemini Robotics-ER 1.6（Google DeepMind）- 2026 年 5 月新發布

| 屬性 | 數值 |
|-----------|-------|
| 領域 | 實體機器人、具身推理 |
| 新能力 | 讀取儀表/視鏡 |
| 部署 | Boston Dynamics Spot |
| 發布日期 | 2026 年 4 月 14 日 |

**最適合用於：** 需要視覺-語言接地以執行實體動作的機器人應用。可透過 Gemini API 與 AI Studio 取得。

### Grok 4（xAI）

| 屬性 | 數值 |
|-----------|-------|
| 上下文視窗 | 256K tokens |
| 輸入成本 | $3.00 / 1M tokens |
| 輸出成本 | $15.00 / 1M tokens |
| 亮點 | 原生工具使用與即時搜尋；具競爭力的推理能力 |
| 發布日期 | 2025 年 7 月（Grok 4.20 beta：2026 年 2 月） |

**最適合用於：** 即時網路研究、重推理任務、即時 X/網路整合。
**考量事項：** Grok 4.1 Fast 以 $0.20/$0.50 提供高流量使用。

### 模型比較：前沿層級（2026 年 5 月）

| 模型 | 推理 | 編碼 | 上下文 | 代理 | 成本 |
|-------|-----------|--------|---------|---------|------|
| Claude Mythos Preview（受限） | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | n/a |
| Claude Opus 4.8 | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | $$$$ |
| Claude Opus 4.7 | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | $$$$ |
| GPT-5.5 | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | $$$$ |
| Claude Opus 4.6 | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | $$$$ |
| GPT-5.4 | ★★★★★ | ★★★★★ | ★★★★ | ★★★★★ | $$$ |
| Claude Sonnet 4.6 | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | $$$ |
| Gemini 3.1 Pro | ★★★★★ | ★★★★ | ★★★★★ | ★★★★ | $$ |
| Grok 4 | ★★★★ | ★★★★ | ★★★★ | ★★★★ | $$$ |
| GPT-5.4-mini | ★★★★ | ★★★★ | ★★★★ | ★★★ | $ |
| Gemini 3.1 Flash | ★★★ | ★★★ | ★★★★★ | ★★★ | $ |
| GPT-5.5 Instant | ★★★★ | ★★★★ | ★★★★ | ★★★★ | $$ |

### 生產傳承與成熟度

雖然前沿模型在基準測試上領先，許多企業系統仍仰賴**久經實戰**的模型：

| 模型家族 | 投入生產起始 | 成熟度說明 |
|--------------|------------------|---------------|
| **GPT-4o** | 2024 年 5 月 | 最成熟的生態系；延遲變異最低；速率限制最高。 |
| **Claude 3.5 Sonnet / 3.7 Sonnet** | 2024 年 6 月 | 工具使用可靠性與結構化輸出的黃金標準。 |
| **Gemini 2.5 Pro** | 2025 年 3 月 | 已在規模化場景中驗證；長上下文穩定。將於 2026 年 6 月棄用，由 3.x 取代。 |
| **o1 / o3** | 2024 年 9 月 | 推理模型的失效模式已被充分理解；o3 取代了 o1。 |

**為何要留在「較舊」的前沿模型上？**
1. **一致性**：新模型有「發布期」的延遲尖峰與行為變動。
2. **成本效益**：前一代在新版本發布後往往便宜 50-80%。
3. **護欄調校**：安全與審核層更為精煉。

---

## 開源模型

### Llama 4 家族（Meta）-- 2026 年 4 月新發布

| 模型 | 參數量 | 上下文 | 架構 | 備註 |
|-------|------------|---------|--------------|-------|
| Llama 4 Scout | 17B 活躍 / 16 專家（MoE） | 10M | Sparse MoE | 業界領先的 10M 上下文；可裝入單張 H100；勝過 Gemma 3、Gemini 2.0 Flash-Lite |
| Llama 4 Maverick | 17B 活躍 / 128 專家（MoE） | 1M | Sparse MoE | 勝過 GPT-4o 與 Gemini 2.0 Flash；以一半活躍參數即可媲美 DeepSeek V3 |
| Llama 4 Behemoth | 約 288B 活躍（估計） | - | Dense MoE | 仍在訓練中；在 STEM 基準上勝過 GPT-4.5、Gemini 2.0 Pro |

**優勢：**
- 首個採用 Mixture-of-Experts 架構的 Llama 世代
- 從底層原生支援多模態（文字、影像、影片輸入）
- 在 Hugging Face 上開放權重；可透過 WhatsApp、Messenger、Instagram 上的 Meta AI 取得
- Scout 的 10M token 上下文視窗在開源模型中業界領先

### Llama 3.x 家族（Meta）-- 前一世代

| 模型 | 參數量 | 上下文 | 授權 | 備註 |
|-------|------------|---------|---------|-------|
| Llama 3.3 70B | 70B | 128K | Llama 3.3 | 仍廣泛部署；強大的通用模型 |
| Llama 3.1 405B | 405B | 128K | Llama 3.1 | 最大的密集 Meta 模型；正被 Llama 4 取代 |

**備註：** Llama 3.x 在生產環境中仍被廣泛使用，但由於 MoE，Llama 4 Scout/Maverick 以更低的活躍參數量提供更優異的效能。

### DeepSeek 家族

| 模型 | 參數量 | 上下文 | 狀態 | 備註 |
|-------|------------|---------|--------|-------|
| **DeepSeek V4 Pro** | 1.6T 總計 / 49B 活躍（MoE） | 1M | GA | 於 2026 年 4 月 24 日預覽。在 1M tokens 下使用約 V3.2 的 27% 計算量 / 10% 記憶體。SWE-bench Verified 80.6%。NIST CAISI 評估（2026 年 5 月）將其定位為落後美國前沿約 8 個月（Elo 約 800）。在 Hugging Face 上開放權重。**API：每 1M 輸入/輸出 $0.435 / $0.87（75% 折扣於 2026 年 5 月 22 日永久化，6 月 1 日生效）。** 快取命中輸入 $0.003625/M。 |
| **DeepSeek V4 Flash** | 284B 總計 / 13B 活躍（MoE） | 1M | GA | 用於高吞吐量工作負載的較小活躍參數變體。**API：每 1M 為 $0.14 / $0.28（快取命中 $0.0028/M）。** 截至 2026 年 5 月，最便宜的前沿級 1M 上下文 API。 |
| DeepSeek-V3.2 | 671B（MoE） | 128K | Frontier | 通用型；98% 快取命中折扣（基礎價每 1M 為 $0.28/$0.42）。在新建專案中大致已被 V4 Flash 取代。 |
| DeepSeek-V3 | 671B（MoE，37B 活躍） | 128K | Frontier | 以訓練成本的一小部分達到 GPT-4o 水準；開放權重。 |
| DeepSeek-R1 | 671B（MoE） | 128K | Reasoning | 在數學/程式上比肩 o1；首個開源推理模型。 |
| DeepSeek-R1-Distill | 7B–70B | - | Reasoning | 蒸餾至較小模型；成本高效的推理。 |

**2026 年 5 月關鍵背景**：DeepSeek V4 Pro（4 月 24 日發布，並於 5 月 22 日將 75% 的促銷折扣永久化）以一小部分成本在多項基準上縮小了與美國前沿模型的差距。以每 1M $0.435 / $0.87 計算，在可比任務上 V4 Pro 約比 Claude Opus 4.7（$5 / $25）便宜 10 倍，比 GPT-5.5（$5 / $30）便宜 5-10 倍。V4 Flash 將底價進一步降至每 1M $0.14 / $0.28，且具備相同的 1M 上下文視窗。兩者皆有的 98% 快取命中折扣，使 V4 成為提示可快取的高流量 RAG 與分類工作負載的主導選擇。據報導，由於 Huawei Ascend 訓練的挑戰，DeepSeek R2（R1 的推理後繼者）仍延遲推出。

### Moonshot Kimi 家族 - 2026 年 5 月新發布

| 模型 | 參數量 | 上下文 | 備註 |
|-------|------------|---------|-------|
| **Kimi K2.6** | 1T 總計 / 32B 活躍（MoE） | - | 於 2026 年 4 月 20 日發布。修改版 MIT 授權。原生影片輸入；Agent Swarm 可擴展至 300 個子代理與 4,000 個協同步驟。在 SWE-Bench Pro 上與 GPT-5.5 打平（58.6%）；SWE-bench Verified 約 80.2%。 |
| Kimi K2-Thinking-0905 | - | - | 首個在 AIME 2025 上達到 100% 的模型（推理變體）。 |

**最適合用於：** 長時程代理工作負載、影片理解、作為閉源前沿的開放權重代理堆疊替代方案。

### Alibaba Qwen 3.x 家族 - 2026 年 5 月新發布

| 模型 | 參數量 | 授權 | 備註 |
|-------|------------|---------|-------|
| **Qwen 3.6 Max-Preview** | 約 1T MoE | 商業預覽 | 於 2026 年 4 月 20–27 日左右發布。262K 上下文。據 Alibaba 表示，在六項編碼基準上居首。 |
| **Qwen 3.6-Plus** | - | - | 於 2026 年 4 月 2 日發布。強化編碼能力。 |
| **Qwen 3.6-35B-A3B** | 35B / 3B 活躍 MoE | Apache 2.0 | 於 2026 年 4 月 16 日發布。開放權重主力模型。 |
| Qwen2.5-Coder-32B | 32B | Apache 2.0 | 前一世代的開源編碼領導者。 |
| Qwen2.5-72B | 72B | Apache 2.0 | 前一世代的多語言領導者。 |
| Qwen2.5-7B | 7B | Apache 2.0 | 高效的自主託管選項。 |

### Mistral 家族

| 模型 | 參數量 | 上下文 | 備註 |
|-------|------------|---------|-------|
| **Mistral Medium 3.5** | 128B 密集 | 256K | 2026 年 5 月新發布。於 2026 年 4 月 29 日發布。將 Magistral（推理）+ Pixtral（視覺）+ Devstral 2（編碼）合併為單一模型。SWE-Bench Verified 77.6%。輸入 tokens 每 M $1.50。 |
| **Voxtral TTS** | 4B 開放權重 | 串流 | 2026 年 5 月新發布（3 月 23 日發布，CC BY-NC 4.0）。70ms 延遲、9 種語言、3 秒語音複製。 |
| Mistral Large 3 | 675B（MoE，41B 活躍） | 256K | Sparse MoE；與最佳開放權重模型同級；在 LMArena 上居開源非推理類第 2 名。 |
| Mistral Small 4 | - | 256K | 混合 instruct/推理/編碼；於 2026 年 3 月發布。 |
| Mistral 3（14B/8B/3B） | 3B–14B | - | 統一家族：多語言、多模態、Apache 2.0。 |
| Mixtral 8x22B | 141B（MoE） | - | 前一世代；在吞吐量上仍可行。 |

### Google Gemma 家族 - 2026 年 5 月新發布

| 模型 | 參數量 | 上下文 | 授權 | 備註 |
|-------|------------|---------|---------|-------|
| **Gemma 4（31B 密集）** | 31B | 256K | Apache 2.0 | 於 2026 年 4 月 2 日發布。140+ 種語言；原生視覺/音訊；function calling。 |
| **Gemma 4（26B-A4B MoE）** | 26B / 4B 活躍 | 256K | Apache 2.0 | Sparse MoE 變體。 |
| **Gemma 4 E4B** | 8B | 256K | Apache 2.0 | 適合邊緣。 |
| **Gemma 4 E2B** | 5.1B / 2.3B 活躍 | 256K | Apache 2.0 | 最小變體；行動裝置/嵌入式。 |

### Meta Muse Spark（閉源權重）- 2026 年 5 月策略轉向

| 屬性 | 數值 |
|-----------|-------|
| 授權 | **閉源權重**——Meta Superintelligence Labs 首個專有模型 |
| 能力 | 具備 Instant / Thinking / Contemplating 模式的多模態推理 |
| 發布日期 | 2026 年 4 月 8 日 |

**策略意義：** Meta 自最初 Llama 時代以來首個非開源模型。這顯示前沿品質的工作可能需要閉源開發的回饋迴路。Llama 4 Behemoth 的發布同時因能力疑慮暫停至 2026 年秋季。開源與閉源的平衡如今呈雙層格局：閉源前沿領先 6–12 個月；開放權重則透過蒸餾、RL 與生態系迭代追趕。

---

## 專用模型

### 編碼精熟（2026 年 5 月）

| 模型 | 專長 | 致勝原因 |
|-------|----------------|-------------|
| **GPT-5.5** | 單次編碼領導者 | SWE-bench Verified 88.7%（第 1）；Terminal-Bench 2.1 78.2%（第 1） |
| **Claude Opus 4.8** | 長時間執行的代理式編碼 | SWE-bench Verified 88.6%；SWE-Bench Pro 69.2%；在 Claude Code 中以並行子代理運作 Dynamic Workflows |
| **Claude Opus 4.7** | 前代旗艦編碼 | SWE-bench Verified 87.6%；SWE-Bench Pro 64.3% |
| **Claude Sonnet 4.6** | 主力編碼 | 以更低成本為 Claude Code 提供動力；1M 上下文 |
| **Llama 4 Maverick** | 開源編碼 | 開放權重；在編碼基準上具競爭力 |
| **Qwen 3.6 Coder / Qwen2.5-Coder-32B** | 自主託管編碼 | 自主託管 IDE 的最佳性價比 |
| **DeepSeek V4 Pro / R1-Distill-70B** | 開源推理 + 程式 | 70B 級最佳開源推理；V4 Pro 是開放權重 1.6T/49B 活躍 MoE |

### 推理與數學

| 模型 | 方法 | 最適合用於 |
|-------|----------|----------|
| **Claude Opus 4.8（thinking）** | 結合並行子代理的自適應思考 | 軟體規劃、程式庫規模的工作、代理式推理 |
| **GPT-5.5 reasoning** | 最大計算量的推理 | 競賽數學（Instant 上 AIME 2025 81.2%）、ARC-AGI-2 85.0% 領先者 |
| **Gemini 3.1 Pro Deep Think** | 持續性的思維鏈 | 科學推理、GPQA Diamond 領先者 |
| **DeepSeek-R1** | 基於 RL 的思考 | 開源邏輯推論、具競爭力的數學 |
| **Grok 4.3（DeepSearch）** | 以網路為依據的推理 | 需要即時資訊的研究任務 |

### 長上下文（1M+）

| 模型 | 視窗 | 召回表現 |
|-------|--------|-------------------|
| **Llama 4 Scout** | 10M | 業界領先的開放權重上下文視窗 |
| **Gemini 3.1 Pro / Flash** | 1M | 1M 上下文下的最佳品質；已在規模化場景中驗證 |
| **Claude Opus 4.8 / 4.7 / Sonnet 4.6** | 1M | 完整 1M 採標準定價；可靠的召回 |
| **Llama 4 Maverick** | 1M | 具 MoE 效率的開放權重 1M 上下文 |

---

## 嵌入模型

### API 嵌入模型（2026 年 5 月）

| 模型 | 維度 | 最大 Tokens | MTEB 分數 | 每 1M 成本 |
|-------|------------|------------|------------|---------|
| OpenAI text-embedding-3-large | 3072 | 8191 | 64.6 | $0.13 |
| OpenAI text-embedding-3-small | 1536 | 8191 | 62.3 | $0.02 |
| Voyage-3 | 1024 | 32000 | 67.8 | $0.06 |
| Cohere embed-v3 | 1024 | 512 | 66.4 | $0.10 |
| Google text-embedding-004 | 768 | 2048 | 66.1 | $0.025 |

### 開源嵌入模型

| 模型 | 維度 | 最大 Tokens | MTEB | 備註 |
|-------|------------|------------|------|-------|
| BGE-large-en-v1.5 | 1024 | 512 | 63.9 | 指令微調 |
| E5-mistral-7b-instruct | 4096 | 32768 | 66.6 | 配合指令表現強 |
| Nomic-embed-text-v1.5 | 768 | 8192 | 62.3 | 長上下文、開源 |
| GTE-Qwen2-7B | 3584 | 32K | 72.1 | 頂尖的開源嵌入 |

### 嵌入模型選型指南

| 需求 | 推薦 | 原因 |
|-------------|-------------|-----|
| 最佳品質 | Voyage-3 或 text-embedding-3-large | 最高 MTEB |
| 成本高效 | text-embedding-3-small | $0.02/1M |
| 自主託管 | GTE-Qwen2-7B | 最佳開源 MTEB |
| 長文件 | Nomic 或 Voyage-3 | 8K+ 上下文 |
| 多語言 | Cohere embed-v3 | 為多語言而生 |

---

## 模型選型框架

### 決策樹

```
What is your primary constraint?

├── Cost → Use smaller model, consider open source
│   ├── Very cost sensitive → DeepSeek V4 Flash, GPT-5.5-mini, Claude Haiku 4.5, Gemini 3.1 Flash
│   └── Moderate budget → Claude Sonnet 4.6, GPT-5.5 Instant, DeepSeek V4 Pro
│
├── Quality + Reasoning → Use frontier models
│   ├── Highest reasoning → Claude Opus 4.8 (thinking), GPT-5.5 reasoning, Gemini 3.1 Pro Deep Think
│   └── Coding + reasoning → Claude Opus 4.8 with Dynamic Workflows, Claude Sonnet 4.6 (Extended Thinking), GPT-5.5
│
├── Latency → Use fast models
│   ├── <100ms response → Gemini 3.1 Flash, GPT-5.5-mini
│   └── <500ms response → Claude Haiku 4.5, Claude Opus 4.8 fast mode, Grok 4.1 Fast
│
├── Self-hosting → Use open models
│   ├── Maximum capability → Llama 4 Maverick, DeepSeek-V3
│   ├── Good balance → Llama 4 Scout, Llama 3.3 70B, Qwen2.5-72B
│   └── Edge/mobile → Mistral 3 3B, Phi-4
│
└── Privacy → Self-host or use on-prem
    └── Choose open models with appropriate license
```

### 語意路由

靜態決策樹正逐漸被**語意路由器（Semantic Routers）**取代：
- **運作方式**：一個小型、快速的嵌入模型將查詢向量化。若匹配到某個「已知容易」的叢集，便路由至廉價模型（Gemini 3.1 Flash、DeepSeek V4 Flash、Claude Haiku 4.5）。若命中某個「代理/邏輯」叢集，則路由至搭配推理的 Claude Opus 4.8 或 GPT-5.5。
- **好處**：在不需硬編碼規則的情況下自動化成本最佳化。
- **實作**：採用如 `semantic-router`（Python）等工具，或自訂的 Weaviate/Pinecone 分類器。

---

## 主權 AI 與資料落地

**2026 年的法規現實：**
企業必須遵守 GDPR（EU）、DPDPA（India）、Saudi Arabia PDPL 以及各產業規範。「主權 AI（Sovereign AI）」如今已成為一個產品類別。

| 解決方案 | 供應商 | 使用情境 |
|----------|----------|----------|
| **Azure Government/Sovereign** | Microsoft | 40+ 個區域的專屬基礎設施；獲准用於 US Gov/EU NIS2 |
| **AWS Sovereign Cloud** | Amazon | 實體隔離的 VPC；符合 GDPR 的 EU 區域 |
| **Google Distributed Cloud** | Google | 氣隙隔離的本地 Gemini 部署 |
| **Private Llama 4 / 3.3** | Meta（自主託管） | 最大化資料主權；開放權重（Llama 4 MoE 或 3.3 密集） |
| **DeepSeek（自主託管）** | DeepSeek（開源） | 開放權重；資料不離開你的基礎設施 |
| **Mistral Large 3（自主託管）** | Mistral（Apache 2.0） | 675B MoE；開放權重；強大的多語言能力 |

**權衡取捨**：主權雲相較標準全球區域帶有 **20-30% 的溢價**，但對金融與政府而言是必要的。

### 規模化成本比較（2026 年 5 月）

假設每天 1M 請求，每次 1K 輸入 + 500 輸出 tokens：

| 模型 | 每日輸入成本 | 每日輸出成本 | 每月總計 |
|-------|----------------|-----------------|-------------|
| Claude Sonnet 4.6 | $3,000 | $7,500 | $315,000 |
| GPT-5.4 | $2,500 | $7,500 | $300,000 |
| Gemini 3.1 Pro | $2,000 | $6,000 | $240,000 |
| GPT-5.4-mini | $750 | $2,250 | $90,000 |
| Gemini 3.1 Flash | $100 | $1,500 | $48,000 |
| 自主託管 Llama 4 Scout* | - | - | 約 $15,000 |
| 自主託管 Llama 3.3 70B* | - | - | 約 $50,000 |

*自主託管 Llama 4 Scout 可裝入單張 H100；Llama 3.3 70B 假設使用 4 張 H100 GPU

---

## 能力比較

### 基準測試表現（2026 年 5 月）

| 模型 | MMLU | HumanEval | SWE-bench Verified | 備註 |
|-------|------|-----------|--------------------|-------|
| **Claude Opus 4.6** | - | - | - | 在推理與編碼各方面皆屬頂尖；具體分數請查閱最新資料 |
| **GPT-5.4** | - | - | - | 事實性錯誤較 GPT-5.2 減少 33%；強大的編碼 + 代理能力 |
| **Claude Sonnet 4.6** | - | - | - | 在許多任務上接近 Opus 水準 |
| **Gemini 3.1 Pro** | - | - | - | 頂尖的 Google 推理能力 |
| **Grok 4** | - | - | - | 具競爭力的推理；即時網路整合 |
| **Llama 4 Maverick** | - | - | - | 在所報告的基準上勝過 GPT-4o、Gemini 2.0 Flash |
| **DeepSeek-R1** | 90.8 | 92.6 | 49.2% | 首個開源推理模型；數學/程式表現強 |

*來源：各自的技術報告與 LMSYS Chatbot Arena / LMArena，2026 年 4 月。最新模型（Opus 4.6、GPT-5.4、Gemini 3.1）的基準分數正快速演進——請務必以當前排行榜驗證。*

### 特定任務建議（2026 年 5 月）

| 任務 | 推薦模型 | 原因 |
|------|--------------------|-----|
| **自主編碼代理** | Claude Sonnet 4.6 / Opus 4.6 | 為 Claude Code 提供動力；1M 上下文；頂尖工具可靠性 |
| **複雜推理** | GPT-5.4 Pro, Claude Opus 4.6（thinking）, DeepSeek-R1 | 最高推理能力 |
| **代理式電腦操作** | GPT-5.4 | 首個具備原生電腦操作能力的通用模型 |
| **高流量 API** | Gemini 3.1 Flash, GPT-5.4-mini | 同級中每 token 成本最低 |
| **長上下文 RAG** | Gemini 3.1 Pro/Flash（1M）, Claude Sonnet 4.6（1M） | 已驗證的長距離召回 |
| **超長上下文** | Llama 4 Scout（10M） | 業界領先的 10M 上下文；開放權重 |
| **多模態即時** | Gemini 3.1 Flash | 原生即時音訊/影片/文字 |
| **私有生產** | Llama 4 Maverick, Llama 3.3 70B, Qwen2.5-72B | 高能力搭配本地掌控 |
| **開源編碼** | Llama 4 Maverick, Qwen2.5-Coder-32B | 開放權重、強大的編碼基準 |
| **創意/聊天** | GPT-5.4 | 強大的對話品質與指令遵循 |

---

## 面試問題

### Q：你會如何為生產級 RAG 系統選擇模型？

**理想回答：**
我會從以下幾個面向評估：

**1. 品質需求：**
- 在實際領域的代表性查詢上進行測試
- 衡量答案正確性、幻覺率、引用準確度

**2. 成本分析：**
```
Monthly cost = requests/day × 30 × avg_tokens × rate
```
務必為前 2-3 名候選方案進行計算。

**3. 延遲需求：**
- 若需要 <200ms TTFT：Gemini 3.1 Flash、Claude Haiku 4.5、GPT-5.4-mini
- 若品質至上：接受 2-3 秒，採用 Claude Opus 4.6 或 GPT-5.4

**4. 維運需求：**
- 自主託管：Llama 4 Scout/Maverick、DeepSeek-V3
- 合規 / 資料落地：Azure Sovereign 或自主託管

**5. 實務選型：**
- 原型階段先從 Claude Sonnet 4.6 或 GPT-5.4 開始
- 針對 80% 的查詢 A/B 測試 Gemini 3.1 Flash（成本考量）
- 透過語意路由將前沿模型保留給困難查詢

### Q：說明專有模型與開源模型之間的權衡取捨。

**理想回答：**
| 因素 | 專有（OpenAI、Anthropic） | 開源（Llama、DeepSeek） |
|--------|--------------------------------|-----------------------------|
| 品質 | 一般而言（略）更高 | 正快速追趕 |
| 成本 | 按 token 計價 | 計算 + 維運 |
| 掌控 | 有限 | 完全 |
| 隱私 | 資料傳至供應商 | 留在本地 |
| 更新 | 自動 | 手動 |
| 客製化 | 有限的微調 | 完全微調 |
| 維運負擔 | 無 | 顯著 |

**關鍵洞見（2026）**：DeepSeek-V3/R1 以及如今的 Llama 4 改變了這場對話——開源模型在許多基準上比肩或勝過 GPT-4o。隨著 Llama 4 Maverick 以一半的活躍參數在推理上媲美 DeepSeek V3，差距比以往任何時候都更小。

### Q：GPT-5.4 Pro 與 Claude Opus 4.6 的延伸思考有何差異？

**理想回答：**
兩者皆使用內部思維鏈，但機制有所不同：

- **GPT-5.4 Pro**：OpenAI 的最大計算量推理層級（每 1M tokens $30/$180）。將高計算量分配給推理。內部思緒不會被揭露。是 o3 系列的後繼者。
- **Claude Opus 4.6 Adaptive Thinking**：在獨立的 `<thinking>` 區塊中回傳思考 tokens。可設定 `budget_tokens`。你可以檢視推理鏈以進行除錯。完整 1M 上下文搭配 128K 最大輸出。

**生產選擇**：在除錯與建立信任方面，Claude 可見的思考更為透明。在數學/競賽任務上追求最大原始推理能力時，GPT-5.4 Pro 領先。追求成本效益的推理時，Claude Sonnet 4.6 或 GPT-5.4-mini 是強力選擇。

---

## 參考資料

- Anthropic: https://platform.claude.com/docs/en/about-claude/models/overview
- OpenAI Platform: https://developers.openai.com/api/docs/models
- Google AI: https://ai.google.dev/gemini-api/docs/models
- Meta Llama: https://www.llama.com/
- DeepSeek: https://api-docs.deepseek.com/
- xAI Grok: https://docs.x.ai/developers/models
- Mistral AI: https://docs.mistral.ai/models/
- LMArena Leaderboard: https://lmarena.ai/
- Hugging Face Open LLM Leaderboard: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard

---

*下一篇：[能力評估](02-capability-assessment.md)*
