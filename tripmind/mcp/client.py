"""TripMind Model Context Protocol (MCP) Client.

AGENTIC AI CONCEPT — Decoupled Tool Client:
1. In traditional architectures, an agent directly invokes Python methods.
2. With an MCP Client:
   - The agent treats tools as external services.
   - It discovers tools dynamically via `list_tools()`.
   - It executes tools via `call_tool(name, arguments)`.
   - Supports both In-Process direct session (for zero-latency local execution)
     and Stdio subprocess connection (for connecting to external MCP servers like Weather or Maps).
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from mcp.server.mcpserver import MCPServer
from tripmind.mcp.server import server as default_mcp_server


class TripMindMCPClient:
    """Client for discovering and executing tools over Model Context Protocol (MCP)."""

    def __init__(self, mcp_server: Optional[MCPServer] = None):
        self.server = mcp_server or default_mcp_server

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Queries the MCP server for all registered tools and their JSON schemas."""
        tools_list = await self.server.list_tools()
        result = []
        for t in tools_list:
            schema = getattr(t, "input_schema", getattr(t, "inputSchema", None))
            # If schema is a pydantic model or dict, normalize it
            if hasattr(schema, "model_dump"):
                schema = schema.model_dump()
            result.append({
                "name": t.name,
                "description": t.description,
                "inputSchema": schema,
                "input_schema": schema,
            })
        return result

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Invokes a tool on the MCP server and extracts the returned payload."""
        response = await self.server.call_tool(name, arguments)
        
        # Check for errors
        if response.is_error:
            error_msg = "\n".join([c.text for c in response.content if hasattr(c, "text")])
            raise RuntimeError(f"MCP Tool '{name}' failed: {error_msg}")

        # Extract text content
        output_parts = []
        for content_item in response.content:
            if hasattr(content_item, "text"):
                output_parts.append(content_item.text)
        
        raw_output = "\n".join(output_parts)
        
        # Attempt JSON decoding if the output is serialized JSON
        try:
            return json.loads(raw_output)
        except Exception:
            return raw_output

    def call_tool_sync(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Synchronous wrapper for invoking MCP tools in non-async execution threads."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                def _runner():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(self.call_tool(name, arguments))
                    finally:
                        new_loop.close()
                return pool.submit(_runner).result()
        else:
            return asyncio.run(self.call_tool(name, arguments))

    async def read_resource(self, uri: str) -> str:
        """Reads a context resource URI from the MCP server."""
        resource_data = await self.server.read_resource(uri)
        # In MCP 2.x, resource_data contains contents
        if hasattr(resource_data, "contents"):
            return "\n".join([c.content for c in resource_data.contents if hasattr(c, "content")])
        return str(resource_data)
