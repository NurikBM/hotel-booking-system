"""Unit tests for Lab 3: Functional Memoization & Cache Optimization.

Covers:
  - memoize decorator basics & transparent return value equivalence
  - hits, misses, and hit_ratio accounting
  - cache_clear functionality
  - LRU eviction when maxsize is exceeded
  - memoized domain functions (memoized_nightly_sum, memoized_calculate_quote_with_loyalty)
  - Speedup benchmark comparing unmemoized vs memoized over 200+ runs
  - Deterministic hash key generation for complex immutable arguments
"""

from __future__ import annotations

import os

from core.domain import Availability, Price, Rule
from core.memo import (
    CacheInfo,
    benchmark_speedup,
    calculate_quote_with_loyalty,
    memoize,
    memoized_calculate_quote_with_loyalty,
    memoized_nightly_sum,
    quote_offer,
    quote_offer_unmemoized,
)
from core.transforms import load_seed, nightly_sum


def test_memoize_decorator_hits_and_misses():
    """Verify memoize caches pure function returns and correctly tracks hits and misses."""
    call_count = 0

    @memoize(maxsize=128)
    def expensive_power(base: int, exp: int) -> int:
        nonlocal call_count
        call_count += 1
        return base**exp

    expensive_power.cache_clear()
    assert expensive_power(2, 10) == 1024
    assert call_count == 1
    assert expensive_power.cache_info().hits == 0
    assert expensive_power.cache_info().misses == 1

    # Second call with same arguments must hit cache
    assert expensive_power(2, 10) == 1024
    assert call_count == 1
    assert expensive_power.cache_info().hits == 1
    assert expensive_power.cache_info().misses == 1

    # Third call with new argument
    assert expensive_power(3, 3) == 27
    assert call_count == 2
    assert expensive_power.cache_info().hits == 1
    assert expensive_power.cache_info().misses == 2
    assert expensive_power.cache_info().currsize == 2


def test_memoize_lru_eviction():
    """Verify that when cache exceeds maxsize, oldest entries are evicted."""

    @memoize(maxsize=3)
    def identity(x: int) -> int:
        return x

    identity.cache_clear()
    identity(1)
    identity(2)
    identity(3)
    assert identity.cache_info().currsize == 3

    # Adding a 4th element evicts element 1
    identity(4)
    assert identity.cache_info().currsize == 3

    # Calling 1 now is a miss (was evicted)
    identity(1)
    assert identity.cache_info().misses == 5


def test_memoize_cache_clear():
    """Verify cache_clear purges all cached entries and resets statistics."""

    @memoize(maxsize=100)
    def multiply(a: int, b: int) -> int:
        return a * b

    multiply.cache_clear()
    multiply(5, 5)
    multiply(5, 5)
    assert multiply.cache_info().hits == 1
    assert multiply.cache_info().currsize == 1

    multiply.cache_clear()
    info = multiply.cache_info()
    assert info.hits == 0
    assert info.misses == 0
    assert info.currsize == 0


def test_memoized_nightly_sum_with_seed_data():
    """Verify memoized_nightly_sum produces identical results to pure nightly_sum."""
    seed_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")
    _, _, rates, prices, _, _ = load_seed(seed_path)

    rate_id = rates[0].id
    checkin = "2026-06-01"
    checkout = "2026-06-06"

    # Compute unmemoized
    expected = nightly_sum(prices, checkin, checkout, rate_id)

    # Compute memoized
    memoized_nightly_sum.cache_clear()
    res1 = memoized_nightly_sum(prices, checkin, checkout, rate_id)
    assert res1 == expected
    assert memoized_nightly_sum.cache_info().misses == 1

    # Second compute should hit cache
    res2 = memoized_nightly_sum(prices, checkin, checkout, rate_id)
    assert res2 == expected
    assert memoized_nightly_sum.cache_info().hits == 1


def test_benchmark_speedup_execution_and_stats():
    """Verify benchmark_speedup runs 200+ iterations, measuring time and speedup factor."""
    queries = (
        (1000000, 3, 2, "standard"),
        (2500000, 5, 1, "silver"),
        (4000000, 2, 4, "gold"),
        (7500000, 7, 2, "platinum"),
        (3000000, 4, 3, "gold"),
    )

    result = benchmark_speedup(
        unmemoized_fn=calculate_quote_with_loyalty,
        memoized_fn=memoized_calculate_quote_with_loyalty,
        queries=queries,
        repetitions=250,
    )

    assert result.iterations == 250
    assert result.cache_info.total_calls == 250
    # For 5 unique queries repeated 250 times, misses <= 5, hits >= 245
    assert result.cache_info.misses <= 5
    assert result.cache_info.hits >= 245
    assert result.cache_info.hit_ratio > 0.95
    assert result.speedup_factor > 0.0


def test_cache_info_properties():
    """Verify CacheInfo dataclass properties and math."""
    info = CacheInfo(hits=80, misses=20, maxsize=100, currsize=20)
    assert info.total_calls == 100
    assert abs(info.hit_ratio - 0.8) < 1e-6

    empty_info = CacheInfo(hits=0, misses=0, maxsize=100, currsize=0)
    assert empty_info.total_calls == 0
    assert empty_info.hit_ratio == 0.0


def test_quote_offer_correct_calculation_and_available():
    """Verify quote_offer correctly calculates total with rules and returns available=True."""
    prices = (
        Price(date="2026-06-01", rate_id="rp_test", amount=2000000),
        Price(date="2026-06-02", rate_id="rp_test", amount=2000000),
    )
    avails = (
        Availability(date="2026-06-01", room_type_id="rt_test", available_rooms=2),
        Availability(date="2026-06-02", room_type_id="rt_test", available_rooms=3),
    )
    rules = (Rule(id="rule_1", kind="discount_pct", payload=(10,)),)

    quote_offer.cache_clear()
    total, is_avail = quote_offer(
        hotel_id="h_1",
        room_type_id="rt_test",
        rate_id="rp_test",
        checkin="2026-06-01",
        checkout="2026-06-03",
        prices_idx=prices,
        avail_idx=avails,
        rules=rules,
    )

    # 4,000,000 - 10% = 3,600,000
    assert total == 3600000
    assert is_avail is True


def test_quote_offer_unavailable_when_any_day_missing():
    """Verify quote_offer returns is_available=False if any day has 0 available rooms."""
    prices = (
        Price(date="2026-06-01", rate_id="rp_test", amount=2000000),
        Price(date="2026-06-02", rate_id="rp_test", amount=2000000),
    )
    avails = (
        Availability(date="2026-06-01", room_type_id="rt_test", available_rooms=2),
        Availability(
            date="2026-06-02", room_type_id="rt_test", available_rooms=0
        ),  # Sold out!
    )
    rules = ()

    total, is_avail = quote_offer(
        hotel_id="h_1",
        room_type_id="rt_test",
        rate_id="rp_test",
        checkin="2026-06-01",
        checkout="2026-06-03",
        prices_idx=prices,
        avail_idx=avails,
        rules=rules,
    )

    assert total == 4000000
    assert is_avail is False


def test_quote_offer_hashability_of_all_arguments():
    """Verify all arguments to quote_offer are hashable and do not raise TypeError."""
    prices = (Price(date="2026-06-01", rate_id="rp_1", amount=1500000),)
    avails = (Availability(date="2026-06-01", room_type_id="rt_1", available_rooms=1),)
    rules = (Rule(id="r1", kind="fixed_discount", payload=(100000,)),)

    # Calling quote_offer must execute without any hashability or unhashable type errors
    res = quote_offer(
        "h1", "rt_1", "rp_1", "2026-06-01", "2026-06-02", prices, avails, rules
    )
    assert isinstance(res, tuple)
    assert len(res) == 2


def test_quote_offer_cache_hits_on_repeated_calls():
    """Verify repeated calls with identical arguments increment lru_cache hits."""
    prices = (Price(date="2026-06-01", rate_id="rp_h", amount=1000000),)
    avails = (Availability(date="2026-06-01", room_type_id="rt_h", available_rooms=5),)
    rules = (Rule(id="rh", kind="discount_pct", payload=(5,)),)

    quote_offer.cache_clear()
    initial_info = quote_offer.cache_info()
    assert initial_info.hits == 0

    # First call: miss
    res1 = quote_offer(
        "h_h", "rt_h", "rp_h", "2026-06-01", "2026-06-02", prices, avails, rules
    )
    info1 = quote_offer.cache_info()
    assert info1.misses == 1
    assert info1.hits == 0

    # Second call: HIT!
    res2 = quote_offer(
        "h_h", "rt_h", "rp_h", "2026-06-01", "2026-06-02", prices, avails, rules
    )
    info2 = quote_offer.cache_info()
    assert info2.hits == 1
    assert res1 == res2


def test_quote_offer_speedup_benchmark():
    """Verify speedup on repeated quote_offer calls over 200+ runs using benchmark_speedup."""
    seed_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")
    hotels, rooms, rates, prices, avails, _ = load_seed(seed_path)

    rules = (
        Rule(id="r_disc", kind="discount_pct", payload=(10,)),
        Rule(id="r_early", kind="early_bird", payload=(14, 500000)),
        Rule(id="r_long", kind="long_stay", payload=(5, 5)),
    )

    relevant_rate_ids = {rates[i].id for i in range(3)}
    relevant_room_ids = {rooms[i].id for i in range(3)}
    prices_sub = tuple(p for p in prices if p.rate_id in relevant_rate_ids)
    avails_sub = tuple(a for a in avails if a.room_type_id in relevant_room_ids)

    # 3 unique queries across 14-night stays with rules
    queries = tuple(
        (
            hotels[i % len(hotels)].id,
            rooms[i].id,
            rates[i].id,
            "2026-06-01",
            "2026-06-15",
            prices_sub,
            avails_sub,
            rules,
        )
        for i in range(3)
    )

    result = benchmark_speedup(
        unmemoized_fn=quote_offer_unmemoized,
        memoized_fn=quote_offer,
        queries=queries,
        repetitions=250,
    )

    assert result.iterations == 250
    assert result.cache_info.hits >= 240
    assert result.cache_info.hit_ratio > 0.90
    assert result.speedup_factor > 1.0
