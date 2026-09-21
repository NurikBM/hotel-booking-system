"""Filters Module: Pure predicate functions and room/hotel filtering.

Coursework Lab 1: Pure filtering transformations.
In pure functional programming, filtering creates a new collection containing
only items that satisfy a boolean predicate function `f(x) -> bool`,
leaving the original collections completely untouched and unmodified.
"""

from __future__ import annotations

from typing import Callable, Iterable
from domain.models import Hotel, Room


def is_room_in_price_range(room: Room, min_price: float, max_price: float) -> bool:
    """Predicate to check if a room's base price falls within [min_price, max_price].

    OVERVIEW:
    A pure boolean predicate function. Returns True if room.base_price is
    between min_price and max_price (inclusive).

    Args:
        room: Immutable Room instance.
        min_price: Minimum nightly price boundary.
        max_price: Maximum nightly price boundary.

    Returns:
        Boolean indicating if room matches the price range.
    """
    return min_price <= room.base_price <= max_price


def filter_rooms_by_price(
    rooms: Iterable[Room],
    min_price: float,
    max_price: float,
) -> list[Room]:
    """Filter a collection of rooms by a price range.

    OVERVIEW:
    Uses Python's built-in `filter` higher-order function with a pure lambda
    or predicate function, returning a new list without mutating the original input.

    Args:
        rooms: Sequence of Room instances.
        min_price: Lower bound price.
        max_price: Upper bound price.

    Returns:
        New list of Room instances matching the criteria.
    """
    predicate: Callable[[Room], bool] = lambda r: is_room_in_price_range(
        r, min_price, max_price
    )
    return list(filter(predicate, rooms))


def filter_rooms_by_capacity(
    rooms: Iterable[Room],
    min_capacity: int,
) -> list[Room]:
    """Filter rooms that can accommodate at least `min_capacity` guests.

    Args:
        rooms: Sequence of Room instances.
        min_capacity: Required guest capacity.

    Returns:
        New list of matching Room instances.
    """
    return list(filter(lambda r: r.capacity >= min_capacity, rooms))


def filter_hotels_by_min_rating(
    hotels: Iterable[Hotel],
    min_rating: float,
) -> list[Hotel]:
    """Filter hotels that meet or exceed a minimum rating threshold.

    OVERVIEW:
    Pure higher-order filter pipeline:
      hotels -> filter(lambda h: h.rating >= min_rating) -> list[Hotel]

    Args:
        hotels: Sequence of Hotel instances.
        min_rating: Minimum acceptable star rating (e.g. 4.0).

    Returns:
        New list of high-rated Hotel instances.
    """
    return list(filter(lambda h: h.rating >= min_rating, hotels))


def filter_hotels_by_location(
    hotels: Iterable[Hotel],
    target_location: str,
) -> list[Hotel]:
    """Filter hotels situated in a specific city or region (case-insensitive).

    Args:
        hotels: Sequence of Hotel instances.
        target_location: Name of the location to match.

    Returns:
        New list of Hotel instances in that location.
    """
    normalized_target = target_location.strip().lower()
    return list(
        filter(
            lambda h: h.location.strip().lower() == normalized_target,
            hotels,
        )
    )
