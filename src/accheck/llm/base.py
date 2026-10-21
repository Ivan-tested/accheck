"""Interface that every LLM adapter implements, plus JSON helpers.

Adapters only send text and return text. Turning the reply into a model
(and retrying when the reply is broken) is done here once, so every
provider - Ollama, OpenAI, Anthropic, the fake one - gets it for free.
"""

import re
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError


class LLMError(Exception):
    pass


class LLMResponseError(LLMError):
    """The model replied, but the reply is not the JSON we asked for."""

    def __init__(self, message: str, raw: str):
        super().__init__(message)
        self.raw = raw


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


T = TypeVar("T", bound=BaseModel)

_FENCE_RE = re.compile(r"```(?:json)?\s*(?P<body>.*?)\s*```", re.DOTALL)


def extract_json(text: str) -> str:
    """Cut the JSON object out of a reply.

    Models often wrap JSON in ```json fences or add a sentence before it.
    """
    fence = _FENCE_RE.search(text)
    if fence:
        text = fence["body"]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        raise ValueError("no JSON object in the reply")
    return text[start : end + 1]


def ask_json(client: LLMClient, system: str, user: str, schema: type[T], retries: int = 1) -> T:
    """Ask the model and validate its reply against `schema`.

    On a broken reply the error is sent back to the model, which usually
    fixes it; after `retries` such attempts LLMResponseError is raised.
    """
    prompt = user
    for attempt in range(retries + 1):
        raw = client.complete(system, prompt)
        try:
            return schema.model_validate_json(extract_json(raw))
        except (ValueError, ValidationError) as error:
            if attempt == retries:
                raise LLMResponseError(f"Invalid reply after {retries + 1} attempt(s): {error}", raw) from error
            prompt = (
                f"{user}\n\nYour previous reply was invalid:\n{error}\n"
                "Reply again with a single valid JSON object only."
            )
    raise AssertionError("unreachable")
