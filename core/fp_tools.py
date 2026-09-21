"""Functional Programming Tools & Pipelines: map, filter, reduce.

Coursework Lab 1: Higher-Order Functions (HOF) & Functional Pipelines.
Demonstrates:
  1. `map` to project or transform data structures immutably.
  2. `filter` to selectively filter elements based on pure predicates.
  3. `reduce` (from functools) to aggregate collections down to a single value
     (such as calculating total revenue or finding extreme values).
"""

from __future__ import annotations

from functools import reduce
from typing import Any, Callable, Iterable, TypeVar
from domain.models import Booking, Hotel, Room

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


def compose(f: Callable[[U], V], g: Callable[[T], U]) -> Callable[[T], V]:
    """Compose two unary functions: (f ∘ g)(x) = f(g(x)).

    OVERVIEW:
    Mathematical function composition. Takes functions f and g,
    and produces a new function that applies g first, then f to the result.
    """
    return lambda x: f(g(x))


# ============================================================================
# MAP PIPELINES
# ============================================================================


def extract_hotel_names(hotels: Iterable[Hotel]) -> list[str]:
    """Extract a list of hotel names using `map`.

    OVERVIEW:
    Demonstrates `map`: projects each Hotel entity to its string `name`
    attribute without modifying any Hotel entity.

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

    OVERVIEW:
    Demonstrates pure immutable transformation via `map`. Each Room is
    transformed into a brand NEW Room instance with updated `base_price`.
    The original Room instances remain completely unaltered.

    Args:
        rooms: Iterable of Room instances.
        multiplier: Price multiplier (e.g. 1.10 for +10%).

    Returns:
        New list of Room instances with new prices.
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


def extract_unique_hotel_amenities(hotels: Iterable[Hotel]) -> set[str]:
    """Aggregate all distinct amenities across all hotels.

    OVERVIEW:
    Functional pipeline combining `map` and `reduce` (union of sets).
    Each hotel's amenities tuple is mapped to a set, then folded with `reduce`.
    """
    amenity_sets = map(lambda h: set(h.amenities), hotels)
    return reduce(lambda acc, current: acc | current, amenity_sets, set())


# ============================================================================
# FILTER PIPELINES
# ============================================================================


def find_affordable_rooms(rooms: Iterable[Room], max_budget: float) -> list[Room]:
    """Filter rooms whose nightly base price does not exceed `max_budget`.

    OVERVIEW:
    Demonstrates `filter` with a pure predicate lambda `r.base_price <= max_budget`.
    """
    return list(filter(lambda r: r.base_price <= max_budget, rooms))


def find_rooms_by_type(rooms: Iterable[Room], target_type: str) -> list[Room]:
    """Filter rooms matching a specific room type (e.g. 'Suite', 'Deluxe').

    OVERVIEW:
    Pure predicate filter comparing normalized room types.
    """
    normalized = target_type.strip().lower()
    return list(filter(lambda r: r.room_type.strip().lower() == normalized, rooms))


# ============================================================================
# REDUCE PIPELINES
# ============================================================================


def calculate_total_revenue(bookings: Iterable[Booking]) -> float:
    """Calculate the sum of all confirmed booking total prices using `reduce`.

    OVERVIEW:
    Demonstrates `reduce`:
      accumulates (accumulator + booking.total_price) starting from 0.0.
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

    OVERVIEW:
    Demonstrates `reduce` by accumulating ratings:
      sum_ratings = reduce(lambda acc, h: acc + h.rating, hotels, 0.0)
      average = sum_ratings / count

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

    OVERVIEW:
    Demonstrates folding a collection to find the extremum (minimum element)
    purely through `reduce` without stateful external variables.

    Args:
        rooms: Iterable of Room entities.

    Returns:
        The Room with the lowest base_price, or None if the collection is empty.
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
