#!/usr/bin/env python3
"""
Nanobot gateway entrypoint.

Resolves environment variables into config.json at runtime,
then launches `nanobot gateway`.

Environment variables:
- LLM_API_KEY -> providers.custom.apiKey
- LLM_API_BASE_URL -> providers.custom.apiBase
- LLM_API_MODEL -> agents.defaults.model
- NANOBOT_GATEWAY_CONTAINER_ADDRESS -> gateway.host
- NANOBOT_GATEWAY_CONTAINER_PORT -> gateway.port
- NANOBOT_WEBCHAT_CONTAINER_ADDRESS -> channels.webchat.host (optional)
- NANOBOT_WEBCHAT_CONTAINER_PORT -> channels.webchat.port
- NANOBOT_LMS_BACKEND_URL -> tools.mcpServers.lms.env.NANOBOT_LMS_BACKEND_URL
- NANOBOT_LMS_API_KEY -> tools.mcpServers.lms.env.NANOBOT_LMS_API_KEY
- NANOBOT_VICTORIALOGS_URL -> tools.mcpServers.observability.env.NANOBOT_VICTORIALOGS_URL
- NANOBOT_VICTORIATRACES_URL -> tools.mcpServers.observability.env.NANOBOT_VICTORIATRACES_URL
- NANOBOT_ACCESS_KEY -> channels.webchat.access_key
"""

import json
import os
from pathlib import Path


def main():
    config_path = Path("/app/nanobot/config.json")
    workspace_path = Path("/app/nanobot/workspace")
    resolved_path = Path("/tmp/nanobot/config.resolved.json")

    # Ensure /tmp/nanobot directory exists
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    # Read base config
    with open(config_path) as f:
        config = json.load(f)

    # Override LLM provider settings from env vars
    if "LLM_API_KEY" in os.environ:
        config.setdefault("providers", {}).setdefault("custom", {})["apiKey"] = (
            os.environ["LLM_API_KEY"]
        )
    if "LLM_API_BASE_URL" in os.environ:
        config.setdefault("providers", {}).setdefault("custom", {})["apiBase"] = (
            os.environ["LLM_API_BASE_URL"]
        )
    if "LLM_API_MODEL" in os.environ:
        config.setdefault("agents", {}).setdefault("defaults", {})["model"] = (
            os.environ["LLM_API_MODEL"]
        )

    # Gateway settings
    if "NANOBOT_GATEWAY_CONTAINER_ADDRESS" in os.environ:
        config.setdefault("gateway", {})["host"] = os.environ[
            "NANOBOT_GATEWAY_CONTAINER_ADDRESS"
        ]
    if "NANOBOT_GATEWAY_CONTAINER_PORT" in os.environ:
        config.setdefault("gateway", {})["port"] = int(
            os.environ["NANOBOT_GATEWAY_CONTAINER_PORT"]
        )

    # Webchat channel settings
    if "NANOBOT_WEBCHAT_CONTAINER_ADDRESS" in os.environ:
        config.setdefault("channels", {}).setdefault("webchat", {})["host"] = (
            os.environ["NANOBOT_WEBCHAT_CONTAINER_ADDRESS"]
        )
    if "NANOBOT_WEBCHAT_CONTAINER_PORT" in os.environ:
        config.setdefault("channels", {}).setdefault("webchat", {})["port"] = int(
            os.environ["NANOBOT_WEBCHAT_CONTAINER_PORT"]
        )
    if "NANOBOT_ACCESS_KEY" in os.environ:
        config.setdefault("channels", {}).setdefault("webchat", {})["access_key"] = (
            os.environ["NANOBOT_ACCESS_KEY"]
        )

    # MCP server environment variables
    # LMS MCP server
    lms_env = {}
    if "NANOBOT_LMS_BACKEND_URL" in os.environ:
        lms_env["NANOBOT_LMS_BACKEND_URL"] = os.environ["NANOBOT_LMS_BACKEND_URL"]
    if "NANOBOT_LMS_API_KEY" in os.environ:
        lms_env["NANOBOT_LMS_API_KEY"] = os.environ["NANOBOT_LMS_API_KEY"]

    if lms_env:
        config.setdefault("tools", {}).setdefault("mcpServers", {}).setdefault(
            "lms", {}
        )["env"] = lms_env

    # Observability MCP server
    obs_env = {}
    if "NANOBOT_VICTORIALOGS_URL" in os.environ:
        obs_env["NANOBOT_VICTORIALOGS_URL"] = os.environ["NANOBOT_VICTORIALOGS_URL"]
    if "NANOBOT_VICTORIATRACES_URL" in os.environ:
        obs_env["NANOBOT_VICTORIATRACES_URL"] = os.environ["NANOBOT_VICTORIATRACES_URL"]

    if obs_env:
        config.setdefault("tools", {}).setdefault("mcpServers", {}).setdefault(
            "observability", {}
        )["env"] = obs_env

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_path}")

    # Launch nanobot gateway
    os.execvp(
        "nanobot",
        [
            "nanobot",
            "gateway",
            "--config",
            str(resolved_path),
            "--workspace",
            str(workspace_path),
        ],
    )


if __name__ == "__main__":
    main()
