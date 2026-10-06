"""Terminal CLI Application: Hotel & Room Booking System.

Pure functional programming interactive demonstration runner (Labs 1, 2, and 3).
Run this file in your terminal:
  $ python3 cli.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

from core.domain import Rule
from core.memo import (
    benchmark_speedup,
    calculate_quote_with_loyalty,
    memoized_calculate_quote_with_loyalty,
    memoized_nightly_sum,
)
from core.recursion import (
    recursive_apply_rules,
    recursive_find_cheapest_quote,
    recursive_search_available_quotes,
)
from core.transforms import (
    by_capacity,
    by_city,
    load_seed,
    sort_hotels_by_stars,
)


def print_header(title: str) -> None:
    line = "=" * 64
    print(f"\n{line}")
    print(f" {title.upper()} ")
    print(f"{line}")


def format_cents(cents: int) -> str:
    return f"{cents / 100:,.2f} KZT"


def get_data():
    seed_path = os.path.join(os.path.dirname(__file__), "data", "seed.json")
    return load_seed(seed_path)


def show_seed_stats() -> None:
    print_header("1. Seed Dataset Statistics (Lab 1)")
    hotels, rooms, rates, prices, avails, guests = get_data()
    print(f"Hotels loaded:        {len(hotels)}")
    print(f"Room Types loaded:    {len(rooms)}")
    print(f"Rate Plans loaded:    {len(rates)}")
    print(f"Price records:        {len(prices)} (60-day calendar)")
    print(f"Availability slots:   {len(avails)}")
    print(f"Guests registered:    {len(guests)}")
    print("\nHotels Summary:")
    for h in hotels:
        print(
            f"  • [{'⭐' * h.stars}] {h.name} ({h.city}) | Features: {', '.join(h.features[:3])}"
        )


def show_closure_filters() -> None:
    print_header("2. Higher-Order Closures & Lambdas (Lab 2)")
    hotels, rooms, _, _, _, _ = get_data()

    print("Filter: by_city('Almaty')")
    almaty_hotels = tuple(filter(by_city("Almaty"), hotels))
    for h in almaty_hotels:
        print(f"  • {h.name} ({h.city})")

    print("\nFilter: by_capacity(3) on room types:")
    family_rooms = tuple(filter(by_capacity(3), rooms))
    for r in family_rooms[:5]:
        print(f"  • {r.name} (Cap: {r.capacity}, Beds: {r.beds})")

    print("\nLambda Sorting: sort_hotels_by_stars:")
    for h in sort_hotels_by_stars(hotels):
        print(f"  • {h.stars}★ {h.name}")


def show_recursive_search() -> None:
    print_header("3. Recursive Offer Search (Lab 2 Recursion)")
    hotels, rooms, rates, prices, avails, _ = get_data()

    city = "Almaty"
    cin = "2026-06-01"
    cout = "2026-06-05"
    guests = 2

    print(
        f"Searching available quotes recursively for {city}, {cin} to {cout}, {guests} guests..."
    )
    t0 = time.perf_counter()
    quotes = recursive_search_available_quotes(
        hotels, rooms, rates, prices, avails, city, cin, cout, guests
    )
    t_elapsed = (time.perf_counter() - t0) * 1000

    print(f"Found {len(quotes)} offers purely via recursion in {t_elapsed:.2f} ms:")
    cheapest = recursive_find_cheapest_quote(quotes)
    if cheapest:
        print("\n🏆 Cheapest Quote (Recursive Extremum):")
        print(f"   {cheapest.hotel.name} - {cheapest.room_type.name}")
        print(
            f"   Rate: {cheapest.rate_plan.name} | Total: {format_cents(cheapest.final_total)}"
        )

    for q in quotes[:3]:
        print(
            f"  • {q.hotel.name} | {q.room_type.name} | {format_cents(q.final_total)}"
        )


def show_recursive_rules() -> None:
    print_header("4. Recursive Business Rules Engine (Lab 2)")
    base_cents = 10000000  # 100,000 KZT

    rules = (
        Rule(id="rule_vip", kind="vip_discount", payload=(10,)),
        Rule(id="rule_early_bird", kind="early_bird", payload=(14, 500000)),
    )

    ctx = {"is_vip": True, "days_ahead": 30}
    final_cents = recursive_apply_rules(base_cents, rules, ctx)

    print(f"Base price:        {format_cents(base_cents)}")
    print("Applied rules:     VIP (10%) + Early Bird (5,000 KZT)")
    print(f"Final discounted:  {format_cents(final_cents)}")


def show_memoization_and_benchmark() -> None:
    print_header("5. Pure Memoization & Performance Benchmark (Lab 3)")
    _, _, rates, prices, _, _ = get_data()

    print("--- Part A: Testing memoized_nightly_sum cache hits ---")
    memoized_nightly_sum.cache_clear()
    rate_id = rates[0].id

    t0 = time.perf_counter()
    res1 = memoized_nightly_sum(prices, "2026-06-01", "2026-06-08", rate_id)
    t_miss = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    res2 = memoized_nightly_sum(prices, "2026-06-01", "2026-06-08", rate_id)
    t_hit = (time.perf_counter() - t1) * 1000

    info = memoized_nightly_sum.cache_info()
    print(f"Call 1 (Miss): {format_cents(res1)} in {t_miss:.4f} ms")
    print(f"Call 2 (Hit):  {format_cents(res2)} in {t_hit:.4f} ms")
    print(
        f"Cache status:  hits={info.hits}, misses={info.misses}, size={info.currsize}"
    )

    print("\n--- Part B: 300-Iteration Speedup Benchmark ---")
    queries = tuple(
        (
            1000000 + i * 500000,
            3 + (i % 4),
            1 + (i % 3),
            ("standard", "silver", "gold", "platinum")[i % 4],
        )
        for i in range(10)
    )

    bench = benchmark_speedup(
        unmemoized_fn=calculate_quote_with_loyalty,
        memoized_fn=memoized_calculate_quote_with_loyalty,
        queries=queries,
        repetitions=300,
    )

    print(f"Iterations:        {bench.iterations}")
    print(f"Unmemoized time:   {bench.unmemoized_time_sec * 1000:.2f} ms")
    print(f"Memoized time:     {bench.memoized_time_sec * 1000:.2f} ms")
    print(f"Speedup Factor:    {bench.speedup_factor:.1f}x faster!")
    print(
        f"Cache Hit Ratio:   {bench.cache_info.hit_ratio * 100:.1f}% ({bench.cache_info.hits} hits)"
    )


def run_tests() -> None:
    print_header("6. Running Test Suite (pytest tests/)")
    subprocess.run([sys.executable, "-m", "pytest", "-v", "tests/"], check=False)


def main() -> None:
    while True:
        print_header("Hotel FP System — Main Menu (Labs 1–3)")
        print("1. View Seed Dataset Statistics (Lab 1)")
        print("2. Closure-Based Filters & Lambdas (Lab 2)")
        print("3. Recursive Hierarchical Search (Lab 2)")
        print("4. Recursive Rules Engine (Lab 2)")
        print("5. Pure Memoization & Speedup Benchmark (Lab 3)")
        print("6. Run Automated Test Suite (pytest)")
        print("0. Exit")

        choice = input("\nSelect an option [0-6]: ").strip()
        if choice == "1":
            show_seed_stats()
        elif choice == "2":
            show_closure_filters()
        elif choice == "3":
            show_recursive_search()
        elif choice == "4":
            show_recursive_rules()
        elif choice == "5":
            show_memoization_and_benchmark()
        elif choice == "6":
            run_tests()
        elif choice == "0":
            print("\nExiting. Goodbye!\n")
            break
        else:
            print("Invalid selection. Try again.")


if __name__ == "__main__":
    main()
