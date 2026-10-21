"""Core data models.

The core works only with these objects. Adapters (Jira, pytest, JUnit, LLMs)
convert their own formats into them, so the core never depends on any
external system.
"""

from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field


# --- Tickets and review ------------------------------------------------------


class Origin(StrEnum):
    EXPLICIT = "explicit"  # written in the ticket
    DERIVED = "derived"  # inferred by the LLM, needs confirmation


class Testability(StrEnum):
    OK = "ok"
    VAGUE = "vague"  # testable after clarification
    UNTESTABLE = "untestable"  # no measurable outcome


class AcceptanceCriterion(BaseModel):
    id: str  # "AC1", "AC2", ...
    text: str
    origin: Origin = Origin.EXPLICIT
    # The fields below are filled in by `review`.
    testability: Testability | None = None
    issue: str | None = None
    suggestion: str | None = None


class Ticket(BaseModel):
    key: str  # "PROJ-123"
    title: str
    description: str = ""
    criteria: list[AcceptanceCriterion] = Field(default_factory=list)


class Readiness(StrEnum):
    READY = "ready"
    NEEDS_CLARIFICATION = "needs_clarification"
    NOT_READY = "not_ready"


class TicketReview(BaseModel):
    ticket_key: str
    readiness: Readiness
    criteria: list[AcceptanceCriterion]
    questions: list[str] = Field(default_factory=list)


# --- Tests and results -------------------------------------------------------
# pytest tries to collect any class whose name starts with "Test" if it is
# imported into a test module; __test__ = False tells it these are not tests.


class TestCase(BaseModel):
    __test__: ClassVar[bool] = False

    id: str  # "tests/test_login.py::test_lock_after_3_attempts"
    name: str
    docstring: str | None = None
    markers: list[str] = Field(default_factory=list)
    asserts: list[str] = Field(default_factory=list)


class TestStatus(StrEnum):
    __test__: ClassVar[bool] = False

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestResult(BaseModel):
    __test__: ClassVar[bool] = False

    test_id: str
    status: TestStatus
    message: str | None = None


# --- Matching and coverage ---------------------------------------------------


class MatchSource(StrEnum):
    MARKER = "marker"  # explicit @pytest.mark.covers(...)
    LLM = "llm"
    MANUAL = "manual"  # confirmed or corrected by a human


class CoverageLevel(StrEnum):
    FULL = "full"
    PARTIAL = "partial"


class Match(BaseModel):
    criterion_id: str
    test_id: str
    source: MatchSource
    level: CoverageLevel = CoverageLevel.FULL
    reason: str | None = None  # why the LLM thinks so / what is missing


class Verdict(StrEnum):
    COVERED_PASSED = "covered_passed"
    COVERED_FAILED = "covered_failed"
    COVERED_NOT_RUN = "covered_not_run"
    PARTIAL = "partial"
    NOT_COVERED = "not_covered"


class CriterionCoverage(BaseModel):
    criterion: AcceptanceCriterion
    verdict: Verdict
    matches: list[Match] = Field(default_factory=list)


class CoverageReport(BaseModel):
    ticket_key: str
    items: list[CriterionCoverage]
    unmatched_tests: list[str] = Field(default_factory=list)
