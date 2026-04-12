"""LLM 추상화 레이어.

Protocol 기반으로 공급자를 교체할 수 있도록 설계.
현재 지원: anthropic, openai
config.py의 LLM_PROVIDER 환경변수로 선택.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from app.core.config import settings


class LLMClient(Protocol):
    """LLM 공급자 추상 인터페이스."""

    async def stream_completion(
        self, system: str, user: str
    ) -> AsyncIterator[str]:
        """system/user 프롬프트를 받아 토큰 단위로 스트리밍한다."""
        ...


# ─────────────────────────────────────────────
# Anthropic 구현체
# ─────────────────────────────────────────────


class AnthropicClient:
    def __init__(self) -> None:
        import anthropic  # optional dependency

        self._client = anthropic.AsyncAnthropic(api_key=settings.LLM_API_KEY)
        self._model = settings.LLM_MODEL or "claude-haiku-4-5-20251001"

    async def stream_completion(self, system: str, user: str) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            async for text in stream.text_stream:
                yield text


# ─────────────────────────────────────────────
# OpenAI 구현체
# ─────────────────────────────────────────────


class OpenAIClient:
    def __init__(self) -> None:
        from openai import AsyncOpenAI  # optional dependency

        self._client = AsyncOpenAI(api_key=settings.LLM_API_KEY)
        self._model = settings.LLM_MODEL or "gpt-4o-mini"

    async def stream_completion(self, system: str, user: str) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


# ─────────────────────────────────────────────
# 팩토리 함수
# ─────────────────────────────────────────────


def get_llm_client() -> LLMClient:
    """설정된 LLM_PROVIDER에 따라 적절한 클라이언트를 반환한다."""
    provider = settings.LLM_PROVIDER.lower()
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "openai":
        return OpenAIClient()
    raise ValueError(
        f"지원하지 않는 LLM_PROVIDER: '{provider}'. "
        "anthropic 또는 openai 중 하나를 설정하세요."
    )
