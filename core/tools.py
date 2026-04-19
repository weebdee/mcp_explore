import json
from typing import Optional, List, Dict, Any
from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPClient

class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[Dict[str, Any]]:
        """Gets all tools from the provided clients and formats them for DeepSeek/OpenAI."""
        tools = []
        for client in clients.values():
            tool_models = await client.list_tools()
            tools += [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": t.inputSchema,
                    }
                }
                for t in tool_models
            ]
        return tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        """Finds the first client that has the specified tool."""
        for client in clients:
            tools = await client.list_tools()
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                return client
        return None

    @classmethod
    def _build_tool_result_part(
        cls,
        tool_call_id: str,
        text: str,
    ) -> Dict[str, Any]:
        """Builds a standard OpenAI/DeepSeek tool result message."""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": text,
        }

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], tool_calls: list
    ) -> List[Dict[str, Any]]:
        """Executes a list of tool requests against the provided clients."""
        tool_result_blocks: list[Dict[str, Any]] = []
        
        for tool_request in tool_calls:
            tool_call_id = tool_request.id
            tool_name = tool_request.function.name
            
            # DeepSeek passes arguments as a JSON string, so we must parse it
            try:
                tool_input = json.loads(tool_request.function.arguments)
            except json.JSONDecodeError:
                tool_input = {}

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            if not client:
                tool_result_part = cls._build_tool_result_part(
                    tool_call_id, json.dumps({"error": "Could not find that tool"})
                )
                tool_result_blocks.append(tool_result_part)
                continue

            tool_output: CallToolResult | None = None
            try:
                tool_output = await client.call_tool(
                    tool_name, tool_input
                )
                items = []
                if tool_output:
                    items = tool_output.content
                content_list = [
                    item.text for item in items if isinstance(item, TextContent)
                ]
                content_json = json.dumps(content_list)
                tool_result_part = cls._build_tool_result_part(
                    tool_call_id,
                    content_json,
                )
            except Exception as e:
                error_message = f"Error executing tool '{tool_name}': {e}"
                print(error_message)
                tool_result_part = cls._build_tool_result_part(
                    tool_call_id,
                    json.dumps({"error": error_message}),
                )

            tool_result_blocks.append(tool_result_part)
            
        return tool_result_blocks