"""Stdio MCP server exposing observability tools for VictoriaLogs and VictoriaTraces."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

from mcp_observability.settings import ObservabilitySettings


class LogsSearchParams(BaseModel):
    """Search logs by query and time range."""

    query: str = Field(..., description="LogsQL query string (e.g., 'severity:ERROR')")
    limit: int = Field(default=100, description="Maximum number of log entries to return")
    time_range: str = Field(default="1h", description="Time range (e.g., '1h', '10m', '1d')")


class LogsErrorCountParams(BaseModel):
    """Count errors per service over a time window."""

    minutes: int = Field(default=60, description="Time window in minutes")


class TracesListParams(BaseModel):
    """List recent traces for a service."""

    service: str = Field(..., description="Service name (e.g., 'Learning Management Service')")
    limit: int = Field(default=10, description="Maximum number of traces to return")


class TracesGetParams(BaseModel):
    """Fetch a specific trace by ID."""

    trace_id: str = Field(..., description="Trace ID (hex string)")


class ObservabilityTools:
    """Observability tool implementations."""

    def __init__(self, victorialogs_url: str, victoriatraces_url: str):
        self.victorialogs_url = victorialogs_url.rstrip("/")
        self.victoriatraces_url = victoriatraces_url.rstrip("/")

    async def logs_search(self, params: LogsSearchParams) -> list[TextContent]:
        """Search logs using VictoriaLogs LogsQL query."""
        async with httpx.AsyncClient() as client:
            url = f"{self.victorialogs_url}/select/logsql/query"
            query = f"_time:{params.time_range} {params.query}"
            resp = await client.post(url, params={"query": query, "limit": params.limit})
            resp.raise_for_status()
            return [TextContent(type="text", text=resp.text)]

    async def logs_error_count(self, params: LogsErrorCountParams) -> list[TextContent]:
        """Count errors per service over a time window."""
        async with httpx.AsyncClient() as client:
            time_range = f"{params.minutes}m"
            query = f"_time:{time_range} severity:ERROR"
            url = f"{self.victorialogs_url}/select/logsql/query"
            resp = await client.post(url, params={"query": query, "limit": 1000})
            resp.raise_for_status()
            
            # Parse and count errors by service
            try:
                logs = resp.json() if resp.text.startswith("[") else []
                service_counts: dict[str, int] = {}
                for entry in logs:
                    service = entry.get("_msg", {}).get("resource.service.name", "unknown")
                    service_counts[service] = service_counts.get(service, 0) + 1
                result = {"time_window": f"{params.minutes} minutes", "errors_by_service": service_counts}
            except (json.JSONDecodeError, AttributeError):
                result = {"time_window": f"{params.minutes} minutes", "raw_count": "Error parsing response"}
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def traces_list(self, params: TracesListParams) -> list[TextContent]:
        """List recent traces for a service."""
        async with httpx.AsyncClient() as client:
            url = f"{self.victoriatraces_url}/select/jaeger/api/traces"
            resp = await client.get(url, params={"service": params.service, "limit": params.limit})
            resp.raise_for_status()
            data = resp.json()
            
            # Simplify response
            traces = []
            for trace in data.get("data", []):
                traces.append({
                    "trace_id": trace.get("traceID"),
                    "spans": len(trace.get("spans", [])),
                    "start_time": trace.get("startTime"),
                    "duration": trace.get("duration"),
                })
            
            return [TextContent(type="text", text=json.dumps({"traces": traces}, indent=2))]

    async def traces_get(self, params: TracesGetParams) -> list[TextContent]:
        """Fetch a specific trace by ID."""
        async with httpx.AsyncClient() as client:
            url = f"{self.victoriatraces_url}/select/jaeger/api/traces/{params.trace_id}"
            resp = await client.get(url)
            resp.raise_for_status()
            return [TextContent(type="text", text=resp.text)]


def create_server(settings: ObservabilitySettings) -> Server:
    """Create the observability MCP server."""
    tools = ObservabilityTools(settings.victorialogs_url, settings.victoriatraces_url)
    server = Server("observability")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="mcp_obs_logs_search",
                description="Search VictoriaLogs using LogsQL query. Use for finding errors, warnings, or specific events.",
                inputSchema=LogsSearchParams.model_json_schema(),
            ),
            Tool(
                name="mcp_obs_logs_error_count",
                description="Count errors per service over a time window. Use to quickly assess system health.",
                inputSchema=LogsErrorCountParams.model_json_schema(),
            ),
            Tool(
                name="mcp_obs_traces_list",
                description="List recent traces for a service. Use to find trace IDs for detailed investigation.",
                inputSchema=TracesListParams.model_json_schema(),
            ),
            Tool(
                name="mcp_obs_traces_get",
                description="Fetch a specific trace by ID. Use to inspect the full span hierarchy of a request.",
                inputSchema=TracesGetParams.model_json_schema(),
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
        try:
            if name == "mcp_obs_logs_search":
                return await tools.logs_search(LogsSearchParams.model_validate(arguments or {}))
            elif name == "mcp_obs_logs_error_count":
                return await tools.logs_error_count(LogsErrorCountParams.model_validate(arguments or {}))
            elif name == "mcp_obs_traces_list":
                return await tools.traces_list(TracesListParams.model_validate(arguments or {}))
            elif name == "mcp_obs_traces_get":
                return await tools.traces_get(TracesGetParams.model_validate(arguments or {}))
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as exc:
            return [TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")]

    _ = list_tools, call_tool
    return server


async def main() -> None:
    settings = ObservabilitySettings()
    server = create_server(settings)
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
