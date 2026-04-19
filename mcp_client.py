import sys
import asyncio
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict] = None,
    ):
        self._command = command
        self._args = args
        self._env = env
        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        _stdio, _write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write)
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized or cache not populated. Call connect_to_server first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        response = await self.session().list_tools()
        return response.tools

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult | None:
        response = await self.session().call_tool(tool_name, tool_input)
        return response

    async def list_prompts(self) -> list[types.Prompt]:
        response = await self.session().list_prompts()
        return response.prompts

    async def get_prompt(self, prompt_name: str, args: dict[str, str]):
        response = await self.session().get_prompt(prompt_name, arguments=args)
        return response.messages

    async def read_resource(self, uri: str) -> Any:
        response = await self.session().read_resource(uri)
        if response.contents:
            content = response.contents[0]
            # FastMCP usually returns TextResourceContents
            if isinstance(content, types.TextResourceContents):
                text = content.text
                # A quick hack to ensure our UI gets a list when it asks for the document index
                if uri == "docs://documents":
                    return [doc_id.strip() for doc_id in text.split("\n") if doc_id.strip()]
                return text
            elif isinstance(content, types.BlobResourceContents):
                return content.blob
        return None

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# For testing
async def main():
    async with MCPClient(
        command="uv" if sys.platform != "win32" else "python",
        args=["run", "mcp_server.py"] if sys.platform != "win32" else ["mcp_server.py"],
    ) as _client:
        tools = await _client.list_tools()
        print(f"Connected successfully! Found tools: {[t.name for t in tools]}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())