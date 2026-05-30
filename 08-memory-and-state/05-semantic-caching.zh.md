# 語意快取（Semantic Caching）

快取技術已從精確字串比對演進到**語意比對（Semantic Matching）**。語意快取透過為「等價」查詢重複使用既有的 completion，可降低 **30-70%** 的成本，並將延遲從數秒縮短到數毫秒。

## 目錄

- [精確快取 vs. 語意快取](#vs)
- [語意比對流程](#pipeline)
- [RedisVL 與 GPTCache](#tech-stack)
- [評估：命中率 vs. 幻覺漂移](#eval)
- [多模態語意快取](#multimodal)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 精確快取 vs. 語意快取

| 特性 | 精確快取（Redis/Memcached） | 語意快取（RedisVL/Qdrant） |
|---------|-------------------------------|---------------------------------|
| **Key** | 雜湊後的查詢字串 | 查詢的 embedding 向量 |
| **比對**| 100% 字串完全一致 | Cosine Similarity > 閾值 |
| **效率**| 低（細微的拼字錯誤就會使快取失效） | 高（能理解意圖） |
| **風險** | 零 | 語意漂移（Semantic Drift，回傳錯誤答案） |

---

## 語意比對流程

1. **Embed**：將傳入的查詢轉換為向量（例如使用 `text-embedding-3-small`）。
2. **Search**：在快取中搜尋最近鄰（nearest neighbor）。
3. **Threshold Check**：若 `distance < 0.05`（非常相似），則回傳快取結果。
4. **LLM Verification**：對於高風險（high-stakes）查詢，使用一個極小的「Verifier Model」（例如 GPT-5.5-mini、Claude Haiku 4.5）來檢查快取的回應是否真的能回答這個新查詢。
5. **Update**：若未命中，則呼叫 LLM 並將新結果存入向量快取。

---

## RedisVL 與 GPTCache

標準技術堆疊：
- **RedisVL**：直接在 Redis 實例中提供低延遲的向量搜尋。
- **Hybrid Caching**：使用 Redis 同時存放 metadata（key）與向量 payload。
- **TTL**：語意快取應設定 TTL（Time-To-Live，存活時間）。常見的模式是 **Dynamic TTL**：熱門答案存活更久，而「過時（stale）」的資訊則會被定期淘汰。

---

## 多模態語意快取

隨著原生多模態的前沿模型（Gemini 3.1 Pro、GPT-5.5、Claude Opus 4.7）問世，我們現在也能快取**圖片與音訊查詢**。
- **Visual Similarity**：若先前已處理過語意相似的圖片，便快取該圖片的描述。
- **Audio Fingerprinting**：為相似的語音指令快取其轉錄文字（transcript）。

---

## 面試問題

### Q：快取中的「語意漂移（Semantic Drift）」是什麼？你如何防止它？

**優秀答案：**
當相似度閾值設定得太寬鬆時（例如 0.8 而非 0.95），就會發生語意漂移。像是 *"How do I fix my car?"* 這樣的查詢，可能會比對到 *"How do I wash my car?"* 的快取回應。為了防止這種情況，我們會採用**多階段驗證（Multi-Stage Validation）**：1) 向量相似度檢查、2) **Entity-Match check**（確保兩個查詢都涉及「Car」以及相同的「Verb」），以及 3) **閾值收緊（Threshold Tightening）**：對於技術或醫療類查詢，我們要求相似度需 $>0.98$ 才會回傳快取結果。

### Q：為什麼在低流量時，語意快取有時反而*比*原始的 LLM 呼叫更昂貴？

**優秀答案：**
因為語意快取本身就需要一次**Embedding API call** 與一次**向量搜尋查詢**。如果 embedding 模型成本為 $0.02、搜尋耗時 100ms，而你主要的 LLM 呼叫僅需 $0.05、耗時 500ms，那麼相對的節省幅度就很小。語意快取唯有在**高規模（High Scale）**（數百萬請求）下才會成為顯著的優勢——此時快取命中率高到足以抵銷這筆「Embedding Tax」，並大幅降低整體延遲。

---

## 參考資料
- Redis. "RedisVL: Python Client for Redis Vector Library" (2025)
- Akiba et al. "GPTCache: A Library for Creating Semantic Cache" (2024/2025)
- Google Cloud. "Generative AI Caching Patterns" (2025)

---

*下一篇：[狀態管理模式](06-state-management-patterns.md)*
