import os
import time
import logging

import pytest

from aitown.server import llm_adapter


def test_mock_adapter_basic():
    adapter = llm_adapter.MockLLMAdapter()
    res = adapter.generate("hello world")
    assert "text" in res
    assert res["meta"]["model"] == "mock"


def test_server_default_success():
    adapter = llm_adapter.ServerDefaultLLMAdapter(simulate_latency=0.0, fail=False)
    res = adapter.generate("what is your name?")
    assert res["meta"]["model"] == "server-default"
    assert "response to" in res["text"]


def test_server_default_failure_triggers_fallback(caplog):
    caplog.set_level(logging.INFO)
    adapter = llm_adapter.ServerDefaultLLMAdapter(simulate_latency=0.0, fail=True)
    # call_with_fallback should catch the RuntimeError and return local rules
    res = llm_adapter.call_with_fallback(adapter, "hello there")
    assert res["meta"]["model"] == "local-rules"
    # ensure fallback log emitted
    found = any("LLM fallback engaged" in r.message for r in caplog.records)
    assert found


def test_get_adapter_env_switch(monkeypatch):
    monkeypatch.setenv("AITOWN_LLM_ADAPTER", "server-default")
    monkeypatch.setenv("AITOWN_LLM_SIMULATE_FAIL", "1")
    adapter = llm_adapter.get_adapter()
    assert isinstance(adapter, llm_adapter.ServerDefaultLLMAdapter)


@pytest.mark.asyncio
async def test_async_adapter_with_mocked_httpx(monkeypatch):
    # Skip if httpx not installed in runtime
    if getattr(llm_adapter, "httpx", None) is None:
        pytest.skip("httpx not installed")

    # create a mock response for OpenAI-compatible payload
    async def handler(request):
        return llm_adapter.httpx.Response(200, json={
            "choices": [{"message": {"content": "Hello from async adapter"}}]
        })

    transport = llm_adapter.httpx.MockTransport(handler)
    client = llm_adapter.httpx.AsyncClient(transport=transport)
    adapter = llm_adapter.AsyncServerDefaultLLMAdapter()
    # replace client's internal client with our mock client
    adapter._client = client

    res = await adapter.agenerate("say hello")
    assert "Hello from async adapter" in res["text"]
