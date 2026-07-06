# Test: Dev Timeline Skill

## Test Case 1: Agent Estimation

**Input**: "How long to implement the News Agent?"

**Expected Response Should Include**:
- Complexity level (High)
- Total estimate (7-9 days)
- Task breakdown (data layer, core logic, integration, testing)
- Dependencies (LLM provider, Base Agent class)
- Risks (prompt iteration, API limits)
- Milestones (weekly checkpoints)

---

## Test Case 2: Sprint Planning

**Input**: "Plan Sprint 5. We've completed database setup and basic API framework."

**Expected Response Should Include**:
- Sprint duration (2 weeks)
- Prioritized tasks (stock service, workspace service)
- Dependencies and blockers
- Milestones with deliverables
- Risk considerations

---

## Test Case 3: Risk Assessment

**Input**: "What are the risks of implementing the RAG system?"

**Expected Response Should Include**:
- Multiple risk factors (embedding quality, data freshness, performance)
- Probability and impact ratings
- Mitigation strategies for each risk
- Recommended approach

---

## Test Case 4: Phase Planning

**Input**: "Help me plan Phase 4 with 3 developers and 4 months."

**Expected Response Should Include**:
- Sprint breakdown (8 sprints)
- Clear priorities (foundation → services → agents → integration)
- Resource allocation
- Milestones every 2 weeks
- Risk buffer included

---

## Validation Criteria

✅ Response includes timeline estimate
✅ Tasks are broken down to 1-2 day increments
✅ Dependencies are clearly identified
✅ Risks and mitigations are included
✅ Milestones are concrete and measurable
✅ Testing time is included
✅ Buffer for unknowns is added (20-30%)

---

## Usage

To test the skill:
1. Open a new conversation
2. Ask one of the test questions above
3. Verify the response includes all expected elements
4. Check that estimates are realistic for the AI Investment OS project

---

## Notes

- The skill should automatically trigger when these questions are asked
- Estimates should be specific to the AI Investment OS project
- Responses should reference the project's architecture and tech stack
- The skill should ask for clarification if context is missing
