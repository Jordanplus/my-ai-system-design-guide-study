# 案例研究：AI 驅動的客戶支援

## 問題

一家電商公司每月處理 **200 萬張支援工單**。他們希望有一套 AI 系統，能在無需人工介入的情況下自動解決 60% 的工單，同時順暢地將複雜問題升級處理。

**面試中給定的限制條件：**
- 全年無休運作，涵蓋 12 種語言
- 必須與既有的 Zendesk 和 Salesforce 整合
- 不能做出不實承諾（退款、出貨日期）
- 人工客服必須能在對話進行到一半時接手
- 成本目標：每張已解決工單 $0.05

---

## 面試題目

> 「設計一套客戶支援 AI，能自動處理『我的訂單在哪裡？』，但也懂得在遇到『我要告你詐欺』時將其升級給人工處理。」

---

## 解決方案架構

```mermaid
flowchart TB
    subgraph Intake["Ticket Intake"]
        TICKET[New Ticket] --> CLASSIFY[Intent Classifier<br/>GPT-4o-mini]
        CLASSIFY --> INTENT{Intent Type}
    end

    subgraph Routing["Smart Routing"]
        INTENT -->|Simple| AUTO[Auto-Resolution Path]
        INTENT -->|Complex| HYBRID[Hybrid Path]
        INTENT -->|Escalate| HUMAN[Immediate Escalation]
    end

    subgraph AutoResolve["Auto-Resolution"]
        AUTO --> TOOLS[Tool Calls<br/>Order API, FAQ DB]
        TOOLS --> DRAFT[Draft Response]
        DRAFT --> SAFETY[Safety Check]
        SAFETY -->|Pass| SEND[Send to Customer]
        SAFETY -->|Fail| HUMAN
    end

    subgraph HybridPath["Hybrid Resolution"]
        HYBRID --> AGENT_DRAFT[AI Drafts Response]
        AGENT_DRAFT --> QUEUE[Human Review Queue]
        QUEUE --> APPROVE{Approve?}
        APPROVE -->|Yes| SEND
        APPROVE -->|Edit| EDIT[Human Edits]
        EDIT --> SEND
    end
```

---

## 關鍵設計決策

### 1. 三層式路由（自動 / 混合 / 升級）

**解答：** 並非所有工單都一樣。我們將其分類為三條路徑：

| 路徑 | 判定標準 | 範例 | 人工參與程度 |
|------|----------|---------|-------------------|
| **自動** | 高信心度、低風險 | 「我的訂單在哪裡？」 | 無 |
| **混合** | 中信心度或中風險 | 「我想要退款」 | 審查 AI 草稿 |
| **升級** | 法律、威脅、VIP、低信心度 | 「這是詐欺」 | 完全由人工處理 |

### 2. 以工具為基礎的解決方式，而非純生成

**解答：** AI 並不「知道」訂單在哪裡。它會呼叫 Order API 工具。這對準確性至關重要：

```python
@tool
def get_order_status(order_id: str) -> dict:
    """Retrieve real-time order status from OMS."""
    order = oms_client.get_order(order_id)
    return {
        "status": order.status,
        "shipped_date": order.shipped_at,
        "estimated_delivery": order.eta,
        "tracking_url": order.tracking_url
    }
```

LLM 負責協調調度工具，但絕不捏造資料。

### 3. 為何要在發送前做安全檢查？

**解答：** 即使是自動解決的工單，也會經過一道安全過濾：

1. **承諾偵測**：標記出像「我保證」或「我們會賠償」這類陳述
2. **情緒不匹配**：抓出當客戶生氣時 AI 卻聽起來很開心的情況
3. **PII 外洩**：確保不會出現任何內部備註或其他客戶資料
4. **競爭對手提及**：標記出 AI 推薦競爭對手的情況

---

## 升級判斷智能

最困難的部分在於知道**何時**該升級。我們使用一個結合多種訊號的信心分數：

```mermaid
flowchart LR
    subgraph Signals["Confidence Signals"]
        S1[Intent Confidence<br/>0.92] --> COMBINE
        S2[Sentiment Score<br/>Negative] --> COMBINE
        S3[Customer Tier<br/>VIP] --> COMBINE
        S4[Topic Risk<br/>Legal = High] --> COMBINE
    end

    COMBINE[Weighted Aggregation] --> SCORE{Final Score}
    SCORE -->|> 0.85| AUTO[Auto-Resolve]
    SCORE -->|0.5 - 0.85| HYBRID[Human Review]
    SCORE -->|< 0.5| ESCALATE[Immediate Escalate]
```

**關鍵洞察：** 一位 VIP 客戶即使只是問一個簡單的問題，仍然會被導向混合路徑，因為一旦出錯的代價更高。

---

## 多語言支援

不需要 12 套各自獨立的模型就能支援 12 種語言：

```mermaid
flowchart LR
    INPUT[Customer Message<br/>Spanish] --> DETECT[Language Detection]
    DETECT --> TRANSLATE_IN[Translate to English]
    TRANSLATE_IN --> PROCESS[Process in English<br/>Tools + LLM]
    PROCESS --> TRANSLATE_OUT[Translate to Spanish]
    TRANSLATE_OUT --> RESPONSE[Response in Spanish]
```

**為何不用原生多語言模型？**

成本考量。GPT-4o 對全部 12 種語言都處理得很好。若為每種語言使用專門的模型，將需要 12 套部署。翻譯雖然會增加延遲，但能讓基礎架構維持簡單。

---

## 人工接手（對話進行中）

當人工接手時，他們需要完整的脈絡：

```python
def handoff_to_human(conversation_id: str, agent_id: str):
    conversation = get_conversation(conversation_id)
    
    # Generate summary for human agent
    summary = llm.generate(f"""
    Summarize this conversation for a human agent:
    - Customer issue
    - What AI already tried
    - Why escalation happened
    
    Conversation:
    {conversation.messages}
    """)
    
    # Create handoff package
    return {
        "summary": summary,
        "customer_sentiment": conversation.sentiment,
        "attempted_solutions": conversation.tool_calls,
        "full_transcript": conversation.messages,
        "customer_tier": conversation.customer.tier
    }
```

---

## 成本分析

| 元件 | 每張工單成本 |
|-----------|-----------------|
| 意圖分類（GPT-4o-mini） | $0.002 |
| 工具呼叫（Order API、FAQ 搜尋） | $0.001 |
| 回應生成（GPT-4o-mini） | $0.008 |
| 安全檢查 | $0.003 |
| 翻譯（若需要，佔 30% 的工單） | $0.004 |
| **平均總計** | **$0.018** |

在 60% 的自動解決率下：**每張已解決工單 $0.03**（遠低於 $0.05 的目標）

---

## 面試延伸問題

**問：如果 AI 一直在道歉，卻從來沒有真正幫上忙怎麼辦？**

答：我們追蹤的是「解決成效」，而不只是「已發送回應」。如果客戶在 24 小時內針對同一個問題再次回覆，該工單就會被標記為「未解決」，而該 AI 行為模式也會被標記出來供審查。我們也會進行每週分析：「哪些用語與客戶的後續回覆相關？」

**問：你如何處理一位堅持要跟真人對話的客戶？**

答：明確的升級用語（「找真人」、「找主管」）無論信心分數為何，都會觸發立即接手。我們絕不與升級請求爭辯。

**問：那些試圖對支援 AI 進行越獄（jailbreak）的客戶怎麼辦？**

答：輸入清理（input sanitization）加上嚴格的純工具回應。AI 無法被誘導透露系統提示（system prompt），因為它並不會生成自由格式的答案：它只呼叫工具並摘要其輸出。系統提示本身也極度狹窄：「你協助處理 [Company] 的訂單問題。你不能討論其他主題。」

---

## 面試重點整理

1. **分層路由在自動化與風險之間取得平衡**：並非每張工單都該被自動解決
2. **以工具為基礎的接地（grounding）可防止幻覺**：AI 是擷取事實，而非生成事實
3. **信心度是多維度的**：意圖清晰度 + 情緒 + 客戶層級 + 主題風險
4. **人工接手需要脈絡**：要做摘要，而不是只把對話逐字稿丟過去

---

*相關章節：[Human-in-the-Loop 模式](../07-agentic-systems/08-human-in-the-loop-patterns.md)、[防護機制實作](../13-reliability-and-safety/01-guardrails-implementation.md)*
