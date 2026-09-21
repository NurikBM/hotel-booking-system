"""Terminal CLI Application: Hotel & Room Booking System.

Pure functional programming interactive demonstration runner.
Run this file in your terminal:
  $ python3 cli.py
"""

from __future__ import annotations

from datetime import date
import sys
import subprocess

from core.filters import (
    filter_hotels_by_location,
    filter_hotels_by_min_rating,
    filter_rooms_by_capacity,
    filter_rooms_by_price,
)
from core.fp_tools import (
    calculate_average_hotel_rating,
    calculate_total_revenue,
    extract_hotel_names,
    extract_unique_hotel_amenities,
    find_affordable_rooms,
    find_cheapest_room,
    transform_rooms_with_multiplier,
)
from core.pricing import (
    calculate_nights,
    calculate_stay_quote,
    calculate_total_price,
)
from data.mock_db import (
    get_sample_bookings,
    get_sample_hotels,
    get_sample_rooms,
)
from domain.models import Room


def print_header(title: str) -> None:
    """Print a visually distinct section header."""
    line = "=" * 64
    print(f"\n{line}")
    print(f" {title.upper()} ")
    print(f"{line}")


def show_hotels_and_rooms() -> None:
    """Display immutable domain data for Hotels and Rooms."""
    print_header("Domain Entities (Immutable Data)")
    hotels = get_sample_hotels()
    rooms = get_sample_rooms()

    print(f"Loaded {len(hotels)} Hotels and {len(rooms)} Rooms:\n")
    for hotel in hotels:
        print(f"🏨 [{hotel.id}] {hotel.name} ({hotel.location})")
        print(f"   Rating: {hotel.rating}/5.0 | Amenities: {', '.join(hotel.amenities)}")
        # Associated rooms
        hotel_rooms = [r for r in rooms if r.hotel_id == hotel.id]
        for r in hotel_rooms:
            print(
                f"   └─ 🛏️ [{r.id}] {r.room_type} | Rate: ${r.base_price:.2f}/night | "
                f"Cap: {r.capacity} | {', '.join(r.amenities)}"
            )
        print()


def demo_pricing_quote() -> None:
    """Demonstrate pure pricing calculations with seasonal multiplier."""
    print_header("Lab 1: Pure Pricing & Seasonal Multiplier Demo")
    rooms = get_sample_rooms()

    print("Available Rooms for Quote Calculation:")
    for idx, r in enumerate(rooms, 1):
        print(f"  {idx}. {r.room_type} (Base: ${r.base_price:.2f}/night)")

    try:
        choice = input("\nSelect a room number (1-6) [default 1]: ").strip()
        selected_idx = int(choice) - 1 if choice else 0
        room: Room = rooms[selected_idx] if 0 <= selected_idx < len(rooms) else rooms[0]

        nights_input = input("Enter number of nights [default 3]: ").strip()
        nights = int(nights_input) if nights_input else 3

        mult_input = input("Enter seasonal multiplier (e.g. 1.0=normal, 1.25=peak, 0.85=low) [default 1.20]: ").strip()
        multiplier = float(mult_input) if mult_input else 1.20

        total = calculate_total_price(room.base_price, nights, multiplier)

        print("\n--- Quote Breakdown (Pure Calculation) ---")
        print(f"Selected Room:       {room.room_type} ({room.id})")
        print(f"Nightly Base Rate:   ${room.base_price:.2f}")
        print(f"Stay Duration:       {nights} night(s)")
        print(f"Seasonal Factor:     {multiplier:.2f}x")
        print(f"Final Total Price:   ${total:.2f}")
    except ValueError as err:
        print(f"Invalid input: {err}. Please enter numeric values.")


def demo_filtering() -> None:
    """Demonstrate pure filtering of rooms and hotels."""
    print_header("Lab 1: Pure Filtering Pipelines")
    rooms = get_sample_rooms()

    print("Filtering Rooms by Price Range:")
    try:
        min_p = float(input("  Enter minimum nightly price [default 100.0]: ") or "100.0")
        max_p = float(input("  Enter maximum nightly price [default 250.0]: ") or "250.0")
    except ValueError:
        min_p, max_p = 100.0, 250.0

    filtered_rooms = filter_rooms_by_price(rooms, min_p, max_p)
    print(f"\nFound {len(filtered_rooms)} rooms matching ${min_p:.2f} - ${max_p:.2f}:")
    for r in filtered_rooms:
        print(f"  • [{r.id}] {r.room_type} @ ${r.base_price:.2f}/night (Capacity: {r.capacity})")

    try:
        cap_input = input("\nEnter minimum guest capacity (1-5) [default 2]: ").strip()
        min_cap = int(cap_input) if cap_input else 2
    except ValueError:
        min_cap = 2

    print(f"\nFiltering Rooms by Minimum Capacity (>= {min_cap} guests):")
    matching_capacity_rooms = filter_rooms_by_capacity(rooms, min_cap)
    if matching_capacity_rooms:
        for r in matching_capacity_rooms:
            print(f"  • [{r.id}] {r.room_type} @ ${r.base_price:.2f}/night (Capacity: {r.capacity})")
    else:
        print(f"  No rooms found with capacity >= {min_cap}.")


def demo_hof_pipelines() -> None:
    """Demonstrate map, filter, and reduce functional pipelines."""
    print_header("Lab 1: Map / Filter / Reduce Pipelines")
    hotels = get_sample_hotels()
    rooms = get_sample_rooms()
    bookings = get_sample_bookings()

    print("1. MAP PIPELINE: Extract Hotel Names")
    names = extract_hotel_names(hotels)
    print(f"   -> Result: {names}\n")

    print("2. MAP PIPELINE: Adjust Room Prices with Seasonal Surge (+15%)")
    surged_rooms = transform_rooms_with_multiplier(rooms[:3], 1.15)
    for orig, surged in zip(rooms[:3], surged_rooms):
        print(f"   Original: ${orig.base_price:.2f}  ──[x1.15 map]──>  Surged: ${surged.base_price:.2f}")
    print()

    print("3. REDUCE PIPELINE: Calculate Confirmed Total Booking Revenue")
    rev = calculate_total_revenue(bookings)
    print(f"   -> Active bookings revenue: ${rev:.2f} (Cancelled bookings excluded)\n")

    print("4. REDUCE PIPELINE: Average Hotel Rating")
    avg_rating = calculate_average_hotel_rating(hotels)
    print(f"   -> Average rating across all hotels: {avg_rating:.2f} / 5.0\n")

    print("5. REDUCE PIPELINE: Find Cheapest Available Room")
    cheapest = find_cheapest_room(rooms)
    if cheapest:
        print(f"   -> Lowest base rate: [{cheapest.id}] {cheapest.room_type} at ${cheapest.base_price:.2f}/night\n")

    print("6. MAP + REDUCE: Unique Hotel Amenities Set")
    amenities = extract_unique_hotel_amenities(hotels)
    print(f"   -> Unique Amenities: {', '.join(sorted(amenities))}")


def run_tests() -> None:
    """Execute pytest suite and display test results in terminal."""
    print_header("Running Lab 1 Test Suite")
    try:
        result = subprocess.run(
            ["pytest", "-v", "tests/test_labs.py"],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if result.returncode == 0:
            print("✅ All Lab 1 unit and functional tests passed successfully!")
        else:
            print(f"❌ Test run completed with return code {result.returncode}")
    except FileNotFoundError:
        # Fallback to python3 -m unittest
        print("pytest command not in PATH, falling back to python3 unittest module...")
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "tests"],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        print(result.stderr)


def main() -> None:
    """Main CLI interaction loop."""
    while True:
        print_header("Hotel & Room Booking System — CLI Runner")
        print("1. View Domain Entities (Hotels & Rooms)")
        print("2. Run Pricing Calculator (Seasonal Multiplier)")
        print("3. Run Room & Hotel Filter Pipelines")
        print("4. Run Map / Filter / Reduce Pipelines")
        print("5. Run Pytest Test Suite")
        print("6. Exit")

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == "1":
            show_hotels_and_rooms()
        elif choice == "2":
            demo_pricing_quote()
        elif choice == "3":
            demo_filtering()
        elif choice == "4":
            demo_hof_pipelines()
        elif choice == "5":
            run_tests()
        elif choice == "6":
            print("\nExiting application. Goodbye!\n")
            break
        else:
            print("\nInvalid choice. Please select an option between 1 and 6.")

        input("\nPress [Enter] to return to the menu...")


if __name__ == "__main__":
    main()
