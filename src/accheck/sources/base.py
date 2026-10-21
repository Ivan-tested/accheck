"""Interfaces that every source adapter implements."""

from typing import Protocol

from accheck.models import Ticket


class TicketNotFoundError(Exception):
    pass


class TicketSource(Protocol):
    def get_ticket(self, key: str) -> Ticket: ...
