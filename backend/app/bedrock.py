"""Amazon Bedrock wrapper for the Nova model family.

Uses the Converse API, which normalises request/response shape across Nova models
and makes it easy to demand JSON-only output. All callers expect strict JSON back.
"""
import functools
import json

import boto3

from . import config


@functools.lru_cache(maxsize=1)
def _client():
    return boto3.client("bedrock-runtime", region_name=config.AWS_REGION)


def invoke_json(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> dict:
    """Call Bedrock and parse the model's response as JSON.

    The prompts must instruct the model to return strict JSON only. We still guard
    against an accidental ```json fence before json.loads.
    """
    resp = _client().converse(
        modelId=config.BEDROCK_MODEL_ID,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.2},
    )
    text = resp["output"]["message"]["content"][0]["text"].strip()
    text = _strip_fence(text)
    return json.loads(text)


def _strip_fence(text: str) -> str:
    if text.startswith("```"):
        # drop the opening fence line and any trailing fence
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text
