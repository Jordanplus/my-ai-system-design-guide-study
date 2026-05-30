# 記憶架構

LLM 的記憶已從「歷史緩衝區」演進為**三層認知架構（Three-Tiered Cognitive Architecture）**。這套階層模仿人類的認知系統（L1-L3），以在速度、成本與回憶容量之間取得平衡。如今的正式環境 agent 技術堆疊，多半在 vector store 之上倚賴專屬的記憶層（Mem0、Zep、Letta、Cognee），而非自行打造。

## 目錄

- [三層階層架構](#hierarchy)
- [第一層：工作記憶（Context）](#tier-1)
- [第二層：情節記憶（Events）](#tier-2)
- [第三層：語意記憶（Knowledge）](#tier-3)
- [記憶整合模式](#consolidation)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 三層階層架構

| 層級 | 類型 | 人類類比 | 技術 | 延遲 |
|------|------|---------------|------------|---------|
| **L1** | 工作記憶 | 當下的專注焦點 | Context Window / KV Cache | <50ms |
| **L2** | 情節記憶 | 過往經驗 | Vector DB / Local Graph | 100-300ms |
| **L3** | 語意記憶 | 一般性知識 | Global Graph / SQL / Mem0 | >500ms |

---

## 第一層：工作記憶（L1）

L1 是模型的**主動專注焦點**。
- **Context Window**：在當前前沿模型上為 128K - 2M tokens（Claude Opus 4.7、Claude Sonnet 4.6、GPT-5.5、Gemini 3.1 Pro）。
- **KV Cache**：用來儲存預先計算好的 keys 與 values 的 GPU「RAM」。
- **管理策略**：**Sliding Windows** 與 **Prefix Caching**（vLLM/PagedAttention）。
- **冗餘性備註**：我們只在 L1 中保留最近的對話輪次與關鍵的系統指令。

---

## 第二層：情節記憶（L2）

L2 儲存本次工作階段、或與該使用者過往工作階段中「先前發生了什麼」。
- **儲存**：Vector databases（Pinecone、Weaviate、Qdrant）。
- **檢索**：語意搜尋。若使用者詢問「我們上週二聊了什麼？」，由 L2 提供答案。
- **模式**：**Experience Replay**。Agent 會檢索過去成功的軌跡，以指引當前的決策。

---

## 第三層：語意記憶（L3）

L3 儲存**不可變的事實（Immutable Facts）**與**習得的規則（Learned Rules）**。
- **Knowledge Graphs**：儲存關係（例如 `User` -- `WORKS_FOR` --> `Company_X`）。
- **Mem0**：一項受管理的服務，會擷取事實（例如「使用者喜歡 Dark Mode」）並使其在全域範圍內皆可取用。
- **真相錨定（Truth Anchoring）**：當 L1 與 L2 提供相互矛盾的資訊時，L3 扮演「Ground Truth」的角色。

---

## 記憶整合模式

記憶透過**整合（Consolidation）**在各層之間移動：
1. **擷取（Extraction）**：在工作階段結束時，由一個 LLM「審閱者（Reviewer）」從 L1 中擷取事實。
2. **建立索引（Indexing）**：事實被儲存到 L2（作為 vectors）與 L3（作為 graph nodes）。
3. **衰減（Decay）**：陳舊、未獲強化的記憶會從 L2 移至冷儲存（L3）或被刪除。

---

## 面試問題

### Q：為何不直接用一個 2M token 的 context window 來承載所有記憶（L1-L3）？

**強而有力的回答：**
雖然技術上可行，但這在**經濟與認知層面皆無效率**。
1. **成本**：每一輪都以 1M+ tokens 呼叫模型，其花費遠高於以 RAG 回憶出脈絡的 10K token 呼叫。
2. **注意力稀釋（Attention Dilution）**：即使是「Long Context」模型，「Lost in the Middle」仍是一項因素。若脈絡被無關的歷史輪次塞滿，模型對*當前*任務的推理能力便會退化。
3. **延遲**：由於需載入 KV cache，TTFT（Time to First Token）會隨脈絡大小而增長。
staff 等級的架構會運用**策略性檢索（Strategic Retrieval）**，讓 context window 保持精簡且聚焦。

### Q：在第三層（全域語意記憶）中，你如何處理「隱私外洩（Privacy Leakage）」？

**強而有力的回答：**
第三層（語意記憶）必須**依命名空間分片（Sharded by Namespace）**。每位使用者或組織在 vector DB 與 Knowledge Graph 中都會取得一個獨一無二的 `namespace_id`。我們在資料庫層實作 **RLS（Row Level Security）**。此外，我們在整合（Consolidation）步驟中使用一層 **PII-Scrubbing Layer**，以確保敏感資料（密碼、PII）絕不會從短暫的 L1 脈絡移入持久化的 L3 知識庫。

---

## 參考資料
- Pack et al. "Generative Agents" (2023/2025 Context)
- OpenAI. "Context Window Optimization" (2025)
- Mem0 Documentation. "Dynamic Memory Management" (2025)

---

*下一篇：[短期脈絡管理](02-short-term-context.md)*
