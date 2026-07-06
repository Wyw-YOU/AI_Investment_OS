# 🚀 Getting Started with Dev Timeline Skill

## Quick Start

### Step 1: Ask a Question
Simply ask about development timeline, planning, or estimation:

```
"How long to implement the News Agent?"
"Help me plan Phase 4 of development."
"What are the risks of our current timeline?"
```

The skill will automatically activate and provide detailed estimates.

---

### Step 2: Provide Context (Optional)
For better estimates, include:
- **Team size**: "We have 3 developers"
- **Experience**: "New to LangGraph but experienced with Python"
- **Constraints**: "Need to launch in 3 months"
- **Current state**: "Database and API framework are done"

---

### Step 3: Review the Response
The skill provides:
- ✅ **Timeline Estimate** - Total effort with buffer
- ✅ **Task Breakdown** - Specific deliverables
- ✅ **Dependencies** - What must be done first
- ✅ **Risks** - Potential blockers
- ✅ **Milestones** - Concrete checkpoints

---

## Example Conversations

### Example 1: Simple Estimate
```
You: How long to implement the Financial Agent?

Skill: [Provides detailed 7-9 day estimate with task breakdown]
```

### Example 2: Sprint Planning
```
You: We're starting Sprint 5. Database and basic API are done. What should we focus on?

Skill: [Creates 2-week sprint plan with priorities and milestones]
```

### Example 3: Phase Planning
```
You: Plan Phase 4 with 3 developers and 4 months.

Skill: [Provides 8-sprint plan with clear roadmap]
```

### Example 4: Risk Assessment
```
You: What are the risks of launching in 2 months?

Skill: [Identifies risks with probability, impact, and mitigations]
```

---

## Common Questions & Quick Answers

### Q: How long for a simple agent?
**A**: 3-4 days (simple), 5-6 days (medium), 7-9 days (complex)

### Q: How long for a full feature?
**A**: 1-2 weeks (simple), 2-4 weeks (medium), 1-2 months (complex)

### Q: How many developers do I need?
**A**: Depends on timeline:
- 4 months → 2-3 developers
- 3 months → 3-4 developers
- 2 months → 4+ developers

### Q: What should we build first?
**A**: Foundation → Core Services → Agents → Integration → Polish

---

## Tips for Best Results

### ✅ DO:
- Be specific about what you're planning
- Provide team context (size, experience)
- Mention constraints (timeline, budget)
- Ask follow-up questions to refine
- Use the estimates as starting points

### ❌ DON'T:
- Ask vague questions ("How long to build everything?")
- Forget to mention dependencies
- Assume perfect conditions
- Skip testing time in your planning
- Ignore the buffer recommendations

---

## Using the Tools

### estimate.py - Quick Estimation
```python
# Navigate to scripts directory
cd .claude/skills/dev-timeline/scripts

# Run the estimation tool
python estimate.py

# Or use in your own code
from estimate import estimate_agent, Complexity

result = estimate_agent("News Agent", Complexity.HIGH)
print(f"Estimated: {result.total_days} days")
```

### Templates - Planning Documents
Use templates in `templates/` directory:
- `phase-template.md` - For phase planning
- `sprint-template.md` - For sprint planning

### References - Detailed Data
Check `references/` for:
- `timeline-reference.md` - Detailed timeline data
- `complexity-guide.md` - Complexity assessment

---

## Understanding the Estimates

### Time Components
```
Base Effort: Core development time
    + Buffer (25%): For unknowns and iteration
    + Testing (20-40%): Quality assurance
    + Documentation (10%): Docs and comments
    = Total Estimate
```

### Complexity Levels
```
Low (1-2 days): Simple CRUD, basic UI
Medium (3-5 days): API endpoints, DB operations
High (5-10 days): Agent implementation, workflows
Very High (10-15+ days): Multi-agent, RAG, complex state
```

### Sprint Velocity
```
Sprint: 2 weeks (10 days)
Effective: 8 days (meetings, reviews)
Output: 12-16 story points
```

---

## Project Context

This skill is specifically designed for **AI Investment OS**:
- **Multi-Agent System**: 8 specialized agents
- **Tech Stack**: FastAPI, Next.js, LangGraph, PostgreSQL, Qdrant
- **Architecture**: Event-driven, Workspace-based memory
- **Deployment**: Docker Compose on single server (2C4G)

Estimates are tailored to this specific project and tech stack.

---

## Refining Estimates

### After Getting Initial Estimate:
1. **Ask about dependencies**: "What needs to be done first?"
2. **Explore parallelization**: "Can we do these in parallel?"
3. **Consider MVP scope**: "What's the minimum for launch?"
4. **Plan for iteration**: "How many rounds of refinement?"
5. **Account for risks**: "What could go wrong?"

### Example Refinement:
```
You: The estimate says 8 days for News Agent. Can we do it in 5?

Skill: To compress to 5 days, we could:
- Skip RAG integration initially (save 1.5 days)
- Use simpler prompt template (save 0.5 days)
- Reduce testing scope (save 1 day)
- But this increases risk of quality issues
```

---

## Tracking & Improvement

### Track Your Progress
Compare actual time vs. estimates:
```
Component: News Agent
Estimated: 8 days
Actual: 10 days
Reason: Prompt iteration took longer than expected
Lesson: Add more buffer for prompt engineering
```

### Improve Future Estimates
- Note common blockers
- Track team velocity
- Update complexity assessments
- Share learnings with team

---

## Advanced Usage

### Custom Estimates
For components not in the standard list:
```
You: How long to build a custom scoring system with 5 factors?

Skill: [Estimates based on complexity assessment]
```

### What-If Scenarios
```
You: What if we add 2 more developers?

Skill: [Adjusts timeline and identifies coordination overhead]
```

### Trade-off Analysis
```
You: Should we build the full RAG system or start simple?

Skill: [Compares approaches with time, risk, and value trade-offs]
```

---

## Troubleshooting

### Q: Estimate seems too long
**A**: Ask about:
- Reducing scope (MVP approach)
- Adding more developers
- Parallelizing tasks
- Using existing libraries/components

### Q: Estimate seems too short
**A**: Consider:
- Team experience with technology
- Integration complexity
- Testing requirements
- Documentation needs
- Buffer for unknowns

### Q: Need help with specific component
**A**: Provide more context:
- What have you already built?
- What's the current state?
- Any blockers or constraints?

---

## Getting Help

### Documentation
- **SKILL.md** - Main skill definition
- **README.md** - Detailed usage guide
- **QUICK_REFERENCE.md** - Fast lookup
- **SKILL_OVERVIEW.md** - Comprehensive overview

### Tools
- **estimate.py** - Quick estimation script
- **templates/** - Planning templates
- **references/** - Detailed data

### Examples
- See example conversations above
- Check test cases in `test_skill.md`

---

## Quick Reference Card

### Trigger Keywords
- development timeline
- project planning
- milestone estimation
- sprint planning
- how long to build
- time estimate
- development schedule

### Typical Agent Timelines
- Simple: 3-4 days
- Medium: 5-6 days
- Complex: 7-9 days
- Very Complex: 10-12 days

### Phase Durations
- PRD: 1-2 weeks
- SAD: 1-2 weeks
- DDD: 2-3 weeks
- Development: 16-20 weeks

### Buffer Recommendations
- New technology: +30-50%
- External APIs: +20-30%
- Complex integrations: +25-35%
- Standard work: +20-25%

---

## Next Steps

1. **Try it out**: Ask your first question
2. **Review the estimate**: Check the detailed breakdown
3. **Ask follow-ups**: Refine and iterate
4. **Use the tools**: estimate.py for quick calculations
5. **Track progress**: Compare actual vs. estimated
6. **Share learnings**: Help improve future estimates

---

**Ready to start? Ask your first question about development timeline!**

Example: "How long to implement the multi-agent workflow system?"
