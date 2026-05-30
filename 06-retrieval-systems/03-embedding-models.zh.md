# Embedding Models

Embedding 模型將文字轉換為高維度向量。技術前沿已超越了靜態的單一向量表示法，邁向 **多解析度 (multi-resolution)、late-interaction，以及多模態 (multimodal)** 的 embedding。

## 目錄

- [Embedding 技術前沿（Matryoshka）]( #matryoshka)
- [Late Interaction（ColBERT v2）]( #late-interaction)
- [Binary 與 Int8 量化]( #quantization)
- [模型選型準則]( #selection)
- [多模態 Embedding（Vision + Text）]( #multimodal)
- [面試問題]( #interview-questions)
- [參考資料]( #references)

---

## Embedding 技術前沿：Matryoshka Embeddings

傳統上，如果你把文字 embed 成 1,536 個維度，那麼搜尋時就只能被迫使用全部 1,536 個維度。

**Matryoshka Representation Learning (MRL)**
- 模型在訓練時被引導將最重要的資訊「儲存」在前幾個維度中。
- **優勢**：你可以用 1,536 維來 embed，但在「快速搜尋」階段只索引前 **64 維**，接著再用完整的 1,536 維對排名最前的結果進行精煉。
- **效率**：記憶體／索引大小可縮減 20 倍，而準確度下降幅度小於 2%。

---

## Late Interaction：ColBERT v2

標準的 embedding 屬於「Bi-Encoders」（每個 chunk 一個向量）。**ColBERT**（Contextualized Late Interaction over BERT）則採用「token 層級」的做法。

- **做法**：ColBERT 不是每個 chunk 一個向量，而是 **每個 token** 一個向量。
- **互動**：在查詢時，模型會將你查詢中的每個 token 與文件中的每個 token 進行比較（即「MaxSim」運算）。
- **現況**：ColBERT v2（以及後繼者如 ColPali、ColQwen2.5、ColNomic，用於文件與 pages-as-images）透過 PLAID 索引大幅壓縮，使其在生產環境中具備可行性。對於「大海撈針」式的技術查詢，它能達到高得多的精準度。

---

## Binary 與 Int8 量化

儲存 `float32` 向量的成本很高。生產環境的索引大量仰賴 **模型內量化 (in-model quantization)**。

- **Binary Embeddings**：將向量轉換為 1 與 0。
  - **記憶體**：縮減 32 倍。
  - **速度**：在現代 CPU 上，Hamming distance（XOR 運算）比 Cosine similarity 快 10 倍。
- **Int8/Int4**：由像 `text-embedding-3-small` 這類模型原生支援。

---

## 模型選型準則

| 模型 | 供應商 | 特性 | Context |
|-------|----------|----------|---------|
| **Gemini Embedding 001** | Google | 多模態（text、image、video、audio、PDF）、共享 3072 維空間、MTEB-English 領先者 | 8k |
| **Qwen3-Embedding-8B** | Open Source | MTEB-Multilingual 領先者、instruction-tuned、長文件表現強 | 32k |
| **Llama-Embed-Nemotron-8B** | NVIDIA | 頂尖的多語言分數、open weights | 8k |
| **Cohere Embed v4** | Cohere | 多模態（text + image）、Matryoshka、binary 量化 | 128k |
| **Voyage-Multimodal-3.5** | Voyage AI | 統一的 text/image、針對 retrieval 調校 | 32k |
| **OpenAI text-embedding-3-large** | OpenAI | Matryoshka、原生 Int8、廣泛支援 | 8k |
| **BGE-M3** | Open Source | 多語言、多粒度（dense + sparse + late-interaction） | 8k |
| **Jina-Embeddings-v3** | Jina AI | 支援 late-interaction、長 context | 128k |

開放權重模型（Qwen3、Llama-Embed-Nemotron、BGE）如今在純 MTEB 分數上已能追平甚至擊敗商用 API。當你想要託管式基礎設施與 SLA 時，選擇商用方案；當高流量下的每次查詢成本比延遲下限更重要時，則選擇開放權重模型。

---

## 多模態 Embedding

純文字的 RAG 會悄悄地丟棄圖表、表格、示意圖以及版面配置訊號，而答案往往就藏在這些之中。現代技術堆疊將頁面、螢幕截圖與插圖視為一等公民的 retrieval 物件：

- **統一的 vision-text embedding**：Cohere Embed v4、Voyage-Multimodal-3.5、Gemini Embedding 001 都共享單一向量空間，因此你可以拿「緊急關閉閥在哪裡？」這類查詢去比對示意圖。
- **搭配 late interaction 的 page-as-image**：ColPali、ColQwen2.5 與 ColNomic 直接對每一頁的渲染結果進行 embed，跳過脆弱的 OCR，並保留視覺層次結構。
- **CLIP 家族模型**：對於圖片密集的目錄（電商、媒體）仍然好用，因為 text-image 對齊正是其核心訊號。

---

## 面試問題

### Q：embedding 中的「Vocabulary Mismatch」（詞彙不匹配）問題是什麼？

**強力解答：**
Embedding 仰賴訓練期間所學到的語意空間。如果使用者的查詢使用了一個較新的詞彙（例如，在 embedding 模型的知識截止之後才發布的模型名稱），而該詞彙不在 embedding 模型的訓練集中，模型可能會賦予它一個通用的「AI」向量，因而錯失特定的細微差異。標準的解法是 **Hybrid Search**（用 BM25 來捕捉特定關鍵字）加上 **Cross-Encoder Reranking**，後者透過同時檢視查詢與文件的 token，能更好地處理分布外 (out-of-distribution) 的詞彙。

### Q：為什麼你會為一個 10 億向量的索引選擇 Matryoshka 模型？

**強力解答：**
若要用標準的 `float32` 1536 維 embedding 擴展到 10 億個向量，HNSW 索引大約需要 ~6TB 的高速 RAM，成本高得令人卻步。有了 Matryoshka 模型，我可以用前 128 個維度（經 Binary 量化）來進行初步檢索。這能將記憶體佔用減少超過 90%，使「Top 1,000」候選結果得以在便宜許多的硬體上找到。接著，我只需為這 1,000 個候選結果取出完整解析度的向量，來執行最終的 reranking。

---

## 參考資料
- Kusupati et al. "Matryoshka Representation Learning" (2022/2024 update)
- Khattab et al. "ColBERT v1 & v2: Efficient Late Interaction" (2021/2023)
- OpenAI. "Introducing New Embedding Models with Matryoshka Support" (2024)

---

*下一篇：[Vector Databases](04-vector-databases.md)*
