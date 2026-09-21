"""Unit & Functional Tests: Lab 1 — Pure Functions, Immutability, and HOF.

Tests cover:
  1. Immutability of domain entities (frozen dataclass guarantees).
  2. Pure transformation functions (nights, pricing with seasonal multipliers, quotes).
  3. Pure filtering predicates and functions.
  4. Higher-order function (HOF) pipelines: map, filter, and reduce.
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
from core.fp_tools import (
    calculate_average_hotel_rating,
    calculate_total_revenue,
    compose,
    extract_hotel_names,
    extract_unique_hotel_amenities,
    find_affordable_rooms,
    find_cheapest_room,
    find_rooms_by_type,
    transform_rooms_with_multiplier,
)
from core.pricing import (
    apply_discount,
    calculate_nights,
    calculate_stay_quote,
    calculate_total_price,
)
from data.mock_db import (
    SAMPLE_BOOKINGS,
    SAMPLE_HOTELS,
    SAMPLE_ROOMS,
    get_sample_bookings,
    get_sample_hotels,
    get_sample_rooms,
)
from domain.models import Booking, Hotel, Review, Room


# ============================================================================
# LAB 1: IMMUTABILITY TESTS
# ============================================================================


def test_domain_entity_immutability() -> None:
    """Verifies that domain entities are strictly immutable and cannot be mutated."""
    room = Room(
        id="r_test",
        hotel_id="h_test",
        room_type="Standard",
        base_price=100.0,
        capacity=2,
        amenities=("WiFi", "AC"),
    )

    # Attempting to reassign an attribute must raise FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        room.base_price = 150.0  # type: ignore

    with pytest.raises(FrozenInstanceError):
        room.room_type = "Deluxe"  # type: ignore

    # Nested collection is a tuple and cannot be appended to
    assert isinstance(room.amenities, tuple)


def test_hotel_and_booking_immutability() -> None:
    """Verifies Hotel and Booking frozen dataclass enforcement."""
    hotel = Hotel(
        id="h_demo",
        name="Seaside Inn",
        location="Miami",
        rating=4.5,
        amenities=["WiFi", "Pool"],
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


# ============================================================================
# LAB 1: PURE TRANSFORMATION FUNCTIONS (PRICING & NIGHTS)
# ============================================================================


def test_calculate_nights_pure_transformation() -> None:
    """Tests date delta calculation for stay duration."""
    d1 = date(2026, 6, 1)
    d2 = date(2026, 6, 5)

    assert calculate_nights(d1, d2) == 4
    assert calculate_nights(d1, d1) == 0
    # Guard against negative nights if dates are reversed
    assert calculate_nights(d2, d1) == 0


def test_calculate_total_price_with_seasonal_multiplier() -> None:
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


def test_apply_discount_pure() -> None:
    """Tests pure percentage discount calculation."""
    assert apply_discount(200.0, 10.0) == 180.0
    assert apply_discount(150.0, 0.0) == 150.0
    assert apply_discount(100.0, 100.0) == 0.0
    # Clamping negative and over-100 values
    assert apply_discount(100.0, -10.0) == 100.0
    assert apply_discount(100.0, 150.0) == 0.0


def test_calculate_stay_quote_integration() -> None:
    """Tests end-to-end stay quote calculation for an immutable Room."""
    room = Room("r1", "h1", "Deluxe", 200.0, 2, ("WiFi",))
    quote = calculate_stay_quote(
        room,
        check_in=date(2026, 7, 1),
        check_out=date(2026, 7, 4),
        seasonal_multiplier=1.1,
    )
    # 3 nights * $200 * 1.1 = $660.0
    assert quote == 660.0


# ============================================================================
# LAB 1: PURE FILTERING FUNCTIONS
# ============================================================================


def test_filter_rooms_by_price() -> None:
    """Tests pure filtering of rooms by price range without mutating inputs."""
    rooms = get_sample_rooms()
    original_count = len(rooms)

    # Filter between $100 and $250
    filtered = filter_rooms_by_price(rooms, 100.0, 250.0)

    # Input list remains unaltered
    assert len(rooms) == original_count
    # Verify every returned room is strictly within range
    assert all(100.0 <= r.base_price <= 250.0 for r in filtered)
    assert len(filtered) == 3


def test_filter_rooms_by_capacity_and_type() -> None:
    """Tests filtering by guest capacity and room type."""
    rooms = get_sample_rooms()

    family_rooms = filter_rooms_by_capacity(rooms, min_capacity=4)
    assert len(family_rooms) == 2
    assert all(r.capacity >= 4 for r in family_rooms)

    chalets = find_rooms_by_type(rooms, "Standard Mountain Chalet")
    assert len(chalets) == 1
    assert chalets[0].id == "r201"


def test_filter_hotels_by_rating_and_location() -> None:
    """Tests pure filtering of hotels by rating and location."""
    hotels = get_sample_hotels()

    high_rated = filter_hotels_by_min_rating(hotels, min_rating=4.5)
    assert len(high_rated) == 2
    assert all(h.rating >= 4.5 for h in high_rated)

    nice_hotels = filter_hotels_by_location(hotels, "Nice")
    assert len(nice_hotels) == 1
    assert nice_hotels[0].name == "Grand Azure Palace"


# ============================================================================
# LAB 1: HIGHER-ORDER FUNCTION (HOF) PIPELINES (MAP, FILTER, REDUCE)
# ============================================================================


def test_map_extract_hotel_names() -> None:
    """Tests using `map` to project hotels to their names."""
    hotels = get_sample_hotels()
    names = extract_hotel_names(hotels)

    assert names == [
        "Grand Azure Palace",
        "Alpine Pine Retreat",
        "Lumiere City Center Hotel",
    ]


def test_map_transform_rooms_with_multiplier() -> None:
    """Tests using `map` to create new Room instances with updated prices."""
    rooms = get_sample_rooms()
    original_prices = [r.base_price for r in rooms]

    # Apply 10% increase (multiplier 1.1)
    updated_rooms = transform_rooms_with_multiplier(rooms, 1.1)

    # Original rooms untouched
    assert [r.base_price for r in rooms] == original_prices
    # Updated rooms reflect the 10% increase
    for orig, updated in zip(rooms, updated_rooms):
        assert updated.base_price == round(orig.base_price * 1.1, 2)
        assert updated.id == orig.id


def test_reduce_calculate_total_revenue() -> None:
    """Tests using `reduce` to aggregate total revenue from confirmed bookings."""
    bookings = get_sample_bookings()

    # Confirmed bookings:
    # b1: 880.0
    # b2: 650.0
    # b3: 170.0
    # b4: 1650.0 (CANCELLED -> excluded)
    # b5: 870.0
    # Total = 880 + 650 + 170 + 870 = 2570.0
    revenue = calculate_total_revenue(bookings)
    assert revenue == 2570.0


def test_reduce_calculate_average_hotel_rating() -> None:
    """Tests using `reduce` to compute average hotel rating."""
    hotels = get_sample_hotels()
    # Ratings: 4.8, 4.6, 4.2 -> sum = 13.6 -> avg = 13.6 / 3 = 4.53
    avg = calculate_average_hotel_rating(hotels)
    assert avg == 4.53


def test_reduce_find_cheapest_room() -> None:
    """Tests using `reduce` to fold over a collection and locate the cheapest room."""
    rooms = get_sample_rooms()
    cheapest = find_cheapest_room(rooms)

    assert cheapest is not None
    assert cheapest.id == "r301"
    assert cheapest.base_price == 85.0


def test_function_composition() -> None:
    """Tests the pure function composition utility `compose(f, g)`."""
    # compose f(x) = x * 1.1 and g(x) = x - 20
    add_fee = lambda x: x + 25.0
    apply_tax = lambda x: round(x * 1.15, 2)

    fee_then_tax = compose(apply_tax, add_fee)
    # (100 + 25) * 1.15 = 143.75
    assert fee_then_tax(100.0) == 143.75
