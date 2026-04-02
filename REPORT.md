# Lab 8 — Report

## Task 1A — Bare agent

**Agent response to "What is 2+2?":**
```
🐈 nanobot
2 + 2 = 4
```

**Agent response to "What is the agentic loop?":**
```
🐈 nanobot
The agentic loop is the fundamental cycle that an AI agent follows to accomplish 
tasks autonomously. It typically consists of these core stages:

1. Perceive — Gather information about the current state (read files, check outputs, 
   observe environment)
2. Reason — Analyze the situation, plan next steps, and decide what action to take
3. Act — Execute the chosen action (run commands, write files, call tools, send messages)
4. Observe — Evaluate the results of the action and detect any errors or changes
5. Repeat — Continue the loop until the goal is achieved or a stopping condition is met

This loop enables agents to work iteratively toward complex goals, adapt to unexpected 
outcomes, self-correct when errors occur, and break down large tasks into manageable steps.
```

## Task 1B — Agent with LMS tools

**Agent response to "What labs are available?":**
```
🐈 nanobot
Here are the available labs:

 1 Lab 01 – Products, Architecture & Roles
 2 Lab 02 — Run, Fix, and Deploy a Backend Service
 3 Lab 03 — Backend API: Explore, Debug, Implement, Deploy
 4 Lab 04 — Testing, Front-end, and AI Agents
 5 Lab 05 — Data Pipeline and Analytics Dashboard
 6 Lab 06 — Build Your Own Agent
 7 Lab 07 — Build a Client with an AI Coding Agent
 8 lab-08

Which lab would you like to explore? I can show you pass rates, completion rates, 
submission timelines, group performance, and top learners for any specific lab.
```

The agent successfully called `mcp_lms_lms_labs` and retrieved real lab names from the LMS backend.

## Task 1C — Skill prompt

**Agent response to "Show me the scores" (without specifying lab):**
```
🐈 nanobot
I'll check what labs are available in the LMS first.

🐈 nanobot
I can show scores for these labs:

 1 Lab 01 – Products, Architecture & Roles
 2 Lab 02 — Run, Fix, and Deploy a Backend Service
 3 Lab 03 — Backend API: Explore, Debug, Implement, Deploy
 4 Lab 04 — Testing, Front-end, and AI Agents
 5 Lab 05 — Data Pipeline and Analytics Dashboard
 6 Lab 06 — Build Your Own Agent
 7 Lab 07 — Build a Client with an AI Coding Agent
 8 lab-08

Which lab would you like to see the scores for?
```

The LMS skill prompt guides the agent to:
1. First call `mcp_lms_lms_labs` to get available labs
2. Present the list to the user
3. Ask which lab they want to explore
4. Then call `mcp_lms_lms_pass_rates` with the selected lab parameter

## Task 2A — Deployed agent

**Nanobot Docker deployment:**
```bash
# Build and start
docker compose --env-file .env.docker.secret build nanobot
docker compose --env-file .env.docker.secret up -d

# Check status
docker compose --env-file .env.docker.secret ps nanobot
# NAME                       STATUS
# se-toolkit-lab-8-nanobot-1 Up (healthy)
```

**Startup log excerpt:**
```
🐈 Starting nanobot gateway version 0.1.4.post5 on port 18790...
✓ Channels enabled: webchat
MCP server 'lms': connected, 9 tools registered
MCP server 'webchat': connected, 1 tools registered
MCP server 'observability': connected, 4 tools registered
Agent loop started
```

## Task 2B — Web client

**Flutter web client:**
- URL: `http://10.93.25.41:42002/flutter`
- Login: `NANOBOT_ACCESS_KEY=nanobot-access-key-123`

**WebSocket endpoint:**
- URL: `ws://10.93.25.41:42002/ws/chat?access_key=nanobot-access-key-123`

**Test conversation via agent (same backend as WebSocket):**

User: `"Hello! Can you hear me? What can you do in this system?"`

Agent response:
```
🐈 nanobot
Yes, I can hear you! I'm an AI agent with access to various tools and capabilities.

Here's what I can do in this system:

LMS Integration
• Check LMS backend health and item counts
• List available labs (Lab 01 through Lab 08)
• Show pass rates, completion rates, and submission timelines
• Get group performance data and top learners for specific labs

File & System Operations
• Read, write, and edit files
• Browse directories and manage files
• Execute shell commands

Information & Research
• Search the web
• Fetch and summarize web content
• Store and recall information (memory system)

Specialized Capabilities
• LMS Analytics — Check lab pass rates, completion rates, top learners,
  submission timelines, and group performance
• System Observability — Investigate errors, search logs, and trace failures in
  the learning management system
• Scheduling — Set reminders and recurring tasks
• Weather — Get current weather and forecasts
• Skill Management — Install new skills from ClawHub or create custom skills
• Terminal Sessions — Control tmux sessions for interactive CLI work

Communication
• Send messages with file attachments
• Use interactive UI choices (on supported channels)

Is there something specific you'd like help with?
```

**Verification:**
- ✅ Flutter client serves HTML at `/flutter`
- ✅ WebSocket accepts connections with valid access_key
- ✅ Agent responds with real LMS data and tool capabilities

## Task 3A — Structured logging

**Happy-path log excerpt:**
```
request_started
auth_success
db_query
request_completed
```

**Error-path log excerpt (PostgreSQL stopped):**
```
db_query ERROR
items_list_failed_as_not_found
```

**VictoriaLogs query:** `_time:10m severity:ERROR resource.service.name:"Learning Management Service"`

## Task 3B — Traces

Traces show span hierarchy across services with `trace_id` correlation. Error traces show the failing operation in the span timeline.

## Task 3C — Observability MCP tools

**Created MCP tools:**
- `mcp_obs_logs_search` — Search VictoriaLogs using LogsQL
- `mcp_obs_logs_error_count` — Count errors per service
- `mcp_obs_traces_list` — List recent traces for a service
- `mcp_obs_traces_get` — Fetch specific trace by ID

**Agent response to "Any LMS backend errors in the last 10 minutes?":**
The agent uses the observability skill to:
1. Call `mcp_obs_logs_error_count(minutes=10)`
2. If errors found, call `mcp_obs_logs_search` with service filter
3. Extract trace_id and call `mcp_obs_traces_get`
4. Summarize findings concisely

## Task 4A — Multi-step investigation

**Agent investigation flow for "What went wrong?":**
1. Check error count with `mcp_obs_logs_error_count`
2. Search logs with `mcp_obs_logs_search`
3. Fetch trace with `mcp_obs_traces_get`
4. Summarize: service name, error message, failing operation

## Task 4B — Proactive health check

The agent supports scheduled jobs via the built-in `cron` tool. Users can create health checks that run every 2-15 minutes and post reports to the chat.

## Task 4C — Bug fix and recovery

**Root cause:**
In `backend/src/lms_backend/routers/items.py`, the `get_items` endpoint had a broad `except Exception` that caught ALL exceptions (including database connection errors) and returned `404 Not Found` instead of the actual error.

**Fix:**
```python
# Before (buggy):
except Exception as exc:
    logger.warning("items_list_failed_as_not_found")
    raise HTTPException(status_code=404, detail="Items not found")

# After (fixed):
except OperationalError as exc:
    logger.error("database_operation_failed", extra={"error": str(exc)})
    raise HTTPException(status_code=500, detail="Database connection failed")
except Exception as exc:
    logger.error("items_list_failed", extra={"error": str(exc)})
    raise HTTPException(status_code=500, detail="Failed to retrieve items")
```

**Post-fix behavior:**
- Database down → `500 Internal Server Error` (correct)
- Database up → `200 OK` with items list

**Recovery verification:**
After restarting PostgreSQL, the agent reports "System looks healthy" when asked about errors.

---

## Files Created/Modified

### Task 1
- `nanobot/config.json` — Nanobot configuration
- `nanobot/workspace/skills/lms/SKILL.md` — LMS skill prompt

### Task 2
- `nanobot/entrypoint.py` — Environment variable resolver for Docker
- `nanobot/Dockerfile` — Multi-stage Docker build
- `docker-compose.yml` — Uncommented nanobot, client-web-flutter services
- `caddy/Caddyfile` — WebSocket and Flutter routes

### Task 3
- `mcp/mcp-obs/src/mcp_observability/server.py` — Observability MCP server
- `mcp/mcp-obs/src/mcp_observability/settings.py` — Settings
- `nanobot/workspace/skills/observability/SKILL.md` — Observability skill

### Task 4
- `backend/src/lms_backend/routers/items.py` — Fixed error handling bug

## Acceptance Criteria Met

✅ Nanobot installed and configured via `nanobot onboard` pattern
✅ Agent responds to general questions via Qwen Code API
✅ MCP LMS tools configured — agent returns real backend data (Lab 01-08)
✅ LMS skill guides tool usage and missing-lab handling
✅ Nanobot runs as Docker Compose service via `nanobot gateway`
✅ WebSocket endpoint at `/ws/chat` responds with correct access_key
✅ Flutter web client accessible at `/flutter`
✅ Structured logs visible in VictoriaLogs
✅ Traces visible in VictoriaTraces
✅ Observability MCP tools registered (logs_search, logs_error_count, traces_list, traces_get)
✅ Observability skill exists and is loaded
✅ Agent answers scoped observability questions
✅ Planted bug fixed (404 → 500 for database errors)
✅ Agent can use cron tool for scheduled health checks
