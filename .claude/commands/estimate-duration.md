# Estimate Duration for PRP

Analyze a PRP file and provide detailed execution time estimates for all tasks.

## PRP File: $ARGUMENTS

## Estimation Process

1. **Load and Analyze PRP**
   - Read the specified PRP file at: $ARGUMENTS
   - Identify all tasks and subtasks across all agents
   - Understand complexity and dependencies
   - Review any existing time estimates in the PRP

2. **Task Breakdown Analysis**
   - Categorize tasks by agent (frontend-dev, backend-dev, trading-dev, ai-dev)
   - Identify task complexity (simple, moderate, complex)
   - Note dependencies between tasks
   - Consider setup and integration overhead

3. **Duration Estimation**
   For each task category, estimate:
   - Minimum time (optimistic scenario)
   - Expected time (realistic scenario)
   - Maximum time (pessimistic scenario)

   Consider these factors:
   - Code complexity and amount of code to write
   - Testing requirements
   - Integration complexity
   - Learning curve for new technologies
   - Debugging and troubleshooting time
   - Documentation needs

4. **Parallel Execution Analysis**
   - Identify which tasks can run in parallel
   - Calculate serial execution time (all tasks sequential)
   - Calculate parallel execution time (with 4 agents working simultaneously)
   - Note any blocking dependencies

5. **Generate Detailed Report**

   Provide a comprehensive report with:

   ### Individual Agent Estimates
   - **Frontend Tasks**: [min-max hours] - List key tasks
   - **Backend Tasks**: [min-max hours] - List key tasks
   - **Trading Tasks**: [min-max hours] - List key tasks
   - **AI/ML Tasks**: [min-max hours] - List key tasks

   ### Execution Scenarios
   - **Serial Execution**: Total hours if one agent works on all tasks
   - **Parallel Execution**: Total hours with 4 agents working simultaneously
   - **Time Savings**: Percentage reduction with parallel execution

   ### Critical Path Analysis
   - Identify the longest dependent task chain
   - Note any bottlenecks or blocking tasks

   ### Assumptions and Risks
   - List key assumptions made in estimates
   - Identify potential risks that could extend timeline
   - Suggest mitigation strategies

   ### Recommendations
   - Optimal task ordering
   - Suggested agent assignments
   - Areas where additional resources might help

6. **Summary**
   - Provide a clear, actionable summary
   - Recommend whether to proceed with the current plan
   - Suggest any PRP modifications to optimize execution time

## Output Format

Present the analysis in a clear, structured markdown format with:
- Tables for numerical estimates
- Bullet points for task lists
- Clear section headers
- Visual indicators (✓, ⚠️, ⏱️) where appropriate

## Note

This is an estimate based on typical development patterns. Actual execution time may vary based on:
- Developer experience and familiarity with technologies
- Code quality and complexity encountered
- External dependencies and API limitations
- Testing and debugging requirements
- Scope changes during implementation
