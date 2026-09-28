"""Terminal CLI Application: Hotel & Room Booking System.

Pure functional programming interactive demonstration runner (Lab 1 & Lab 2).
Run this file in your terminal:
  $ python3 cli.py
"""

from __future__ import annotations

import subprocess
import sys

from core.filters import filter_rooms_by_capacity
from core.fp_tools import (
    make_amenity_filter,
    make_price_filter,
    recursive_aggregate_cities,
    recursive_aggregate_city,
    recursive_calculate_discount,
    recursive_find_cheapest_room,
    sort_rooms_by_price,
)
from data.mock_db import (
    get_sample_cities,
    get_sample_discount_tree,
    get_sample_hotels,
    get_sample_rooms,
)


def print_header(title: str) -> None:
    """Print a visually distinct section header."""
    line = "=" * 64
    print(f"\n{line}")
    print(f" {title.upper()} ")
    print(f"{line}")


def show_sample_data() -> None:
    """Display immutable domain data for Hotels and Rooms (Lab 1)."""
    print_header("1. Sample Data (Immutable Domain Entities)")
    hotels = get_sample_hotels()
    rooms = get_sample_rooms()

    print(f"Loaded {len(hotels)} Hotels and {len(rooms)} Rooms:\n")
    for hotel in hotels:
        print(f"🏨 [{hotel.id}] {hotel.name} ({hotel.location})")
        print(f"   Rating: {hotel.rating}/5.0 | Amenities: {', '.join(hotel.amenities)}")
        hotel_rooms = [r for r in rooms if r.hotel_id == hotel.id]
        for r in hotel_rooms:
            print(
                f"   └─ 🛏️ [{r.id}] {r.room_type} | Rate: ${r.base_price:.2f}/night | "
                f"Cap: {r.capacity} | {', '.join(r.amenities)}"
            )
        print()


def search_and_filter_rooms() -> None:
    """Filter rooms using Lab 1 & Lab 2 closure-based predicates."""
    print_header("2. Search & Filter Rooms (Closures & Predicates)")
    rooms = get_sample_rooms()

    print("Default rooms count:", len(rooms))
    min_p_input = input("Enter minimum price [default 100]: ").strip()
    min_p = float(min_p_input) if min_p_input else 100.0

    max_p_input = input("Enter maximum price [default 300]: ").strip()
    max_p = float(max_p_input) if max_p_input else 300.0

    amenity_input = input("Enter required amenity (e.g. Balcony, AC, WiFi) [default none]: ").strip()

    # 1. Apply closure price filter (Lab 2)
    price_filter_fn = make_price_filter(min_p, max_p)
    filtered = list(filter(price_filter_fn, rooms))

    # 2. Apply closure amenity filter if provided (Lab 2)
    if amenity_input:
        amenity_filter_fn = make_amenity_filter(amenity_input)
        filtered = list(filter(amenity_filter_fn, filtered))

    # 3. Sort results using pure lambda (Lab 2)
    sorted_filtered = sort_rooms_by_price(filtered, descending=False)

    print(f"\nMatched {len(sorted_filtered)} room(s):")
    for r in sorted_filtered:
        print(
            f" • [{r.id}] {r.room_type} — ${r.base_price:.2f}/night (Cap: {r.capacity}) "
            f"Amenities: {', '.join(r.amenities)}"
        )


def demo_recursive_algorithms() -> None:
    """Demonstrate recursive algorithms on hierarchical structures (Lab 2)."""
    print_header("3. Recursive Algorithms Demo (Lab 2)")
    cities = get_sample_cities()

    # Recursive Algorithm 1: Aggregation
    print("--- Algorithm 1: Recursive City Hierarchy Aggregation ---")
    for city in cities:
        agg = recursive_aggregate_city(city)
        print(f"🏙️  City: {city.name:10s} -> Rooms: {agg['room_count']}, Total Capacity: {agg['total_capacity']} guests")

    all_agg = recursive_aggregate_cities(cities)
    print(f"\n🌐 All Cities Total -> Rooms: {all_agg['room_count']}, Total Capacity: {all_agg['total_capacity']} guests")

    # Recursive Algorithm 2: Recursive Search & Nested Discount Parsing
    print("\n--- Algorithm 2: Recursive Search & Nested Discount Parsing ---")
    cheapest = recursive_find_cheapest_room(cities)
    if cheapest:
        print(f"🔍 Cheapest Room found recursively across all cities: [{cheapest.id}] {cheapest.room_type} at ${cheapest.base_price:.2f}/night")

    discount_tree = get_sample_discount_tree()
    base_price = 1000.0
    discounted = recursive_calculate_discount(base_price, discount_tree)
    print(f"🏷️  Nested Discount Tree Evaluation: Base ${base_price:.2f} -> Final ${discounted:.2f}")


def run_pytest() -> None:
    """Run pytest suite for Lab 1 and Lab 2."""
    print_header("4. Running Pytest Suite (tests/test_lab1.py & tests/test_lab2.py)")
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "tests/test_lab1.py", "tests/test_lab2.py"],
            capture_output=True,
            text=True,
        )
        print(res.stdout)
        if res.stderr:
            print(res.stderr)
        if res.returncode == 0:
            print("✅ All unit and functional tests passed successfully!")
        else:
            print("❌ Some tests failed.")
    except Exception as exc:
        print(f"Error running pytest: {exc}")


def main_menu() -> None:
    """Terminal interactive menu loop."""
    while True:
        print_header("Hotel & Room Booking System (Lab 1 & Lab 2)")
        print("1. Load sample data")
        print("2. Search/filter rooms")
        print("3. Recursive aggregation demo")
        print("4. Run pytest")
        print("0. Exit")

        try:
            choice = input("\nEnter choice [0-4]: ").strip()
        except EOFError:
            break

        if choice == "1":
            show_sample_data()
        elif choice == "2":
            search_and_filter_rooms()
        elif choice == "3":
            demo_recursive_algorithms()
        elif choice == "4":
            run_pytest()
        elif choice == "0":
            print("\nExiting. Goodbye!")
            break
        else:
            print("\nInvalid choice. Please select an option between 0 and 4.")


if __name__ == "__main__":
    main_menu()
