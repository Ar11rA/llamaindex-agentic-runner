"""
Custom LLM implementations for providers not natively supported by LlamaIndex.

Provides wrappers for:
- GeminiVertexLLM: Google Gemini via Vertex AI with OAuth credentials and custom base URL
- BedrockGatewayLLM: AWS Bedrock via AI Gateway with bearer token authentication
"""

import json
import os
from typing import Optional, Any, Sequence

from llama_index.core.llms import (
    CustomLLM,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
    ChatMessage,
    ChatResponse,
)
from llama_index.core.llms.callbacks import llm_completion_callback
from pydantic import PrivateAttr


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI VERTEX AI LLM
# ─────────────────────────────────────────────────────────────────────────────


class GeminiVertexLLM(CustomLLM):
    """
    Custom LLM wrapper for Google Gemini via Vertex AI with custom credentials.

    Supports custom base URLs (e.g., AI Gateway proxies) and OAuth tokens.
    Uses the google.genai client library.
    """

    model: str = "gemini-2.0-flash-lite-001"
    temperature: float = 0.0
    max_tokens: int = 4096
    base_url: Optional[str] = None
    access_token: Optional[str] = None
    project: str = "aigateway"
    location: str = "global"
    api_version: str = "v1"

    _client: Any = PrivateAttr(default=None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client = self._create_client()

    def _create_client(self) -> Any:
        """Create the google.genai client with custom credentials."""
        from google import genai
        from google.genai.types import HttpOptions
        from google.oauth2.credentials import Credentials

        client_kwargs: dict[str, Any] = {
            "vertexai": True,
            "project": self.project,
            "location": self.location,
        }

        # Add custom HTTP options if base_url specified
        if self.base_url:
            client_kwargs["http_options"] = HttpOptions(
                api_version=self.api_version,
                base_url=self.base_url,
            )

        # Add credentials if access token provided
        if self.access_token:
            client_kwargs["credentials"] = Credentials(self.access_token)

        return genai.Client(**client_kwargs)

    @property
    def metadata(self) -> LLMMetadata:
        """Return LLM metadata."""
        return LLMMetadata(
            model_name=self.model,
            is_chat_model=True,
            context_window=1000000,  # Gemini 1.5/2.0 context
            num_output=self.max_tokens,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Synchronous completion."""
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                **kwargs,
            },
        )
        return CompletionResponse(text=response.text)

    @llm_completion_callback()
    async def acomplete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Async completion."""
        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                **kwargs,
            },
        )
        return CompletionResponse(text=response.text)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        """Streaming completion."""
        full_text = ""
        for chunk in self._client.models.generate_content_stream(
            model=self.model,
            contents=prompt,
            config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                **kwargs,
            },
        ):
            if hasattr(chunk, "text") and chunk.text:
                full_text += chunk.text
                yield CompletionResponse(text=full_text, delta=chunk.text)

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Chat completion."""
        # Convert messages to content format
        contents = self._messages_to_contents(messages)
        response = self._client.models.generate_content(
            model=self.model,
            contents=contents,
            config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                **kwargs,
            },
        )
        return ChatResponse(
            message=ChatMessage(role="assistant", content=response.text)
        )

    async def achat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponse:
        """Async chat completion."""
        contents = self._messages_to_contents(messages)
        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                **kwargs,
            },
        )
        return ChatResponse(
            message=ChatMessage(role="assistant", content=response.text)
        )

    def _messages_to_contents(self, messages: Sequence[ChatMessage]) -> list[dict]:
        """Convert ChatMessages to Gemini content format."""
        contents = []
        for msg in messages:
            role = "user" if msg.role.value in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})
        return contents


# ─────────────────────────────────────────────────────────────────────────────
# BEDROCK GATEWAY LLM
# ─────────────────────────────────────────────────────────────────────────────


class BedrockGatewayLLM(CustomLLM):
    """
    Custom LLM for AWS Bedrock via AI Gateway with bearer token authentication.

    Supports custom endpoint URLs and bearer token auth instead of AWS credentials.
    Uses boto3 with custom authorization header injection.
    """

    model: str = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    temperature: float = 0.5
    max_tokens: int = 4096
    endpoint_url: Optional[str] = None
    region_name: str = "us-east-1"
    bearer_token: Optional[str] = None
    anthropic_version: str = "bedrock-2023-05-31"

    _client: Any = PrivateAttr(default=None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client = self._create_client()

    def _create_client(self) -> Any:
        """Create boto3 bedrock-runtime client with bearer token auth."""
        import boto3
        from botocore.config import Config

        # Get bearer token from param or env
        token = self.bearer_token or os.environ.get("AWS_BEARER_TOKEN_BEDROCK")

        client_kwargs: dict[str, Any] = {
            "service_name": "bedrock-runtime",
            "region_name": self.region_name,
            "config": Config(
                retries={"max_attempts": 3},
            ),
        }

        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        client = boto3.client(**client_kwargs)

        # Override authorization by adding bearer token to requests
        if token:

            def add_bearer_token(request, **kwargs):
                request.headers["Authorization"] = f"Bearer {token}"

            client.meta.events.register(
                "before-send.bedrock-runtime.*", add_bearer_token
            )

        return client

    @property
    def metadata(self) -> LLMMetadata:
        """Return LLM metadata."""
        return LLMMetadata(
            model_name=self.model,
            is_chat_model=True,
            context_window=200000,  # Claude 3.5
            num_output=self.max_tokens,
        )

    def _build_request_body(self, prompt: str) -> dict:
        """Build the native Bedrock request payload for Anthropic models."""
        return {
            "anthropic_version": self.anthropic_version,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }

    def _build_chat_request_body(self, messages: Sequence[ChatMessage]) -> dict:
        """Build request payload from chat messages."""
        formatted_messages = []
        system_prompt = None

        for msg in messages:
            if msg.role.value == "system":
                system_prompt = msg.content
            else:
                formatted_messages.append(
                    {
                        "role": msg.role.value,
                        "content": [{"type": "text", "text": msg.content}],
                    }
                )

        body: dict[str, Any] = {
            "anthropic_version": self.anthropic_version,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": formatted_messages,
        }

        if system_prompt:
            body["system"] = system_prompt

        return body

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Synchronous completion."""
        request_body = self._build_request_body(prompt)

        response = self._client.invoke_model(
            modelId=self.model,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        text = response_body.get("content", [{}])[0].get("text", "")

        return CompletionResponse(text=text)

    @llm_completion_callback()
    async def acomplete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Async completion - wraps sync for now (boto3 is sync)."""
        return self.complete(prompt, **kwargs)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        """Streaming completion."""
        request_body = self._build_request_body(prompt)

        response = self._client.invoke_model_with_response_stream(
            modelId=self.model,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )

        full_text = ""
        for event in response.get("body", []):
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk.get("type") == "content_block_delta":
                delta_text = chunk.get("delta", {}).get("text", "")
                full_text += delta_text
                yield CompletionResponse(text=full_text, delta=delta_text)

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Chat completion."""
        request_body = self._build_chat_request_body(messages)

        response = self._client.invoke_model(
            modelId=self.model,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        text = response_body.get("content", [{}])[0].get("text", "")

        return ChatResponse(message=ChatMessage(role="assistant", content=text))

    async def achat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponse:
        """Async chat completion - wraps sync for now."""
        return self.chat(messages, **kwargs)
