"""Unit & Functional Tests: Lab 2 — Closures, Lambdas, and Recursion.

Tests verify:
  1. Closure-based filter factories (`make_price_filter`, `make_amenity_filter`).
  2. Lambdas used for sorting and transformations.
  3. Recursive Algorithm 1: Hierarchical aggregation of City -> Hotels -> Rooms.
  4. Recursive Algorithm 2: Recursive search for cheapest room in hierarchy.
  5. Recursive Algorithm 2: Recursive parsing and calculation of nested discount structures.
"""

from __future__ import annotations

from core.fp_tools import (
    make_amenity_filter,
    make_price_filter,
    recursive_aggregate_cities,
    recursive_aggregate_city,
    recursive_calculate_discount,
    recursive_count_rooms,
    recursive_find_cheapest_room,
    recursive_sum_capacity,
    sort_hotels_by_rating,
    sort_rooms_by_price,
)
from data.mock_db import (
    get_sample_cities,
    get_sample_discount_tree,
    get_sample_hotels,
    get_sample_rooms,
)
from domain.models import City, DiscountNode, HotelNode, Room


def test_closure_make_price_filter() -> None:
    """Verifies make_price_filter produces a pure predicate closure."""
    rooms = get_sample_rooms()

    # Create two distinct closures with their own lexical scopes
    budget_filter = make_price_filter(50.0, 150.0)
    luxury_filter = make_price_filter(250.0, 600.0)

    budget_rooms = list(filter(budget_filter, rooms))
    luxury_rooms = list(filter(luxury_filter, rooms))

    assert len(budget_rooms) == 3
    assert all(50.0 <= r.base_price <= 150.0 for r in budget_rooms)

    assert len(luxury_rooms) == 2
    assert all(250.0 <= r.base_price <= 600.0 for r in luxury_rooms)


def test_closure_make_amenity_filter() -> None:
    """Verifies make_amenity_filter produces an amenity-checking closure."""
    rooms = get_sample_rooms()

    balcony_filter = make_amenity_filter("Balcony")
    fireplace_filter = make_amenity_filter("fireplace")  # Case-insensitive

    balcony_rooms = list(filter(balcony_filter, rooms))
    fireplace_rooms = list(filter(fireplace_filter, rooms))

    assert len(balcony_rooms) == 3
    assert all("Balcony" in r.amenities for r in balcony_rooms)

    assert len(fireplace_rooms) == 1
    assert fireplace_rooms[0].id == "r202"


def test_lambdas_in_sorting() -> None:
    """Verifies sorting functions utilizing lambda key extractors."""
    rooms = get_sample_rooms()
    sorted_asc = sort_rooms_by_price(rooms, descending=False)
    sorted_desc = sort_rooms_by_price(rooms, descending=True)

    assert sorted_asc[0].base_price <= sorted_asc[1].base_price
    assert sorted_asc[0].id == "r301"  # $85.0
    assert sorted_desc[0].id == "r102"  # $550.0

    hotels = get_sample_hotels()
    sorted_hotels = sort_hotels_by_rating(hotels, descending=True)
    assert sorted_hotels[0].rating == 4.8
    assert sorted_hotels[-1].rating == 4.2


def test_recursive_count_rooms_and_capacity() -> None:
    """Verifies recursive counting of rooms and capacity across hierarchical nodes."""
    # Base case: empty
    assert recursive_count_rooms(()) == 0
    assert recursive_sum_capacity(()) == 0

    # Single Room node
    single_room = Room("r_demo", "h_demo", "Standard", 100.0, 3, ("WiFi",))
    assert recursive_count_rooms(single_room) == 1
    assert recursive_sum_capacity(single_room) == 3

    # HotelNode
    hotel_node = HotelNode(
        id="h_demo",
        name="Demo Inn",
        rating=4.5,
        rooms=(single_room, Room("r_demo2", "h_demo", "Suite", 200.0, 4, ())),
    )
    assert recursive_count_rooms(hotel_node) == 2
    assert recursive_sum_capacity(hotel_node) == 7


def test_recursive_aggregate_city_and_cities() -> None:
    """Verifies recursive aggregation of entire City and multi-city structures."""
    cities = get_sample_cities()
    # City 1: Nice (1 hotel, 2 rooms, capacities 2 + 4 = 6)
    nice_agg = recursive_aggregate_city(cities[0])
    assert nice_agg["room_count"] == 2
    assert nice_agg["total_capacity"] == 6

    # Multi-city aggregation: 3 cities * 2 rooms each = 6 rooms total
    # Capacities: Nice (2+4=6), Chamonix (2+5=7), Paris (1+2=3) -> Total = 16
    all_cities_agg = recursive_aggregate_cities(cities)
    assert all_cities_agg["room_count"] == 6
    assert all_cities_agg["total_capacity"] == 16


def test_recursive_find_cheapest_room() -> None:
    """Verifies recursive search for the cheapest room across nested structures."""
    cities = get_sample_cities()

    # Search in empty node -> None
    assert recursive_find_cheapest_room(()) is None

    # Search in City 1 (Nice: r101 $220, r102 $550) -> r101 ($220)
    cheapest_nice = recursive_find_cheapest_room(cities[0])
    assert cheapest_nice is not None
    assert cheapest_nice.id == "r101"
    assert cheapest_nice.base_price == 220.0

    # Search across all cities (Paris has r301 at $85.0)
    cheapest_overall = recursive_find_cheapest_room(cities)
    assert cheapest_overall is not None
    assert cheapest_overall.id == "r301"
    assert cheapest_overall.base_price == 85.0


def test_recursive_calculate_discount() -> None:
    """Verifies recursive evaluation of nested discount trees without loops."""
    # Base case: flat discount without sub-discounts
    simple_discount = DiscountNode(name="Flat 10%", percentage=10.0)
    assert recursive_calculate_discount(200.0, simple_discount) == 180.0

    # Nested tree:
    # Top: 10% on $1000 -> $900.0
    # Sub 1: 5% on $900 -> $855.0
    # Sub 2: 2% on $855 -> $837.90
    discount_tree = get_sample_discount_tree()
    discounted_price = recursive_calculate_discount(1000.0, discount_tree)
    assert discounted_price == 837.90
