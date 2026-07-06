# Development Timeline Reference

This document provides reference timelines for common components in the AI Investment OS project.

---

## Agent Development Timelines

### Simple Agent (e.g., Macro Agent)
**Total: 3-4 days**

| Task | Days | Notes |
|------|------|-------|
| Agent interface | 0.5 | Inherit from BaseAgent |
| Core logic | 1.0 | Simple data aggregation |
| Prompt design | 0.5 | Structured prompts |
| Output parsing | 0.5 | JSON validation |
| Unit tests | 0.5 | Mock LLM responses |
| Integration | 0.5 | LangGraph node |
| Documentation | 0.2 | JSDoc/README |

---

### Medium Agent (e.g., Technical Agent)
**Total: 5-6 days**

| Task | Days | Notes |
|------|------|-------|
| Agent interface | 0.5 | Inherit from BaseAgent |
| Data layer | 1.0 | Technical indicators |
| Core analysis | 1.5 | MACD, RSI, etc. |
| Prompt design | 1.0 | Complex analysis prompts |
| Output parsing | 0.5 | Structured JSON |
| Unit tests | 1.0 | Multiple scenarios |
| Integration | 0.5 | LangGraph node |

---

### Complex Agent (e.g., News Agent, Financial Agent)
**Total: 7-9 days**

| Task | Days | Notes |
|------|------|-------|
| Agent interface | 0.5 | Inherit from BaseAgent |
| Data integration | 2.0 | External API setup |
| Core analysis | 2.0 | Sentiment/financial analysis |
| RAG integration | 1.5 | Vector search |
| Prompt engineering | 1.5 | Iterative refinement |
| Output validation | 0.5 | JSON schema |
| Unit tests | 1.5 | Edge cases |
| Integration | 0.5 | LangGraph node |
| Documentation | 0.5 | Usage examples |

---

### Very Complex Agent (e.g., Quant Agent)
**Total: 10-12 days**

| Task | Days | Notes |
|------|------|-------|
| Agent interface | 0.5 | Inherit from BaseAgent |
| Factor model | 3.0 | Multiple factors |
| Scoring system | 2.0 | Weighted scoring |
| Backtesting logic | 2.0 | Historical validation |
| Prompt design | 1.5 | Complex reasoning |
| Output structure | 1.0 | Detailed JSON |
| Unit tests | 2.0 | Many scenarios |
| Integration | 0.5 | LangGraph node |
| Documentation | 1.0 | Technical docs |

---

## Service Development Timelines

### Simple Service (e.g., Auth Service)
**Total: 3-4 days**

| Task | Days | Notes |
|------|------|-------|
| Data models | 0.5 | User model |
| Business logic | 1.0 | Auth flows |
| API endpoints | 1.0 | Login/register |
| JWT integration | 0.5 | Token management |
| Tests | 0.5 | Unit + integration |
| Documentation | 0.3 | API docs |

---

### Medium Service (e.g., Stock Service)
**Total: 5-7 days**

| Task | Days | Notes |
|------|------|-------|
| Data models | 1.0 | Stock, snapshot |
| Database setup | 1.0 | Migrations, indexes |
| Business logic | 1.5 | CRUD operations |
| API endpoints | 1.5 | REST API |
| Caching | 0.5 | Redis integration |
| Tests | 1.0 | Unit + integration |
| Documentation | 0.5 | API docs |

---

### Complex Service (e.g., Workspace Service)
**Total: 7-10 days**

| Task | Days | Notes |
|------|------|-------|
| Data models | 1.5 | Multiple entities |
| Database design | 1.5 | Complex schema |
| Business logic | 2.0 | Workspace management |
| API endpoints | 2.0 | Full CRUD + queries |
| State management | 1.0 | Workspace state |
| Tests | 1.5 | Comprehensive |
| Documentation | 1.0 | Detailed docs |

---

## Frontend Component Timelines

### Simple Component (e.g., Stock Card)
**Total: 1-2 days**

| Task | Days | Notes |
|------|------|-------|
| Component structure | 0.3 | React component |
| Styling | 0.5 | TailwindCSS |
| Data integration | 0.3 | API call |
| Testing | 0.3 | Unit tests |
| Polish | 0.2 | Responsive |

---

### Medium Component (e.g., K-Line Chart)
**Total: 3-4 days**

| Task | Days | Notes |
|------|------|-------|
| Component structure | 0.5 | Complex layout |
| Chart integration | 1.0 | ECharts/TradingView |
| Data processing | 0.5 | Transform data |
| Interactivity | 0.5 | Zoom, pan |
| Styling | 0.5 | Responsive |
| Testing | 0.5 | Integration |

---

### Complex Component (e.g., Workspace Dashboard)
**Total: 5-7 days**

| Task | Days | Notes |
|------|------|-------|
| Layout design | 1.0 | Multi-section |
| State management | 1.0 | Complex state |
| Multiple charts | 1.5 | Various visualizations |
| Real-time updates | 1.0 | WebSocket |
| Responsive design | 1.0 | Mobile support |
| Testing | 1.0 | E2E tests |

---

## Workflow & Infrastructure Timelines

### LangGraph Workflow Setup
**Total: 4-5 days**

| Task | Days | Notes |
|------|------|-------|
| State definition | 0.5 | AgentState class |
| Node setup | 1.0 | Agent nodes |
| Edge definition | 0.5 | DAG structure |
| Parallel execution | 1.0 | Concurrent nodes |
| Error handling | 0.5 | Fallback logic |
| Testing | 1.0 | Workflow tests |

---

### Docker & Deployment
**Total: 3-4 days**

| Task | Days | Notes |
|------|------|-------|
| Dockerfiles | 1.0 | All services |
| docker-compose | 1.0 | Multi-container |
| Environment config | 0.5 | Secrets, vars |
| CI/CD pipeline | 1.0 | GitHub Actions |
| Documentation | 0.5 | Setup guide |

---

### RAG System Setup
**Total: 5-7 days**

| Task | Days | Notes |
|------|------|-------|
| Vector DB setup | 1.0 | Qdrant config |
| Embedding pipeline | 1.5 | Text → vectors |
| Indexing | 1.0 | Data ingestion |
| Search logic | 1.0 | Similarity search |
| Integration | 1.0 | Agent context |
| Testing | 1.0 | Relevance tests |

---

## Sprint Velocity Reference

### Team Velocity (2 developers)
- **Sprint duration**: 2 weeks (10 working days)
- **Effective days**: 8 days (accounting for meetings, reviews)
- **Expected output**: 12-16 story points per sprint

### Story Point Mapping
- **1 point**: 0.5-1 day (simple task)
- **2 points**: 1-2 days (medium task)
- **3 points**: 2-3 days (complex task)
- **5 points**: 4-5 days (very complex task)
- **8 points**: 6-8 days (epic-level task)

---

## Phase Duration Reference

### Phase 1: Product Design (PRD)
**Duration**: 1-2 weeks
**Team**: Product owner + 1 developer
**Output**: Complete PRD document

### Phase 2: System Architecture Design (SAD)
**Duration**: 1-2 weeks
**Team**: Tech lead + 1 senior developer
**Output**: Architecture document, tech decisions

### Phase 3: Detailed Design (DDD)
**Duration**: 2-3 weeks
**Team**: Tech lead + 2 developers
**Output**: Domain models, API specs, DB schema

### Phase 4: Development (Sprints)
**Duration**: 16-20 weeks (8-10 sprints)
**Team**: 2-4 developers
**Output**: Working software

---

## Testing Time Multipliers

| Test Type | Multiplier | Notes |
|-----------|-----------|-------|
| Unit tests | +20% | Add to task estimate |
| Integration tests | +30% | Complex integrations |
| E2E tests | +40% | Full user flows |
| Performance tests | +25% | Optimization work |
| Security audit | +20% | Security review |

---

## Documentation Time

| Document Type | Time | Notes |
|--------------|------|-------|
| API documentation | 0.5-1 day | Per service |
| Architecture doc | 1-2 days | System overview |
| User guide | 2-3 days | End-user docs |
| Developer guide | 1-2 days | Setup, contribution |
| Code comments | +10% | Inline docs |

---

## Risk Buffer Recommendations

| Project Phase | Buffer | Reason |
|--------------|--------|--------|
| New technology | +30-50% | Learning curve |
| External APIs | +20-30% | API changes, rate limits |
| Complex integrations | +25-35% | Integration issues |
| Real-time systems | +30-40% | Performance tuning |
| Security-critical | +20-30% | Audit requirements |

---

## Common Blockers & Solutions

### Blocker: LLM API Issues
**Impact**: 2-5 days
**Solution**: Implement fallback providers, retry logic

### Blocker: Data Quality
**Impact**: 1-3 days
**Solution**: Data validation, cleaning pipelines

### Blocker: Performance Issues
**Impact**: 3-5 days
**Solution**: Profiling, caching, optimization

### Blocker: Integration Failures
**Impact**: 2-4 days
**Solution**: Better error handling, monitoring

---

## Tips for Accurate Estimation

1. **Break down tasks** to 1-2 day increments
2. **Include testing time** (20-40% of dev time)
3. **Add buffer** for unknowns (20-30%)
4. **Consider dependencies** and wait times
5. **Account for code review** and iteration
6. **Include documentation** time
7. **Plan for rework** (10-20% typical)
