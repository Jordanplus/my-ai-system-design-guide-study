# 🎓 推薦的 AI 課程與學習路徑

一份為 AI 工程師、ML 實務工作者與產品團隊精心整理的**可靠、值得信賴且與時俱進**的線上課程清單。此處的每一門課程皆已於 **2026 年 5 月**驗證，沒有灌水內容，也沒有過時的 MOOC。

---

## 目錄

- [基礎：LLM 與 Transformer](#foundation)
- [RAG Pipeline](#rag)
- [Agentic AI 與多代理系統](#agents)
- [Context 與記憶體管理](#context-memory)
- [AI 評估與可觀測性](#evals)
- [Prompt Engineering 與 Context Engineering](#prompting)
- [Fine-tuning 與調適](#finetuning)
- [推論最佳化與 MLOps](#mlops)
- [AI 安全與護欄](#safety)
- [Coding Agent 與開發者 AI 工具](#coding-agents)
- [給 PM 與非工程師](#pm-track)
- [YouTube 頻道與免費內容](#free)
- [學習路徑建議](#paths)

---

## 基礎：LLM 與 Transformer <a name="foundation"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[Neural Networks: Zero to Hero](https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ)** | Andrej Karpathy (YouTube) | 免費 | 由 OpenAI/Tesla 傳奇人物製作、權威性的從零開始系列。從頭打造 GPT。 |
| **[CS324: Large Language Models](https://stanford-cs324.github.io/winter2022/)** | Stanford | 免費 | 史丹佛水準的講義筆記，涵蓋 LLM 基礎、scaling law、對齊。 |
| **[Generative AI with LLMs](https://www.coursera.org/learn/generative-ai-with-llms)** | DeepLearning.AI + AWS (Coursera) | 約 $50 | LLM 的實作入門，涵蓋訓練、fine-tuning、RLHF。由 Andrew Ng 的團隊製作。 |
| **[Practical Deep Learning for Coders](https://course.fast.ai/)** | fast.ai | 免費 | 由下而上、程式碼優先的取向。最適合在實作中學習的工程師。 |

---

## RAG Pipeline <a name="rag"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[Building and Evaluating Advanced RAG](https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/)** | DeepLearning.AI + LlamaIndex | 免費 | 涵蓋 sentence-window retrieval、auto-merging，以及使用 TruLens 的 RAG 評估。 |
| **[Vector Databases: from Embeddings to Applications](https://www.deeplearning.ai/short-courses/vector-databases-embeddings-applications/)** | DeepLearning.AI + Weaviate | 免費 | 對 embedding、向量儲存與 hybrid search 的實務導覽。 |
| **[Building RAG Agents with LLMs](https://courses.nvidia.com/courses/course-v1:DLI+S-FX-15+V1/)** | NVIDIA Deep Learning Institute | 免費 | 使用 NVIDIA NIM 的企業級 RAG。涵蓋 chunking、reranking、評估。 |
| **[LlamaIndex — Documentation: Learning](https://docs.llamaindex.ai/en/stable/understanding/)** | LlamaIndex | 免費 | 官方 LlamaIndex 學習路徑——最適合深入精通 RAG pipeline。 |
| **[RAG Fundamentals (Haystack)](https://haystack.deepset.ai/tutorials)** | deepset / Haystack | 免費 | 使用 Haystack 框架、以 pipeline 為基礎的 RAG 實作教學。 |

---

## Agentic AI 與多代理系統 <a name="agents"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[AI Agents in LangGraph](https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/)** | DeepLearning.AI + LangChain | 免費 | 由創作者親自講授的 LangGraph。涵蓋 ReAct、持久化、human-in-the-loop、多代理。 |
| **[Multi AI Agent Systems with crewAI](https://www.deeplearning.ai/short-courses/multi-ai-agent-systems-with-crewai/)** | DeepLearning.AI + crewAI | 免費 | 官方 CrewAI 課程。涵蓋 Crews、Flows 與真實世界的商業自動化。 |
| **[Building Agentic RAG with LlamaIndex](https://www.deeplearning.ai/short-courses/building-agentic-rag-with-llamaindex/)** | DeepLearning.AI + LlamaIndex | 免費 | Routing、tool-calling 代理，以及多文件的 agentic retrieval。 |
| **[Functions, Tools and Agents with LangChain](https://www.deeplearning.ai/short-courses/functions-tools-agents-langchain/)** | DeepLearning.AI + LangChain | 免費 | Tool-calling、OpenAI function calling、從頭打造。 |
| **[Developing AI Agents using AutoGen](https://www.deeplearning.ai/short-courses/ai-agentic-design-patterns-with-autogen/)** | DeepLearning.AI + Microsoft | 免費 | AutoGen 多代理模式。涵蓋辯論、tool-use 與程式碼執行代理。 |
| **[CS294/194-196: LLM Agents (Berkeley)](https://rdi.berkeley.edu/llm-agents/f24)** | UC Berkeley | 免費 | 研究所層級的 LLM 代理課程。涵蓋記憶體、規劃、安全、評估。 |

---

## Context 與記憶體管理 <a name="context-memory"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[Building Systems with the ChatGPT API](https://www.deeplearning.ai/short-courses/building-systems-with-chatgpt/)** | DeepLearning.AI + OpenAI | 免費 | 涵蓋多輪對話狀態、context 管理、moderation chain。 |
| **[Prompt Engineering with Llama 2](https://www.deeplearning.ai/short-courses/prompt-engineering-with-llama-2/)** | DeepLearning.AI + Meta | 免費 | 展示 Llama 2 的 context window 取捨與 system prompt 管理。 |
| **[Reasoning with o1](https://www.deeplearning.ai/short-courses/reasoning-with-o1/)** | DeepLearning.AI + OpenAI | 免費 | 深入探討 o1 推理、budget token、thinking 模式。可直接套用至 o3 與 Claude 3.7 Extended Thinking。 |
| **[Mem0 Documentation](https://docs.mem0.ai/)** | Mem0 (官方) | 免費 | 生產環境代理中多層級記憶體的權威參考。 |

---

## AI 評估與可觀測性 <a name="evals"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[Evals for AI: Maven Course](https://maven.com/hamel-shreya/evals-for-ai)** | Hamel Husain & Shreya Shankar (Maven) | 付費 (約 $400) | AI 評估的業界黃金標準。已在數十家公司的生產環境中採用。本 repo 的評估指南即以此課程為基礎。 |
| **[Evaluating and Debugging Generative AI](https://www.deeplearning.ai/short-courses/evaluating-debugging-generative-ai/)** | DeepLearning.AI + W&B | 免費 | 涵蓋 tracing、使用 W&B Weave 的評估，以及實驗追蹤。 |
| **[Quality and Safety for LLM Applications](https://www.deeplearning.ai/short-courses/quality-safety-llm-applications/)** | DeepLearning.AI + WhyLabs | 免費 | 涵蓋幻覺偵測、毒性、偏見評估與漂移監控。 |
| **[LangSmith Evaluation Tutorials](https://docs.smith.langchain.com/evaluation)** | LangChain | 免費 | 若你使用 LangChain 生態系，官方 LangSmith 文件是最佳的實作評估參考。 |
| **[Phoenix + Langfuse official docs](https://docs.arize.com/phoenix)** | Arize Phoenix | 免費 | 使用 Phoenix 進行開源評估的實作教學。 |

> 📖 另請參閱本 repo 的配套指南：
> - [AI Evals：完整研究指南 (Phoenix + Langfuse)](ai_evals_comprehensive_study_guide.md)
> - [AI Evals：LangWatch + Langfuse 指南](ai_evals_complete_guide_langwatch_langfuse.md)

---

## Prompt Engineering 與 Context Engineering <a name="prompting"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[ChatGPT Prompt Engineering for Developers](https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/)** | DeepLearning.AI + OpenAI | 免費 | 基礎性的 prompt engineering 課程。由 Isa Fulford 與 Andrew Ng 講授。 |
| **[Prompting Fundamentals (Anthropic)](https://www.anthropic.com/learn)** | Anthropic | 免費 | 直接來自 Claude 團隊。涵蓋 prompt 設計、XML 標籤、chain-of-thought。 |
| **[DSPy: Building Optimizable Pipelines](https://github.com/stanfordnlp/dspy)** | Stanford NLP (GitHub) | 免費 | 並非課程，但 DSPy repo 的 notebook 是學習程式化 prompting 的最佳途徑。 |
| **[Prompt Engineering Guide](https://www.promptingguide.ai/)** | DAIR.AI | 免費 | 全面、由社群維護的參考資料，涵蓋所有主要的 prompting 技巧。 |

---

## Fine-tuning 與調適 <a name="finetuning"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[Finetuning Large Language Models](https://www.deeplearning.ai/short-courses/finetuning-large-language-models/)** | DeepLearning.AI + Lamini | 免費 | 涵蓋 LoRA、完整 fine-tuning、資料集準備、評估。簡潔且實用。 |
| **[Reinforcement Learning from Human Feedback](https://www.deeplearning.ai/short-courses/reinforcement-learning-from-human-feedback/)** | DeepLearning.AI + AWS | 免費 | 深入探討 RLHF：reward model、PPO、偏好資料集。 |
| **[Hugging Face NLP Course](https://huggingface.co/learn/nlp-course/chapter1/1)** | Hugging Face | 免費 | 使用 HF 生態系 (Trainer、PEFT 等) 進行 transformer fine-tuning 的最佳免費課程。 |
| **[How Diffusion Models Work](https://www.deeplearning.ai/short-courses/how-diffusion-models-work/)** | DeepLearning.AI | 免費 | 用於影像模型 fine-tuning (stable diffusion、影像用 LoRA)。 |

---

## 推論最佳化與 MLOps <a name="mlops"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[ML Engineering for Production (MLOps)](https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops)** | DeepLearning.AI (Coursera) | 付費 | 關於生產級 ML 的 4 門課程專項：部署、監控、pipeline。 |
| **[Efficiently Serving LLMs](https://www.deeplearning.ai/short-courses/efficiently-serving-llms/)** | DeepLearning.AI + Predibase | 免費 | 涵蓋 vLLM、PagedAttention、量化、LoRA serving。正是本指南所涵蓋的內容。 |
| **[vLLM Documentation & Tutorial](https://docs.vllm.ai/en/latest/)** | vLLM | 免費 | 官方 vLLM 文件是高吞吐量 serving 最與時俱進的參考資料。 |

---

## AI 安全與護欄 <a name="safety"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[Red Teaming LLM Applications](https://www.deeplearning.ai/short-courses/red-teaming-llm-applications/)** | DeepLearning.AI + Giskard | 免費 | 實作 red teaming、prompt injection、jailbreak 偵測、偏見測試。 |
| **[AI Safety Fundamentals](https://aisafetyfundamentals.com/alignment-fast-track/)** | BlueDot Impact | 免費 | 關於 AI 對齊與安全最值得信賴的免費課程。Anthropic、DeepMind 的專業人員皆有採用。 |
| **[NVIDIA AI Red Team (NEMO Guardrails)](https://github.com/NVIDIA/NeMo-Guardrails)** | NVIDIA | 免費 | 使用 NeMo Guardrails 打造生產級護欄的實作 notebook。 |

---

## Coding Agent 與開發者 AI 工具 <a name="coding-agents"></a>

| 課程 | 提供者 | 費用 | 為何值得信賴 |
|--------|----------|------|-----------------|
| **[Claude Code — Official Docs](https://docs.anthropic.com/en/home)** | Anthropic | 免費 | Claude Code 權威性的起點。涵蓋 CLAUDE.md、SDK 與權限。 |
| **[Building Code Agents (Hugging Face)](https://huggingface.co/learn/agents-course/unit1/introduction)** | Hugging Face | 免費 | HuggingFace 的官方代理課程——包含一個關於打造程式碼執行代理的單元。 |
| **[Introduction to OpenHands](https://github.com/All-Hands-AI/OpenHands/blob/main/docs/getting-started.md)** | All-Hands AI | 免費 | OpenHands 自主 coding agent 的官方入門指南。 |

> 📖 另請參閱本 repo 的指南：[Claude Code 指南](09-frameworks-and-tools/09-claude-code.md) 與 [OpenCoder 全景](09-frameworks-and-tools/10-opencoderguide.md)

---

## 給 PM 與非工程師 <a name="pm-track"></a>

這些課程不需要任何 Python 經驗：

| 課程 | 提供者 | 費用 | 為何值得推薦 |
|--------|----------|------|--------------|
| **[AI for Everyone](https://www.coursera.org/learn/ai-for-everyone)** | DeepLearning.AI (Coursera) | 免費 | Andrew Ng 為非技術角色設計的課程。涵蓋 AI 能做與不能做什麼、專案領導。 |
| **[Prompt Engineering for Everyone](https://learnprompting.org/)** | Learn Prompting | 免費 | 為非工程師撰寫、淺顯易懂的 prompt engineering 指南。 |
| **[Evals for AI (Maven)](https://maven.com/hamel-shreya/evals-for-ai)** | Hamel Husain & Shreya Shankar | 付費 | 儘管包含程式碼，這門課程是為 PM 與 QA 設計的，而不僅限於工程師。強烈推薦。 |
| **[AI Product Management](https://www.productschool.com/blog/product-management/ai-product-manager/)** | Product School | 免費 (部落格) | 為打造 AI 驅動產品的 PM 提供的實務指南。 |
| **[Google: Introduction to Generative AI](https://cloud.google.com/learn/training/machinelearning-ai)** | Google Cloud Skills Boost | 免費 | 對生成式 AI、LLM 與負責任 AI 的無程式碼入門介紹。 |

---

## YouTube 頻道與免費內容 <a name="free"></a>

| 頻道 / 資源 | 重點 | 為何值得追蹤 |
|-------------------|-------|------------|
| **[Andrej Karpathy](https://www.youtube.com/@AndrejKarpathy)** | 基礎、transformer | 對 LLM 實際運作方式的最佳解說 |
| **[Yannic Kilcher](https://www.youtube.com/@YannicKilcher)** | 論文評析 | 對最新 ML 研究論文的清晰導覽 |
| **[Aleksa Gordić - The AI Epiphany](https://www.youtube.com/@TheAIEpiphany)** | 論文評析 | 深入的技術論文剖析 |
| **[AI Jason](https://www.youtube.com/@AIJasonZ)** | 代理、LangChain、實務 | 適合 agentic 框架的優秀入門影片 |
| **[Sam Witteveen](https://www.youtube.com/@samwitteveenai)** | Gemini、RAG、代理 | 最佳的實務 AI YouTuber 之一 |
| **[Matt Wolfe](https://www.youtube.com/@mreflow)** | AI 新聞、產品演示 | 最適合掌握 AI 新聞與工具的最新動態 |
| **[Hamel Husain (blog)](https://hamel.dev/)** | 評估、生產級 AI、LLM | 來自 evals maven 課程作者的真實生產洞見 |
| **[Simon Willison (blog)](https://simonwillison.net/)** | LLM 新聞、工具、coding | 最值得信賴的每日 AI 新聞來源 |
| **[The Latent Space podcast](https://www.latent.space/)** | 技術性 AI 訪談 | 最佳的技術性 AI podcast——與研究人員的深入對談 |
| **[Lex Fridman Podcast](https://lexfridman.com/podcast/)** | 廣泛的 AI/ML 訪談 | 與頂尖 AI 研究人員的長篇訪談 |

---

## 學習路徑建議 <a name="paths"></a>

### 🛤️ 路徑：「我是 AI 新手，想快速動手做東西」

```
Week 1: Prompt Engineering for Developers (DeepLearning.AI) — free, 2 hrs
Week 2: Building Systems with ChatGPT API (DeepLearning.AI) — free, 2 hrs
Week 3: Building and Evaluating Advanced RAG (DeepLearning.AI) — free, 2 hrs
Week 4: AI Agents in LangGraph (DeepLearning.AI) — free, 4 hrs
Month 2: Pick a real project, use this guide as reference
```

### 🛤️ 路徑：「我想深入理解 LLM」

```
Week 1-3: Neural Networks: Zero to Hero (Karpathy) — free, 12+ hrs
Week 4-6: CS324 Stanford LLMs — free, 30+ hrs
Month 2: Generative AI with LLMs (Coursera DeepLearning.AI)
Month 3: CS294 LLM Agents (Berkeley)
```

### 🛤️ 路徑：「我想打造可上線的 AI 評估」

```
Week 1: Evaluating and Debugging Generative AI (DeepLearning.AI + W&B) — free
Week 2: This repo's evals guides (Phoenix/Langfuse) — free  ← start here
Week 3-4: Quality and Safety for LLM Applications (DeepLearning.AI)
Month 2: Evals for AI (Maven, Hamel + Shreya) — paid, worth it
```

### 🛤️ 路徑：「我是 PM，正在學習如何貢獻於 AI 產品品質」

```
Week 1: AI for Everyone (Coursera) — free
Week 2: Prompt Engineering for Everyone (learnprompting.org) — free
Week 3: AI Evals guide in this repo — free (especially Chapters 1-3 on error analysis)
Month 2: Evals for AI (Maven) — paid, has PM track
```

### 🛤️ 路徑：「我想在團隊中部署 coding agent」

```
Day 1: Claude Code docs (anthropic.com) — free
Week 1: This repo's Claude Code Guide + OpenCoder Landscape Guide
Week 2: Building Code Agents (Hugging Face) — free
Month 1: Run Claude Code on a real project in CI
```

---

## 如何掌握最新動態

AI 發展迅速。除了課程之外，以下習慣能讓你掌握最新動態：

1. **追蹤 Simon Willison 的部落格**——每日、值得信賴的 AI 新聞摘要
2. **閱讀 Anthropic + OpenAI 的發行說明**——第一手來源勝過二手摘要
3. **收看 Latent Space podcast**——最佳的技術深度
4. **貢獻開源**——OpenHands、LlamaIndex、DSPy——真正的學習發生在 PR 之中
5. **為本 repo 加星**——我們會隨著局勢變化而更新它 ⭐

---

*由 [Om Bharatiya](https://github.com/ombharatiya) 維護。歡迎提交 PR 新增課程！*
