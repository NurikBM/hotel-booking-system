"""Pure Functional Memoization & Cache Optimization Engine.

Coursework Lab 3:
  1. `memoize`: Higher-order function & decorator for pure function caching with
     configurable cache capacity, LRU/FIFO eviction, and detailed metrics.
  2. Cache Introspection: `cache_info()` returning hits, misses, maxsize, currsize, hit_ratio.
  3. `cache_clear()`: Pure cache reset capability.
  4. Specialized memoized functions:
     - `memoized_nightly_sum`: Cached nightly rate aggregator.
     - `memoized_quote_calculation`: Cached total calculator with loyalty rules.
  5. `benchmark_speedup`: Rigorous benchmark utility measuring execution times, speedup
     factor, and hit ratios across hundreds of test queries on seed dataset.
"""

from __future__ import annotations

import functools
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, TypeVar

from core.domain import Availability, Price, Rule
from core.recursion import check_dates_available_rec, recursive_apply_rules
from core.transforms import generate_date_range, nightly_sum

F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class CacheInfo:
    """Statistics about cache performance."""

    hits: int
    misses: int
    maxsize: int | None
    currsize: int

    @property
    def total_calls(self) -> int:
        return self.hits + self.misses

    @property
    def hit_ratio(self) -> float:
        total = self.total_calls
        return (self.hits / total) if total > 0 else 0.0


@dataclass(frozen=True)
class BenchmarkResult:
    """Benchmark results comparing unmemoized vs memoized execution."""

    iterations: int
    unmemoized_time_sec: float
    memoized_time_sec: float
    speedup_factor: float
    cache_info: CacheInfo


def _make_hashable_key(arg: Any) -> Any:
    """Convert arguments to deterministic hashable representations."""
    if isinstance(arg, (int, float, str, bool, type(None))):
        return arg
    if isinstance(arg, (list, tuple)):
        return tuple(_make_hashable_key(x) for x in arg)
    if isinstance(arg, (set, frozenset)):
        return frozenset(_make_hashable_key(x) for x in arg)
    if isinstance(arg, dict):
        return tuple(sorted((k, _make_hashable_key(v)) for k, v in arg.items()))
    if hasattr(arg, "__dict__"):
        # Dataclass or custom object
        return (
            type(arg).__name__,
            tuple(sorted((k, _make_hashable_key(v)) for k, v in arg.__dict__.items())),
        )
    return arg


def memoize(maxsize: int | None = 1024) -> Callable[[F], F]:
    """Pure memoization decorator with LRU eviction and cache statistics tracking."""

    def decorator(fn: F) -> F:
        cache: OrderedDict[Any, Any] = OrderedDict()
        hits = 0
        misses = 0

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal hits, misses

            # Build hashable key
            key_args = tuple(_make_hashable_key(a) for a in args)
            key_kwargs = tuple(
                sorted((k, _make_hashable_key(v)) for k, v in kwargs.items())
            )
            cache_key = (key_args, key_kwargs)

            if cache_key in cache:
                hits += 1
                # Move to end for LRU ordering
                cache.move_to_end(cache_key)
                return cache[cache_key]

            misses += 1
            result = fn(*args, **kwargs)

            # Evict oldest if full
            if maxsize is not None and len(cache) >= maxsize:
                cache.popitem(last=False)

            cache[cache_key] = result
            return result

        def cache_info() -> CacheInfo:
            return CacheInfo(
                hits=hits,
                misses=misses,
                maxsize=maxsize,
                currsize=len(cache),
            )

        def cache_clear() -> None:
            nonlocal hits, misses
            cache.clear()
            hits = 0
            misses = 0

        def cache_keys() -> tuple[Any, ...]:
            return tuple(cache.keys())

        # Attach management functions
        wrapper.cache_info = cache_info  # type: ignore[attr-defined]
        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        wrapper.cache_keys = cache_keys  # type: ignore[attr-defined]
        wrapper.is_memoized = True  # type: ignore[attr-defined]

        return wrapper  # type: ignore[return-value]

    return decorator


# ============================================================================
# SPECIALIZED MEMOIZED DOMAIN PRICING FUNCTIONS
# ============================================================================


@memoize(maxsize=2048)
def memoized_nightly_sum(
    prices: tuple[Price, ...],
    checkin: str,
    checkout: str,
    rate_id: str,
) -> int:
    """Memoized version of nightly_sum with pure LRU cache."""
    return nightly_sum(prices, checkin, checkout, rate_id)


def calculate_quote_with_loyalty(
    base_price: int,
    nights: int,
    guests: int,
    loyalty_status: str,
) -> int:
    """Uncached quote calculator with loyalty tier discounts."""
    # Loyalty discount table
    discounts = {
        "standard": 0,
        "silver": 5,
        "gold": 10,
        "platinum": 15,
    }
    pct = discounts.get(loyalty_status.lower(), 0)

    # Extra guest surcharge if > 2 guests (10% per additional guest)
    extra_guests = max(0, guests - 2)
    surcharge = (base_price * (10 * extra_guests)) // 100

    subtotal = base_price + surcharge
    discount = (subtotal * pct) // 100
    return max(0, subtotal - discount)


@memoize(maxsize=4096)
def memoized_calculate_quote_with_loyalty(
    base_price: int,
    nights: int,
    guests: int,
    loyalty_status: str,
) -> int:
    """Memoized quote calculator with loyalty tier discounts."""
    return calculate_quote_with_loyalty(base_price, nights, guests, loyalty_status)


def quote_offer_unmemoized(
    hotel_id: str,
    room_type_id: str,
    rate_id: str,
    checkin: str,
    checkout: str,
    prices_idx: tuple[Price, ...],
    avail_idx: tuple[Availability, ...],
    rules: tuple[Rule, ...],
) -> tuple[int, bool]:
    """Uncached version of quote_offer for benchmark comparisons."""
    dates = generate_date_range(checkin, checkout)
    is_available = check_dates_available_rec(avail_idx, room_type_id, dates, 0)
    base_sum = nightly_sum(prices_idx, checkin, checkout, rate_id)
    context = {
        "hotel_id": hotel_id,
        "room_type_id": room_type_id,
        "nights": len(dates),
    }
    final_total = recursive_apply_rules(base_sum, rules, context)
    return (final_total, is_available)


@lru_cache
def quote_offer(
    hotel_id: str,
    room_type_id: str,
    rate_id: str,
    checkin: str,
    checkout: str,
    prices_idx: tuple[Price, ...],
    avail_idx: tuple[Availability, ...],
    rules: tuple[Rule, ...],
) -> tuple[int, bool]:
    """Calculate total quoted amount and check availability across the stay.

    Memoized via functools.lru_cache.
    Reuses nightly_sum (core.transforms) for pricing reduction over dates,
    check_dates_available_rec (core.recursion) for recursive availability verification,
    and recursive_apply_rules (core.recursion) for sequential business rule evaluation.
    """
    return quote_offer_unmemoized(
        hotel_id=hotel_id,
        room_type_id=room_type_id,
        rate_id=rate_id,
        checkin=checkin,
        checkout=checkout,
        prices_idx=prices_idx,
        avail_idx=avail_idx,
        rules=rules,
    )


# ============================================================================
# BENCHMARK SUITE (LAB 3 EVALUATION)
# ============================================================================


def benchmark_speedup(
    unmemoized_fn: Callable[..., Any],
    memoized_fn: Any,
    queries: tuple[tuple[Any, ...], ...],
    repetitions: int = 300,
) -> BenchmarkResult:
    """Execute benchmark comparing unmemoized vs memoized function on a set of queries.

    Repeats queries cyclically for `repetitions` calls.
    Returns BenchmarkResult with time measurements and cache statistics.
    """
    if not queries:
        raise ValueError("queries cannot be empty for benchmarking")

    if hasattr(memoized_fn, "cache_clear"):
        memoized_fn.cache_clear()

    n_q = len(queries)

    # Measure unmemoized
    t0 = time.perf_counter()
    for i in range(repetitions):
        q = queries[i % n_q]
        unmemoized_fn(*q)
    t_unmemoized = time.perf_counter() - t0

    # Measure memoized
    t1 = time.perf_counter()
    for i in range(repetitions):
        q = queries[i % n_q]
        memoized_fn(*q)
    t_memoized = time.perf_counter() - t1

    raw_info = memoized_fn.cache_info() if hasattr(memoized_fn, "cache_info") else None
    if raw_info is not None and not isinstance(raw_info, CacheInfo):
        info = CacheInfo(
            hits=raw_info.hits,
            misses=raw_info.misses,
            maxsize=raw_info.maxsize,
            currsize=raw_info.currsize,
        )
    elif isinstance(raw_info, CacheInfo):
        info = raw_info
    else:
        info = CacheInfo(0, 0, None, 0)

    speedup = (t_unmemoized / t_memoized) if t_memoized > 0 else 1.0

    return BenchmarkResult(
        iterations=repetitions,
        unmemoized_time_sec=t_unmemoized,
        memoized_time_sec=t_memoized,
        speedup_factor=round(speedup, 2),
        cache_info=info,
    )
