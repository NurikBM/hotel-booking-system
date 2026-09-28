"""Functional Programming Tools: Closures, Lambdas, and Recursive Algorithms.

Coursework Lab 2:
  1. Closure-based filter factories (`make_price_filter`, `make_amenity_filter`).
  2. Lambdas for sorting and transformations.
  3. Recursive Algorithm 1: Aggregation of City -> Hotels -> Rooms hierarchical structure.
  4. Recursive Algorithm 2: Recursive search / nested discount parsing.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable
from core.filters import is_room_in_price_range
from core.pricing import apply_discount
from domain.models import City, DiscountNode, Hotel, HotelNode, Room


# ============================================================================
# 1. CLOSURES & FUNCTION FACTORIES (LAB 2)
# ============================================================================


def make_price_filter(min_p: float, max_p: float) -> Callable[[Room], bool]:
    """Create a closure-based room filter by price range.

    The returned function captures `min_p` and `max_p` in its closure scope
    and reuses the pure `is_room_in_price_range` predicate from Lab 1.

    Args:
        min_p: Minimum allowable room base price.
        max_p: Maximum allowable room base price.

    Returns:
        Predicate function `Room -> bool`.
    """

    def price_filter(room: Room) -> bool:
        return is_room_in_price_range(room, min_p, max_p)

    return price_filter


def make_amenity_filter(required: str) -> Callable[[Room], bool]:
    """Create a closure-based room filter checking for a required amenity.

    The returned predicate captures normalized `required` in its closure scope
    and checks membership against the room's immutable amenities tuple.

    Args:
        required: Name of the amenity (case-insensitive).

    Returns:
        Predicate function `Room -> bool`.
    """
    normalized_target = required.strip().lower()

    def amenity_filter(room: Room) -> bool:
        return any(a.strip().lower() == normalized_target for a in room.amenities)

    return amenity_filter


# ============================================================================
# 2. LAMBDAS IN PIPELINES (LAB 2)
# ============================================================================


def sort_rooms_by_price(
    rooms: Iterable[Room],
    descending: bool = False,
) -> list[Room]:
    """Sort rooms using a pure lambda key extractor.

    Args:
        rooms: Sequence of Room instances.
        descending: True for highest-to-lowest price order.

    Returns:
        New sorted list of Room instances.
    """
    return sorted(rooms, key=lambda r: r.base_price, reverse=descending)


def sort_hotels_by_rating(
    hotels: Iterable[Hotel],
    descending: bool = True,
) -> list[Hotel]:
    """Sort hotels using a pure lambda key extractor.

    Args:
        hotels: Sequence of Hotel instances.
        descending: True for highest-to-lowest rating order.

    Returns:
        New sorted list of Hotel instances.
    """
    return sorted(hotels, key=lambda h: h.rating, reverse=descending)


# ============================================================================
# 3. RECURSIVE ALGORITHM 1: HIERARCHY AGGREGATION (LAB 2)
# ============================================================================


def recursive_count_rooms(node: City | HotelNode | tuple[Any, ...]) -> int:
    """Recursively count total rooms in a City -> Hotels -> Rooms structure.

    Recursion Idea:
      - Base case 1: empty tuple or None -> 0.
      - Base case 2: single Room instance -> 1.
      - Recursive step:
        - If City: delegate to node.hotels.
        - If HotelNode: delegate to node.rooms.
        - If tuple: count of first element + recursive count of remaining elements (tail).
    """
    if not node:
        return 0
    if isinstance(node, Room):
        return 1
    if isinstance(node, HotelNode):
        return recursive_count_rooms(node.rooms)
    if isinstance(node, City):
        return recursive_count_rooms(node.hotels)
    if isinstance(node, tuple):
        # Base case for empty tail handled automatically
        return recursive_count_rooms(node[0]) + recursive_count_rooms(node[1:])
    return 0


def recursive_sum_capacity(node: City | HotelNode | tuple[Any, ...]) -> int:
    """Recursively sum total guest capacity in a City -> Hotels -> Rooms structure.

    Recursion Idea:
      - Base case 1: empty tuple or None -> 0.
      - Base case 2: single Room instance -> room.capacity.
      - Recursive step:
        - If City: delegate to node.hotels.
        - If HotelNode: delegate to node.rooms.
        - If tuple: capacity of first element + recursive sum of remaining elements (tail).
    """
    if not node:
        return 0
    if isinstance(node, Room):
        return node.capacity
    if isinstance(node, HotelNode):
        return recursive_sum_capacity(node.rooms)
    if isinstance(node, City):
        return recursive_sum_capacity(node.hotels)
    if isinstance(node, tuple):
        return recursive_sum_capacity(node[0]) + recursive_sum_capacity(node[1:])
    return 0


def recursive_aggregate_city(city: City) -> dict[str, int]:
    """Recursively aggregate metrics (room count, total guest capacity) for a City.

    Evaluates the City -> Hotels -> Rooms tree without iterative loops.
    """
    return {
        "room_count": recursive_count_rooms(city),
        "total_capacity": recursive_sum_capacity(city),
    }


def recursive_aggregate_cities(cities: tuple[City, ...]) -> dict[str, int]:
    """Recursively aggregate metrics across multiple City nodes.

    Recursion Idea:
      - Base case: empty tuple of cities -> 0 rooms, 0 capacity.
      - Recursive step: aggregate first city + recursively aggregate remaining cities.
    """
    if not cities:
        return {"room_count": 0, "total_capacity": 0}

    first_city_agg = recursive_aggregate_city(cities[0])
    rest_agg = recursive_aggregate_cities(cities[1:])

    return {
        "room_count": first_city_agg["room_count"] + rest_agg["room_count"],
        "total_capacity": first_city_agg["total_capacity"] + rest_agg["total_capacity"],
    }


# ============================================================================
# 4. RECURSIVE ALGORITHM 2: HIERARCHY SEARCH & DISCOUNT PARSING (LAB 2)
# ============================================================================


def recursive_find_cheapest_room(
    node: City | HotelNode | tuple[Any, ...],
) -> Room | None:
    """Recursively search for the room with lowest base price in a tree structure.

    Recursion Idea:
      - Base case 1: empty tuple or None -> None.
      - Base case 2: single Room instance -> return the room.
      - Recursive step:
        - If City: delegate to node.hotels.
        - If HotelNode: delegate to node.rooms.
        - If tuple: find cheapest in head (node[0]) and cheapest in tail (node[1:]),
          then return the one with smaller base_price.
    """
    if not node:
        return None
    if isinstance(node, Room):
        return node
    if isinstance(node, HotelNode):
        return recursive_find_cheapest_room(node.rooms)
    if isinstance(node, City):
        return recursive_find_cheapest_room(node.hotels)
    if isinstance(node, tuple):
        first = recursive_find_cheapest_room(node[0])
        rest = recursive_find_cheapest_room(node[1:])
        if first is None:
            return rest
        if rest is None:
            return first
        return first if first.base_price <= rest.base_price else rest
    return None


def recursive_calculate_discount(
    base_price: float,
    discount: DiscountNode,
) -> float:
    """Recursively parse and apply a nested discount hierarchy.

    Reuses Lab 1 pure `apply_discount` without mutating data or using loops.

    Recursion Idea:
      - Base case: discount has no sub_discounts -> apply discount.percentage.
      - Recursive step: apply current discount, then fold through sub_discounts recursively.
    """
    current_price = apply_discount(base_price, discount.percentage)
    if not discount.sub_discounts:
        return current_price

    def _apply_sub_discounts(
        price: float,
        subs: tuple[DiscountNode, ...],
    ) -> float:
        if not subs:
            return price
        # Recurse on head sub_discount, then pass result to remaining sub_discounts
        new_price = recursive_calculate_discount(price, subs[0])
        return _apply_sub_discounts(new_price, subs[1:])

    return _apply_sub_discounts(current_price, discount.sub_discounts)
