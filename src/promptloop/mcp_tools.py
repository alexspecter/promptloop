"""
MCP Tools Integration for PromptLoop.

Provides utilities to bridge FastMCP servers with the PromptLoop engine,
making it simple to give local LLMs access to external tools.

Usage:
    from mcp import FastMCP
    from promptloop.mcp_tools import mcp_to_promptloop

    mcp = FastMCP("MyTools")

    @mcp.tool()
    def get_weather(city: str) -> str:
        return f"The weather in {city} is sunny."

    tools, handler = mcp_to_promptloop(mcp)

    run_chat(
        ...,
        tools=tools,
        tool_handler=handler,
    )
"""

from typing import Any, Dict, List, Tuple, Callable


def mcp_to_promptloop(
    mcp_server: Any,
) -> Tuple[List[Dict[str, Any]], Callable[[str, dict], str]]:
    """
    Converts a FastMCP server instance into PromptLoop-compatible
    tools list and tool_handler callable.

    Args:
        mcp_server: A FastMCP server instance with registered tools.

    Returns:
        A tuple of (tools, tool_handler):
        - tools: A list of tool schema dicts for the LLM.
        - tool_handler: A callable that dispatches tool calls by name.
    """
    # Extract tool schemas from the FastMCP server
    raw_tools = mcp_server.list_tools()
    tools = []
    tool_map: Dict[str, Callable] = {}

    for tool in raw_tools:
        # Build a simplified schema for the LLM
        schema = {
            "name": tool.name,
            "description": tool.description or "",
        }

        # Include parameter schema if available
        if hasattr(tool, "inputSchema") and tool.inputSchema:
            schema["parameters"] = tool.inputSchema
        elif hasattr(tool, "input_schema") and tool.input_schema:
            schema["parameters"] = tool.input_schema

        tools.append(schema)

        # Map tool name to callable
        tool_map[tool.name] = tool

    def tool_handler(name: str, arguments: dict) -> str:
        """Dispatches a tool call to the correct FastMCP tool."""
        if name not in tool_map:
            raise ValueError(
                f"Unknown tool: '{name}'. Available: {list(tool_map.keys())}"
            )

        # FastMCP tools can be called via the server's call_tool method
        try:
            result = mcp_server.call_tool(name, arguments)
            # MCP returns a list of content blocks; extract text
            if isinstance(result, list):
                return "\n".join(
                    block.text if hasattr(block, "text") else str(block)
                    for block in result
                )
            return str(result)
        except Exception as e:
            return f"Tool execution error: {e}"

    return tools, tool_handler
