"""Lazy sequences, generators, and infinite streams for Lab 5.

Implements pure lazy evaluation over hotel datasets, calendar streams, and matching offers:
1. iter_available_days: lazy generator yielding (date, available_count) for a room type.
2. lazy_offers: generator yielding (hotel, room, rate, price) for offers matching a predicate.
3. lazy_calendar_stream: generator creating an arbitrary/infinite sequence of dates.
4. take_lazy & drop_lazy: pure functional stream combinators without intermediate list allocation.
5. lazy_filter & lazy_map: composable stream operators preserving laziness.
6. LazySequence: immutable wrapper for lazy pipeline chaining and deferred evaluation.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

from core.domain import Availability, Hotel, Price, RatePlan, RoomType
from core.transforms import generate_date_range, nightly_sum

T = TypeVar("T")
U = TypeVar("U")


def iter_available_days(
    avail: tuple[Availability, ...], room_type_id: str
) -> Iterator[tuple[str, int]]:
    """Lazily yield (date, available) tuples for a given room_type_id.

    Yields on demand without creating full intermediate lists.
    """
    for a in avail:
        if a.room_type_id == room_type_id:
            yield (a.date, a.available_rooms)


def lazy_offers(
    hotels: tuple[Hotel, ...],
    room_types: tuple[RoomType, ...],
    rates: tuple[RatePlan, ...],
    prices: tuple[Price, ...],
    avail: tuple[Availability, ...],
    predicate: Callable[[Hotel, RoomType, RatePlan, int], bool] | None = None,
    checkin: str = "2026-06-01",
    checkout: str = "2026-06-04",
) -> Iterator[tuple[Hotel, RoomType, RatePlan, int]]:
    """Stream (hotel, room, rate, price for period) for offers satisfying the condition.

    Evaluates prices and yields results one-by-one as requested, stopping as soon
    as consumers (e.g. take_lazy) stop requesting items.
    """
    stay_dates = set(generate_date_range(checkin, checkout))

    # Pre-index availability by (room_type_id, date) for quick lookup
    avail_map: dict[tuple[str, str], int] = {
        (a.room_type_id, a.date): a.available_rooms for a in avail
    }

    # Group room types by hotel_id
    rooms_by_hotel: dict[str, list[RoomType]] = {}
    for r in room_types:
        rooms_by_hotel.setdefault(r.hotel_id, []).append(r)

    # Group rates by room_type_id
    rates_by_room: dict[str, list[RatePlan]] = {}
    for rt in rates:
        rates_by_room.setdefault(rt.room_type_id, []).append(rt)

    for hotel in hotels:
        for room in rooms_by_hotel.get(hotel.id, []):
            # Check if room has availability for all stay dates
            is_avail = all(avail_map.get((room.id, d), 0) > 0 for d in stay_dates)
            if not is_avail:
                continue

            for rate in rates_by_room.get(room.id, []):
                total_price = nightly_sum(prices, checkin, checkout, rate.id)
                if total_price <= 0:
                    continue

                if predicate is None or predicate(hotel, room, rate, total_price):
                    yield (hotel, room, rate, total_price)


def lazy_calendar_stream(start_date: str, days: int | None = None) -> Iterator[str]:
    """Yield a continuous (finite or infinite) lazy stream of ISO date strings (YYYY-MM-DD).

    If days is None, streams indefinitely.
    """
    cur = datetime.date.fromisoformat(start_date)
    step = 0
    one_day = datetime.timedelta(days=1)
    while days is None or step < days:
        yield cur.isoformat()
        cur += one_day
        step += 1


def take_lazy(iterable: Iterator[T] | Iterable[T], n: int) -> Iterator[T]:
    """Take the first n elements from an iterator or iterable lazily without materializing the rest."""
    if n <= 0:
        return
    it = iter(iterable)
    count = 0
    for item in it:
        yield item
        count += 1
        if count >= n:
            break


def drop_lazy(iterable: Iterator[T] | Iterable[T], n: int) -> Iterator[T]:
    """Drop the first n elements from an iterator or iterable, yielding the remainder lazily."""
    it = iter(iterable)
    dropped = 0
    for item in it:
        if dropped < n:
            dropped += 1
            continue
        yield item


def lazy_filter(
    predicate: Callable[[T], bool], iterable: Iterator[T] | Iterable[T]
) -> Iterator[T]:
    """Lazily filter elements by predicate."""
    for item in iterable:
        if predicate(item):
            yield item


def lazy_map(fn: Callable[[T], U], iterable: Iterator[T] | Iterable[T]) -> Iterator[U]:
    """Lazily transform elements using fn."""
    for item in iterable:
        yield fn(item)


@dataclass(frozen=True)
class LazySequence(Generic[T]):
    """Pure immutable wrapper over an iterator factory.

    Supports method chaining: .filter(), .map(), .take(), .drop(), .to_tuple().
    Evaluation is strictly deferred until terminal operators (e.g. to_tuple, head, fold) are called.
    """

    factory: Callable[[], Iterator[T]]

    @classmethod
    def from_iterable(cls, items: Iterable[T]) -> LazySequence[T]:
        return cls(lambda: iter(items))

    def __iter__(self) -> Iterator[T]:
        return self.factory()

    def filter(self, predicate: Callable[[T], bool]) -> LazySequence[T]:
        return LazySequence(lambda: lazy_filter(predicate, self.factory()))

    def map(self, fn: Callable[[T], U]) -> LazySequence[U]:
        return LazySequence(lambda: lazy_map(fn, self.factory()))

    def take(self, n: int) -> LazySequence[T]:
        return LazySequence(lambda: take_lazy(self.factory(), n))

    def drop(self, n: int) -> LazySequence[T]:
        return LazySequence(lambda: drop_lazy(self.factory(), n))

    def to_tuple(self) -> tuple[T, ...]:
        """Terminal operator: materialize the lazy stream to an immutable tuple."""
        return tuple(self.factory())

    def head(self) -> T | None:
        """Terminal operator: extract the first element or None if empty."""
        for item in self.factory():
            return item
        return None
