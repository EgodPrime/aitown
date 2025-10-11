import asyncio

import pytest

from aitown.helpers import llm_helper


class DummyResp:
    def __init__(self, content: str):
        self._content = content

    def __getitem__(self, item):
        # emulate dict-like access: choices -> list -> 0 -> message -> content
        if item == "choices":
            return [{"message": {"content": self._content}}]
        raise KeyError(item)


def test_generate_sync(monkeypatch):
    expected = "hello from llm"

    def fake_create(*args, **kwargs):
        return {"choices": [{"message": {"content": expected}}]}

    monkeypatch.setattr(llm_helper.client.chat.completions, "create", fake_create)

    out = llm_helper.generate("hi")
    assert out == expected


def test_generate_async(monkeypatch):
    expected = "async hello"
    async def fake_create(*args, **kwargs):
        return {"choices": [{"message": {"content": expected}}]}

    monkeypatch.setattr(llm_helper.async_client.chat.completions, "create", fake_create)

    out = asyncio.run(llm_helper.generate_async("hi async"))
    assert out == expected


def test_generate_sync_exception_returns_empty(monkeypatch):
    # sync client raising should result in empty string (logged)
    def raise_exc(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(llm_helper.client.chat.completions, "create", raise_exc)

    out = llm_helper.generate("whatever")
    assert out == ""


def test_generate_async_exception_returns_empty(monkeypatch):
    # async client raising should result in empty string
    async def raise_exc(*args, **kwargs):
        raise RuntimeError("async boom")

    monkeypatch.setattr(llm_helper.async_client.chat.completions, "create", raise_exc)

    out = asyncio.run(llm_helper.generate_async("whatever async"))
    assert out == ""


def test_generate_temperature_forwarded_sync(monkeypatch):
    # ensure temperature from cfg is forwarded to sync create call
    expected = "temp hello"

    # set custom temperature
    monkeypatch.setattr(llm_helper, "cfg", {**llm_helper.cfg, "temperature": 0.2})

    def fake_create(*args, **kwargs):
        assert kwargs.get("temperature") == 0.2
        return {"choices": [{"message": {"content": expected}}]}

    monkeypatch.setattr(llm_helper.client.chat.completions, "create", fake_create)

    out = llm_helper.generate("hi temp")
    assert out == expected


def test_generate_temperature_forwarded_async(monkeypatch):
    expected = "temp async hello"

    monkeypatch.setattr(llm_helper, "cfg", {**llm_helper.cfg, "temperature": 0.33})

    async def fake_create(*args, **kwargs):
        assert kwargs.get("temperature") == 0.33
        return {"choices": [{"message": {"content": expected}}]}

    monkeypatch.setattr(llm_helper.async_client.chat.completions, "create", fake_create)

    out = asyncio.run(llm_helper.generate_async("hi temp async"))
    assert out == expected
