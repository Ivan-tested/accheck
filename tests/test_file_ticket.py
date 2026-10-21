from pathlib import Path

import pytest

from accheck.models import Origin
from accheck.sources.base import TicketNotFoundError
from accheck.sources.file_ticket import FileTicketSource, parse_ticket

EXAMPLES = Path(__file__).parent.parent / "examples" / "tickets"


def test_reads_key_title_and_criteria():
    ticket = FileTicketSource(EXAMPLES).get_ticket("SHOP-101")

    assert ticket.key == "SHOP-101"
    assert ticket.title == "Lock user account after failed login attempts"
    assert [c.id for c in ticket.criteria] == ["AC1", "AC2", "AC3", "AC4"]
    assert ticket.criteria[0].text == "After 3 consecutive failed login attempts the account is locked"
    assert all(c.origin == Origin.EXPLICIT for c in ticket.criteria)


def test_section_after_criteria_goes_back_to_description():
    ticket = FileTicketSource(EXAMPLES).get_ticket("SHOP-101")

    assert "Protect accounts" in ticket.description
    assert "Lockout duration is fixed" in ticket.description
    assert "consecutive failed" not in ticket.description


def test_numbered_list_items():
    ticket = FileTicketSource(EXAMPLES).get_ticket("SHOP-102")

    assert len(ticket.criteria) == 4
    assert ticket.criteria[2].text == "The promo code field accepts a code and applies the discount"


def test_ticket_without_criteria_section():
    ticket = FileTicketSource(EXAMPLES).get_ticket("SHOP-103")

    assert ticket.criteria == []
    assert "export orders" in ticket.description


def test_russian_section_title():
    text = "# ABC-1: Заголовок\n\nОписание\n\n## Критерии приёмки\n* Первый\n* Второй\n"

    ticket = parse_ticket(text)

    assert [c.text for c in ticket.criteria] == ["Первый", "Второй"]
    assert ticket.description == "Описание"


def test_subheading_inside_criteria_section_keeps_it_open():
    text = "# ABC-1: T\n\n## Acceptance Criteria\n### Login\n- One\n### Logout\n- Two\n## Notes\n- not a criterion\n"

    ticket = parse_ticket(text)

    assert [c.text for c in ticket.criteria] == ["One", "Two"]


def test_missing_file_raises():
    with pytest.raises(TicketNotFoundError):
        FileTicketSource(EXAMPLES).get_ticket("SHOP-999")


def test_missing_title_raises():
    with pytest.raises(ValueError, match="KEY-123"):
        parse_ticket("Just some text\n- item\n")
