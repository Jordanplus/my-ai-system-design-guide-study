# LLM 系統的存取控制

安全的存取控制對於多使用者與多租戶的 LLM 應用而言至關重要。本章涵蓋認證（authentication）、授權（authorization）以及資料隔離模式。

## 目錄

- [存取控制需求](#access-control-requirements)
- [認證模式](#authentication-patterns)
- [授權模型](#authorization-models)
- [租戶隔離](#tenant-isolation)
- [API Key 管理](#api-key-management)
- [稽核與合規](#audit-and-compliance)
- [面試問題](#interview-questions)
- [參考資料](#references)

---

## 存取控制需求

### 安全面向

| 面向 | 說明 | 控制機制 |
|-----------|-------------|----------|
| **認證（Authentication）** | 是誰發出這個請求？ | API keys、OAuth、JWT |
| **授權（Authorization）** | 他們可以做什麼？ | RBAC、ABAC、政策 |
| **隔離（Isolation）** | 他們可以看到哪些資料？ | 租戶過濾、加密 |
| **稽核（Audit）** | 他們做了什麼？ | 記錄、合規報告 |

### LLM 特有的考量

| 考量 | 風險 | 緩解措施 |
|---------|------|------------|
| Prompt injection | 繞過存取控制 | 輸入驗證 |
| 資料外洩 | 跨租戶曝露 | 嚴格過濾 |
| 模型輸出 | 曝露受保護的資訊 | 輸出過濾 |
| 上下文污染 | 注入未授權的資料 | 上下文驗證 |

---

## 認證模式

### API Key 認證

```python
class APIKeyAuthenticator:
    def __init__(self, key_store):
        self.key_store = key_store
    
    async def authenticate(self, api_key: str) -> AuthResult:
        if not api_key:
            return AuthResult(authenticated=False, error="Missing API key")
        
        # Hash the key for lookup
        key_hash = self.hash_key(api_key)
        
        # Look up in store
        key_record = await self.key_store.get(key_hash)
        
        if not key_record:
            return AuthResult(authenticated=False, error="Invalid API key")
        
        if key_record.expired:
            return AuthResult(authenticated=False, error="Expired API key")
        
        if key_record.revoked:
            return AuthResult(authenticated=False, error="Revoked API key")
        
        return AuthResult(
            authenticated=True,
            user_id=key_record.user_id,
            tenant_id=key_record.tenant_id,
            scopes=key_record.scopes
        )
    
    def hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
```

### 帶有 Scope 的 JWT

```python
class JWTAuthenticator:
    def __init__(self, public_key: str):
        self.public_key = public_key
    
    async def authenticate(self, token: str) -> AuthResult:
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                audience="llm-api"
            )
            
            return AuthResult(
                authenticated=True,
                user_id=payload["sub"],
                tenant_id=payload.get("tenant_id"),
                scopes=payload.get("scopes", []),
                expires_at=datetime.fromtimestamp(payload["exp"])
            )
        except jwt.ExpiredSignatureError:
            return AuthResult(authenticated=False, error="Token expired")
        except jwt.InvalidTokenError as e:
            return AuthResult(authenticated=False, error=str(e))
```

---

## 授權模型

### 角色型存取控制（RBAC）

```python
class RBACAuthorizer:
    ROLE_PERMISSIONS = {
        "admin": ["*"],
        "developer": ["generate", "embed", "fine_tune", "read_metrics"],
        "user": ["generate", "embed"],
        "viewer": ["read_metrics"]
    }
    
    def authorize(self, user: User, action: str) -> bool:
        permissions = self.ROLE_PERMISSIONS.get(user.role, [])
        
        if "*" in permissions:
            return True
        
        return action in permissions
```

### 屬性型存取控制（ABAC）

```python
class ABACAuthorizer:
    def __init__(self, policy_engine):
        self.policy_engine = policy_engine
    
    async def authorize(
        self,
        subject: dict,       # Who (user attributes)
        action: str,         # What (operation)
        resource: dict,      # On what (resource attributes)
        context: dict        # When/where (environmental)
    ) -> AuthzResult:
        # Evaluate all applicable policies
        policies = await self.policy_engine.get_policies(action)
        
        for policy in policies:
            result = policy.evaluate(subject, action, resource, context)
            if result == PolicyResult.DENY:
                return AuthzResult(allowed=False, reason=policy.name)
            if result == PolicyResult.ALLOW:
                return AuthzResult(allowed=True)
        
        return AuthzResult(allowed=False, reason="No matching policy")
```

### 模型層級的權限

```python
class ModelAccessControl:
    MODEL_TIERS = {
        "gpt-4o": ["enterprise", "professional"],
        "gpt-4o-mini": ["enterprise", "professional", "starter"],
        "claude-3.5-sonnet": ["enterprise"],
        "claude-3.5-haiku": ["enterprise", "professional", "starter"]
    }
    
    def can_access_model(self, user: User, model: str) -> bool:
        allowed_tiers = self.MODEL_TIERS.get(model, [])
        return user.tier in allowed_tiers
    
    def get_available_models(self, user: User) -> list[str]:
        return [
            model for model, tiers in self.MODEL_TIERS.items()
            if user.tier in tiers
        ]
```

---

## 租戶隔離

### 資料隔離模式

```python
class TenantIsolatedVectorStore:
    def __init__(self, vector_db):
        self.db = vector_db
    
    async def search(
        self,
        tenant_id: str,
        query_embedding: list[float],
        top_k: int = 10
    ) -> list[dict]:
        # CRITICAL: Always filter by tenant_id at database level
        results = await self.db.search(
            query_vector=query_embedding,
            top_k=top_k,
            filter={"tenant_id": {"$eq": tenant_id}}  # Mandatory filter
        )
        
        return results
    
    async def insert(
        self,
        tenant_id: str,
        documents: list[dict]
    ):
        # CRITICAL: Always include tenant_id in metadata
        for doc in documents:
            doc["metadata"]["tenant_id"] = tenant_id
        
        await self.db.insert(documents)
```

### Prompt 隔離

```python
class TenantAwarePromptBuilder:
    def build_prompt(
        self,
        tenant_id: str,
        user_query: str,
        context: list[dict]
    ) -> str:
        # Verify all context belongs to tenant
        for doc in context:
            if doc.get("tenant_id") != tenant_id:
                raise SecurityError("Cross-tenant context detected")
        
        # Build isolated prompt
        return f"""
[Tenant: {tenant_id}]
Context from tenant documents:
{self.format_context(context)}

User query: {user_query}
"""
```

### 快取隔離

```python
class TenantIsolatedCache:
    def __init__(self, cache_backend):
        self.cache = cache_backend
    
    def _scoped_key(self, tenant_id: str, key: str) -> str:
        return f"tenant:{tenant_id}:{key}"
    
    async def get(self, tenant_id: str, key: str) -> any:
        return await self.cache.get(self._scoped_key(tenant_id, key))
    
    async def set(self, tenant_id: str, key: str, value: any, ttl: int = 3600):
        await self.cache.set(
            self._scoped_key(tenant_id, key),
            value,
            ttl=ttl
        )
```

---

## API Key 管理

### Key 生命週期

```python
class APIKeyManager:
    KEY_PREFIX = "llm_"
    
    async def create_key(
        self,
        user_id: str,
        tenant_id: str,
        name: str,
        scopes: list[str],
        expires_in_days: int = 365
    ) -> APIKey:
        # Generate secure key
        raw_key = self.KEY_PREFIX + secrets.token_urlsafe(32)
        key_hash = self.hash_key(raw_key)
        
        # Store metadata (not the raw key)
        key_record = APIKeyRecord(
            id=generate_id(),
            hash=key_hash,
            user_id=user_id,
            tenant_id=tenant_id,
            name=name,
            scopes=scopes,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=expires_in_days)
        )
        
        await self.store.save(key_record)
        
        # Return raw key only once (not stored)
        return APIKey(
            id=key_record.id,
            key=raw_key,  # Only returned on creation
            name=name,
            scopes=scopes,
            expires_at=key_record.expires_at
        )
    
    async def revoke_key(self, key_id: str, reason: str):
        await self.store.update(key_id, {
            "revoked": True,
            "revoked_at": datetime.now(),
            "revoke_reason": reason
        })
        
        await self.audit_log.log("api_key_revoked", {
            "key_id": key_id,
            "reason": reason
        })
```

### Key 輪替

```python
class KeyRotator:
    async def rotate_key(self, old_key_id: str) -> APIKey:
        old_key = await self.key_store.get(old_key_id)
        
        # Create new key with same permissions
        new_key = await self.key_manager.create_key(
            user_id=old_key.user_id,
            tenant_id=old_key.tenant_id,
            name=f"{old_key.name} (rotated)",
            scopes=old_key.scopes
        )
        
        # Grace period: old key still works temporarily
        await self.key_store.update(old_key_id, {
            "deprecated": True,
            "deprecated_at": datetime.now(),
            "grace_period_ends": datetime.now() + timedelta(days=7)
        })
        
        await self.notify_user(old_key.user_id, new_key)
        
        return new_key
```

---

## 稽核與合規

### 稽核記錄

```python
class AuditLogger:
    async def log_request(
        self,
        request: LLMRequest,
        response: LLMResponse,
        auth: AuthResult
    ):
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request.id,
            "user_id": auth.user_id,
            "tenant_id": auth.tenant_id,
            "action": "llm_generate",
            "model": request.model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cost": response.cost,
            "latency_ms": response.latency_ms,
            # Hash content for privacy
            "input_hash": self.hash_content(request.prompt),
            "output_hash": self.hash_content(response.content)
        }
        
        await self.audit_store.append(audit_entry)
```

### 合規報告

```python
class ComplianceReporter:
    async def generate_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        logs = await self.audit_store.query(
            tenant_id=tenant_id,
            start=start_date,
            end=end_date
        )
        
        return ComplianceReport(
            tenant_id=tenant_id,
            period=(start_date, end_date),
            total_requests=len(logs),
            unique_users=len(set(l["user_id"] for l in logs)),
            models_used=list(set(l["model"] for l in logs)),
            total_cost=sum(l["cost"] for l in logs),
            data_access_events=self.extract_data_access(logs),
            security_events=await self.get_security_events(tenant_id, start_date, end_date)
        )
```

---

## 面試問題

### Q：你如何在 RAG 系統中實作多租戶隔離？

**理想答案：**

「多租戶隔離需要縱深防禦（defense in depth）：

**向量資料庫層級：**
- 每一個向量都在 metadata 中包含 tenant_id
- 所有查詢都在資料庫層級依 tenant_id 過濾
- 切勿在檢索之後才過濾（資料已經外洩到記憶體中）

**快取層級：**
- 所有快取 key 都以 tenant_id 為前綴
- 語意快取（semantic cache）以租戶為範圍
- 即使是相同的查詢也不會產生跨租戶的快取命中

**Prompt 層級：**
- 在納入之前，先驗證上下文文件屬於發出請求的租戶
- 切勿混用來自多個租戶的上下文

**輸出層級：**
- 驗證回應不包含跨租戶的資訊
- 以輸出過濾作為額外的防護措施

**稽核：**
- 記錄所有帶有租戶上下文的存取
- 監控跨租戶的存取嘗試

關鍵原則：tenant_id 是每一個資料存取點上的強制過濾條件，而非可選的參數。」

### Q：你如何為一個 LLM 服務管理 API key？

**理想答案：**

「安全的 API key 管理：

**建立：**
- 產生具備密碼學強度的隨機 key
- 只儲存其 hash，原始 key 僅回傳一次
- 與使用者、租戶、scope、到期時間相關聯

**驗證：**
- 對傳入的 key 進行 hash，並與儲存的 hash 比對
- 檢查到期與撤銷狀態
- 驗證 scope 是否符合所請求的動作

**輪替：**
- 支援帶有寬限期的 key 輪替
- 舊 key 在過渡期間（7 天）仍可運作
- 通知使用者即將到期

**安全性：**
- 對失敗的認證嘗試進行速率限制
- 一旦懷疑遭到入侵就立即撤銷
- 稽核所有 key 操作

**Scope：**
- 細緻化：模型存取、操作類型、每日限額
- 預設採用最小權限原則

關鍵原則：絕不儲存原始 key、支援輪替、實作最小權限。」

---

## 參考資料

- OAuth 2.0: https://oauth.net/2/
- OWASP API Security: https://owasp.org/API-Security/

---

*上一篇：[安全基礎](01-security-fundamentals.md)*
