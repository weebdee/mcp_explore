import os
from openai import AsyncOpenAI

class DeepSeek:
    def __init__(self, model: str):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def add_user_message(self, messages: list, content: str):
        messages.append({
            "role": "user",
            "content": content
        })

    def add_assistant_message(self, messages: list, content: str):
        messages.append({
            "role": "assistant",
            "content": content
        })

    def text_from_message(self, message):
        try:
            return message.choices[0].message.content
        except (AttributeError, IndexError):
            return "Error parsing response."

    async def chat(
        self,
        messages: list,
        system: str = None,
        temperature: float = 1.0,
        tools: list = None,
    ):
        # DeepSeek (and OpenAI) expects the system prompt to be the first message
        formatted_messages = []
        if system:
            formatted_messages.append({"role": "system", "content": system})
        
        formatted_messages.extend(messages)

        params = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
        }

        # If we have MCP tools, we pass them here
        if tools:
            params["tools"] = tools

        try:
            response = await self.client.chat.completions.create(**params)
            return response
        except Exception as e:
            print(f"\n[Error communicating with DeepSeek API]: {e}")
            return None