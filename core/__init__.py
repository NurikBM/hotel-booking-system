"""Core Functional Programming Modules for Hotel Booking System.

Labs implemented:
- Lab 1: Immutable Domain Models & Transformations (core.domain, core.transforms)
- Lab 2: Closures, Lambdas & Recursion (core.transforms, core.recursion)
- Lab 3: Pure Memoization, Caching & Performance Benchmarking (core.memo)
"""

from core.domain import (
    Availability,
    Booking,
    CartItem,
    Event,
    Guest,
    Hotel,
    Payment,
    Price,
    RatePlan,
    RoomType,
    Rule,
)
from core.memo import (
    BenchmarkResult,
    CacheInfo,
    benchmark_speedup,
    memoize,
    memoized_nightly_sum,
    quote_offer,
    quote_offer_unmemoized,
)
from core.recursion import (
    BookingQuote,
    check_dates_available_rec,
    recursive_apply_rules,
    recursive_find_cheapest_quote,
    recursive_search_available_quotes,
)
from core.transforms import (
    apply_discount,
    by_capacity,
    by_city,
    by_features,
    by_price_range,
    calculate_cart_total,
    calculate_nights,
    generate_date_range,
    hold_item,
    load_seed,
    nightly_sum,
    remove_hold,
    sort_hotels_by_stars,
    sort_prices_by_amount,
    sort_rooms_by_capacity,
)

__all__ = [
    "Availability",
    "BenchmarkResult",
    "Booking",
    "BookingQuote",
    "CacheInfo",
    "CartItem",
    "Event",
    "Guest",
    "Hotel",
    "Payment",
    "Price",
    "RatePlan",
    "RoomType",
    "Rule",
    "apply_discount",
    "benchmark_speedup",
    "by_capacity",
    "by_city",
    "by_features",
    "by_price_range",
    "calculate_cart_total",
    "calculate_nights",
    "check_dates_available_rec",
    "generate_date_range",
    "hold_item",
    "load_seed",
    "memoize",
    "memoized_nightly_sum",
    "nightly_sum",
    "quote_offer",
    "quote_offer_unmemoized",
    "recursive_apply_rules",
    "recursive_find_cheapest_quote",
    "recursive_search_available_quotes",
    "remove_hold",
    "sort_hotels_by_stars",
    "sort_prices_by_amount",
    "sort_rooms_by_capacity",
]
