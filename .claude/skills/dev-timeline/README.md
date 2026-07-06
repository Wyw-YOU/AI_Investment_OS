# Development Timeline Expert - Skill Usage Guide

## Overview

This skill provides expert guidance on planning and estimating development timelines for the AI Investment OS project—a sophisticated multi-agent investment research platform.

---

## When to Use This Skill

Use this skill when you need help with:

- **Timeline Estimation**: "How long will it take to implement the News Agent?"
- **Sprint Planning**: "What should we focus on in the next sprint?"
- **Milestone Definition**: "What are the key milestones for Phase 4?"
- **Project Roadmap**: "Help me create a 3-month development roadmap"
- **Risk Assessment**: "What are the risks for this feature?"
- **Resource Planning**: "How many developers do we need?"
- **Priority Setting**: "What should we build first?"

---

## How to Use

### 1. Describe Your Question

Be specific about what you're planning:
- Which component or feature?
- What's the current state?
- Any constraints (timeline, team size, etc.)?

**Example**:
```
I need to plan the development of the multi-agent workflow system using LangGraph. 
We have 2 developers and want to complete it in 3 weeks.
```

### 2. Provide Context

Help the skill give better estimates:
- Team experience level
- Existing codebase state
- External dependencies
- Quality requirements

**Example**:
```
Our team is new to LangGraph but experienced with Python and FastAPI.
We've already set up the basic infrastructure and database.
```

### 3. Ask Follow-up Questions

Iterate on the estimates:
- "What if we add more developers?"
- "Can we parallelize these tasks?"
- "What's the MVP scope?"
- "What can we defer to later?"

---

## Response Format

The skill provides structured estimates including:

### Timeline Estimate
- **Complexity**: Low/Medium/High/Very High
- **Estimated Effort**: X days/weeks
- **Buffer**: Included (25% typical)

### Task Breakdown
- Numbered list of specific tasks
- Time estimate for each task
- Clear acceptance criteria

### Dependencies
- What needs to be completed first
- External dependencies
- Team dependencies

### Risks & Mitigations
- Potential blockers
- Mitigation strategies
- Contingency plans

### Milestones
- Weekly or bi-weekly checkpoints
- Concrete deliverables
- Measurable outcomes

---

## Example Questions

### Simple Estimate
```
Q: How long to implement the Technical Agent?
```

### Sprint Planning
```
Q: We're starting Sprint 5 next week. We've completed the database setup and 
basic API framework. What should we focus on?
```

### Phase Planning
```
Q: Help me plan Phase 4 (Development). We have 3 developers and 4 months.
```

### Risk Assessment
```
Q: What are the risks of implementing the RAG system with Qdrant?
```

### Resource Planning
```
Q: We want to launch in 3 months. How many developers do we need?
```

### Priority Setting
```
Q: We have limited time. What are the must-have features for MVP?
```

---

## Available Tools

### estimate.py
Quick complexity estimation script.

**Usage**:
```python
from estimate import estimate_agent, estimate_component, Complexity

# Estimate an agent
result = estimate_agent("News Agent", Complexity.HIGH)
print(result.total_days)  # Output: 8.75 days

# Estimate a custom component
result = estimate_component(
    name="Custom Service",
    component_type=ComponentType.SERVICE,
    complexity=Complexity.MEDIUM
)
```

### Templates
- `phase-template.md`: Template for phase planning
- `sprint-template.md`: Template for sprint planning

### References
- `timeline-reference.md`: Detailed timeline references
- `complexity-guide.md`: How to assess complexity

---

## Understanding Estimates

### Time Components

**Base Effort**: Core development time
**Buffer**: 25% added for unknowns and iteration
**Testing**: 20-40% of development time
**Documentation**: 10% of development time

### Complexity Levels

**Low (1-2 days)**
- Simple CRUD operations
- Basic UI components
- Straightforward integrations

**Medium (3-5 days)**
- API endpoints with business logic
- Database operations with complex queries
- UI with moderate interactivity

**High (5-10 days)**
- Agent implementation
- Workflow orchestration
- Complex integrations
- Real-time features

**Very High (10-15+ days)**
- Multi-agent coordination
- RAG system implementation
- Complex state management
- Performance-critical systems

---

## Best Practices

### For Accurate Estimates

1. **Break down tasks** to 1-2 day increments
2. **Include all phases**: Design, implement, test, document
3. **Account for dependencies** and wait times
4. **Add buffer** for unknowns (20-30%)
5. **Consider team experience** with technologies
6. **Plan for iteration** and rework

### For Sprint Planning

1. **Prioritize by value** and dependencies
2. **Balance complexity** across sprints
3. **Include buffer** for unexpected issues
4. **Plan for testing** within each sprint
5. **Leave time for review** and refinement

### For Risk Management

1. **Identify risks early** in planning
2. **Plan mitigation strategies** upfront
3. **Add contingency time** for high-risk items
4. **Monitor risks** throughout development
5. **Escalate blockers** quickly

---

## Customization

### Adjusting for Team Size

**Solo Developer**:
- Multiply estimates by 1.5-2x
- Less parallelization
- More context switching

**Small Team (2-3)**:
- Use estimates as-is
- Good parallelization
- Moderate communication overhead

**Larger Team (4+)**:
- Multiply estimates by 0.8-0.9x
- High parallelization
- More coordination needed

### Adjusting for Experience

**Team New to Stack**:
- Add 30-50% to estimates
- Include learning time
- Plan for more iteration

**Experienced Team**:
- Use estimates as-is or reduce by 10-20%
- Faster iteration
- Better estimation accuracy

---

## Integration with Project

This skill is specifically designed for the AI Investment OS project and understands:

- **Architecture**: Multi-agent system with LangGraph
- **Tech Stack**: Python, FastAPI, Next.js, PostgreSQL, Qdrant
- **Domain**: Investment research, stock analysis
- **Phases**: PRD → SAD → DDD → Development

For questions about other projects, provide additional context about the architecture and tech stack.

---

## Limitations

- Estimates are based on typical team velocity
- Actual time may vary based on team experience
- External dependencies can significantly impact timelines
- Scope changes require re-estimation
- Estimates assume focused work without major interruptions

---

## Getting Help

For more detailed guidance:

1. **Read the reference docs**: Check `references/` directory
2. **Use the estimation tool**: Run `scripts/estimate.py`
3. **Consult the templates**: Use templates in `templates/` directory
4. **Ask specific questions**: More detail = better estimates

---

## Contributing

To improve this skill:

1. Track actual vs. estimated time for tasks
2. Note common blockers and solutions
3. Update estimates based on team velocity
4. Add new component estimates as needed
5. Refine complexity assessments based on experience
