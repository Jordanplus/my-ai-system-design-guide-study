# 案例研究：文件智慧處理流程（Document Intelligence Pipeline）

## 問題

一家法律科技公司需要每月處理 **50,000 份合約**，從中擷取關鍵條款（締約方、日期、義務、終止條款），並載入到可搜尋的資料庫中。

**面試中給定的限制條件：**
- 文件長度從 2 頁到 200 頁不等
- 掃描版 PDF 與原生數位檔案混雜
- 多語言（英文、德文、法文、西班牙文）
- 擷取準確率：關鍵欄位達 95% 以上
- 成本目標：每份文件低於 $0.50

---

## 面試題目

> 「設計一條流程，能接收一份 100 頁的合約 PDF，並將締約方、生效日期、終止條件與付款條款等結構化資料擷取為 JSON。」

---

## 解決方案架構

```mermaid
flowchart TB
    subgraph Intake["Document Intake"]
        PDF[Contract PDF] --> CLASSIFY{Native or Scanned?}
        CLASSIFY -->|Native| PARSE[PyMuPDF Parser]
        CLASSIFY -->|Scanned| OCR[Vision-LLM OCR<br/>Gemini 3 Flash]
    end

    subgraph Structure["Structure Recovery"]
        PARSE --> MARKDOWN[Markdown Conversion]
        OCR --> MARKDOWN
        MARKDOWN --> SECTION[Section Detection<br/>Headers, Clauses]
    end

    subgraph Extract["Extraction Layer"]
        SECTION --> PARALLEL{{"Parallel Extractors"}}
        PARALLEL --> E1[Parties Extractor]
        PARALLEL --> E2[Dates Extractor]
        PARALLEL --> E3[Obligations Extractor]
        PARALLEL --> E4[Termination Extractor]
    end

    subgraph Validate["Validation"]
        E1 --> MERGE[Merge Results]
        E2 --> MERGE
        E3 --> MERGE
        E4 --> MERGE
        MERGE --> VALIDATE[Cross-Field Validation]
        VALIDATE --> OUTPUT[Structured JSON]
    end
```

---

## 關鍵設計決策

### 1. 以 Vision-LLM 取代傳統 OCR

**解答：** 掃描版合約常帶有印章、手寫註記，以及複雜的版面配置（表格、多欄）。傳統 OCR（Tesseract）會產生雜亂破碎的輸出。Gemini 3 Flash 能「看見」版面，並產生保留表格的乾淨 Markdown。雖然成本較高，但準確率的提升值得這個代價。

| 方法 | 100 頁掃描合約 | 準確率 | 成本 |
|--------|---------------------------|----------|------|
| Tesseract | 雜訊多、表格破碎 | 60% | $0.02 |
| AWS Textract | 較佳，但版面仍有困難 | 75% | $0.15 |
| Gemini 3 Flash | 乾淨的 Markdown，表格完整 | 92% | $0.35 |

### 2. 平行擷取器 vs 單次擷取（Single-Pass）

**解答：** 用單一 prompt 要求擷取所有欄位，效果會比專用擷取器來得差。每個擷取器都有聚焦的 prompt 與 schema：

```python
parties_schema = {
    "type": "object",
    "properties": {
        "party_a": {"type": "object", "properties": {
            "name": {"type": "string"},
            "role": {"type": "string"},
            "address": {"type": "string"}
        }},
        "party_b": {"type": "object", "properties": {...}}
    }
}

# Each extractor runs in parallel
async def extract_all(document: str):
    results = await asyncio.gather(
        extract_parties(document, parties_schema),
        extract_dates(document, dates_schema),
        extract_obligations(document, obligations_schema),
        extract_termination(document, termination_schema)
    )
    return merge_results(results)
```

### 3. 跨欄位驗證（Cross-Field Validation）

**解答：** 擷取錯誤往往會透過不一致性顯現出來：
- 如果 `effective_date` 晚於 `termination_date`，就表示有問題
- 如果 `party_a` 的名稱出現在 `obligations` 中，但拼法不同，則標記為待審查
- 如果擷取到 `payment_amount`，但 `payment_frequency` 為 null，則屬於不完整

---

## 處理 200 頁文件

context window 的挑戰：

```mermaid
flowchart LR
    subgraph Chunking["Smart Chunking"]
        DOC[200-page Contract] --> DETECT[Section Detector]
        DETECT --> SECTIONS[Logical Sections<br/>Recitals, Terms, Exhibits]
    end

    subgraph Process["Selective Processing"]
        SECTIONS --> FILTER{Relevant Section?}
        FILTER -->|Yes| EXTRACT[Extract Fields]
        FILTER -->|No| SKIP[Skip / Store Reference]
    end

    subgraph Merge["Result Assembly"]
        EXTRACT --> RESULTS[Partial Results]
        SKIP --> REFS[Section References]
        RESULTS --> FINAL[Final JSON]
        REFS --> FINAL
    end
```

**關鍵洞見：** 並非全部 200 頁都包含可擷取的欄位。附件（隨附的原始文件）以參照的方式儲存，而不加以處理。「條款與條件」（Terms and Conditions）章節往往佔了文件的 80%，但也涵蓋了大多數關鍵欄位。

---

## 多語言處理

德文合約使用的結構與英文合約不同。我們維護各語言專屬的擷取器：

```python
EXTRACTORS = {
    "en": {
        "parties": EnglishPartiesExtractor(),
        "dates": StandardDatesExtractor(),
        "termination": EnglishTerminationExtractor()
    },
    "de": {
        "parties": GermanPartiesExtractor(),  # Handles "GmbH", "AG" patterns
        "dates": GermanDatesExtractor(),       # DD.MM.YYYY format
        "termination": GermanTerminationExtractor()  # "Kündigung" patterns
    }
}
```

---

## 成本拆解

| 階段 | 每份 100 頁文件的成本 |
|-------|----------------------|
| OCR（Gemini 3 Flash，若為掃描版） | $0.18 |
| 章節偵測（GPT-4o-mini） | $0.03 |
| 欄位擷取（4 個平行，GPT-4o-mini） | $0.12 |
| 驗證 | $0.02 |
| **總計（掃描版）** | **$0.35** |
| **總計（原生 PDF）** | **$0.17** |

平均（60% 原生、40% 掃描版）：**每份文件 $0.24**（低於 $0.50 的目標）

---

## 面試延伸問題

**Q：如果擷取的信心分數很低怎麼辦？**

A：我們會為每個欄位輸出一個信心分數。低於 0.8 的欄位會被標記為待人工審查。UI 會顯示一個「審查佇列」，讓人工只需驗證不確定的欄位，而不必審閱整份文件。這將人工投入的時間平均降低到每份文件 30 秒。

**Q：你們如何處理版面非標準的合約？**

A：我們維護一個已知合約範本的「版面庫」（layout library）。章節偵測器會先嘗試比對已知範本。若無相符，則回退到啟發式偵測（尋找編號章節、全大寫標題等）。未知版面會被標記，並在人工審查後加入版面庫。

**Q：那些關鍵條款定義在附件中的合約呢？**

A：我們會偵測交叉參照（「如附件 A 所定義」）並加以解析。當主文件參照到附件時，擷取的 prompt 會納入相關的附件內容。這可避免在答案位於附件中時出現「null」的擷取結果。

---

## 面試重點整理

1. **Vision-LLM 在複雜版面（表格、註記）上勝過傳統 OCR**
2. **平行的專用擷取器在結構化擷取上優於單次擷取**
3. **跨欄位驗證能在擷取錯誤進入資料庫之前將其攔截**
4. **並非所有頁面都需要處理**：偵測相關章節，略過附件

---

*相關章節：[OCR 與版面分析](../10-document-processing/01-ocr-and-layout.md)、[結構化生成](../05-prompting-and-context/06-structured-generation.md)*
