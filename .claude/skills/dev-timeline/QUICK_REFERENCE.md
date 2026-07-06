# Dev Timeline Skill - Quick Reference

## Trigger Keywords
- development timeline
- project planning
- milestone estimation
- sprint planning
- development phases
- project roadmap
- how long to build
- time estimate
- development schedule

---

## Project Context
**AI Investment OS** - Multi-Agent Investment Research Platform

### Tech Stack
- **Frontend**: Next.js 14+, React 18, TailwindCSS, ECharts
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy 2.0
- **AI/ML**: LangGraph, LLM APIs, Qdrant (vector DB)
- **Database**: PostgreSQL, Redis, MinIO
- **Deployment**: Docker Compose, Nginx

### Key Components
- **8 Specialized Agents**: Planner, News, Financial, Technical, Macro, Risk, Quant, Report
- **6 Bounded Contexts**: Identity, Investment, Workspace, Agent, Analytics, Automation
- **Core Systems**: Multi-Agent Engine, Workspace Memory, Automation System

---

## Estimation Framework

### Complexity Levels
| Level | Days | Examples |
|-------|------|----------|
| Low | 1-2 | Simple CRUD, basic UI |
| Medium | 3-5 | API endpoints, DB operations |
| High | 5-10 | Agent implementation, workflows |
| Very High | 10-15+ | Multi-agent coordination, RAG |

### Time Components
- **Base effort**: Core development
- **Buffer**: +25% for unknowns
- **Testing**: +20-40% of dev time
- **Documentation**: +10%

### Typical Agent Development
- **Simple Agent**: 3-4 days
- **Medium Agent**: 5-6 days
- **Complex Agent**: 7-9 days
- **Very Complex Agent**: 10-12 days

---

## Response Template

When estimating, provide:

1. **Timeline Estimate**
   - Complexity level
   - Total days (with buffer)
   - Breakdown by task

2. **Task Breakdown**
   - Numbered list of tasks
   - Time for each task
   - Acceptance criteria

3. **Dependencies**
   - What must be done first
   - External dependencies
   - Team dependencies

4. **Risks & Mitigations**
   - Potential blockers
   - Probability and impact
   - Mitigation strategies

5. **Milestones**
   - Weekly/bi-weekly checkpoints
   - Concrete deliverables
   - Measurable outcomes

---

## Phase Durations

### Phase 1: Product Design (PRD)
**1-2 weeks** | Product owner + 1 dev

### Phase 2: System Architecture (SAD)
**1-2 weeks** | Tech lead + 1 senior dev

### Phase 3: Detailed Design (DDD)
**2-3 weeks** | Tech lead + 2 devs

### Phase 4: Development
**16-20 weeks** | 2-4 developers

---

## Sprint Velocity

### Team of 2 Developers
- **Sprint**: 2 weeks (10 days)
- **Effective**: 8 days (meetings, reviews)
- **Output**: 12-16 story points

### Story Points
- **1 pt**: 0.5-1 day (simple)
- **2 pts**: 1-2 days (medium)
- **3 pts**: 2-3 days (complex)
- **5 pts**: 4-5 days (very complex)
- **8 pts**: 6-8 days (epic)

---

## Common Questions & Answers

### "How long for [Agent]?"
→ Use agent complexity table
→ Include data, logic, prompts, tests, integration
→ Add 25% buffer

### "Plan our sprints"
→ Break into 2-week cycles
→ Prioritize: Foundation → Services → Agents → Integration
→ Balance complexity across sprints

### "What are the risks?"
→ Multi-agent coordination
→ External API dependencies
→ Performance optimization
→ State management complexity

### "How many developers?"
→ Solo: 1.5-2x estimates
→ Team of 2-3: As-is
→ Team of 4+: 0.8-0.9x estimates

---

## Key Principles

1. **Break down tasks** to 1-2 days
2. **Include testing** in estimates
3. **Add buffer** for unknowns (20-30%)
4. **Consider dependencies** and wait times
5. **Plan for iteration** and rework
6. **Track actual vs. estimated** time

---

## Tools & Resources

### estimate.py
```python
from estimate import estimate_agent, Complexity
result = estimate_agent("News Agent", Complexity.HIGH)
# Returns: 8.75 days total
```

### Templates
- `templates/phase-template.md`
- `templates/sprint-template.md`

### References
- `references/timeline-reference.md`
- `references/complexity-guide.md`

---

## Integration Points

This skill works with:
- **Multi-Agent Developer**: Agent implementation guidance
- **Code Review**: Quality assurance
- **Testing**: Test strategy and coverage
- **Documentation**: Technical writing

---

## Tips for Better Estimates

✅ **DO**:
- Ask about team experience
- Consider external dependencies
- Include all phases (design, implement, test, document)
- Plan for iteration
- Add buffer for unknowns

❌ **DON'T**:
- Forget testing time
- Ignore dependencies
- Assume perfect conditions
- Skip documentation
- Neglect code review time

---

## Customization

### For Your Team
- Track actual vs. estimated time
- Note common blockers
- Update estimates based on velocity
- Adjust for team experience

### For Your Project
- Add component-specific estimates
- Document common patterns
- Track risk occurrences
- Refine complexity assessments

---

## Emergency Estimates

When you need quick numbers:

**Simple Feature**: 2-3 days
**Medium Feature**: 1-2 weeks
**Complex Feature**: 2-4 weeks
**Major System**: 1-2 months

**Single Agent**: 1-2 weeks
**Agent Fleet**: 2-3 months
**Full MVP**: 4-6 months

---

*This skill is specifically designed for the AI Investment OS project. For other projects, provide additional context about architecture and tech stack.*
