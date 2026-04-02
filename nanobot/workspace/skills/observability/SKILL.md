---
name: observability
description: Use observability MCP tools for logs and traces investigation
always: true
---

# Observability Skill

You have access to observability MCP tools that let you query VictoriaLogs and VictoriaTraces. Use these tools to investigate system health, find errors, and diagnose failures.

## Available Tools

### Log Tools (VictoriaLogs)
- `mcp_obs_logs_search` — Search logs using LogsQL query
- `mcp_obs_logs_error_count` — Count errors per service over a time window

### Trace Tools (VictoriaTraces)
- `mcp_obs_traces_list` — List recent traces for a service
- `mcp_obs_traces_get` — Fetch a specific trace by ID

## Investigation Strategy

### When the user asks "What went wrong?" or "Check system health":

1. **Start with error count** — Call `mcp_obs_logs_error_count` with `minutes=10` to see if there are recent errors
2. **Search for errors** — If errors exist, call `mcp_obs_logs_search` with:
   - `query: "severity:ERROR"` or `query: "severity:ERROR resource.service.name:\"Learning Management Service\""`
   - `time_range: "10m"`
   - `limit: 20`
3. **Extract trace ID** — Look for `trace_id` in the log results
4. **Fetch the trace** — Call `mcp_obs_traces_get` with the trace ID to see the full span hierarchy
5. **Summarize findings** — Explain:
   - What service failed
   - What error occurred
   - Which operations were involved (from trace spans)
   - The root cause if identifiable

### When the user asks about specific errors:

- **Time-based**: "errors in the last hour" → `mcp_obs_logs_error_count(minutes=60)`
- **Service-based**: "LMS backend errors" → `mcp_obs_logs_search(query="severity:ERROR resource.service.name:\"Learning Management Service\"")`
- **Event-based**: "database failures" → `mcp_obs_logs_search(query="event:db_query severity:ERROR")`

## LogsQL Query Examples

```
# All errors in last hour
_time:1h severity:ERROR

# LMS backend errors
_time:10m severity:ERROR resource.service.name:"Learning Management Service"

# Database query failures
_time:30m event:db_query severity:ERROR

# Find trace ID in logs
_time:10m trace_id:* severity:ERROR
```

## Response Format

- **Be concise** — Summarize findings, don't dump raw JSON
- **Highlight key info** — Service name, error message, trace ID, failing operation
- **Explain the chain** — "The request failed at step X, which caused Y to fail"
- **Note healthy systems** — "No errors found in the last 10 minutes. System appears healthy."

## Example Investigation Flow

**User:** "What went wrong?"

**You:**
1. (Call `mcp_obs_logs_error_count(minutes=10)`)
2. "I found 15 errors in the last 10 minutes, all in the Learning Management Service."
3. (Call `mcp_obs_logs_search(query="severity:ERROR resource.service.name:\"Learning Management Service\"", time_range="10m", limit=10)`)
4. "The errors show database connection failures. Let me fetch the trace to see the full picture."
5. (Extract trace_id from logs, call `mcp_obs_traces_get(trace_id="...")`)
6. "The trace shows the request failed when trying to connect to PostgreSQL. The database appears to be down or unreachable."
