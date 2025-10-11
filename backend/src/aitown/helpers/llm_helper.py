from __future__ import annotations

from loguru import logger
from typing import Dict, Optional

import openai
import asyncio

from .config_helper import get_config

cfg = get_config("llm")
base_url = cfg.get("base_url")
model = cfg.get("model")
api_key = cfg.get("api_key")

client = openai.OpenAI(base_url=base_url, api_key=api_key)

# provide an async client for true async usage
async_client = openai.AsyncOpenAI(base_url=base_url, api_key=api_key)


def generate(prompt: str) -> str:
    """Generate text from the configured OpenAI-compatible LLM. 
    
    This function will log errors and return an empty string on failure 
    so that callers do not have to handle exceptions.

    Args:
        prompt: The input prompt string.

    Returns:
        The generated text response from the LLM, or an empty string on failure.
    """
    try:
        resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=cfg.get("temperature", 0.7))
        # openai returns choices -> message -> content
        text: str = resp["choices"][0]["message"]["content"]
        return text.strip()
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return ""


async def generate_async(prompt: str) -> str:
    """Asynchronous generation using the AsyncOpenAI client.

    Calls the async chat completions endpoint and returns the content.
    """
    try:
        resp = await async_client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}], temperature=cfg.get("temperature", 0.7)
        )
        text: str = resp["choices"][0]["message"]["content"]
        return text.strip()
    except Exception as e:
        logger.error(f"LLM async generation failed: {e}")
        return ""
    
