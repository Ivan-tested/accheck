import pytest
from pydantic import BaseModel

from accheck.llm.base import LLMError, LLMResponseError, ask_json, extract_json
from accheck.llm.fake import FakeLLM


class Answer(BaseModel):
    verdict: str
    score: int


# --- FakeLLM -----------------------------------------------------------------


def test_fake_returns_replies_in_order_and_records_calls():
    llm = FakeLLM(["first", "second"])

    assert llm.complete("sys", "one") == "first"
    assert llm.complete("sys", "two") == "second"
    assert [c.user for c in llm.calls] == ["one", "two"]
    assert llm.calls[0].system == "sys"


def test_fake_serializes_dicts_and_models():
    llm = FakeLLM([{"verdict": "ok", "score": 1}, Answer(verdict="bad", score=0)])

    assert Answer.model_validate_json(llm.complete("s", "u")) == Answer(verdict="ok", score=1)
    assert Answer.model_validate_json(llm.complete("s", "u")) == Answer(verdict="bad", score=0)


def test_fake_reply_can_be_built_from_prompt():
    llm = FakeLLM([lambda system, user: user.upper()])

    assert llm.complete("s", "hello") == "HELLO"


def test_fake_raises_when_out_of_replies():
    llm = FakeLLM([])

    with pytest.raises(LLMError, match="no reply left"):
        llm.complete("s", "u")


# --- extract_json ------------------------------------------------------------


@pytest.mark.parametrize(
    "reply",
    [
        '{"a": 1}',
        '```json\n{"a": 1}\n```',
        'Sure! Here is the result:\n{"a": 1}\nHope it helps.',
        '```\n{"a": 1}\n```',
    ],
)
def test_extract_json_strips_fences_and_chatter(reply):
    assert extract_json(reply) == '{"a": 1}'


def test_extract_json_without_object_raises():
    with pytest.raises(ValueError, match="no JSON object"):
        extract_json("I cannot answer that.")


# --- ask_json ----------------------------------------------------------------


def test_ask_json_returns_validated_model():
    llm = FakeLLM(['```json\n{"verdict": "ok", "score": 5}\n```'])

    answer = ask_json(llm, "sys", "question", Answer)

    assert answer == Answer(verdict="ok", score=5)
    assert len(llm.calls) == 1


def test_ask_json_retries_with_error_in_prompt():
    llm = FakeLLM(['{"verdict": "ok"}', {"verdict": "ok", "score": 2}])

    answer = ask_json(llm, "sys", "question", Answer)

    assert answer.score == 2
    retry_prompt = llm.calls[1].user
    assert retry_prompt.startswith("question")
    assert "score" in retry_prompt  # the validation error names the missing field
    assert "valid JSON" in retry_prompt


def test_ask_json_gives_up_after_retries():
    llm = FakeLLM(["not json", "still not json"])

    with pytest.raises(LLMResponseError) as error:
        ask_json(llm, "sys", "question", Answer, retries=1)

    assert error.value.raw == "still not json"
    assert len(llm.calls) == 2


def test_ask_json_without_retries_calls_once():
    llm = FakeLLM(['{"verdict": "ok", "score": "many"}'])

    with pytest.raises(LLMResponseError):
        ask_json(llm, "sys", "question", Answer, retries=0)

    assert len(llm.calls) == 1
