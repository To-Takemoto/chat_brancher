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
        self.set_target_url("https://openrouter.ai/api/v1/chat/completions")
        self.set_model("openai/gpt-3.5-turbo")

    async def __aenter__(self):
        self.__client = httpx.AsyncClient(http2=True)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self.__client:
            await self.__client.aclose()
        if exc_type:
            print(traceback)
            logger.error(f"An error occurred: {exc_type.__name__}: {exc_value}")

    def set_target_url(self, target_url: str) -> None:
        """
        openrouterのapiのurlを指定することでどう言ったことを行うかを指定する。
        デフォルトはcompletionsで、
        """
        self.__target_url = target_url

    def set_model(self, model_name: str) -> None:
        """
        モデルを指定する。デフォルトはgpt3.5turbo
        """
        def validate_model(model_name: str):
            model_list = [item["id"] for item in self._fetch_llm_models()["data"]]
            if model_name in model_list:
                return True
            else:
                logger.error("provided model not found in openrouter...")
                raise TypeError
        if validate_model(model_name):
            self.__model = model_name

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
    
    @staticmethod
    def _fetch_llm_models() -> dict:
        """
        ハードコーディングされたAPIからモデル情報を取得する関数

        Returns:
            dict: レスポンスデータを辞書形式で返す
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    "https://openrouter.ai/api/v1/models",
                    params={"supported_parameters": "temperature,top_p,tools"},
                    headers={"accept": "application/json"}
                    )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP error occurred: {response.status_code}", "details": response.text}
        except httpx.RequestError as e:
            logger.warn("error on fetch llm models...")

async def main():
    async with LLMClient() as client:
        messages = [{"role": "user", "content": "こんにちは~"}]
        response = await client.post_basic_message(messages, include_meta_data=False)
        print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())