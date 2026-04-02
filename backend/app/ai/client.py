import os

from openai import OpenAI

MODEL = "openai/gpt-oss-120b"


def get_ai_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
