import httpx
import os
from dotenv import load_dotenv
load_dotenv()
import structlog

logger = structlog.get_logger()


class LLMClient:
    def __init__(self) -> None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Please set the OPENROUTER_API_KEY environment variable.")
        self.__headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.set_target_url()
        self.set_model()

    async def __aenter__(self):
        self.__client = httpx.AsyncClient(http2=True)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self.__client:
            await self.__client.aclose()
        if exc_type:
            print(traceback)
            logger.error(f"An error occurred: {exc_type.__name__}: {exc_value}")

    def set_target_url(self, target_url: str = None) -> None:
        """
        openrouterのapiのurlを指定することでどう言ったことを行うかを指定する。
        デフォルトはcompletionsで、
        """
        self.__target_url = target_url if target_url else "https://openrouter.ai/api/v1/chat/completions"

    def set_model(self, model_name: str = None) -> None:
        """
        モデルを指定する。デフォルトはgpt3.5turbo
        """
        self.__model = model_name if model_name else "openai/gpt-3.5-turbo"

    async def post_basic_message(
        self,
        messages: list[dict[str, str]],
        include_meta_data: bool = False
        ) -> str | dict:
        """
        
        """
        data = {"model": self.__model, "messages": messages}
        try:
            response = await self.__client.post(
                self.__target_url, headers=self.__headers, json=data
            )
            response.raise_for_status()
            response_data = response.json()
            if not include_meta_data:
                response_data = response_data["choices"][0]["message"]["content"]
            return response_data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise

async def main():
    async with LLMClient() as client:
        messages = [{"role": "user", "content": "こんにちは~"}]
        response = await client.post_basic_message(messages, include_meta_data=False)
        print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())