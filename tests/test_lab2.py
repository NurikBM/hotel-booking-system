"""Unit tests for Lab 2: Closures, Lambdas, and Recursive Algorithms.

Covers:
  - Closures: by_city, by_capacity, by_features
  - Lambda sorting functions
  - Recursive Algorithm 1: Hierarchical quote search (recursive_search_available_quotes)
  - Recursive Algorithm 2: Rule / discount engine (recursive_apply_rules)
  - Recursive Extremum Search: recursive_find_cheapest_quote
"""

from __future__ import annotations

import pytest

from core.domain import Availability, Hotel, Price, RatePlan, RoomType, Rule
from core.recursion import (
    BookingQuote,
    recursive_apply_rules,
    recursive_find_cheapest_quote,
    recursive_search_available_quotes,
)
from core.transforms import (
    by_capacity,
    by_city,
    by_features,
    by_price_range,
    sort_hotels_by_stars,
    sort_rooms_by_capacity,
)


def test_closure_by_price_range():
    """Verify by_price_range closure filters Price instances within monetary boundaries."""
    p1 = Price(date="2026-06-01", rate_id="rp1", amount=1500000)
    p2 = Price(date="2026-06-01", rate_id="rp2", amount=2500000)
    p3 = Price(date="2026-06-01", rate_id="rp3", amount=4000000)

    filter_budget = by_price_range(1000000, 2000000, "KZT")
    filter_mid = by_price_range(2000000, 3000000, "KZT")

    assert filter_budget(p1) is True
    assert filter_budget(p2) is False
    assert filter_mid(p2) is True
    assert filter_mid(p3) is False

    with pytest.raises(ValueError):
        by_price_range(5000000, 1000000)


def test_closure_by_city():
    """Verify by_city closure filters hotels case-insensitively."""
    hotel1 = Hotel(id="h1", name="H1", stars=4, city="Almaty", features=())
    hotel2 = Hotel(id="h2", name="H2", stars=5, city="Astana", features=())

    almaty_filter = by_city("almaty")
    astana_filter = by_city("ASTANA")
    other_filter = by_city("Shymkent")

    assert almaty_filter(hotel1) is True
    assert almaty_filter(hotel2) is False
    assert astana_filter(hotel2) is True
    assert other_filter(hotel1) is False


def test_closure_by_capacity():
    """Verify by_capacity closure filters rooms based on guest requirements."""
    room_single = RoomType(id="r1", hotel_id="h1", name="Single", capacity=1, beds=1)
    room_family = RoomType(id="r2", hotel_id="h1", name="Family", capacity=4, beds=3)

    cap_1 = by_capacity(1)
    cap_3 = by_capacity(3)

    assert cap_1(room_single) is True
    assert cap_1(room_family) is True
    assert cap_3(room_single) is False
    assert cap_3(room_family) is True

    with pytest.raises(ValueError):
        by_capacity(0)


def test_closure_by_features():
    """Verify by_features closure checks required subsets of amenities."""
    hotel = Hotel(
        id="h1",
        name="Spa Resort",
        stars=5,
        city="Almaty",
        features=("spa", "mountain_view", "wifi", "pool"),
    )

    req_wifi = by_features(("wifi",))
    req_spa_view = by_features(("spa", "mountain_view"))
    req_gym = by_features(("gym",))

    assert req_wifi(hotel) is True
    assert req_spa_view(hotel) is True
    assert req_gym(hotel) is False


def test_lambda_sorters():
    """Verify lambda combinators for sorting hotels, rooms, and prices."""
    hotels = (
        Hotel(id="h1", name="H1", stars=3, city="Almaty"),
        Hotel(id="h2", name="H2", stars=5, city="Almaty"),
        Hotel(id="h3", name="H3", stars=4, city="Almaty"),
    )
    sorted_hotels = sort_hotels_by_stars(hotels, descending=True)
    assert tuple(h.stars for h in sorted_hotels) == (5, 4, 3)

    rooms = (
        RoomType(id="r1", hotel_id="h1", name="Triple", capacity=3, beds=2),
        RoomType(id="r2", hotel_id="h1", name="Single", capacity=1, beds=1),
        RoomType(id="r3", hotel_id="h1", name="Double", capacity=2, beds=1),
    )
    sorted_rooms = sort_rooms_by_capacity(rooms, descending=False)
    assert tuple(r.capacity for r in sorted_rooms) == (1, 2, 3)


def test_recursive_search_available_quotes():
    """Verify recursive traversal across Hotel -> RoomType -> RatePlan hierarchy."""
    hotels = (Hotel(id="h1", name="Almaty Hotel", stars=4, city="Almaty"),)
    rooms = (
        RoomType(id="r1", hotel_id="h1", name="Double", capacity=2, beds=1),
        RoomType(id="r2", hotel_id="h1", name="Single", capacity=1, beds=1),
    )
    rates = (
        RatePlan(id="rp1", room_type_id="r1", name="Standard", meals="none"),
        RatePlan(id="rp2", room_type_id="r2", name="Standard", meals="none"),
    )
    prices = (
        Price(date="2026-06-01", rate_id="rp1", amount=2000000),
        Price(date="2026-06-02", rate_id="rp1", amount=2000000),
        Price(date="2026-06-01", rate_id="rp2", amount=1500000),
        Price(date="2026-06-02", rate_id="rp2", amount=1500000),
    )
    avails = (
        Availability(date="2026-06-01", room_type_id="r1", available_rooms=3),
        Availability(date="2026-06-02", room_type_id="r1", available_rooms=2),
        # r2 has 0 availability on day 2
        Availability(date="2026-06-01", room_type_id="r2", available_rooms=1),
        Availability(date="2026-06-02", room_type_id="r2", available_rooms=0),
    )

    quotes = recursive_search_available_quotes(
        hotels=hotels,
        room_types=rooms,
        rate_plans=rates,
        prices=prices,
        availabilities=avails,
        city="Almaty",
        checkin="2026-06-01",
        checkout="2026-06-03",
        guests=2,
    )

    # Only r1 matches guests=2 AND has availability > 0 on both days
    assert len(quotes) == 1
    quote = quotes[0]
    assert quote.room_type.id == "r1"
    assert quote.base_total == 4000000


def test_recursive_apply_rules():
    """Verify recursive discount and rule evaluation chain."""
    rules = (
        Rule(
            id="rule_vip",
            kind="vip_discount",
            payload=(10,),
        ),
        Rule(
            id="rule_early",
            kind="early_bird",
            payload=(14, 500000),
        ),
    )

    # Test with both conditions true
    ctx_both = {"is_vip": True, "days_in_advance": 30}
    # 2000000 -> 10% off = 1800000 -> minus 500000 = 1300000
    res1 = recursive_apply_rules(2000000, rules, ctx_both)
    assert res1 == 1300000

    # Test with only loyalty true
    ctx_vip = {"is_vip": True, "days_in_advance": 5}
    res2 = recursive_apply_rules(2000000, rules, ctx_vip)
    assert res2 == 1800000


def test_recursive_find_cheapest_quote():
    """Verify recursive tail-search for minimum quote."""
    hotel = Hotel(id="h1", name="Hotel", stars=4, city="Almaty")
    room = RoomType(id="r1", hotel_id="h1", name="Room", capacity=2, beds=1)
    rp = RatePlan(id="rp1", room_type_id="r1", name="Plan")

    quotes = (
        BookingQuote(hotel, room, rp, "2026-06-01", "2026-06-02", 1, 5000000, 5000000),
        BookingQuote(hotel, room, rp, "2026-06-01", "2026-06-02", 1, 3200000, 3200000),
        BookingQuote(hotel, room, rp, "2026-06-01", "2026-06-02", 1, 4100000, 4100000),
    )

    cheapest = recursive_find_cheapest_quote(quotes)
    assert cheapest is not None
    assert cheapest.final_total == 3200000

    # Empty list test
    assert recursive_find_cheapest_quote(()) is None
