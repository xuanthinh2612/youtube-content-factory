from openai import AsyncOpenAI

from service.settings import app_settings
from service.models import ProjectJob


class OpenAIResponsesClient:
    def __init__(self):
        self.client: AsyncOpenAI | None = None

    def _get_openai_client(self) -> AsyncOpenAI:
        if self.client is None:
            if not app_settings.openai_api_key:
                raise RuntimeError("Set OPENAI_API_KEY to generate content")
            self.client = AsyncOpenAI(api_key=app_settings.openai_api_key)
        return self.client

    async def create_response(self, response_parameters):
        return await self._get_openai_client().responses.create(**response_parameters)

    async def close(self):
        if self.client is not None:
            await self.client.close()
            self.client = None


openai_client = OpenAIResponsesClient()


async def send_openai_response(
    job: ProjectJob,
    agent_instructions: str,
    agent_input_text: str,
    output_format=None,
):
    response_parameters = {
        "model": "gpt-6-luna",
        "reasoning": {"effort": "high"},
        "instructions": agent_instructions,
        "input": agent_input_text,
    }
    if output_format is not None:
        response_parameters["text"] = output_format
    if job.provider != "openai":
        raise ValueError(f"Unsupported LLM provider for job {job.id}: {job.provider}")
    return await openai_client.create_response(response_parameters)
