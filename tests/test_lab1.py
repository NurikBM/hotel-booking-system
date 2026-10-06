"""Unit tests for Lab 1: Immutable Domain Models & Functional Transformations.

Covers:
  - Domain models immutability (frozen dataclasses)
  - Seed loading (load_seed)
  - Pure date operations (calculate_nights, generate_date_range)
  - Nightly price reduction (nightly_sum)
  - Immutable cart operations (hold_item, remove_hold, calculate_cart_total)
  - Pure integer discount calculation (apply_discount)
"""

from __future__ import annotations

import dataclasses
import os

import pytest

from core.domain import (
    Availability,
    CartItem,
    Guest,
    Hotel,
    Price,
    RatePlan,
    RoomType,
)
from core.transforms import (
    apply_discount,
    calculate_cart_total,
    calculate_nights,
    generate_date_range,
    hold_item,
    load_seed,
    nightly_sum,
    remove_hold,
)


def test_domain_models_immutability():
    """Verify that domain entities are immutable frozen dataclasses."""
    hotel = Hotel(
        id="h_test",
        name="Test Hotel",
        stars=4,
        city="Almaty",
        features=("wifi", "pool"),
    )
    assert hotel.id == "h_test"
    assert hotel.features == ("wifi", "pool")

    # Attempting to mutate must raise FrozenInstanceError
    with pytest.raises(dataclasses.FrozenInstanceError):
        hotel.name = "Modified Name"  # type: ignore[misc]


def test_load_seed_structure():
    """Verify load_seed loads realistic dataset into tuples of domain objects."""
    seed_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")
    hotels, rooms, rates, prices, avails, guests = load_seed(seed_path)

    assert len(hotels) >= 5
    assert len(rooms) >= 20
    assert len(rates) >= 40
    assert len(prices) >= 1000
    assert len(avails) >= 500
    assert len(guests) >= 50

    assert all(isinstance(h, Hotel) for h in hotels)
    assert all(isinstance(r, RoomType) for r in rooms)
    assert all(isinstance(rp, RatePlan) for rp in rates)
    assert all(isinstance(p, Price) for p in prices)
    assert all(isinstance(a, Availability) for a in avails)
    assert all(isinstance(g, Guest) for g in guests)

    # Verify money is strictly int
    assert all(isinstance(p.amount, int) for p in prices)


def test_calculate_nights_and_date_range():
    """Verify pure date calculations between ISO-8601 strings."""
    assert calculate_nights("2026-06-01", "2026-06-04") == 3
    assert calculate_nights("2026-06-15", "2026-06-16") == 1

    dates = generate_date_range("2026-06-01", "2026-06-04")
    assert dates == ("2026-06-01", "2026-06-02", "2026-06-03")

    with pytest.raises(ValueError):
        calculate_nights("2026-06-04", "2026-06-01")


def test_nightly_sum_with_reduce():
    """Verify nightly_sum aggregates amounts via reduce across the stay."""
    prices = (
        Price(date="2026-06-01", rate_id="rp_1", amount=1500000),
        Price(date="2026-06-02", rate_id="rp_1", amount=1500000),
        Price(date="2026-06-03", rate_id="rp_1", amount=1800000),
        Price(date="2026-06-01", rate_id="rp_2", amount=9999999),
    )

    total = nightly_sum(prices, "2026-06-01", "2026-06-04", "rp_1")
    assert total == 1500000 + 1500000 + 1800000
    assert total == 4800000
    assert isinstance(total, int)


def test_nightly_sum_missing_date_raises_error():
    """Verify nightly_sum raises ValueError when calendar data is incomplete."""
    prices = (Price(date="2026-06-01", rate_id="rp_1", amount=1500000),)
    with pytest.raises(ValueError, match="Missing price records"):
        nightly_sum(prices, "2026-06-01", "2026-06-03", "rp_1")


def test_cart_hold_and_remove_immutability():
    """Verify pure cart hold and remove operations preserve immutable state."""
    item1 = CartItem(
        id="c1",
        guest_id="g1",
        room_type_id="r1",
        rate_id="rp1",
        checkin="2026-06-01",
        checkout="2026-06-03",
        guests_count=2,
        total_price=3000000,
    )
    item2 = CartItem(
        id="c2",
        guest_id="g1",
        room_type_id="r2",
        rate_id="rp2",
        checkin="2026-06-05",
        checkout="2026-06-07",
        guests_count=1,
        total_price=2500000,
    )

    cart0: tuple[CartItem, ...] = ()
    cart1 = hold_item(cart0, item1)
    cart2 = hold_item(cart1, item2)

    assert cart0 == ()
    assert len(cart1) == 1
    assert len(cart2) == 2
    assert calculate_cart_total(cart2) == 5500000

    cart3 = remove_hold(cart2, "c1")
    assert len(cart3) == 1
    assert cart3[0].id == "c2"
    assert len(cart2) == 2  # cart2 remains unchanged


def test_apply_discount_pure_integer_math():
    """Verify discount application strictly uses integer math with cents."""
    assert apply_discount(1000000, 10) == 900000
    assert apply_discount(1000000, 0) == 1000000
    assert apply_discount(1000000, 100) == 0
    assert isinstance(apply_discount(1555555, 15), int)

    with pytest.raises(ValueError):
        apply_discount(1000000, -5)
    with pytest.raises(ValueError):
        apply_discount(1000000, 105)
