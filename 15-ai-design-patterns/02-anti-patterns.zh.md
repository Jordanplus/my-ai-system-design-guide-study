# AI 反模式

辨識「不該做什麼」與了解最佳實踐同等重要。本章彙整了 AI 系統設計中常見的錯誤。

## 目錄

- [架構反模式](#architecture-anti-patterns)
- [RAG 反模式](#rag-anti-patterns)
- [Agent 反模式](#agent-anti-patterns)
- [Prompting 反模式](#prompting-anti-patterns)
- [評估反模式](#evaluation-anti-patterns)
- [生產環境反模式](#production-anti-patterns)
- [面試問題](#interview-questions)

---

## 架構反模式

### 萬能 Prompt（The God Prompt）

**問題：** 用單一龐大的 prompt 試圖完成所有事情。

```python
# ANTI-PATTERN: God Prompt
SYSTEM_PROMPT = """
You are a helpful assistant. You can:
1. Answer questions about our products
2. Help with technical support
3. Process refunds
4. Schedule appointments
5. Translate languages
6. Write code
7. Analyze data
8. Generate reports
... [continues for 5000 tokens]
"""
```

**為何失敗：**
- context 被指令佔用，而非使用者內容
- 模型在互相衝突的指令間掙扎
- 不可能針對所有情況進行最佳化
- 任何更新都會牽動全部功能

**解法：**
```python
# PATTERN: Specialized components
class QueryRouter:
    async def route(self, query: str) -> str:
        intent = await self.classify_intent(query)
        handler = self.handlers[intent]
        return await handler.process(query)
```

---

### 單一供應商依賴

**問題：** 整個系統依賴單一 LLM 供應商。

```python
# ANTI-PATTERN: Single provider
async def generate(prompt: str) -> str:
    return await openai.chat.completions.create(...)
```

**為何失敗：**
- 供應商當機 = 系統完全失效
- rate limit 影響所有流量
- 缺乏價格談判籌碼
- 被鎖定在單一模型家族

**解法：**
```python
# PATTERN: Multi-provider with failover
class LLMClient:
    def __init__(self):
        self.providers = [OpenAI(), Anthropic(), Google()]
    
    async def generate(self, prompt: str) -> str:
        for provider in self.providers:
            try:
                return await provider.generate(prompt)
            except ProviderError:
                continue
        raise AllProvidersFailedError()
```

---

### 過早 Fine-Tuning

**問題：** 在用盡較簡單的方法之前就進行 fine-tuning。

**為何失敗：**
- 昂貴且耗時
- 需要高品質的訓練資料（通常難以取得）
- 難以更新與維護
- 往往沒有必要

**決策流程：**
```
Try prompting first
    ↓ (not working)
Try few-shot examples
    ↓ (not working)
Try RAG for knowledge
    ↓ (not working)
Consider fine-tuning (with 500+ examples)
```

---

## RAG 反模式

### 全部檢索（Retrieve Everything）

**問題：** 不論相關性如何，一律檢索過多文件。

```python
# ANTI-PATTERN: Retrieve everything
results = vector_db.search(query, top_k=50)
context = "\n".join([r.text for r in results])
```

**為何失敗：**
- 雜訊淹沒了訊號
- 超出 context 上限
- 把 token 浪費在不相關的內容上
- 「迷失在中間（Lost in the middle）」效應

**解法：**
```python
# PATTERN: Quality over quantity
results = vector_db.search(query, top_k=20)
reranked = await reranker.rerank(query, results)
context = "\n".join([r.text for r in reranked[:5] if r.score > 0.7])
```

---

### 沒有 Chunking 策略

**問題：** 對文件進行任意切分或根本不切分。

```python
# ANTI-PATTERN: Fixed-size blind chunking
chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
```

**為何失敗：**
- 在句子、段落中間斷開
- 失去語意連貫性
- 把相關資訊拆散
- 檢索品質低落

**解法：**
```python
# PATTERN: Semantic-aware chunking
chunks = semantic_chunker.chunk(
    text,
    chunk_size=500,
    overlap=100,
    respect_boundaries=["paragraph", "section"]
)
```

---

### 忽略 Metadata

**問題：** 把所有文件都當成一樣的純文字。

```python
# ANTI-PATTERN: Ignore metadata
embedding = embed(document.text)
vector_db.insert(embedding, {"text": document.text})
```

**為何失敗：**
- 無法依日期、來源、類型進行篩選
- 沒有針對個別文件的存取控制
- 無法為新舊內容賦予不同權重
- 失去寶貴的 context

**解法：**
```python
# PATTERN: Rich metadata
vector_db.insert(embedding, {
    "text": document.text,
    "source": document.source,
    "date": document.date,
    "access_level": document.access_level,
    "document_type": document.type,
    "section": document.section
})

# Filter query
results = vector_db.search(
    query,
    filter={"date": {"$gte": "2024-01-01"}, "access_level": user.level}
)
```

---

## Agent 反模式

### 無限迴圈風險

**問題：** 沒有為 agent 設定終止條件。

```python
# ANTI-PATTERN: No limits
while not done:
    action = await agent.decide_action()
    result = await execute(action)
    done = agent.check_done(result)
```

**為何失敗：**
- agent 可能永遠迴圈下去
- 成本失控暴增
- 永遠不會回覆給使用者
- 資源耗盡

**解法：**
```python
# PATTERN: Multiple termination conditions
MAX_STEPS = 20
MAX_COST = 10.0
MAX_TIME = 300  # seconds

for step in range(MAX_STEPS):
    if cost_tracker.total > MAX_COST:
        return "Cost limit reached"
    if time.time() - start > MAX_TIME:
        return "Time limit reached"
    
    action = await agent.decide_action()
    result = await execute(action)
    
    if agent.check_done(result):
        return result
    
return "Step limit reached"
```

---

### 不安全的工具存取

**問題：** 給予 agent 不受限制的工具存取權。

```python
# ANTI-PATTERN: Full access
tools = [
    delete_file,
    execute_shell_command,
    send_email,
    database_query  # unrestricted!
]
```

**為何失敗：**
- agent 可能刪除關鍵檔案
- 可能外洩資料
- 可能執行惡意指令
- 沒有稽核軌跡

**解法：**
```python
# PATTERN: Scoped, validated tools
tools = [
    ScopedFileTool(allowed_dirs=["/tmp/agent"]),
    RestrictedShellTool(allowed_commands=["ls", "cat"]),
    EmailTool(requires_confirmation=True),
    ReadOnlyDatabaseTool(allowed_tables=["products"])
]
```

---

### 沒有記憶的 Agent

**問題：** agent 每一輪都從頭開始。

```python
# ANTI-PATTERN: Stateless agent
async def handle_message(message: str) -> str:
    return await agent.run(message)  # No context
```

**為何失敗：**
- 無法執行多輪任務
- 重複犯下相同錯誤
- 無法從經驗中學習
- 使用者體驗低落

**解法：**
```python
# PATTERN: Persistent memory
async def handle_message(session_id: str, message: str) -> str:
    memory = await memory_store.get(session_id)
    response = await agent.run(message, memory=memory)
    await memory_store.update(session_id, memory)
    return response
```

---

## Prompting 反模式

### 模糊的指令

**問題：** 用含糊的 prompt 卻期待得到特定行為。

```python
# ANTI-PATTERN: Vague
prompt = "Help the user with their request."
```

**為何失敗：**
- 「Help」沒有明確定義
- 沒有指定格式
- 沒有界線
- 行為不一致

**解法：**
```python
# PATTERN: Specific and structured
prompt = """
You are a customer support agent for TechCorp.

Your role:
- Answer questions about our products
- Help troubleshoot issues
- Escalate to human when unsure

Response format:
1. Acknowledge the issue
2. Provide a solution or ask clarifying questions
3. Offer next steps

Do NOT:
- Make promises about refunds (escalate instead)
- Provide legal or medical advice
- Share internal company information
"""
```

---

### 沒有輸出格式

**問題：** 期待結構化輸出，卻沒有指定格式。

```python
# ANTI-PATTERN: Hope for structure
prompt = "Extract the person's name, date, and location from this text."
response = await llm.generate(prompt)
# Response: "The person is John, he was there on March 5th in NYC"
# Now try to parse that...
```

**解法：**
```python
# PATTERN: Explicit format
prompt = """
Extract information and return as JSON:
{
    "name": "string",
    "date": "YYYY-MM-DD",
    "location": "string"
}

Text: ...
"""
# Or use structured output APIs
response = await llm.generate(prompt, response_format={"type": "json_object"})
```

---

## 評估反模式

### 憑感覺的評估（Vibes-Based Evaluation）

**問題：** 把「我看起來覺得不錯」當成評估方法。

```python
# ANTI-PATTERN: Manual spot-checking
for i in range(5):
    response = await generate(test_prompts[i])
    print(response)  # Developer looks at it
# "Looks good, ship it!"
```

**為何失敗：**
- 無法重現
- 範例是精挑細選出來的
- 沒有基準（baseline）比較
- 遺漏邊界情況

**解法：**
```python
# PATTERN: Systematic evaluation
eval_dataset = load_eval_set()  # 100+ examples
results = []

for example in eval_dataset:
    response = await generate(example["input"])
    score = await evaluate(response, example["expected"])
    results.append(score)

metrics = {
    "accuracy": sum(results) / len(results),
    "failures": [e for e, r in zip(eval_dataset, results) if r < 0.5]
}
```

---

### 在測試集上訓練

**問題：** 用評估資料來做開發決策。

```python
# ANTI-PATTERN: Overfitting to eval
for iteration in range(100):
    accuracy = evaluate_on_test_set()  # Same set every time
    tweak_prompt_based_on_failures(test_set)  # Optimizing for test set
```

**為何失敗：**
- 對特定範例過度擬合（overfit）
- 真實世界的表現有所不同
- 無法真正衡量泛化能力

**解法：**
```python
# PATTERN: Proper data splits
dev_set = load_dev_set()      # For iteration
test_set = load_test_set()    # Final evaluation only

# Iterate on dev set
for iteration in range(100):
    accuracy = evaluate(dev_set)
    improve_based_on(dev_set)

# Final evaluation on untouched test set
final_accuracy = evaluate(test_set)
```

---

## 生產環境反模式

### 沒有 Rate Limiting

**問題：** 每位使用者可以無限次呼叫 LLM。

```python
# ANTI-PATTERN: Open access
@app.route("/generate")
async def generate():
    return await llm.generate(request.prompt)  # No limits!
```

**為何失敗：**
- 單一使用者就能耗盡整個預算
- 阻斷服務（DoS）風險
- 成本暴增的意外
- 沒有公平使用機制

**解法：**
```python
# PATTERN: Rate limiting
@app.route("/generate")
@rate_limit(requests_per_minute=10, requests_per_day=100)
@cost_limit(max_cost_per_day=1.0)
async def generate():
    return await llm.generate(request.prompt)
```

---

### 沒有快取

**問題：** 每一個完全相同的請求都打到 LLM。

```python
# ANTI-PATTERN: No cache
async def answer_faq(question: str) -> str:
    return await llm.generate(question)  # Same FAQ, same cost every time
```

**為何失敗：**
- 在相同查詢上白白浪費金錢
- 不必要的延遲
- 同一個問題卻得到不一致的答案

**解法：**
```python
# PATTERN: Semantic caching
async def answer_faq(question: str) -> str:
    cached = await cache.get_similar(question, threshold=0.95)
    if cached:
        return cached.response
    
    response = await llm.generate(question)
    await cache.set(question, response)
    return response
```

---

## 面試問題

### Q：你在 LLM 應用中看到最嚴重的反模式是什麼？

**優秀的回答：**

「危害最大的是『萬能 Prompt（God Prompt）』反模式：用單一龐大的 prompt 試圖處理所有情境。

**為何它很常見：** 從一個 prompt 開始，再隨著需求出現而不斷加上指令，看起來比較簡單。

**為何失敗：**
- context 被指令佔用，而非使用者內容
- 互相衝突的指令會讓模型混淆
- 無法針對不同使用情境進行最佳化
- 任何變更都會帶來難以預測的副作用

**修正方法：** 路由到專門的 handler。每個 handler 都有一個針對單一任務最佳化的聚焦 prompt。router 本身可以很簡單（基於關鍵字），也可以很聰明（針對複雜情況採用基於 LLM 的方式）。

這不只適用於 prompt。普遍原則是：把複雜度拆解成專門的元件，而不是把所有東西都塞進單一的巨石（monolith）裡。」

### Q：你如何避免 agent 成本失控？

**優秀的回答：**

「在不同層級設置多重限制：

**單次請求限制：**
- 最大步數（例如 20）
- 最大 token 數（例如 50K）
- 最長時間（例如 5 分鐘）

**單一 session 限制：**
- 每日 token 預算
- 每日成本上限

**單一使用者限制：**
- rate limiting（每分鐘／每小時／每天的請求數）
- 成本歸屬與上限

**監控：**
- 即時成本追蹤
- 異常告警（單次請求 > $1）
- 成本暴增時觸發斷路器（circuit breaker）

**架構：**
- 從便宜模型逐級升級到昂貴模型（cascade）
- 為常見操作做快取
- 批次處理相似的請求

關鍵在於假設 agent 會試圖永遠執行下去。在每一層都建立硬性停止點。我曾看過在沒有適當限制的情況下，agent 在幾分鐘內就跑出 $1000 的帳單。」

---

*上一篇：[設計模式](01-design-patterns.md)*
