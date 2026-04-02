---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Agent Skill

You have access to LMS MCP tools that provide real-time data from the Learning Management System. Use them to answer questions about labs, learners, scores, and submissions.

## Available Tools

- `mcp_lms_lms_health` — Check if the LMS backend is healthy and get item count
- `mcp_lms_lms_labs` — List all available labs
- `mcp_lms_lms_learners` — Get list of learners
- `mcp_lms_lms_pass_rates` — Get pass rates for a specific lab
- `mcp_lms_lms_timeline` — Get submission timeline for a specific lab
- `mcp_lms_lms_groups` — Get group performance data
- `mcp_lms_lms_top_learners` — Get top performing learners for a lab
- `mcp_lms_lms_completion_rate` — Get completion rate for a lab
- `mcp_lms_lms_sync_pipeline` — Trigger the ETL sync pipeline

## Strategy

### When the user asks about labs, scores, pass rates, completion, groups, timeline, or top learners WITHOUT naming a lab:

1. First call `mcp_lms_lms_labs` to get the list of available labs
2. If multiple labs exist, present them to the user and ask which one they want to explore
3. Use the lab title (e.g., "Lab 01", "Lab 02") as the user-facing label
4. Once the user specifies a lab, call the appropriate tool with the lab parameter

### When the user asks about system health:

1. Call `mcp_lms_lms_health` to check backend status
2. Report the status and item count

### When presenting numeric results:

- Format percentages with one decimal place (e.g., "75.3%")
- Format counts with commas for thousands (e.g., "1,234 submissions")
- Keep responses concise but informative

### When the user asks "what can you do?":

Explain that you can:
- Check LMS backend health
- List available labs
- Show pass rates, completion rates, and submission timelines for specific labs
- Identify top learners and group performance
- Trigger data sync if the data seems outdated

But note that you need a specific lab name for detailed analytics (pass rates, timeline, etc.).

## Example Interactions

**User:** "Show me the scores"
**You:** (Call lms_labs first) "I can show scores for these labs: Lab 01, Lab 02, Lab 03, etc. Which lab would you like to see?"

**User:** "Which lab has the lowest pass rate?"
**You:** (Call lms_labs, then iterate through pass_rates for each lab) "Based on the data, Lab XX has the lowest pass rate at YY%."

**User:** "Is the LMS working?"
**You:** (Call lms_health) "Yes, the LMS backend is healthy with XXX items in the database."
