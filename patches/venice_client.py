import os
import re
from typing import List

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion

from letta.llm_api.openai_client import OpenAIClient
from letta.schemas.embedding_config import EmbeddingConfig
from letta.schemas.llm_config import LLMConfig
from letta.schemas.message import Message as PydanticMessage
from letta.schemas.openai.chat_completion_response import ChatCompletionResponse
from letta.settings import model_settings


class VeniceClient(OpenAIClient):
    def _prepare_client_kwargs(self, llm_config: LLMConfig) -> dict:
        api_key, _, _ = self.get_byok_overrides(llm_config)
        if not api_key:
            api_key = model_settings.venice_api_key or os.environ.get("VENICE_API_KEY")

        base_url = llm_config.model_endpoint or model_settings.venice_base_url
        return {"api_key": api_key or "DUMMY_API_KEY", "base_url": base_url}

    def _prepare_client_kwargs_embedding(self, embedding_config: EmbeddingConfig) -> dict:
        api_key = model_settings.venice_api_key or os.environ.get("VENICE_API_KEY") or "DUMMY_API_KEY"
        base_url = embedding_config.embedding_endpoint or model_settings.venice_base_url
        return {"api_key": api_key, "base_url": base_url}

    async def _prepare_client_kwargs_async(self, llm_config: LLMConfig) -> dict:
        api_key, _, _ = await self.get_byok_overrides_async(llm_config)
        if not api_key:
            api_key = model_settings.venice_api_key or os.environ.get("VENICE_API_KEY")

        base_url = llm_config.model_endpoint or model_settings.venice_base_url
        return {"api_key": api_key or "DUMMY_API_KEY", "base_url": base_url}

    def _filter_none_values(self, data: dict) -> dict:
        """Remove None values from request data as Venice API rejects them."""
        return {k: v for k, v in data.items() if v is not None}

    def request(self, request_data: dict, llm_config: LLMConfig) -> dict:
        """Override to filter None values before sending to Venice API."""
        filtered_data = self._filter_none_values(request_data)
        kwargs = self._prepare_client_kwargs(llm_config)
        client = OpenAI(**kwargs)
        if "input" in filtered_data and "messages" not in filtered_data:
            resp = client.responses.create(**filtered_data)
            return resp.model_dump()
        else:
            response: ChatCompletion = client.chat.completions.create(**filtered_data)
            return response.model_dump()

    async def request_async(self, request_data: dict, llm_config: LLMConfig) -> dict:
        """Override to filter None values before sending to Venice API."""
        filtered_data = self._filter_none_values(request_data)
        kwargs = await self._prepare_client_kwargs_async(llm_config)
        client = AsyncOpenAI(**kwargs)
        if "input" in filtered_data and "messages" not in filtered_data:
            resp = await client.responses.create(**filtered_data)
            return resp.model_dump()
        else:
            response: ChatCompletion = await client.chat.completions.create(**filtered_data)
            return response.model_dump()

    async def convert_response_to_chat_completion(
        self,
        response_data: dict,
        input_messages: List[PydanticMessage],
        llm_config: LLMConfig,
    ) -> ChatCompletionResponse:
        """
        Override to extract <think> tags from Venice model responses.
        Venice models output reasoning in <think></think> tags inline in the content.
        """
        # First, get the standard OpenAI response
        response = await super().convert_response_to_chat_completion(response_data, input_messages, llm_config)

        # Extract <think> tags from the content if present
        if response.choices and response.choices[0].message.content:
            content = response.choices[0].message.content
            
            # Pattern to match <think>...</think> tags (including multiline)
            think_pattern = r'<think>(.*?)</think>'
            matches = re.findall(think_pattern, content, re.DOTALL)
            
            if matches:
                # Extract reasoning content
                reasoning_text = '\n'.join(match.strip() for match in matches)
                
                # Remove <think> tags from the main content
                cleaned_content = re.sub(think_pattern, '', content, flags=re.DOTALL).strip()
                
                # Update the response with extracted reasoning
                response.choices[0].message.reasoning_content = reasoning_text
                response.choices[0].message.content = cleaned_content if cleaned_content else None

        return response
