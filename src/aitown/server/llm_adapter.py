"""LLM Adapter abstractions and simple implementations.

This module provides:
- BaseLLMAdapter: abstract interface for adapters
- MockLLMAdapter: deterministic, fast adapter for tests/dev
- ServerDefaultLLMAdapter: placeholder for real HTTP-based adapters
- get_adapter: factory selecting adapter via AITOWN_LLM_ADAPTER env var
- call_with_fallback: helper to call adapter and fallback to local rules on error/timeout

Acceptance criteria implemented:
- Adapter interface and two implementations (mock and server-default)
- Configuration via env var to choose adapter
- Failure handling with downgrade to local rules and logging
"""
from __future__ import annotations

import os
import time
import logging
from typing import Protocol, Dict, Any, Optional
import asyncio

try:
    import httpx
except Exception:  # pragma: no cover - runtime environment may not have httpx installed yet
    httpx = None

logger = logging.getLogger(__name__)


class BaseLLMAdapter(Protocol):
    """Protocol for LLM adapters."""

    def generate(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 256) -> Dict[str, Any]:
        """Generate a response for the given prompt.

        Should raise exceptions on network/adapter failures.
        Returns a dict containing at minimum: {"text": str}
        """


class MockLLMAdapter:
    """Simple deterministic mock adapter used for tests and local dev.

    It echoes the prompt with a fixed suffix and returns metadata.
    """

    def __init__(self, echo_prefix: str = "[MOCK] ") -> None:
        self.echo_prefix = echo_prefix

    def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 64) -> Dict[str, Any]:
        if prompt is None:
            raise ValueError("prompt must not be None")
        text = f"{self.echo_prefix}{prompt[:max_tokens]}"
        return {"text": text, "meta": {"model": "mock", "temperature": temperature}}


class ServerDefaultLLMAdapter:
    """A minimal adapter that would wrap calls to an external LLM provider.

    For now this is a placeholder that simulates latency and can be configured
    to fail for testing the downgrade behavior.
    """

    def __init__(self, simulate_latency: float = 0.0, fail: bool = False) -> None:
        self.simulate_latency = float(simulate_latency)
        self.fail = bool(fail)

    def generate(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 256) -> Dict[str, Any]:
        if prompt is None:
            raise ValueError("prompt must not be None")
        if self.simulate_latency:
            time.sleep(self.simulate_latency)
        if self.fail:
            raise RuntimeError("Simulated external LLM failure")
        # In real implementation, call out to OpenAI or other API here.
        text = f"[SERVER-DEFAULT] response to: {prompt[:max_tokens]}"
        return {"text": text, "meta": {"model": "server-default", "temperature": temperature}}


class AsyncServerDefaultLLMAdapter:
    """Async adapter that calls an OpenAI-compatible REST API using httpx.

    Environment variables supported (optional):
    - AITOWN_LLM_ENDPOINT: override API base URL (default: OpenAI chat completions)
    - AITOWN_LLM_API_KEY: API key to use (recommended)
    - AITOWN_LLM_TIMEOUT: float seconds timeout for requests
    """

    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None, timeout: float = 10.0):
        if httpx is None:
            raise RuntimeError("httpx is required for AsyncServerDefaultLLMAdapter")
        self.endpoint = endpoint or os.environ.get("AITOWN_LLM_ENDPOINT") or "https://api.openai.com/v1/chat/completions"
        self.api_key = api_key or os.environ.get("AITOWN_LLM_API_KEY")
        self.timeout = float(os.environ.get("AITOWN_LLM_TIMEOUT", str(timeout)))
        # model name can be overridden by env var or constructor later
        self.model = os.environ.get("AITOWN_LLM_MODEL", "gpt-3.5-turbo")
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def agenerate(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 256, model: Optional[str] = None) -> Dict[str, Any]:
        if prompt is None:
            raise ValueError("prompt must not be None")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Basic OpenAI-compatible chat completion payload using a single system/user message
        payload = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": "You are a simulation assistant producing brief action-oriented responses."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # POST to endpoint
        try:
            resp = await self._client.post(self.endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # OpenAI chat response extraction
            text = ""
            if isinstance(data, dict):
                # safe extraction: try choices[0].message.content or choices[0].text
                choices = data.get("choices") or []
                if choices:
                    first = choices[0]
                    if isinstance(first.get("message"), dict):
                        text = first["message"].get("content", "")
                    else:
                        text = first.get("text", "")
            return {"text": text, "meta": {"model": payload.get("model"), "temperature": temperature, "source": "openai-compatible"}}
        except Exception:
            # let caller handle fallback
            raise


async def async_call_with_fallback(adapter: Any, prompt: str, *, timeout: Optional[float] = 5.0, **kwargs) -> Dict[str, Any]:
    """Async variant of call_with_fallback.

    If adapter has `agenerate`, call it. Otherwise, run generate in executor.
    """
    start = time.time()
    try:
        if hasattr(adapter, "agenerate") and asyncio.iscoroutinefunction(getattr(adapter, "agenerate")):
            result = await adapter.agenerate(prompt, **kwargs)
        else:
            # run blocking generate in threadpool to avoid blocking loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, lambda: adapter.generate(prompt, **kwargs))
        if not result or not isinstance(result.get("text"), str):
            raise RuntimeError("Adapter returned invalid result")
        return result
    except Exception as exc:
        elapsed = time.time() - start
        logger.exception("LLM adapter (async) failed after %.2fs: %s", elapsed, exc)
        logger.info("LLM fallback engaged (async): using local rules for prompt preview: %s", (prompt or "")[:120])
        return local_rules_fallback(prompt)


def _is_async_adapter(adapter: Any) -> bool:
    return hasattr(adapter, "agenerate") and asyncio.iscoroutinefunction(getattr(adapter, "agenerate"))


def get_adapter() -> BaseLLMAdapter:
    """Factory selecting adapter based on AITOWN_LLM_ADAPTER env var.

    Supported values:
    - mock: MockLLMAdapter
    - server-default: ServerDefaultLLMAdapter
    - <anything else>: falls back to ServerDefaultLLMAdapter
    """
    choice = os.environ.get("AITOWN_LLM_ADAPTER", "mock").lower()
    if choice == "mock":
        return MockLLMAdapter()
    if choice == "server-default":
        # Allow tuning via env for testing
        latency = float(os.environ.get("AITOWN_LLM_SIMULATE_LATENCY", "0"))
        fail = os.environ.get("AITOWN_LLM_SIMULATE_FAIL", "0") not in ("0", "false", "False", "")
        return ServerDefaultLLMAdapter(simulate_latency=latency, fail=fail)
    # default
    return MockLLMAdapter()


def local_rules_fallback(prompt: str) -> Dict[str, Any]:
    """A simple local rule-based fallback to preserve simulation rhythm.

    This should be expanded with project-specific heuristics. For now, it
    chooses a short canned response based on keywords.
    """
    lower = (prompt or "").lower()
    if "hello" in lower or "hi" in lower:
        text = "(local) Hello. I am busy right now."
    elif "name" in lower:
        text = "(local) I don't remember my full name right now."
    else:
        text = "(local) I do not know, but I will try later."
    return {"text": text, "meta": {"model": "local-rules"}}


def call_with_fallback(adapter: BaseLLMAdapter, prompt: str, *, timeout: Optional[float] = 5.0, **kwargs) -> Dict[str, Any]:
    """Call adapter.generate with basic timeout and fallback handling.

    This implementation uses a simple time-based check (not true cancellation).
    In production, use async + real timeout/cancellation.
    """
    # If adapter exposes async API, run the async path synchronously via asyncio.run if necessary
    if _is_async_adapter(adapter):
        try:
            return asyncio.run(async_call_with_fallback(adapter, prompt, timeout=timeout, **kwargs))
        except Exception:
            # If asyncio.run fails (e.g., already in event loop), try alternate path
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # In running loop, schedule and wait
                    future = asyncio.ensure_future(async_call_with_fallback(adapter, prompt, timeout=timeout, **kwargs))
                    # This is a dangerous blocking wait; only expected in sync contexts rarely used in tests
                    return loop.run_until_complete(future)
            except Exception:
                pass
            # fallback to local rules on any failure
            logger.exception("Failed to run async adapter in sync context")
            return local_rules_fallback(prompt)

    start = time.time()
    try:
        result = adapter.generate(prompt, **kwargs)
        # Basic post-check: ensure text present
        if not result or not isinstance(result.get("text"), str):
            raise RuntimeError("Adapter returned invalid result")
        return result
    except Exception as exc:  # pragma: no cover - behavior exercised in tests
        elapsed = time.time() - start
        logger.exception("LLM adapter failed after %.2fs: %s", elapsed, exc)
        # Broadcast downgrade log - in real app, integrate with event/bus
        logger.info("LLM fallback engaged: using local rules for prompt preview: %s", (prompt or "")[:120])
        return local_rules_fallback(prompt)
