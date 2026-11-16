"""Functional Reactive Programming (FRP): booking event bus for Lab 6.

Design
------
* ``Event`` is an immutable ``NamedTuple(name, ts, payload)`` (spec signature).
* ``EventBus`` is an immutable value. ``subscribe`` and ``publish`` do not change the bus
  they are called on; they return a NEW ``EventBus`` (new handler table / new state / new log).
  Usage: ``bus = bus.publish("HOLD", {...})``.
* Handlers are pure ``(Event, state: dict) -> new_state: dict`` functions. They never
  mutate ``state`` and never touch globals, so a view is simply a left fold of the event log:
  ``state = reduce(lambda s, e: handler(e, s), events, initial_state())``.
* Time is injected: ``publish`` accepts an explicit ``ts``; otherwise a deterministic
  sequence timestamp derived from the log length is used (no ``datetime.now()``), so tests
  and replays are reproducible.

Views kept in the bus state (``initial_state()``):
    active_holds    tuple of hold dicts not yet booked/cancelled
    latest_bookings tuple of the most recent bookings (newest first)
    price_changes   tuple of the most recent price changes (newest first)
    occupancy       dict date -> number of booked rooms
    searches        number of SEARCH events seen
"""

from __future__ import annotations

import functools
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, NamedTuple

from core.domain import Booking, CartItem
from core.transforms import generate_date_range

EVENT_NAMES: tuple[str, ...] = (
    "SEARCH",
    "HOLD",
    "BOOKED",
    "CANCELLED",
    "PRICE_CHANGED",
)
MAX_BOOKINGS = 5
MAX_PRICE_CHANGES = 8


class Event(NamedTuple):
    """Immutable event record (name, ISO timestamp, payload)."""

    name: str
    ts: str
    payload: dict


Handler = Callable[[Event, dict], dict]


def initial_state() -> dict:
    """Empty state for all views."""
    return {
        "active_holds": (),
        "latest_bookings": (),
        "price_changes": (),
        "occupancy": {},
        "searches": 0,
    }


def seq_ts(n: int) -> str:
    """Deterministic ISO-like timestamp for the n-th event (pure, no clock)."""
    return f"2026-06-01T00:{n // 60 % 60:02d}:{n % 60:02d}"


# ============================================================================
# PURE HANDLERS (state-in -> state-out)
# ============================================================================


def _bump_occupancy(occupancy: dict, nights: Iterable[str], delta: int) -> dict:
    """Return a NEW occupancy dict with ``delta`` added to each night (never below 0)."""
    updated = dict(occupancy)
    for d in nights:
        updated[d] = max(0, updated.get(d, 0) + delta)
    return {d: n for d, n in updated.items() if n > 0}


def _booking_nights(items: Iterable[dict]) -> tuple[str, ...]:
    return tuple(
        d for it in items for d in generate_date_range(it["checkin"], it["checkout"])
    )


def on_search(event: Event, state: dict) -> dict:
    """SEARCH: count searches."""
    return {**state, "searches": state["searches"] + 1}


def on_hold(event: Event, state: dict) -> dict:
    """HOLD: add (or replace by item id) an active hold."""
    hold = event.payload
    kept = tuple(h for h in state["active_holds"] if h["item_id"] != hold["item_id"])
    return {**state, "active_holds": (*kept, dict(hold))}


def on_booked_release_holds(event: Event, state: dict) -> dict:
    """BOOKED: holds that became part of the booking are no longer active."""
    booked_ids = {it["item_id"] for it in event.payload["items"]}
    remaining = tuple(
        h for h in state["active_holds"] if h["item_id"] not in booked_ids
    )
    return {**state, "active_holds": remaining}


def on_booked_record(event: Event, state: dict) -> dict:
    """BOOKED: remember the booking (newest first, bounded)."""
    record = {**event.payload, "status": "confirmed", "ts": event.ts}
    others = tuple(
        b for b in state["latest_bookings"] if b["booking_id"] != record["booking_id"]
    )
    return {**state, "latest_bookings": ((record, *others))[:MAX_BOOKINGS]}


def on_booked_occupancy(event: Event, state: dict) -> dict:
    """BOOKED: occupy every night of every booked item."""
    nights = _booking_nights(event.payload["items"])
    return {**state, "occupancy": _bump_occupancy(state["occupancy"], nights, +1)}


def on_cancelled_mark(event: Event, state: dict) -> dict:
    """CANCELLED: mark the booking as cancelled in the latest-bookings view."""
    target = event.payload["booking_id"]
    updated = tuple(
        {**b, "status": "cancelled"} if b["booking_id"] == target else b
        for b in state["latest_bookings"]
    )
    return {**state, "latest_bookings": updated}


def on_cancelled_occupancy(event: Event, state: dict) -> dict:
    """CANCELLED: free every night of every cancelled item."""
    nights = _booking_nights(event.payload["items"])
    return {**state, "occupancy": _bump_occupancy(state["occupancy"], nights, -1)}


def on_cancelled_release_holds(event: Event, state: dict) -> dict:
    """CANCELLED: drop holds that reference the cancelled items, if any remain."""
    ids = {it["item_id"] for it in event.payload["items"]}
    remaining = tuple(h for h in state["active_holds"] if h["item_id"] not in ids)
    return {**state, "active_holds": remaining}


def on_price_changed(event: Event, state: dict) -> dict:
    """PRICE_CHANGED: record the change (newest first, bounded)."""
    change = {**event.payload, "ts": event.ts}
    return {
        **state,
        "price_changes": ((change, *state["price_changes"]))[:MAX_PRICE_CHANGES],
    }


DEFAULT_SUBSCRIPTIONS: tuple[tuple[str, Handler], ...] = (
    ("SEARCH", on_search),
    ("HOLD", on_hold),
    ("BOOKED", on_booked_release_holds),
    ("BOOKED", on_booked_record),
    ("BOOKED", on_booked_occupancy),
    ("CANCELLED", on_cancelled_mark),
    ("CANCELLED", on_cancelled_occupancy),
    ("CANCELLED", on_cancelled_release_holds),
    ("PRICE_CHANGED", on_price_changed),
)


# ============================================================================
# EVENT BUS (immutable value)
# ============================================================================


@dataclass(frozen=True)
class EventBus:
    """Immutable event bus: handler table + current view state + event log."""

    handlers: tuple[tuple[str, Handler], ...] = ()
    state: dict = None  # type: ignore[assignment]
    log: tuple[Event, ...] = ()

    def __post_init__(self) -> None:
        if self.state is None:
            object.__setattr__(self, "state", initial_state())

    def subscribe(self, name: str, handler: Handler) -> EventBus:
        """Return a new bus with ``handler`` also subscribed to event ``name``."""
        return EventBus((*self.handlers, (name, handler)), self.state, self.log)

    def publish(self, name: str, payload: dict, ts: str | None = None) -> EventBus:
        """Return a new bus after folding ``name`` handlers over the state.

        Handlers subscribed under ``"*"`` receive every event.
        """
        event = Event(
            name, ts if ts is not None else seq_ts(len(self.log)), dict(payload)
        )
        matching = tuple(h for n, h in self.handlers if n in (name, "*"))
        new_state = functools.reduce(
            lambda state, handler: handler(event, state), matching, self.state
        )
        return EventBus(self.handlers, new_state, (*self.log, event))

    def publish_all(self, events: Iterable[tuple[str, dict]]) -> EventBus:
        """Publish several ``(name, payload)`` pairs in order."""
        return functools.reduce(lambda bus, e: bus.publish(e[0], e[1]), events, self)


def default_bus() -> EventBus:
    """Bus pre-wired with all default view handlers."""
    return functools.reduce(
        lambda bus, sub: bus.subscribe(sub[0], sub[1]),
        DEFAULT_SUBSCRIPTIONS,
        EventBus(),
    )


def replay(
    events: Iterable[Event], handlers: tuple[tuple[str, Handler], ...] | None = None
) -> dict:
    """Rebuild view state purely from an event log (event sourcing)."""
    table = DEFAULT_SUBSCRIPTIONS if handlers is None else handlers
    return functools.reduce(
        lambda state, ev: functools.reduce(
            lambda s, h: h(ev, s), (h for n, h in table if n in (ev.name, "*")), state
        ),
        events,
        initial_state(),
    )


# ============================================================================
# PAYLOAD BUILDERS (pure projections of domain values onto event payloads)
# ============================================================================


def search_payload(city: str, guests: int, found: int) -> dict:
    return {"city": city, "guests": guests, "found": found}


def hold_payload(item: CartItem) -> dict:
    return {
        "item_id": item.id,
        "room_type_id": item.room_type_id,
        "rate_id": item.rate_id,
        "checkin": item.checkin,
        "checkout": item.checkout,
        "guests": item.guests_count,
        "total": item.total_price,
    }


def booking_payload(booking: Booking) -> dict[str, Any]:
    return {
        "booking_id": booking.id,
        "guest_id": booking.guest_id,
        "total": booking.total,
        "items": tuple(hold_payload(it) for it in booking.items),
    }


def price_change_payload(rate_id: str, date: str, old: int, new: int) -> dict:
    return {"rate_id": rate_id, "date": date, "old": old, "new": new}
