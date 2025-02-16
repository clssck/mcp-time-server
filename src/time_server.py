import asyncio
import json
import logging
from collections.abc import Sequence
from datetime import datetime, timedelta
from enum import Enum
from zoneinfo import ZoneInfo

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool
from mcp.types import ErrorData as McpErrorData
from pydantic import BaseModel


class ErrorData(McpErrorData):
    """Local ErrorData class that inherits from mcp.types.ErrorData"""


class TimeTools(str, Enum):
    GET_CURRENT_TIME = "get_current_time"
    CONVERT_TIME = "convert_time"


class TimeResult(BaseModel):
    timezone: str
    datetime: str
    is_dst: bool


class TimeConversionResult(BaseModel):
    source: TimeResult
    target: TimeResult
    time_difference: str


class TimeConversionInput(BaseModel):
    source_tz: str
    time: str
    target_tz_list: list[str]


def get_local_tz(local_tz_override: str | None = None) -> ZoneInfo:
    if local_tz_override:
        return ZoneInfo(local_tz_override)

    # Get local timezone from datetime.now()
    tzinfo = datetime.now().astimezone(tz=None).tzinfo
    if tzinfo is not None:
        return ZoneInfo(str(tzinfo))
    raise McpError(
        error=ErrorData(
            code=1001,
            message="Could not determine local timezone - tzinfo is None",
        ),
    )


def get_zoneinfo(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except Exception as e:
        error_msg = f"Invalid timezone: {e!s}"
        raise McpError(
            error=ErrorData(
                code=1002,
                message=error_msg,
            ),
        ) from e


class TimeServer:
    @staticmethod
    def get_current_time(timezone_name: str) -> TimeResult:
        """Get current time in specified timezone"""
        timezone = get_zoneinfo(timezone_name)
        current_time = datetime.now(timezone)

        return TimeResult(
            timezone=timezone_name,
            datetime=current_time.isoformat(timespec="seconds"),
            is_dst=bool(current_time.dst()),
        )

    @staticmethod
    def convert_time(
        source_tz: str,
        time_str: str,
        target_tz: str,
    ) -> TimeConversionResult:
        """Convert time between timezones"""
        source_timezone = get_zoneinfo(source_tz)
        target_timezone = get_zoneinfo(target_tz)

        try:
            parsed_time = datetime.strptime(time_str + " +0000", "%H:%M %z").time()
        except ValueError as e:
            error_msg = "Invalid time format. Expected HH:MM [24-hour format]"
            raise ValueError(error_msg) from e

        now = datetime.now(source_timezone)
        source_time = datetime(
            now.year,
            now.month,
            now.day,
            parsed_time.hour,
            parsed_time.minute,
            tzinfo=source_timezone,
        )

        target_time = source_time.astimezone(target_timezone)
        source_offset = source_time.utcoffset() or timedelta()
        target_offset = target_time.utcoffset() or timedelta()
        hours_difference = (target_offset - source_offset).total_seconds() / 3600

        if hours_difference.is_integer():
            time_diff_str = f"{hours_difference:+.1f}h"
        else:
            # For fractional hours like Nepal's UTC+5:45
            time_diff_str = f"{hours_difference:+.2f}".rstrip("0").rstrip(".") + "h"

        return TimeConversionResult(
            source=TimeResult(
                timezone=source_tz,
                datetime=source_time.isoformat(timespec="seconds"),
                is_dst=bool(source_time.dst()),
            ),
            target=TimeResult(
                timezone=target_tz,
                datetime=target_time.isoformat(timespec="seconds"),
                is_dst=bool(target_time.dst()),
            ),
            time_difference=time_diff_str,
        )


logger = logging.getLogger(__name__)
# Suppress INFO logs for MCP request types
logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)


def create_tools(local_tz: str) -> list[Tool]:
    """Create and return the list of available tools."""
    local_tz_desc = (
        "IANA timezone name (e.g., 'America/New_York', 'Europe/London'). "
        f"Use '{local_tz}' as local timezone if no timezone provided."
    )
    return [
        Tool(
            name=TimeTools.GET_CURRENT_TIME.value,
            description="Get current time in a specific timezones",
            inputSchema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": local_tz_desc,
                    },
                },
                "required": ["timezone"],
            },
        ),
        Tool(
            name=TimeTools.CONVERT_TIME.value,
            description="Convert time between timezones",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_timezone": {
                        "type": "string",
                        "description": local_tz_desc,
                    },
                    "time": {
                        "type": "string",
                        "description": "Time to convert in 24-hour format (HH:MM)",
                    },
                    "target_timezone": {
                        "type": "string",
                        "description": local_tz_desc,
                    },
                },
                "required": ["source_timezone", "time", "target_timezone"],
            },
        ),
    ]


async def handle_tool_call(
    name: str,
    arguments: dict[str, str],
    time_server: TimeServer,
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for time queries."""

    def raise_error(error_msg: str) -> None:
        raise ValueError(error_msg)

    def raise_missing_arg(arg_name: str) -> None:
        raise_error(f"Missing required argument: {arg_name}")

    def raise_unknown_tool(tool_name: str) -> None:
        raise_error(f"Unknown tool: {tool_name}")

    try:
        match name:
            case TimeTools.GET_CURRENT_TIME.value:
                timezone = arguments.get("timezone")
                if not timezone:
                    raise_missing_arg("timezone")

                assert isinstance(timezone, str)  # Type narrowing for mypy
                result = time_server.get_current_time(timezone)

            case TimeTools.CONVERT_TIME.value:
                required_args = ["source_timezone", "time", "target_timezone"]
                if not all(k in arguments for k in required_args):
                    raise_missing_arg(", ".join(required_args))

                result = time_server.convert_time(
                    arguments["source_timezone"],
                    arguments["time"],
                    arguments["target_timezone"],
                )
            case _:
                raise_unknown_tool(name)

        return [
            TextContent(
                type="text",
                text=json.dumps(result.model_dump(), indent=2),
            ),
        ]

    except Exception as e:
        error_msg = f"Error processing mcp-server-time query: {e!s}"
        raise ValueError(error_msg) from e


async def run_server(server: Server) -> None:
    """Run the MCP server with stdio transport."""
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Starting MCP Time Server")
        await server.run(read_stream, write_stream, options)
        logger.info("MCP Time Server running")


async def serve(local_timezone: str | None = None) -> None:
    try:
        server = Server("mcp-time")
        time_server = TimeServer()
        local_tz = str(get_local_tz(local_timezone))

        @server.list_tools()
        async def list_tools() -> list[Tool]:
            await asyncio.sleep(0)
            return create_tools(local_tz)

        @server.call_tool()
        async def call_tool(
            name: str,
            arguments: dict[str, str],
        ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
            await asyncio.sleep(0)
            return await handle_tool_call(name, arguments, time_server)

        await run_server(server)
    except Exception:
        logger.exception("Error in MCP Time Server")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Shutting down MCP Time Server")
