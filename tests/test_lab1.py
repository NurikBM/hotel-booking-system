"""Unit & Functional Tests: Lab 1 — Pure Functions, Immutability, and HOF Pipelines.

Tests verify:
  1. Immutability of domain entities (frozen dataclass contracts).
  2. Pure transformation functions (stay duration nights and pricing calculations).
  3. Pure discount and quote calculations.
  4. Predicate filters for rooms and hotels.
  5. Higher-Order Functions: map transformations.
  6. Higher-Order Functions: reduce aggregations (revenue, rating, cheapest room).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, datetime
import pytest

from core.filters import (
    filter_hotels_by_location,
    filter_hotels_by_min_rating,
    filter_rooms_by_capacity,
    filter_rooms_by_price,
    is_room_in_price_range,
)
from core.pricing import (
    apply_discount,
    calculate_average_hotel_rating,
    calculate_nights,
    calculate_stay_quote,
    calculate_total_price,
    calculate_total_revenue,
    extract_hotel_names,
    find_cheapest_room,
    transform_rooms_with_multiplier,
)
from data.mock_db import (
    get_sample_bookings,
    get_sample_hotels,
    get_sample_rooms,
)
from domain.models import Booking, Hotel, Room


def test_domain_immutability() -> None:
    """Verifies that domain entities are strictly immutable."""
    room = Room(
        id="r_test",
        hotel_id="h_test",
        room_type="Standard",
        base_price=100.0,
        capacity=2,
        amenities=("WiFi", "AC"),
    )

    with pytest.raises(FrozenInstanceError):
        room.base_price = 150.0  # type: ignore

    hotel = Hotel(
        id="h_demo",
        name="Seaside Inn",
        location="Miami",
        rating=4.5,
        amenities=("WiFi", "Pool"),
        room_ids=("r_test",),
    )
    with pytest.raises(FrozenInstanceError):
        hotel.rating = 5.0  # type: ignore

    booking = Booking(
        id="b_demo",
        room_id="r_test",
        guest_name="Jane Doe",
        check_in=date(2026, 5, 1),
        check_out=date(2026, 5, 4),
        total_price=300.0,
        status="CONFIRMED",
    )
    with pytest.raises(FrozenInstanceError):
        booking.status = "CANCELLED"  # type: ignore


def test_calculate_nights_pure() -> None:
    """Tests date delta calculation for stay duration."""
    d1 = date(2026, 6, 1)
    d2 = date(2026, 6, 5)

    assert calculate_nights(d1, d2) == 4
    assert calculate_nights(d1, d1) == 0
    # Guard against negative nights if dates are reversed
    assert calculate_nights(d2, d1) == 0


def test_calculate_total_price_pure() -> None:
    """Tests total price with standard, peak, and low-season multipliers."""
    # Standard season (1.0)
    assert calculate_total_price(100.0, 3, seasonal_multiplier=1.0) == 300.0

    # Peak season (+25% -> 1.25)
    assert calculate_total_price(100.0, 3, seasonal_multiplier=1.25) == 375.0

    # Low season (-15% -> 0.85)
    assert calculate_total_price(120.0, 2, seasonal_multiplier=0.85) == 204.0

    # Edge cases
    assert calculate_total_price(100.0, 0, 1.25) == 0.0
    assert calculate_total_price(0.0, 5, 1.0) == 0.0


def test_apply_discount_and_stay_quote() -> None:
    """Tests pure percentage discount and complete stay quote calculation."""
    assert apply_discount(200.0, 10.0) == 180.0
    assert apply_discount(150.0, 0.0) == 150.0
    assert apply_discount(100.0, 100.0) == 0.0
    assert apply_discount(100.0, -10.0) == 100.0
    assert apply_discount(100.0, 150.0) == 0.0

    room = Room("r1", "h1", "Deluxe", 200.0, 2, ("WiFi",))
    quote = calculate_stay_quote(
        room,
        check_in=date(2026, 7, 1),
        check_out=date(2026, 7, 4),
        seasonal_multiplier=1.1,
        discount_percent=10.0,
    )
    # 3 nights * $200 * 1.1 = $660.0; -10% discount = $594.0
    assert quote == 594.0


def test_pure_filtering_functions() -> None:
    """Tests pure filtering of rooms and hotels without mutating input collections."""
    rooms = get_sample_rooms()
    original_count = len(rooms)

    filtered = filter_rooms_by_price(rooms, 100.0, 250.0)
    assert len(rooms) == original_count
    assert all(100.0 <= r.base_price <= 250.0 for r in filtered)
    assert len(filtered) == 3

    assert is_room_in_price_range(rooms[0], 200.0, 300.0) is True
    assert is_room_in_price_range(rooms[0], 50.0, 100.0) is False

    family_rooms = filter_rooms_by_capacity(rooms, min_capacity=4)
    assert len(family_rooms) == 2
    assert all(r.capacity >= 4 for r in family_rooms)

    hotels = get_sample_hotels()
    high_rated = filter_hotels_by_min_rating(hotels, min_rating=4.5)
    assert len(high_rated) == 2

    nice_hotels = filter_hotels_by_location(hotels, "Nice")
    assert len(nice_hotels) == 1
    assert nice_hotels[0].name == "Grand Azure Palace"


def test_map_transformations() -> None:
    """Tests map pipelines for projecting hotel names and adjusting room rates."""
    hotels = get_sample_hotels()
    names = extract_hotel_names(hotels)
    assert names == [
        "Grand Azure Palace",
        "Alpine Pine Retreat",
        "Lumiere City Center Hotel",
    ]

    rooms = get_sample_rooms()
    original_prices = [r.base_price for r in rooms]
    updated_rooms = transform_rooms_with_multiplier(rooms, 1.10)

    # Original rooms untouched
    assert [r.base_price for r in rooms] == original_prices
    # Updated prices increased by 10%
    for orig, updated in zip(rooms, updated_rooms):
        assert updated.base_price == round(orig.base_price * 1.10, 2)


def test_reduce_aggregations() -> None:
    """Tests reduce folding for total revenue, average ratings, and cheapest room."""
    bookings = get_sample_bookings()
    # Confirmed: b1 (880.0), b2 (650.0), b3 (170.0), b5 (870.0) = 2570.0; b4 is CANCELLED
    assert calculate_total_revenue(bookings) == 2570.0

    hotels = get_sample_hotels()
    # Ratings: 4.8, 4.6, 4.2 -> sum = 13.6 -> avg = 13.6 / 3 = 4.53
    assert calculate_average_hotel_rating(hotels) == 4.53

    rooms = get_sample_rooms()
    cheapest = find_cheapest_room(rooms)
    assert cheapest is not None
    assert cheapest.id == "r301"
    assert cheapest.base_price == 85.0
