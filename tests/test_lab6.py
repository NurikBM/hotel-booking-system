"""Unit tests for Lab 6: FRP event bus and pure view handlers.

Covers: event ordering, immutability of bus/state, each view (holds, bookings,
price changes, occupancy), several handlers on one event, events without
subscribers, wildcard subscription and event-log replay.
"""

from __future__ import annotations

import copy

from core.domain import Booking, CartItem
from core.frp import (
    Event,
    EventBus,
    booking_payload,
    default_bus,
    hold_payload,
    initial_state,
    on_hold,
    price_change_payload,
    replay,
    search_payload,
    seq_ts,
)


def _item(item_id: str = "ci_1", cin: str = "2026-06-01", cout: str = "2026-06-03"):
    return CartItem(item_id, "g1", "rt1", "rp1", cin, cout, 2, 100)


def _booking(items, booking_id="bk_1"):
    return Booking(booking_id, "g1", tuple(items), sum(i.total_price for i in items))


def test_event_is_immutable_named_tuple():
    ev = Event("HOLD", "2026-06-01T00:00:00", {"a": 1})
    assert ev.name == "HOLD" and ev.ts.startswith("2026") and ev.payload == {"a": 1}
    assert isinstance(ev, tuple)


def test_publish_returns_new_bus_and_keeps_old_unchanged():
    bus = default_bus()
    snapshot = copy.deepcopy(bus.state)
    new_bus = bus.publish("HOLD", hold_payload(_item()))
    assert new_bus is not bus
    assert bus.state == snapshot and bus.log == ()
    assert len(new_bus.log) == 1 and len(new_bus.state["active_holds"]) == 1


def test_events_are_logged_in_order_with_deterministic_ts():
    bus = default_bus().publish_all(
        [("SEARCH", search_payload("Almaty", 2, 3)), ("HOLD", hold_payload(_item()))]
    )
    assert [e.name for e in bus.log] == ["SEARCH", "HOLD"]
    assert [e.ts for e in bus.log] == [seq_ts(0), seq_ts(1)]
    assert bus.publish("SEARCH", {}, ts="X").log[-1].ts == "X"


def test_handler_is_pure_and_does_not_mutate_state():
    state = initial_state()
    before = copy.deepcopy(state)
    new_state = on_hold(Event("HOLD", "t", hold_payload(_item())), state)
    assert state == before
    assert new_state is not state and len(new_state["active_holds"]) == 1


def test_active_holds_view_released_on_booking():
    items = [_item("a"), _item("b", "2026-06-05", "2026-06-06")]
    bus = default_bus()
    for it in items:
        bus = bus.publish("HOLD", hold_payload(it))
    assert len(bus.state["active_holds"]) == 2
    bus = bus.publish("BOOKED", booking_payload(_booking(items[:1])))
    assert [h["item_id"] for h in bus.state["active_holds"]] == ["b"]


def test_latest_bookings_and_occupancy_views():
    it = _item()
    bus = default_bus().publish("BOOKED", booking_payload(_booking([it])))
    assert bus.state["latest_bookings"][0]["booking_id"] == "bk_1"
    assert bus.state["latest_bookings"][0]["status"] == "confirmed"
    assert bus.state["occupancy"] == {"2026-06-01": 1, "2026-06-02": 1}


def test_cancel_updates_status_and_frees_occupancy():
    it = _item()
    payload = booking_payload(_booking([it]))
    bus = default_bus().publish("BOOKED", payload).publish("CANCELLED", payload)
    assert bus.state["latest_bookings"][0]["status"] == "cancelled"
    assert bus.state["occupancy"] == {}


def test_price_changes_view_newest_first_and_bounded():
    bus = default_bus()
    for n in range(12):
        bus = bus.publish(
            "PRICE_CHANGED", price_change_payload("rp1", "2026-06-01", n, n + 1)
        )
    changes = bus.state["price_changes"]
    assert len(changes) == 8 and changes[0]["new"] == 12


def test_multiple_handlers_and_unsubscribed_event():
    calls = []

    def h1(ev, state):
        calls.append("h1")
        return {**state, "x": 1}

    def h2(ev, state):
        calls.append("h2")
        return {**state, "y": state["x"] + 1}

    bus = EventBus().subscribe("HOLD", h1).subscribe("HOLD", h2)
    after = bus.publish("HOLD", {})
    assert calls == ["h1", "h2"] and after.state["y"] == 2
    ignored = bus.publish("SEARCH", {})
    assert ignored.state == bus.state and len(ignored.log) == 1


def test_wildcard_subscription_and_replay_equals_live_state():
    counter = lambda ev, st: {**st, "n": st.get("n", 0) + 1}  # noqa: E731
    bus = default_bus().subscribe("*", counter)
    bus = bus.publish_all(
        [("SEARCH", {}), ("HOLD", hold_payload(_item())), ("SEARCH", {})]
    )
    assert bus.state["n"] == 3
    rebuilt = replay(bus.log)
    assert rebuilt["searches"] == 2 and len(rebuilt["active_holds"]) == 1
