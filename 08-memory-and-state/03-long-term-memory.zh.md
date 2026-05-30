# 長期記憶

長期記憶（L2 與 L3）負責提供跨 session 的持久化能力。生產環境的技術堆疊已經從單純的「History RAG」演進到結合 Vector、Graph 與 Relational 資料的 **Multi-Representation Stores**。如今專門的記憶服務（Zep、Mem0、Letta、Cognee）將這些儲存層封裝起來，並內建對話摘要、entity extraction 與時序感知（temporal awareness）等功能。

## 目錄

- [情節記憶（敘事）](#episodic)
- [語意記憶（知識）](#semantic)
- [Hybrid Vector-Graph 儲存](#hybrid)
- [記憶修剪與衰減](#pruning)
- [隱私與多租戶](#privacy)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 情節記憶（Episodic Memory）：個人日誌

情節記憶儲存的是 **Trajectories（軌跡）**：一連串的事件及其結果。
- **資料結構**：`(Timestamp, Interaction_ID, Trajectory_Summary, Embedding)`。
- **背後的理由**：如果某個 agent 上個月用特定的工具序列成功建立了一個 React 元件，那麼當今天被要求再建立一個時，它應該要能「回憶」起那次成功的經驗。
- **實作備註**：我們儲存 *Summary* 以供檢索，並將 *Raw Logs* 存放在冷儲存（S3/GCS）中，以供事後鑑識分析（forensic analysis）。

---

## 語意記憶（Semantic Memory）：事實儲存庫

語意記憶儲存關於各個 entity 的 **Discovered Facts（已發掘的事實）**。
- **Entity 辨識**：使用「Fact Extraction Agent」來解析每一輪的使用者對話。
- **三元組（triplet）範例**：
  - `(User_1, HAS_PREFERENCE, Dark_Mode)`
  - `(Company_X, USES_SDK, Stripe)`
- **技術**：Knowledge Graphs（Neo4j、AWS Neptune）結合關聯式標記（relational tagging）。

---

## Hybrid Vector-Graph 儲存

Staff 等級的工程師會採用 **GraphRAG 風格的 Memory**。
- **Vector Search** 找出「Related（相關）」的節點。
- **Graph Traversal** 找出「Connected（相連）」的節點。
- **致勝之處**：如果我搜尋「Project Alpha」，vector search 會找到這個名稱，但 graph traversal 則會找出那 10 位開發者、deadline，以及連結的程式碼儲存庫。

---

## 記憶修剪與衰減

如果記憶無節制地成長，它就會變成一種負債。
- **Temporal Decay（時序衰減）**：較舊的記憶若沒有被頻繁存取，其「relevance score（相關性分數）」就會逐漸降低。
- **Consolidation（彙整）**：將 10 筆關於「billing」的獨立互動合併成一個高品質的摘要節點。
- **Explicit Forgetting（明確遺忘）**：刪除與某個 user ID 關聯的所有情節與語意叢集（cluster），以遵循 GDPR 的「被遺忘權（Right to be Forgotten）」。

---

## 隱私與多租戶

> [!CAUTION]
> **Cross-Session Leakage（跨 session 洩漏）** 是全域記憶中排名第一的安全風險。
> 請確保 `user_id` 在你的 vector DB metadata 中是一個硬性的 partition key。絕對不要依賴 LLM 來依使用者過濾結果。

---

## 面試問題

### Q：在長期記憶上，你如何在 Vector DB 與 Knowledge Graph 之間做選擇？

**理想答案：**
我會將 **Vector DBs** 用於 **Episodic Context（情節脈絡）**（非結構化的 log、過往對話），因為我需要在語意上進行「Fuzzy（模糊）」匹配。我會將 **Knowledge Graphs** 用於 **Structural Semantic Knowledge（結構化語意知識）**（關係、屬性、階層），因為我需要「Deterministic（確定性）」的 traversal。生產系統會採用 **Hybrid（混合）** 方法：由 vector index 指向 graph ID，讓系統先找到正確的「Starting Node（起始節點）」，再進行 traversal 以取得高精度的脈絡。

### Q：在學習式 agentic memory 的脈絡下，什麼是「Catastrophic Forgetting（災難性遺忘）」？

**理想答案：**
在 fine-tuned 的 agent 中，catastrophic forgetting 發生於新的訓練資料抹除了舊有的知識時。而在 **Agentic Memory（以 RAG 為基礎）** 中，它指的是 **Index Overload（索引過載）**。如果某個 agent 在它的記憶中加入了 1,000 筆低品質的新「事實」，檢索精度就會下降，實質上使它「忘記」那些較舊、品質較高的事實，因為它們被淹沒在雜訊之中。我們會以 **Quality-Weighted Retrieval（品質加權檢索）** 來緩解這個問題：由 supervisor 給予高「Verification Scores（驗證分數）」的記憶，會被提升排序，優先於原始的 log。

---

## 參考資料
- Neo4j. "Knowledge Graphs for Generative AI" (2025)
- Pinecone. "The Managed Memory Layer" (2025)
- GraphRAG. "Reasoning over Relationships" (2024/2025)

---

*下一篇：[使用 Mem0 的 Agentic Memory](04-agentic-memory-mem0.md)*
