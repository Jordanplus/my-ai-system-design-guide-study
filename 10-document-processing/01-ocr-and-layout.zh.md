# OCR 與版面分析

傳統 OCR（Tesseract、各種專用引擎）大致上已被 **原生多模態 LLM**（Gemini 3.1 Pro、GPT-5.5、Claude Sonnet 4.6、Claude Opus 4.7）所取代。我們不再「辨識字元」，而是「理解版面」。

## 目錄

- [典範轉移：傳統 OCR vs. Vision-LLM](#shift)
- [Vision-LLM 版面擷取](#layout-extraction)
- [閱讀順序與邏輯結構](#reading-order)
- [處理低品質掃描與手寫文字](#quality)
- [成本與延遲的取捨](#tradeoffs)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 典範轉移：傳統 OCR vs. Vision-LLM

| 特性 | 傳統 OCR（Tesseract/AWS Textract） | Vision-LLM（Gemini 3.1 Pro、GPT-5.5、Claude Opus 4.7） |
|---------|-------------------------------------------|--------------------------------------------------------|
| **主要機制** | 字元辨識 | 視覺 token 理解 |
| **邏輯** | 點與線分析 | 語意脈絡 |
| **閱讀順序** | 單純由上而下 | 能感知多欄、複雜版面 |
| **手寫文字** | 差 | 優異（達人類水準） |
| **輸出** | 文字區塊 + 邊界框（Bounding box） | 結構化的 Markdown/JSON |

---

## Vision-LLM 版面擷取

標準工作流程是 **Screenshot-to-Markdown**（截圖轉 Markdown）。
1. **Rasterize（點陣化）**：將 PDF 頁面轉換為圖片。
2. **Visual Prompting（視覺提示）**：要求視覺模型「將以下頁面轉錄為 GitHub-flavored Markdown，並保留表格與標題」。
3. **Structured Recovery（結構復原）**：利用模型的空間感知能力重建邏輯階層。

---

## 閱讀順序與邏輯結構

> [!IMPORTANT]
> 在天真的 RAG 實作中，一個常見的失敗是讓一個段落被切斷在欄與欄之間。
> Vision-LLM 透過「看見」欄間的留白槽溝（gutter）來解決這個問題，並正確地排序文字；這與規則式的解析器不同，後者可能會橫跨兩欄直線讀過去。

---

## 處理低品質掃描

現代的多模態模型對以下情況具有強健性：
- **Skew/Rotation（傾斜／旋轉）**：在視覺注意力層中自動校正。
- **Bleed-through（透印）**：模型運用語意脈絡來「忽略」紙張背面透出的文字。
- **Handwritten Annotations（手寫註記）**：可被擷取到一個獨立的 `annotations` JSON 欄位中。

---

## 成本與延遲的取捨

| 模型層級 | 使用情境 | 延遲 | 成本（1K 頁） |
|------------|----------|---------|-----------------|
| **Gemini 3.1 Flash** | 大量批次處理 | 1-2s / 頁 | $1-3 |
| **GPT-5.5 / Claude Sonnet 4.6** | 高精度／法律 | 3-5s / 頁 | $8-18 |
| **本地端（Llama 4 Vision）** | 含 PII 敏感資料／地端部署 | <1s / 頁 | 僅基礎設施成本 |

---

## 面試問題

### Q：既然有了 vision LLM，為什麼你還會使用 AWS Textract 或 Azure AI Search（OCR）？

**強力的回答：**
**嚴格的空間中繼資料與合規性**。如果我的應用程式需要每一個字詞的精確像素級邊界框（例如用於法律文件遮蔽工具），專用的 OCR 引擎往往更精確且更便宜。此外，OCR 引擎是 **Deterministic（決定性的）**：它們不會「幻覺」出根本不存在的字詞。對於要求 100% 字元精準度、而非「版面理解」的高風險文件處理而言，傳統引擎在混合式管線中仍佔有一席之地。

### Q：你會如何有效率地用 Vision LLM 處理一份 500 頁的 PDF？

**強力的回答：**
我們採用 **Parallel Map-Reduce（平行 Map-Reduce）** 模式。
1. **Map**：我們啟動 50 個平行 worker（使用 AWS Lambda 或 Modal），每個處理 10 頁。每個 worker 呼叫一個快速的 Vision 模型（例如 Gemini 3 Flash）來取得 Markdown。
2. **Consolidate（彙整）**：由一個中央 agent 檢視這些 Markdown 片段，以確保標題的連續性。
3. **Cache（快取）**：我們將產出的 Markdown 儲存到向量資料庫中。
這能將處理時間從 30 分鐘（循序處理）縮短到 20 秒以內。

---

## 參考資料
- Google DeepMind. "Gemini 2.0: Understanding Multi-column Documents" (2025)
- OpenAI. "Vision Models for Document Understanding" (2025)
- Tesseract v6. "The Integration of Hybrid Transformer OCR" (2025)

---

*下一篇：[多模態解析與 Markdown 轉換](02-multimodal-parsing.md)*
