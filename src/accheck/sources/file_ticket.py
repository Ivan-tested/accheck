"""Ticket source that reads tickets from Markdown files.

Expected file layout (<dir>/<KEY>.md):

    # PROJ-123: Ticket title

    Free-form description...

    ## Acceptance Criteria
    - First criterion
    - Second criterion

Each list item in the criteria section becomes AC1, AC2, ... A ticket without
that section gets an empty criteria list; `review` will derive them later.
"""

import re
from pathlib import Path

from accheck.models import AcceptanceCriterion, Ticket
from accheck.sources.base import TicketNotFoundError

DEFAULT_AC_TITLES = ("acceptance criteria", "критерии приёмки", "критерии приемки")

_TITLE_RE = re.compile(r"^#\s+(?P<key>[A-Z][A-Z0-9]*-\d+)\s*:\s*(?P<title>.+)$")
_HEADING_RE = re.compile(r"^(?P<level>#{2,6})\s+(?P<text>.+?)\s*$")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?P<text>.+?)\s*$")


class FileTicketSource:
    def __init__(self, directory: Path, ac_titles: tuple[str, ...] = DEFAULT_AC_TITLES):
        self.directory = Path(directory)
        self.ac_titles = tuple(t.lower() for t in ac_titles)

    def get_ticket(self, key: str) -> Ticket:
        path = self.directory / f"{key}.md"
        if not path.is_file():
            raise TicketNotFoundError(f"Ticket file not found: {path}")
        return parse_ticket(path.read_text(encoding="utf-8"), self.ac_titles)


def parse_ticket(text: str, ac_titles: tuple[str, ...] = DEFAULT_AC_TITLES) -> Ticket:
    lines = text.splitlines()

    title_index, match = _find_title(lines)
    body = lines[title_index + 1 :]

    description_lines: list[str] = []
    criteria_texts: list[str] = []
    ac_level: int | None = None  # heading level of the open AC section

    for line in body:
        heading = _HEADING_RE.match(line)
        if heading:
            level = len(heading["level"])
            if heading["text"].strip().lower() in ac_titles:
                ac_level = level
                continue
            if ac_level is not None and level <= ac_level:
                ac_level = None  # a sibling/parent heading closes the AC section

        if ac_level is not None:
            item = _LIST_ITEM_RE.match(line)
            if item:
                criteria_texts.append(item["text"])
        else:
            description_lines.append(line)

    criteria = [
        AcceptanceCriterion(id=f"AC{i}", text=t) for i, t in enumerate(criteria_texts, start=1)
    ]
    return Ticket(
        key=match["key"],
        title=match["title"].strip(),
        description="\n".join(description_lines).strip(),
        criteria=criteria,
    )


def _find_title(lines: list[str]) -> tuple[int, re.Match[str]]:
    for i, line in enumerate(lines):
        if line.strip():
            match = _TITLE_RE.match(line.strip())
            if match:
                return i, match
            break
    raise ValueError("First non-empty line must be '# KEY-123: Title'")
