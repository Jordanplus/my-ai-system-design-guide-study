# 進階檢索模式

除了基礎之外，生產級的 RAG 系統會運用專門的模式來處理複雜的 query-document 落差。這些模式是高精準度搜尋的「獨門秘方」，並且愈來愈常被整合進託管式的 RAG 服務中。

## 目錄

- [Query Decomposition（多重查詢）](#query-decomposition)
- [Hypothetical Document Embeddings (HyDE)](#hyde)
- [Contextual Retrieval（Anthropic 模式）](#contextual)
- [迭代式文件擴充](#enrichment)
- [In-Context Reranking](#reranking)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## Query Decomposition（多重查詢）

複雜的使用者查詢通常是「Compound Queries（複合查詢）」。
- **使用者**：「比較我們 Q3 與 Q4 的營收並解釋為何下滑。」
- **Decomposition（拆解）**：
  1. 「Q3 Revenue」
  2. 「Q4 Revenue」
  3. 「Q4 營收變動的原因」
- **實作方式**：使用 LLM 產生這 3 個子查詢，針對全部子查詢搜尋 DB，並彙整其 context。

---

## Hypothetical Document Embeddings (HyDE)

查詢很短，文件卻很長。這種「Asymmetry（不對稱性）」會造成檢索失敗。
- **模式**：
  1. 取得使用者查詢。
  2. 詢問 LLM：「為這個問題寫出一段假設性的答案。」
  3. **對這個假設性答案進行 embedding**，而非對查詢進行 embedding。
- **為什麼？**：這個假設性答案與真實文件處於相同的「Vector neighborhood（向量鄰域）」中，因此能帶來高出許多的 recall。

---

## Contextual Retrieval（Anthropic 模式）

這個模式由 Anthropic 在 2024 年底加以標準化，用來解決 **Context Dilution（脈絡稀釋）**。

- **問題**：某個 chunk 可能寫著「It costs $200」，但若缺少 header，我們便無從得知「It」指的是「Widget-X」。
- **模式**：在 ingestion 期間，對於每一個 300-token 的 chunk，讓 LLM 撰寫一段 50-token 的 context 字串（例如：「This chunk is about the pricing for Widget-X in the North American market」）。
- **效益**：針對片段化的資料，可將檢索精準度提升 30-50%。

---

## 迭代式文件擴充

我們不只儲存原始文件，而是儲存「Enriched（已擴充）」的中繼資料。
- **Summary（摘要）**：儲存文件的一段式摘要。
- **Q&A Generation（問答生成）**：產生這份文件能回答的 5 個問題，並將這些問題*連同*文件一起進行 embedding。
- **現況**：目前大多數高階的 RAG 系統會對 **「Questions（問題）」** 而非 **「Answers（答案）」** 進行 embedding，以契合使用者的查詢意圖。

---

## In-Context Reranking

由於 1M-2M 的 context window 現已成為標準（Claude Sonnet 4.6、Gemini 3.1 Pro），**Rank-by-Context** 成為一個可行的模式。
1. 檢索 Top 100 篇文件。
2. 將全部 100 篇放入 context window。
3. 詢問模型：「閱讀這 100 篇文件，找出最相關的 5 篇。接著，用那 5 篇來作答。」
- **優勢**：這充分運用了模型的 **Long Context Reasoning（長脈絡推理）** 來執行 reranking，而無需另外使用一個 Cross-Encoder 模型。

---

## 面試問題

### Q：為什麼 HyDE（Hypothetical Document Embedding）對某些應用而言具有風險？

**理想答案：**
HyDE 仰賴「Hallucinating（幻覺式產生）」一個基準答案來尋找真實資料。如果使用者的查詢描述的是不存在或邏輯上不可能的事物，LLM 仍然會產生一個假設性的答案。這可能會從資料庫中拉入「Incorrect but Semantically Similar（錯誤但語意相近）」的資料，進而強化模型最初的幻覺。標準的緩解方式是採用 **Hybrid（混合）方法**：用真實查詢（Keyword）檢索一次，再用 HyDE 查詢檢索一次，然後使用 **RRF** 將兩者結合。

### Q：什麼是「Asymmetric Retrieval（不對稱檢索）」問題？

**理想答案：**
Asymmetric retrieval 指的是這樣的事實：使用者查詢通常很短（3-10 個字），而文件 chunk 卻很長（300-500 個字）。兩者在向量空間中處於不同的統計分布，因而導致「Distance Bias（距離偏差）」。高效能系統會使用 **Asymmetric Encoders（不對稱編碼器，一個模型負責查詢、一個模型負責文件）** 或 **Query Expansion（查詢擴充，HyDE）** 來解決此問題，將查詢「膨脹」成類似文件的分布。

---

## 參考資料
- Gao et al. "Precise Zero-Shot Dense Retrieval without Relevance Labels" (HyDE, 2023/2024)
- Anthropic. "The Contextual Retrieval Playbook" (2024)
- LlamaIndex. "Query Transformation Cookbook" (2025)

---

*下一篇：[Agentic Systems](../07-agentic-systems/01-agents-fundamentals.md)*
