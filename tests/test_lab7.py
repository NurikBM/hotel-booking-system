"""Unit tests for Lab 7: compose/pipe utilities and Search/Quote/Booking facades.

Covers: compose associativity and order, pipe, injected fakes (DI), real wiring on
seed data, Left on validator failure, Right on success, empty cart, no mutation.
"""

from __future__ import annotations

import os

import pytest

from core.compose import all_of, compose, pipe, rank_by
from core.domain import CartItem
from core.ftypes import DEFAULT_RULES, Left, Right
from core.lazy import lazy_offers
from core.service import (
    BookingService,
    QuoteService,
    SearchService,
    build_services,
    city_filter,
    price_scorer,
    validate_all,
)
from core.transforms import load_seed


@pytest.fixture(scope="module")
def seed():
    return load_seed(os.path.join(os.path.dirname(__file__), "..", "data", "seed.json"))


def _item(
    item_id="ci_1", rt="rt_h_almaty_rixos_1", rp="rp_rt_h_almaty_rixos_1_standard"
):
    return CartItem(item_id, "guest_001", rt, rp, "2026-06-01", "2026-06-04", 1, 0)


def test_compose_order_and_identity():
    inc = lambda x: x + 1  # noqa: E731
    dbl = lambda x: x * 2  # noqa: E731
    assert compose(inc, dbl)(5) == 11  # inc(dbl(5))
    assert compose()(7) == 7


def test_compose_is_associative():
    f, g, h = (lambda x: x + 1), (lambda x: x * 3), (lambda x: x - 2)
    assert compose(compose(f, g), h)(4) == compose(f, compose(g, h))(4)


def test_pipe_left_to_right_and_single_value():
    assert pipe(5, lambda x: x + 1, lambda x: x * 2) == 12
    assert pipe("x") == "x"


def test_all_of_and_rank_by_do_not_mutate_input():
    data = (3, 1, 2)
    assert all_of(lambda x: x > 0, lambda x: x < 3)(2) is True
    assert all_of()(object()) is True
    assert rank_by((lambda x: x,))(data) == (1, 2, 3) and data == (3, 1, 2)


def test_search_service_with_injected_fakes():
    from core.domain import Hotel, RatePlan, RoomType

    hotel = Hotel("h1", "H", 3, "C")
    room = RoomType("r1", "h1", "R", 2)
    offers = [
        (hotel, room, RatePlan(id=pid, room_type_id="r1"), price)
        for pid, price in (("pA", 5), ("pB", 1), ("pC", 3))
    ]
    svc = SearchService(
        filters=(lambda req: lambda o: o[3] <= req["max"],),
        scorers=(lambda o: o[3],),
    )
    assert svc.search({"offers": offers, "max": 3}) == (
        ("h1", "r1", "pB"),
        ("h1", "r1", "pC"),
    )
    assert svc.search({"offers": offers, "max": 3, "limit": 1}) == (("h1", "r1", "pB"),)


def test_search_service_on_seed_data_is_sorted_and_filtered(seed):
    hotels, rooms, rates, prices, avail, _ = seed
    search, _q, _b = build_services(rooms, rates, prices, avail, DEFAULT_RULES)
    offers = lazy_offers(
        hotels, rooms, rates, prices, avail, None, "2026-06-01", "2026-06-04"
    )
    ids = search.search({"offers": offers, "city": "Almaty", "guests": 2, "limit": 5})
    assert 0 < len(ids) <= 5
    hotel_ids = {h.id for h in hotels if h.city == "Almaty"}
    assert all(i[0] in hotel_ids for i in ids)


def test_quote_service_delegates_to_injected_quoter(seed):
    assert QuoteService(lambda item: 42).quote(_item()) == 42
    _h, rooms, rates, prices, avail, _g = seed
    _s, quote, _b = build_services(rooms, rates, prices, avail, DEFAULT_RULES)
    assert quote.quote(_item()) > 0
    assert quote.quote(_item(rt="missing")) == 0


def test_booking_confirm_right_on_valid_cart(seed):
    _h, rooms, rates, prices, avail, guests = seed
    _s, _q, booking = build_services(rooms, rates, prices, avail, DEFAULT_RULES)
    cart = (_item(),)
    result = booking.confirm(guests[0], cart)
    assert isinstance(result, Right)
    assert result.value.total > 0 and result.value.items[0].total_price > 0
    assert cart[0].total_price == 0  # input item untouched


def test_booking_confirm_left_when_validator_fails(seed):
    _h, rooms, rates, prices, avail, guests = seed
    _s, _q, booking = build_services(rooms, rates, prices, avail, DEFAULT_RULES)
    bad = _item(rt="does_not_exist")
    res = booking.confirm(guests[0], (bad,))
    assert isinstance(res, Left) and res.error["code"] == "room_type_not_found"
    assert isinstance(booking.confirm(guests[0], ()), Left)


def test_booking_service_uses_only_injected_dependencies():
    from core.domain import Guest

    guest = Guest("g", "n", "e", "p")
    order = []

    def validator(item):
        order.append("validate")
        return Right(item)

    def quoter(item):
        order.append("quote")
        return 10

    def finalizer(g, items):
        order.append("finalize")
        return Right(items)

    svc = BookingService((validator,), quoter, finalizer)
    res = svc.confirm(guest, (_item(),))
    assert order == ["validate", "quote", "finalize"]
    assert res.value[0].total_price == 10
    assert isinstance(validate_all(())(()), Left)
    assert city_filter({})(("h",)) is True and price_scorer((0, 0, 0, 9)) == 9
