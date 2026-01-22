from typing import Any, Literal

from pydantic import Field

from letta.constants import DEFAULT_EMBEDDING_CHUNK_SIZE, MIN_CONTEXT_WINDOW
from letta.errors import ErrorCode, LLMAuthenticationError, LLMError
from letta.llm_api.venice import venice_get_model_list_async
from letta.log import get_logger
from letta.schemas.embedding_config import EmbeddingConfig
from letta.schemas.enums import ProviderCategory, ProviderType
from letta.schemas.llm_config import LLMConfig
from letta.schemas.providers.base import Provider

logger = get_logger(__name__)

DEFAULT_EMBEDDING_BATCH_SIZE = 1024
DEFAULT_VENICE_BASE_URL = "https://api.venice.ai/api/v1"
SUPPORTED_LLM_TYPES = {"text", "chat", "language"}


class VeniceProvider(Provider):
    provider_type: Literal[ProviderType.venice] = Field(ProviderType.venice, description="The type of the provider.")
    provider_category: ProviderCategory = Field(ProviderCategory.base, description="The category of the provider (base or byok)")
    api_key: str | None = Field(None, description="API key for the Venice API.", deprecated=True)
    base_url: str = Field(DEFAULT_VENICE_BASE_URL, description="Base URL for the Venice API.")

    async def check_api_key(self):
        api_key = await self.api_key_enc.get_plaintext_async() if self.api_key_enc else None
        if not api_key:
            raise ValueError("No API key provided")

        try:
            await venice_get_model_list_async(self.base_url, api_key=api_key)
        except Exception as e:
            message = f"Failed to authenticate with Venice: {e}"
            if isinstance(e, LLMError):
                raise
            raise LLMAuthenticationError(message=message, code=ErrorCode.UNAUTHENTICATED)

    async def _get_models_async(self) -> list[dict]:
        api_key = await self.api_key_enc.get_plaintext_async() if self.api_key_enc else None
        response = await venice_get_model_list_async(self.base_url, api_key=api_key)
        data = response.get("data", response)
        if not isinstance(data, list):
            logger.warning("Unexpected Venice models payload: %s", type(data).__name__)
            return []
        return data

    async def list_llm_models_async(self) -> list[LLMConfig]:
        data = await self._get_models_async()
        configs: list[LLMConfig] = []
        for model in data:
            if not isinstance(model, dict):
                continue
            model_name = model.get("id")
            if not model_name:
                continue
            model_type = model.get("type")
            if model_type and model_type not in SUPPORTED_LLM_TYPES:
                continue
            context_window = self._extract_context_window(model)
            if context_window <= 0:
                context_window = MIN_CONTEXT_WINDOW

            configs.append(
                LLMConfig(
                    model=model_name,
                    model_endpoint_type="venice",
                    model_endpoint=self.base_url,
                    context_window=context_window,
                    handle=self.get_handle(model_name),
                    max_tokens=self.get_default_max_output_tokens(model_name),
                    provider_name=self.name,
                    provider_category=self.provider_category,
                )
            )
        return configs

    async def list_embedding_models_async(self) -> list[EmbeddingConfig]:
        data = await self._get_models_async()
        configs: list[EmbeddingConfig] = []
        for model in data:
            if not isinstance(model, dict):
                continue
            if model.get("type") != "embedding":
                continue
            model_name = model.get("id")
            if not model_name:
                continue
            embedding_dim = self._extract_embedding_dim(model)
            configs.append(
                EmbeddingConfig(
                    embedding_model=model_name,
                    embedding_endpoint_type="venice",
                    embedding_endpoint=self.base_url,
                    embedding_dim=embedding_dim,
                    embedding_chunk_size=DEFAULT_EMBEDDING_CHUNK_SIZE,
                    handle=self.get_handle(model_name, is_embedding=True),
                    batch_size=DEFAULT_EMBEDDING_BATCH_SIZE,
                )
            )
        return configs

    def _extract_context_window(self, model: dict[str, Any]) -> int:
        model_spec = model.get("model_spec") or {}
        raw_value = (
            model_spec.get("availableContextTokens")
            or model_spec.get("context_length")
            or model.get("context_length")
        )
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return 0

    def _extract_embedding_dim(self, model: dict[str, Any]) -> int:
        model_spec = model.get("model_spec") or {}
        raw_value = (
            model_spec.get("embeddingDimension")
            or model_spec.get("embedding_dim")
            or model_spec.get("embedding_dimension")
        )
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return 1536
