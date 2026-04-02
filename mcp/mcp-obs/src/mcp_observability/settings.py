"""Settings for the observability MCP server."""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ObservabilitySettings(BaseSettings):
    """Configuration for the observability MCP server."""

    model_config = SettingsConfigDict(env_prefix="NANOBOT_")

    victorialogs_url: str = Field(
        default="http://localhost:42010",
        description="VictoriaLogs HTTP API URL",
    )
    victoriatraces_url: str = Field(
        default="http://localhost:42011",
        description="VictoriaTraces HTTP API URL",
    )
