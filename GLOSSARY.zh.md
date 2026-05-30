# AI 系統設計術語表

本指南通篇使用之關鍵術語的快速參考。

---

## A

**Agentic Coding** — 由 LLM 自主編輯檔案、執行 shell 指令、撰寫測試並反覆迭代，直到完成一項編碼任務。Claude Code、OpenHands 與 Cline 即為範例。

**Agentic System（代理式系統）** — 使用工具自主規劃並執行多步驟任務的 LLM 應用程式。

**Attention Mechanism（注意力機制）** — 讓模型聚焦於輸入相關部分的神經網路元件。Self-attention 會將每個 token 與所有其他 token 進行比較。

**ABAC（Attribute-Based Access Control，屬性型存取控制）** — 依據使用者、資源與環境的屬性，而非固定角色來進行存取控制。

---

## B

**Batching（批次處理）** — 將多個請求一併處理以提升 GPU 使用率。Continuous batching 會在其他請求仍在生成時加入新請求。

**BM25** — 傳統的關鍵字排序演算法。常與向量搜尋結合以進行 hybrid retrieval。

**Budget Tokens** — 用於 Extended Thinking（Claude）或 reasoning（o3）的可設定運算預算。預算越高 → 內部推理步驟越多 → 準確度與成本越高。

---

## C

**Chain-of-Thought (CoT)** — 在給出最終答案前引導出逐步推理的提示技巧。

**Chunking（切塊）** — 將文件切分成較小片段以供 embedding 與檢索。策略包括固定大小、語意式與階層式。

**Claude Code** — Anthropic 原生於終端機的自主編碼代理。使用 bash、text_editor 與 computer 工具，在整個專案中讀取、編輯並執行程式碼。透過 CLAUDE.md 清單檔案進行控制。

**Cline** — 開源的 VS Code 擴充套件，提供具備工具使用能力（檔案編輯、終端機、瀏覽器）的自主 AI 編碼功能。原生支援 MCP。

**Computer-Use** — 一種模型能力（Claude 3.5+ 原生支援），可透過模擬滑鼠點擊、鍵盤輸入與螢幕截圖來控制 GUI。可實現瀏覽器與桌面自動化。

**Context7** — 在執行階段擷取最新函式庫文件的 MCP 伺服器，解決編碼代理「訓練資料過時」的問題。

**Context Window（上下文視窗）** — LLM 在單一請求中所能處理的最大 token 數。範圍從 4K 到 1M+ tokens 不等。

**Cosine Similarity（餘弦相似度）** — 衡量兩個向量之間相似程度的指標。比較 embeddings 的標準度量。

**Cursor** — AI 原生 IDE（VS Code 的分支），具備深度模型整合，用於程式碼自動完成、代理式編輯與多檔案上下文感知。

---

## D

**DPO（Direct Preference Optimization，直接偏好最佳化）** — 一種 fine-tuning 方法，直接在偏好資料上進行最佳化，而不需另設 reward model。

**DSPy** — 透過可最佳化的模組（而非手動撰寫的 prompts）來程式化 LLM 的框架。

---

## E

**Embedding** — 文字的稠密向量表示。用於語意搜尋與相似度比較。

**Ensemble（集成）** — 結合多個模型輸出以提升可靠性。包括投票、辯論與 mixture-of-agents。

**Extended Thinking** — Claude（3.7+）的內部推理模式，模型會在產生回應前先進行一次草稿式（scratchpad）推理。可透過 `thinking.budget_tokens` 設定。預設不會顯示給終端使用者。

---

## F

**Few-Shot Prompting** — 在 prompt 中包含範例以引導模型行為。

**Fine-Tuning** — 在特定任務的資料上訓練一個預訓練模型以提升效能。

**Function Calling** — LLM 輸出結構化工具呼叫（而非純文字）的能力。

---

## G

**Guardrails（防護欄）** — 對輸入/輸出進行驗證，以防止有害或離題的回應。

**Grounding** — 將 LLM 回應連結至事實來源，以降低 hallucination。

**Grok 4.3** - xAI 的前沿推理模型。在推理基準測試上與 GPT-5.5、Claude Opus 4.7 及 Gemini 3.1 Pro 競爭。可透過 xAI API 及 X 內部使用。

---

## H

**Hallucination（幻覺）** — 模型生成看似合理但事實上不正確的資訊。

**HNSW（Hierarchical Navigable Small World）** — 用於向量資料庫中近似最近鄰搜尋的圖形式演算法。

**Human-in-the-Loop (HITL)** — 用於對 AI 輸出進行人為監督、核准或修正的模式。

---

## I

**In-Context Learning** — 模型根據 prompt 中的範例適應任務，而無需更新權重。

**Inference（推論）** — 執行已訓練的模型以生成預測/輸出。

---

## J

**JSON Mode** — 保證輸出為有效 JSON 結構的 LLM 輸出模式（舊版）。在較新的 API 中已由 **Structured Outputs** 取代。

---

## K

**KV Cache** — 從 attention 運算快取下來的 key-value 配對。可實現高效的自迴歸生成。

---

## L

**LangChain** — 以 chains、agents 與整合來建構 LLM 應用程式的框架。

**LlamaIndex** — 聚焦於 LLM 應用程式之文件處理與檢索的資料框架。

**LiveCodeBench** — 在來自競技程式設計平台的真實世界問題上評估編碼模型的基準測試。對於生產環境的編碼任務，比 HumanEval 更可靠。

**LoRA（Low-Rank Adaptation）** — 一種參數高效的 fine-tuning，訓練小型 adapter 矩陣而非完整的模型權重。

**LLM-as-Judge** — 使用一個 LLM 來評估另一個 LLM 的輸出。

---

## M

**MCP（Model Context Protocol）** - 用於與 LLM 進行標準化工具/資源整合的開放協定。由 Anthropic 於 2024 年 11 月推出；治理權於 2025 年 12 月移交至 Linux Foundation 的 Agentic AI Foundation；已被 Anthropic、OpenAI、Google、Microsoft、AWS 採用。2.0 版（於 2026 年 3 月批准）新增 Streamable HTTP transport 與 OAuth 2.1 驗證。

**Mixture of Agents (MoA)** — 一種 ensemble 模式，由多個 agents 共同貢獻以合成出一個回應。

**Multi-Tenancy（多租戶）** — 以共享基礎設施為多個客戶提供服務，並達成資料隔離。

---

## O

**o3** — OpenAI 的高運算量推理模型（2025 年 1 月發布）。使用內部 chain-of-thought 來分配測試時運算量（test-time compute）。提供標準版與「mini」版。擅長數學、程式碼與科學。

**OCR（Optical Character Recognition，光學字元辨識）** — 從影像或掃描文件中擷取文字。

**OpenHands** — 開源的自主軟體工程代理（前身為 OpenDevin）。支援多種後端 LLM，於 Docker sandbox 中執行。

---

## P

**Prompt Caching** — 針對重複的 prompt 前綴重複使用 KV cache。在 Anthropic（cache_control）、Google（隱式）及部分 OpenAI 端點原生提供。對於長且固定的前綴，可降低 60-90% 的成本。

**Prompt Injection** — 以惡意輸入操縱 LLM 行為的攻擊。

**Prefix Caching** — 跨請求重複使用常見 prompt 前綴的 KV cache。

---

## Q

**QLoRA** — 將 LoRA 與 4-bit 量化結合，以達成記憶體高效的 fine-tuning。

**Quantization（量化）** — 降低模型精度（例如從 FP16 降至 INT4）以減少記憶體並提升速度。

---

## R

**RAG（Retrieval-Augmented Generation）** — 透過檢索相關文件來為 LLM 生成提供上下文的模式。

**RBAC（Role-Based Access Control，角色型存取控制）** — 依據具有預先定義權限的使用者角色來進行存取控制。

**ReAct** — 在 Reasoning（推理）與 Acting（行動）步驟之間交替進行的代理模式。

**Reranking（重新排序）** — 第二階段的評分，用以提升檢索精確度。Cross-encoders 提供比 bi-encoders 更高的準確度。

**RLHF（Reinforcement Learning from Human Feedback）** — 使用人類偏好來校準模型行為的訓練方法。

---

## S

**Self-Consistency** — 取樣多條推理路徑並選出最常見的答案。

**Semantic Search（語意搜尋）** — 使用 embeddings，依據意義而非關鍵字來尋找文件。

**Speculative Decoding** — 使用小型 draft model 提出 tokens，再由大型模型驗證。

**Structured Outputs** — OpenAI（以及 Anthropic 的工具模式）保證模型輸出符合所提供 JSON Schema 的能力。比舊版 JSON mode 更為嚴格。

**SWE-bench Verified** — 自主軟體工程的業界標準基準測試。衡量解決真實 GitHub issues 的能力。頂尖模型（Claude 3.7、o3）得分達 50–70%+。

**System Prompt** — 為 LLM 對話設定上下文與行為的指令。

---

## T

**Temperature** — 控制 LLM 輸出隨機性的參數。越低 = 越具決定性。

**Token** — 文字處理的基本單位。在英文中大約等於 0.75 個單字或 4 個字元。

**Tool Use** — LLM 呼叫外部函式/API 的能力。

**Transformer** — 以 self-attention 為基礎的神經網路架構。現代 LLM 的基礎。

---

## V

**Vector Database（向量資料庫）** — 針對儲存與搜尋高維向量（embeddings）而最佳化的資料庫。

---

## W

**Windsurf** — AI 原生 IDE（由 Codeium 開發），具備緊密的代理式整合。使用「Flows」——具決定性的代理式序列。為 Cursor 的替代方案。

---

## Z

**Zero-Shot** — 不含範例的提示，依賴模型既有的知識。

---

*另見：[PATTERNS.md](PATTERNS.md)，提供設計模式快速參考*
