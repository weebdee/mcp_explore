from core.deepseek import DeepSeek
from mcp_client import MCPClient
from core.tools import ToolManager
from typing import Dict, Any, List

class Chat:
    def __init__(self, llm_service: DeepSeek, clients: dict[str, MCPClient]):
        self.llm_service: DeepSeek = llm_service
        self.clients: dict[str, MCPClient] = clients
        # Use standard Python dictionaries instead of Anthropic's MessageParam
        self.messages: List[Dict[str, Any]] = []

    async def _process_query(self, query: str):
        # Allow passing if it's already handled by cli_chat
        pass 
        # Note: cli_chat.py overrides this to add context, so we don't append blindly here.

    async def run(
        self,
        query: str,
    ) -> str:
        final_text_response = ""

        # cli_chat overrides _process_query to inject the document context properly
        await self._process_query(query)

        while True:
            # 1. We must AWAIT the chat call because we made DeepSeek async
            response = await self.llm_service.chat(
                messages=self.messages,
                tools=await ToolManager.get_all_tools(self.clients),
            )

            if not response or not response.choices:
                return "Error: No response from the model or API failed."

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            # 2. Reconstruct the assistant's message exactly as DeepSeek expects it
            assistant_msg = {"role": "assistant", "content": message.content or ""}
            
            # If there are tool calls, we MUST append them to the assistant's message history
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in message.tool_calls
                ]
            
            self.messages.append(assistant_msg)

            # 3. Check for DeepSeek's specific finish reason for tools
            if finish_reason == "tool_calls" and message.tool_calls:
                if message.content:
                    print(message.content) # Print any thinking text before the tool call
                
                # 4. Pass ONLY the tool calls to the ToolManager
                tool_result_messages = await ToolManager.execute_tool_requests(
                    self.clients, message.tool_calls
                )

                # 5. Extend history with the formatted tool results
                self.messages.extend(tool_result_messages)
            else:
                # Loop ends here if no tools are called
                final_text_response = message.content or ""
                break

        return final_text_response