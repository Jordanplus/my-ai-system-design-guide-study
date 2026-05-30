# Chunking 策略

Chunking 是將文件切分成可供檢索的離散片段的過程。生產環境的 pipeline 已經超越了盲目的固定大小切分，轉向**結構感知與語意片段**，而 late chunking 與上下文前綴（contextual prepending）等較新的技術，如今也已成為主流工具箱的一部分。

## 目錄

- [檢索與上下文之間的拉鋸](#tension)
- [遞迴式結構切分](#recursive)
- [語意 Chunking](#semantic)
- [階層式（父子）Chunking](#hierarchical)
- [內容專屬策略（程式碼、PDF、表格）](#content-specific)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 檢索與上下文之間的拉鋸

| 面向 | 小 Chunk（100t） | 大 Chunk（1000t） |
|--------|---------------------|----------------------|
| **精確度** | 高（精準匹配） | 低（被稀釋） |
| **上下文** | 差（句子被切斷） | 豐富（包含周邊資訊） |
| **儲存** | 高（向量較多） | 低（向量較少） |
| **延遲** | 低（搜尋快速） | 高（檢索負擔重） |

**準則**：要*找到*資訊，越小越好；但要*思考*推理，越大越好。使用**階層式 Chunking** 兼得兩者。

---

## 遞迴式結構切分

我們不是每 500 個字元就切一刀，而是在邏輯邊界處切分：
`[雙換行] > [單換行] > [句號] > [空格]`。

**最佳實務**：使用 **Markdown 感知切分（Markdown-Aware Splitting）**。如果文件帶有 `#` 標題，請確保把標題前綴加到*每一個*子 chunk 上，以保留上下文（Contextual Chunking）。

---

## 語意 Chunking

語意 chunking 使用 embedding model 來偵測「主題轉換」。

1. 將文字切分成個別句子。
2. 只要句子之間的 embedding 相似度維持在門檻之上（例如 0.82），就將它們歸為同一組。
3. 一旦相似度下降，就開啟新的 chunk。

**細節**：生產環境的 pipeline 越來越常使用 **Cross-Encoder 分段器（Cross-Encoder Segmenters）**。一個極小的模型會掃描文字，並在每個語意斷點預測出一個「Separator token」。這比餘弦相似度門檻法的準確度高出 10 倍。

---

## 階層式（父子）Chunking

這是生產環境 RAG 的業界標準。

- **流程**： 
  1. 建立 1,500 token 的「父（Parent）」chunk。
  2. 將每個父 chunk 再細分成 5 個 300 token 的「子（Child）」chunk。
  3. **只索引子 chunk**。
  4. 在檢索時，如果某個子 chunk 命中，就**將完整的父 chunk 上下文回傳**給 LLM。
- **為什麼？**：子 chunk 很小，向量資料庫容易匹配。父 chunk 則提供足夠的上下文，讓 LLM 能真正正確推理，避免「上下文斷裂」造成的幻覺。

---

## 內容專屬策略

### 1. 程式碼 Chunking
- **策略**：使用 AST（Abstract Syntax Tree，抽象語法樹）剖析。
- **準則**：絕不從函式主體中間切開。讓 import 與 class 宣告與其方法保持在一起。

### 2. 表格 Chunking
- **策略**：對表格使用 Markdown 格式。
- **現代做法**：「摘要式表格（Summarized Tables）」。在向量資料庫中儲存表格的自然語言摘要，但回傳給 LLM 的則是完整的 Markdown 表格。

### 3. PDF／版面 Chunking
- **策略**：使用 **Vision-Language Model（VLM，視覺語言模型）** 預處理（例如 ColPali）。
- **細節**：不只儲存文字，而是儲存能代表頁面*位置版面*的 embedding，確保圖表與側欄不會與正文混在一起。

---

## 面試問題

### Q：為什麼帶 overlap 的固定大小 chunking 對生產系統而言會有問題？

**強力答案：**
固定大小 chunking 是「內容盲目」的。它經常在思緒中途切斷句子、打斷數學方程式，並把標題與其描述文字分開。雖然「Overlap」（例如 10%）藉由在 chunk 之間重複 10% 的文字來緩解這個問題，卻無法解決核心癥結：模型的 attention 被迫從破碎的字串中重建意義。現代 pipeline 偏好**語意或邏輯式 Chunking（Semantic or Logical Chunking）**，因為它能確保每個向量都代表一個「完整語意單元」，進而帶來顯著更高的檢索精確度。

### Q：什麼是「Contextual Retrieval」（Anthropic 提出的模式）？

**強力答案：**
Contextual Retrieval 是指在 embedding 每個 chunk 之前，先在其前面加上一句全域性的上下文。舉例來說，如果某個 chunk 講的是「電池續航力」，但它出自一份「2025 Model X 無人機」的手冊，就會在這個 chunk 加上 `[Drone_Model_X_Manual]:` 這段文字。這能確保「電池續航力」的向量受到「無人機」上下文的影響，避免它被誤檢索到「手機電池」這類查詢上。

---

## 參考資料
- Anthropic. "Contextual Retrieval: Improving RAG Accuracy" (2024)
- LlamaIndex. "Advanced Chunking Strategies for RAG" (2025)
- LangChain. "RecursiveCharacterTextSplitter Benchmarks" (2024)

---

*下一篇： [Embedding Models](03-embedding-models.md)*
