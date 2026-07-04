# Security Checklist — AI Investment OS

## OWASP Top 10 适用项

### A01: Broken Access Control
- [ ] 所有 API 端点（除 `/health` 和 `/docs`）需要 JWT 认证
- [ ] 用户只能访问自己的 portfolio，不能跨用户操作
- [ ] WebSocket 连接建立时验证 token
- [ ] Admin 端点有额外的 role check

### A03: Injection
- [ ] 所有数据库操作使用 SQLAlchemy ORM（无原始 SQL 拼接）
- [ ] 用户输入通过 Pydantic Model 校验（类型、长度、范围）
- [ ] LLM 输出在展示给用户前做 HTML escape（防 XSS 通过 AI 传播）

### A05: Security Misconfiguration
- [ ] DEBUG 模式在生产环境关闭
- [ ] CORS 白名单仅包含前端域名
- [ ] API 密钥通过环境变量注入，不硬编码
- [ ] Docker 容器以非 root 用户运行

### A07: Identification and Authentication Failures
- [ ] JWT token 有合理过期时间（24h 或更短）
- [ ] 密码使用 bcrypt/argon2 哈希存储
- [ ] 登录接口有 rate limiting（防暴力破解）

### A08: Software and Data Integrity Failures
- [ ] LLM 输出经过 JSON Schema 校验后再使用
- [ ] 外部 API 返回数据做类型和范围校验
- [ ] Agent confidence 值不直接信任，需在合理范围内

## 项目特有安全点

### LLM Security
- [ ] Agent prompt 中不包含用户私有数据
- [ ] LLM 输出的 HTML/JS 内容不直接渲染到前端
- [ ] Agent 置信度需要聚合校验，单个 Agent 不能直接触发高风险操作
- [ ] 限制 LLM 单次调用的 token 上限（防 DoS）

### Financial Data Security
- [ ] 股票代码输入校验（只允许 6 位数字）
- [ ] Portfolio 权重总和校验（不能超过 1.0）
- [ ] 金额字段使用 Decimal 而非 float（防精度问题）

### WebSocket Security
- [ ] 连接数限制（每用户最多 3 个连接）
- [ ] 消息大小限制（防大 payload 攻击）
- [ ] 空闲连接超时断开（30s 无心跳自动断开）
