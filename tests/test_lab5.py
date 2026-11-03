"""Unit tests for Lab 5: Lazy Evaluation, Streams, and Deferred Offers.

Covers:
1. iter_available_days: yielding availability tuples on demand without full list creation.
2. lazy_offers: stream (hotel, room, rate, price) satisfying predicate conditions.
3. take_lazy & drop_lazy: stream slicing without materializing infinite or long sequences.
4. lazy_calendar_stream: generator creating arbitrary/infinite date sequences.
5. lazy_filter and lazy_map: composable stream operators.
6. LazySequence: chaining map/filter/take/drop with strictly deferred materialization.
7. Verification that lazy_offers halts computation as soon as k items are taken.
"""

from __future__ import annotations

import inspect
import os

import pytest

from core.domain import Availability
from core.lazy import (
    LazySequence,
    drop_lazy,
    iter_available_days,
    lazy_calendar_stream,
    lazy_filter,
    lazy_map,
    lazy_offers,
    take_lazy,
)
from core.transforms import load_seed


@pytest.fixture(scope="module")
def seed_data():
    seed_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")
    return load_seed(seed_path)


def test_iter_available_days_is_generator():
    """Verify iter_available_days returns an iterator and yields correctly."""
    sample_avails = (
        Availability(room_type_id="rt_1", date="2026-06-01", available_rooms=5),
        Availability(room_type_id="rt_2", date="2026-06-01", available_rooms=3),
        Availability(room_type_id="rt_1", date="2026-06-02", available_rooms=4),
    )
    gen = iter_available_days(sample_avails, "rt_1")
    assert inspect.isgenerator(gen)

    # Lazily collect items
    results = tuple(gen)
    assert len(results) == 2
    assert results[0] == ("2026-06-01", 5)
    assert results[1] == ("2026-06-02", 4)


def test_lazy_calendar_stream_infinite_and_take():
    """Verify lazy_calendar_stream can stream dates indefinitely and take_lazy extracts k elements."""
    stream = lazy_calendar_stream("2026-01-01")
    assert inspect.isgenerator(stream)

    first_5 = tuple(take_lazy(stream, 5))
    assert len(first_5) == 5
    assert first_5 == (
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
        "2026-01-05",
    )


def test_drop_lazy_combinator():
    """Verify drop_lazy skips n items lazily."""
    nums = iter(range(10))
    dropped = tuple(drop_lazy(nums, 6))
    assert dropped == (6, 7, 8, 9)


def test_lazy_filter_and_map_operators():
    """Verify lazy_filter and lazy_map maintain lazy execution semantics."""

    def double(x: int) -> int:
        return x * 2

    def is_even(x: int) -> bool:
        return x % 2 == 0

    gen_map = lazy_map(double, (1, 2, 3, 4))
    assert inspect.isgenerator(gen_map)
    assert tuple(gen_map) == (2, 4, 6, 8)

    gen_filter = lazy_filter(is_even, (1, 2, 3, 4, 5, 6))
    assert inspect.isgenerator(gen_filter)
    assert tuple(gen_filter) == (2, 4, 6)


def test_lazy_offers_with_seed_data(seed_data):
    """Verify lazy_offers finds matching offers lazily across seed data."""
    hotels, room_types, rates, prices, avail, _guests = seed_data

    # Find offers with price under 100,000 KZT (10,000,000 cents)
    budget_cents = 10_000_000
    gen = lazy_offers(
        hotels=hotels,
        room_types=room_types,
        rates=rates,
        prices=prices,
        avail=avail,
        predicate=lambda h, r, rt, p: p <= budget_cents,
        checkin="2026-06-01",
        checkout="2026-06-04",
    )
    assert inspect.isgenerator(gen)

    # Take first 3 offers
    first_3 = tuple(take_lazy(gen, 3))
    assert len(first_3) <= 3
    for hotel, room, rate, price in first_3:
        assert price <= budget_cents
        assert room.hotel_id == hotel.id
        assert rate.room_type_id == room.id


def test_lazy_offers_short_circuit_evaluations(seed_data):
    """Verify that taking 2 offers does not evaluate the entire dataset."""
    hotels, room_types, rates, prices, avail, _guests = seed_data

    eval_count = 0

    def counting_predicate(h, r, rt, p):
        nonlocal eval_count
        eval_count += 1
        return True

    gen = lazy_offers(
        hotels=hotels,
        room_types=room_types,
        rates=rates,
        prices=prices,
        avail=avail,
        predicate=counting_predicate,
        checkin="2026-06-01",
        checkout="2026-06-03",
    )

    first_2 = tuple(take_lazy(gen, 2))
    assert len(first_2) == 2
    # Because there are 48 rates in the dataset, evaluating only 2 items should stop well before 48
    assert eval_count <= 5


def test_lazy_sequence_monadic_style_chaining():
    """Verify LazySequence allows deferred chaining of filter, map, drop, and take."""
    evaluated = []

    def tracking_mapper(x: int) -> int:
        evaluated.append(x)
        return x * 10

    lazy_seq = (
        LazySequence.from_iterable(range(1, 100))
        .filter(lambda x: x % 2 != 0)
        .map(tracking_mapper)
        .drop(2)
        .take(3)
    )

    # Before terminal operator, nothing is evaluated
    assert len(evaluated) == 0

    # Terminal operator
    res = lazy_seq.to_tuple()
    # Range odds: 1, 3, 5, 7, 9, 11 -> *10: 10, 30, 50, 70, 90, 110 -> drop 2: 50, 70, 90, 110 -> take 3: 50, 70, 90
    assert res == (50, 70, 90)
    # Head terminal
    first_item = LazySequence.from_iterable([10, 20, 30]).map(lambda x: x + 1).head()
    assert first_item == 11
