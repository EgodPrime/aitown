"""Example script to call an OpenAI-compatible endpoint using AsyncServerDefaultLLMAdapter.

Usage:
  python scripts/openai_integration_example.py --base-url http://192.168.2.29:8021/v1 --api-key asd --model qwen3-30b-a3b

The script will print the response text.
"""
import asyncio
import argparse
from aitown.server.llm_adapter import AsyncServerDefaultLLMAdapter


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--api-key", required=True)
    p.add_argument("--model", default=None)
    p.add_argument("--prompt", default="Say hello briefly.")
    args = p.parse_args()

    adapter = AsyncServerDefaultLLMAdapter(endpoint=args.base_url + "/chat/completions", api_key=args.api_key)
    try:
        res = await adapter.agenerate(args.prompt, model=args.model)
        print("Response text:")
        print(res.get("text"))
    finally:
        # close httpx client
        try:
            await adapter._client.aclose()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
