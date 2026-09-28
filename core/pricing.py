"""Pricing Module: Pure calculation functions and map/reduce pipelines.

Coursework Lab 1: Pure transformation functions and map/reduce pipelines.
All functions in this module are strictly pure:
  1. Deterministic: the same inputs will ALWAYS produce the exact same output.
  2. Side-effect free: no mutation of parameters, no network/file I/O, no global state.
"""

from __future__ import annotations

from datetime import date
from functools import reduce
from typing import Callable, Iterable
from domain.models import Booking, Hotel, Room


def calculate_nights(check_in: date, check_out: date) -> int:
    """Calculate the number of nights between check-in and check-out dates.

    Duration is (check_out - check_in).days. If check_out is on or before
    check_in, returns 0 nights.

    Args:
        check_in: Guest arrival date.
        check_out: Guest departure date.

    Returns:
        Non-negative integer representing total stay nights.
    """
    delta_days = (check_out - check_in).days
    return max(0, delta_days)


def calculate_total_price(
    base_price: float,
    nights: int,
    seasonal_multiplier: float = 1.0,
) -> float:
    """Calculate the total price for a stay with a seasonal pricing multiplier.

    Formula: Total = base_price * nights * seasonal_multiplier

    Args:
        base_price: Nightly base rate for the room.
        nights: Number of nights.
        seasonal_multiplier: Factor reflecting demand/season (default 1.0).

    Returns:
        Total price rounded to two decimal places.
    """
    if nights <= 0 or base_price <= 0.0 or seasonal_multiplier < 0.0:
        return 0.0
    raw_total = base_price * float(nights) * float(seasonal_multiplier)
    return round(raw_total, 2)


def apply_discount(total_price: float, discount_percent: float) -> float:
    """Apply a percentage discount to an existing total price.

    Args:
        total_price: The baseline cost.
        discount_percent: Discount between 0 and 100 percent.

    Returns:
        Discounted total price rounded to 2 decimal places.
    """
    if total_price <= 0.0:
        return 0.0
    clamped_discount = max(0.0, min(100.0, discount_percent))
    discount_amount = total_price * (clamped_discount / 100.0)
    return round(total_price - discount_amount, 2)


def calculate_stay_quote(
    room: Room,
    check_in: date,
    check_out: date,
    seasonal_multiplier: float = 1.0,
    discount_percent: float = 0.0,
) -> float:
    """Calculate the complete stay quote for an immutable Room entity.

    Args:
        room: Immutable Room instance.
        check_in: Check-in date.
        check_out: Check-out date.
        seasonal_multiplier: Seasonal demand factor.
        discount_percent: Optional percentage discount.

    Returns:
        Total calculated quote for the reservation.
    """
    nights = calculate_nights(check_in, check_out)
    subtotal = calculate_total_price(room.base_price, nights, seasonal_multiplier)
    if discount_percent > 0.0:
        return apply_discount(subtotal, discount_percent)
    return subtotal


# ============================================================================
# MAP & REDUCE PIPELINES (LAB 1)
# ============================================================================


def extract_hotel_names(hotels: Iterable[Hotel]) -> list[str]:
    """Extract a list of hotel names using `map`.

    Args:
        hotels: Iterable of Hotel entities.

    Returns:
        List of hotel names.
    """
    return list(map(lambda h: h.name, hotels))


def transform_rooms_with_multiplier(
    rooms: Iterable[Room],
    multiplier: float,
) -> list[Room]:
    """Produce a new list of Room entities with prices adjusted by a multiplier.

    Demonstrates pure immutable transformation via `map`. Each Room is
    transformed into a brand new Room instance with updated `base_price`.
    The original Room instances remain completely unaltered.

    Args:
        rooms: Iterable of Room instances.
        multiplier: Price multiplier (e.g. 1.10 for +10%).

    Returns:
        New list of Room instances with updated prices.
    """
    transform_room: Callable[[Room], Room] = lambda r: Room(
        id=r.id,
        hotel_id=r.hotel_id,
        room_type=r.room_type,
        base_price=round(r.base_price * multiplier, 2),
        capacity=r.capacity,
        amenities=r.amenities,
    )
    return list(map(transform_room, rooms))


def calculate_total_revenue(bookings: Iterable[Booking]) -> float:
    """Calculate the sum of all confirmed booking total prices using `reduce`.

    Only takes into account bookings whose status is not 'CANCELLED'.

    Args:
        bookings: Iterable of Booking instances.

    Returns:
        Sum of revenue rounded to 2 decimal places.
    """
    confirmed_bookings = filter(lambda b: b.status.upper() != "CANCELLED", bookings)
    total = reduce(lambda acc, b: acc + b.total_price, confirmed_bookings, 0.0)
    return round(total, 2)


def calculate_average_hotel_rating(hotels: Iterable[Hotel]) -> float:
    """Compute the average rating across a collection of hotels using `reduce`.

    Args:
        hotels: Iterable of Hotel entities.

    Returns:
        Average rating (0.0 if empty), rounded to 2 decimal places.
    """
    hotel_list = list(hotels)
    if not hotel_list:
        return 0.0
    total_rating = reduce(lambda acc, h: acc + h.rating, hotel_list, 0.0)
    return round(total_rating / len(hotel_list), 2)


def find_cheapest_room(rooms: Iterable[Room]) -> Room | None:
    """Find the room with the lowest base price using `reduce`.

    Args:
        rooms: Iterable of Room entities.

    Returns:
        The Room with the lowest base_price, or None if empty.
    """
    room_list = list(rooms)
    if not room_list:
        return None
    return reduce(
        lambda cheapest, current: (
            current if current.base_price < cheapest.base_price else cheapest
        ),
        room_list,
    )
