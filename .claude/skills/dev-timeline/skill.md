---
name: dev-timeline
description: Multi-Agent AI Investment OS development timeline expert. Helps plan, estimate, and track development cycles for complex multi-agent systems. Use this skill whenever users ask about development timeline, project planning, milestone estimation, sprint planning, development phases, project roadmap, or when discussing how long features will take to build in this AI Investment OS project.
---

# Development Timeline Expert

A specialized skill for designing and managing development timelines for the AI Investment OS project—a multi-agent investment research platform with sophisticated architecture.

## Project Understanding

This skill is deeply embedded in the AI Investment OS domain knowledge. The project consists of:

### Four Development Phases

**Phase 1: Product Design (PRD)**
- Product vision and user personas
- Core features: Dashboard, Market, Stocks, Workspace, Candidate Pool, Reports, Strategy, Automation
- User flows and permission systems (Guest → User → Pro → Admin)
- Data flow architecture

**Phase 2: System Architecture Design (SAD)**
- High-level architecture: Frontend → API Gateway → Agent Engine → Memory Layer
- Key technologies: Next.js, FastAPI, LangGraph, PostgreSQL, Qdrant, Redis, MinIO, Celery
- Deployment: Single server (2C4G) with Docker Compose
- Performance design: Agent parallelization, caching, WebSocket streaming

**Phase 3: Detailed Design (DDD + Module Design)**
- 6 Bounded Contexts: Identity, Investment, Workspace, Agent, Analytics, Automation
- 8 specialized Agents: Planner, News, Financial, Technical, Macro, Risk, Quant, Report
- Workflow: LangGraph DAG with parallel execution
- RAG design with Qdrant vector database
- Event-driven architecture with WebSocket

**Phase 4: Development Specifications (Engineering)**
- Coding standards: Python 3.11+, FastAPI, Pydantic V2, SQLAlchemy 2.0
- Layered architecture: Controller → Service → Domain
- Agent development: Structured prompts, JSON output, stateless design
- Git workflow: main/dev/feature/* branches
- CI/CD: Lint → Test → Build → Docker → Deploy
- Docker deployment: Full containerization

## How to Use This Skill

### When Users Ask About:

1. **Timeline Estimation**
   - Read the relevant development document from "AI Investment OS开发文档/"
   - Assess complexity based on component count and dependencies
   - Provide realistic estimates considering team size and expertise

2. **Sprint Planning**
   - Break down features into deliverable sprints (1-2 weeks each)
   - Identify dependencies between components
   - Prioritize based on core value vs. complexity

3. **Milestone Definition**
   - Define clear phase boundaries with acceptance criteria
   - Create checkpoints for architecture review
   - Establish testing and deployment milestones

4. **Risk Assessment**
   - Identify high-risk components (e.g., multi-agent orchestration)
   - Plan for learning curves (LangGraph, Qdrant, etc.)
   - Account for integration complexity

### Estimation Framework

**Complexity Levels:**
- **Low (1-2 days)**: Simple CRUD operations, static displays, basic components
- **Medium (3-5 days)**: API endpoints, database operations, UI with moderate logic
- **High (5-10 days)**: Agent implementation, workflow orchestration, complex integrations
- **Very High (10-15+ days)**: Multi-agent coordination, RAG system, real-time systems

**Key Factors for Estimation:**
1. Number of components involved
2. External API integrations required
3. State management complexity
4. Testing requirements
5. Documentation needs

### Template Response Structure

When providing timeline estimates, include:

```markdown
## Timeline Estimate: [Feature/Phase Name]

**Complexity**: [Low/Medium/High/Very High]

**Estimated Effort**: [X days/weeks]

### Breakdown:
1. [Component 1] - [X days]
2. [Component 2] - [X days]
3. [Component 3] - [X days]

### Dependencies:
- [What needs to be completed first]
- [External dependencies]

### Risks & Considerations:
- [Potential blockers]
- [Mitigation strategies]

### Milestones:
- **Week 1**: [Deliverable]
- **Week 2**: [Deliverable]
- **Week 3**: [Deliverable]
```

### Example: Agent Implementation Timeline

When users ask "How long to implement the News Agent?", respond with:

```markdown
## Timeline Estimate: News Agent Implementation

**Complexity**: High

**Estimated Effort**: 5-7 days

### Breakdown:
1. **Data layer setup** (1-2 days)
   - News API integration (AKShare/Tushare)
   - Database schema for news storage
   - Vector embedding pipeline

2. **Agent core logic** (2-3 days)
   - Prompt engineering for sentiment analysis
   - Event extraction system
   - Impact assessment logic
   - Output parsing and validation

3. **Integration** (1-2 days)
   - LangGraph workflow node
   - State management (input/output)
   - Error handling and fallback

4. **Testing** (1 day)
   - Unit tests for agent logic
   - Integration tests with workflow
   - Mock data testing

### Dependencies:
- Base Agent class implementation
- LLM provider setup
- Vector database (Qdrant) configured

### Risks:
- Prompt quality may require iteration
- News API rate limits or data quality
- Embedding model performance

### Milestones:
- **Day 1-2**: Data pipeline working
- **Day 3-5**: Agent logic complete
- **Day 6**: Integrated with workflow
- **Day 7**: Testing complete, ready for review
```

## Development Phase Timelines

### Phase 1: Product Design (PRD)
**Duration**: 1-2 weeks
**Key Deliverables**:
- Complete product vision document
- User personas and flows
- Feature specifications
- Acceptance criteria

**Milestones**:
- Week 1: Core features defined
- Week 2: Full PRD approved

---

### Phase 2: System Architecture Design (SAD)
**Duration**: 1-2 weeks
**Key Deliverables**:
- High-level architecture diagram
- Technology stack decisions
- Deployment architecture
- Performance requirements

**Milestones**:
- Week 1: Architecture proposed
- Week 2: Architecture reviewed and approved

---

### Phase 3: Detailed Design (DDD + Module Design)
**Duration**: 2-3 weeks
**Key Deliverables**:
- Domain models for all 6 bounded contexts
- Agent specifications (8 agents)
- Workflow DAG definitions
- Database schema
- API specifications

**Milestones**:
- Week 1: Domain models complete
- Week 2: Agent specifications complete
- Week 3: API and DB design finalized

---

### Phase 4: Development
**Duration**: 8-12 weeks (varies based on team size)

**Sprint 1-2: Foundation (Weeks 1-3)**
- Project setup (monorepo, Docker, CI/CD)
- Database migrations
- Basic API framework
- Authentication system

**Sprint 3-4: Core Services (Weeks 4-6)**
- Stock service
- Workspace service
- Basic frontend framework

**Sprint 5-6: Agent Foundation (Weeks 7-9)**
- Base Agent class
- Planner Agent
- LangGraph workflow setup
- News Agent (as reference implementation)

**Sprint 7-8: Agent Fleet (Weeks 10-12)**
- Financial Agent
- Technical Agent
- Macro Agent
- Risk Agent

**Sprint 9-10: Advanced Features (Weeks 13-15)**
- Quant Agent
- Report Agent
- Multi-agent orchestration
- RAG integration

**Sprint 11-12: Integration & Polish (Weeks 16-18)**
- Candidate Pool automation
- Strategy center
- Report generation
- Frontend polish

**Sprint 13-14: Testing & Deployment (Weeks 19-20)**
- End-to-end testing
- Performance optimization
- Security audit
- Production deployment

---

## Specialized Guidance

### For Multi-Agent Development
- **Start with one agent** (News Agent is good) as reference
- **Establish patterns** before building the fleet
- **Test agent coordination** early and often
- **Plan for agent failures** with fallback mechanisms

### For LangGraph Workflow
- **Visualize the DAG** before coding
- **Test parallel execution** thoroughly
- **Plan state management** carefully
- **Monitor workflow performance** from the start

### For RAG Integration
- **Start with simple retrieval** before adding complexity
- **Test embedding quality** early
- **Plan for data freshness** (news updates)
- **Monitor retrieval relevance** continuously

### For Workspace System
- **Design for long-term memory** from the start
- **Plan data retention policies**
- **Consider user data isolation** carefully
- **Implement backup and recovery**

## Tools & Templates

### Available Tools
- `estimate.py` - Automated complexity estimation
- Phase templates in `templates/` directory
- Reference examples in `references/` directory

### When to Use Tools
- **For quick estimates**: Use `estimate.py` with component parameters
- **For detailed plans**: Use phase templates from `templates/`
- **For best practices**: Consult `references/` directory

## Communication Style

When providing timeline estimates:

1. **Be realistic** - Don't over-promise
2. **Be specific** - Break down into concrete tasks
3. **Highlight dependencies** - Make blockers visible
4. **Include buffers** - Add 20-30% for unknowns
5. **Suggest priorities** - Recommend what to tackle first

## Response Quality Checklist

Before responding, verify:

- [ ] Estimated effort is realistic for the complexity
- [ ] Dependencies are clearly identified
- [ ] Risks and mitigations are included
- [ ] Milestones are concrete and measurable
- [ ] Tasks are broken down to 1-2 day increments
- [ ] Testing is included in the timeline
- [ ] Documentation time is accounted for

## Notes

- This skill assumes a small team (2-4 developers)
- Timelines may need adjustment for solo developers
- All estimates include buffer for iteration and refinement
- Testing time is included in all estimates
- Documentation is assumed to be part of each sprint

For questions about specific implementations, suggest consulting the detailed development documents in "AI Investment OS开发文档/" directory.
