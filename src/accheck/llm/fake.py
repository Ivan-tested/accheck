"""LLM adapter for tests: returns prepared replies instead of calling a model.

    llm = FakeLLM(['{"readiness": "ready"}'])
    llm.complete("system", "user")  # -> '{"readiness": "ready"}'
    llm.calls                        # -> [LLMCall(system="system", user="user")]

A reply can also be a dict or a pydantic model (sent as JSON) or a function
that builds the reply from the prompt.
"""

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from pydantic import BaseModel

from accheck.llm.base import LLMError

Reply = str | dict | BaseModel | Callable[[str, str], str]


@dataclass
class LLMCall:
    system: str
    user: str


class FakeLLM:
    def __init__(self, replies: Iterable[Reply]):
        self._replies = list(replies)
        self.calls: list[LLMCall] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append(LLMCall(system, user))
        if not self._replies:
            raise LLMError(f"FakeLLM has no reply left for call #{len(self.calls)}")
        reply = self._replies.pop(0)
        if callable(reply):
            return reply(system, user)
        if isinstance(reply, BaseModel):
            return reply.model_dump_json()
        if isinstance(reply, dict):
            return json.dumps(reply)
        return reply
