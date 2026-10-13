"""Pure Functional Monads & Validation Engine for Hotel Booking System.

Coursework Lab 4:
  1. Functional Containers:
     - `Maybe[T]`: `Some[T]` / `Nothing` for safe optional value encapsulation.
     - `Either[E, T]`: `Right[T]` / `Left[E]` for pure error accumulation and validation.
     - Methods: `map`, `bind`, `get_or_else` on all containers.
     - `maybe_to_either`: Bridges Maybe and Either railway pipelines.
  2. Pure Booking Validators (Railway Oriented Programming):
     - `safe_rate`: Pure lookup returning Maybe[RatePlan].
     - `safe_room_type`: Pure lookup returning Maybe[RoomType].
     - `validate_dates`: ISO regex, calendar boundaries and ordering validation.
     - `validate_cart_item`: Capacity, rate-room integrity, stay limits, and availability.
     - `validate_booking`: Non-empty items, all items validated, price calendars, cancellation policy.
  3. Booking Pipeline:
     - `validate_and_calculate_booking`: Pure monadic composition calculating validated totals
       via quote_offer with zero runtime errors.
"""

from __future__ import annotations

import calendar
import dataclasses
import functools
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from core.domain import (
    Availability,
    Booking,
    CartItem,
    Guest,
    Price,
    RatePlan,
    RoomType,
    Rule,
)
from core.memo import quote_offer
from core.recursion import check_dates_available_rec
from core.transforms import generate_date_range

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


# ============================================================================
# SECTION 1: FUNCTIONAL CONTAINERS (MAYBE & EITHER)
# ============================================================================


@dataclass(frozen=True)
class Some(Generic[T]):
    """Represents a present value in the Maybe monad."""

    value: T

    def map(self, f: Callable[[T], U]) -> Maybe[U]:
        return Some(f(self.value))

    def bind(self, f: Callable[[T], Maybe[U]]) -> Maybe[U]:
        return f(self.value)

    def get_or_else(self, default: Any) -> T:
        return self.value


@dataclass(frozen=True)
class Nothing:
    """Represents an absent value in the Maybe monad."""

    def map(self, f: Callable[..., Any]) -> Nothing:
        return self

    def bind(self, f: Callable[..., Any]) -> Nothing:
        return self

    def get_or_else(self, default: Any) -> Any:
        return default


Maybe = Some[T] | Nothing


@dataclass(frozen=True)
class Right(Generic[T]):
    """Represents a successful value in the Either monad."""

    value: T

    def map(self, f: Callable[[T], U]) -> Either[Any, U]:
        return Right(f(self.value))

    def bind(self, f: Callable[[T], Either[E, U]]) -> Either[E, U]:
        return f(self.value)

    def get_or_else(self, default: Any) -> T:
        return self.value


@dataclass(frozen=True)
class Left(Generic[E]):
    """Represents an error value in the Either monad."""

    error: E

    def map(self, f: Callable[..., Any]) -> Left[E]:
        return self

    def bind(self, f: Callable[..., Any]) -> Left[E]:
        return self

    def get_or_else(self, default: Any) -> Any:
        return default


Either = Left[E] | Right[T]


def maybe_to_either(m: Maybe[T], error: dict) -> Either[dict, T]:
    """Convert a Maybe container to an Either container."""
    if isinstance(m, Some):
        return Right(m.value)
    return Left(error)


# ============================================================================
# SECTION 2: PURE VALIDATORS (WITHOUT EXCEPTIONS)
# ============================================================================

_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

DEFAULT_RULES: tuple[Rule, ...] = (
    Rule(id="rule_min_stay", kind="min_stay", payload=(1,)),
    Rule(id="rule_max_stay", kind="max_stay", payload=(30,)),
    Rule(id="rule_vip_discount", kind="vip_discount", payload=(10,)),
    Rule(id="rule_long_stay", kind="long_stay", payload=(5, 5)),
)


def safe_rate(rates: tuple[RatePlan, ...], rate_id: str) -> Maybe[RatePlan]:
    """Pure safe lookup of a RatePlan by ID."""
    for r in rates:
        if r.id == rate_id:
            return Some(r)
    return Nothing()


def safe_room_type(
    room_types: tuple[RoomType, ...], room_type_id: str
) -> Maybe[RoomType]:
    """Pure safe lookup of a RoomType by ID."""
    for rt in room_types:
        if rt.id == room_type_id:
            return Some(rt)
    return Nothing()


def _validate_single_date(d: str) -> Either[dict, tuple[int, int, int]]:
    """Validates date format and calendar range purely and safely."""
    if not isinstance(d, str) or not _DATE_REGEX.match(d):
        return Left(
            {
                "code": "invalid_date",
                "message": f"Invalid date format: '{d}'. Expected YYYY-MM-DD.",
                "date": d,
            }
        )

    parts = d.split("-")
    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])

    if year < 1:
        return Left(
            {
                "code": "invalid_date",
                "message": f"Invalid year: {year}. Year must be positive.",
                "date": d,
            }
        )

    if not (1 <= month <= 12):
        return Left(
            {
                "code": "invalid_date",
                "message": f"Invalid month: {month}. Month must be 1..12.",
                "date": d,
            }
        )

    max_days = calendar.monthrange(year, month)[1]
    if not (1 <= day <= max_days):
        return Left(
            {
                "code": "invalid_date",
                "message": f"Invalid day: {day} for month {month} (max {max_days}).",
                "date": d,
            }
        )

    return Right((year, month, day))


def validate_dates(checkin: str, checkout: str) -> Either[dict, tuple[str, ...]]:
    """Validate date strings and return Right(dates) or Left(error).

    Checks date format, valid calendar day, and strict ordering checkout > checkin.
    """
    cin_res = _validate_single_date(checkin)
    if isinstance(cin_res, Left):
        return cin_res

    cout_res = _validate_single_date(checkout)
    if isinstance(cout_res, Left):
        return cout_res

    # ISO date strings with zero-padded months and days compare lexicographically
    if not (checkout > checkin):
        return Left(
            {
                "code": "invalid_date_range",
                "message": f"Checkout date '{checkout}' must be strictly after checkin '{checkin}'.",
                "checkin": checkin,
                "checkout": checkout,
            }
        )

    return Right(generate_date_range(checkin, checkout))


def validate_cart_item(
    item: CartItem,
    availability: tuple[Availability, ...],
    rules: tuple[Rule, ...],
    room_types: tuple[RoomType, ...],
    rates: tuple[RatePlan, ...],
) -> Either[dict, CartItem]:
    """Validate CartItem through a monadic bind pipeline.

    Validates:
      1. Dates and date range.
      2. Room type existence.
      3. Guest count (1 <= guests <= capacity).
      4. Rate plan existence and room type match.
      5. Min / max stay requirements from rules.
      6. Availability for every night in the date range.
    """
    dates_res = validate_dates(item.checkin, item.checkout)
    if isinstance(dates_res, Left):
        return dates_res
    dates = dates_res.value

    # Validate room type
    rt_maybe = safe_room_type(room_types, item.room_type_id)
    if isinstance(rt_maybe, Nothing):
        return Left(
            {
                "code": "room_type_not_found",
                "message": f"Room type '{item.room_type_id}' does not exist.",
                "room_type_id": item.room_type_id,
            }
        )
    room_type = rt_maybe.value

    # Validate guests count
    if item.guests_count < 1:
        return Left(
            {
                "code": "invalid_guests_count",
                "message": f"Guests count must be >= 1, got {item.guests_count}.",
                "guests_count": item.guests_count,
            }
        )

    if item.guests_count > room_type.capacity:
        return Left(
            {
                "code": "capacity_exceeded",
                "message": (
                    f"Guests count {item.guests_count} exceeds capacity "
                    f"{room_type.capacity} for room type '{room_type.name}'."
                ),
                "capacity": room_type.capacity,
                "guests_count": item.guests_count,
            }
        )

    # Validate rate plan
    rate_maybe = safe_rate(rates, item.rate_id)
    if isinstance(rate_maybe, Nothing):
        return Left(
            {
                "code": "rate_not_found",
                "message": f"Rate plan '{item.rate_id}' does not exist.",
                "rate_id": item.rate_id,
            }
        )
    rate = rate_maybe.value

    if rate.room_type_id != item.room_type_id:
        return Left(
            {
                "code": "rate_room_mismatch",
                "message": (
                    f"Rate plan '{rate.id}' belongs to room type '{rate.room_type_id}', "
                    f"not '{item.room_type_id}'."
                ),
                "rate_id": rate.id,
                "expected_room_type_id": rate.room_type_id,
                "actual_room_type_id": item.room_type_id,
            }
        )

    # Validate stay limits (min_stay / max_stay) from rules
    stay_nights = len(dates)
    min_stays = [
        r.payload[0]
        for r in rules
        if r.kind == "min_stay" and len(r.payload) > 0 and isinstance(r.payload[0], int)
    ]
    max_stays = [
        r.payload[0]
        for r in rules
        if r.kind == "max_stay" and len(r.payload) > 0 and isinstance(r.payload[0], int)
    ]

    min_stay_limit = max(min_stays) if min_stays else None
    max_stay_limit = min(max_stays) if max_stays else None

    if min_stay_limit is not None and stay_nights < min_stay_limit:
        return Left(
            {
                "code": "min_stay_violation",
                "message": (
                    f"Stay duration {stay_nights} nights is less than the required minimum "
                    f"stay of {min_stay_limit} nights."
                ),
                "nights": stay_nights,
                "min_stay": min_stay_limit,
            }
        )

    if max_stay_limit is not None and stay_nights > max_stay_limit:
        return Left(
            {
                "code": "max_stay_violation",
                "message": (
                    f"Stay duration {stay_nights} nights exceeds the allowed maximum "
                    f"stay of {max_stay_limit} nights."
                ),
                "nights": stay_nights,
                "max_stay": max_stay_limit,
            }
        )

    # Check availability for all dates using recursive checker
    is_available = check_dates_available_rec(availability, item.room_type_id, dates, 0)
    if not is_available:

        def _is_day_available(target_date: str) -> bool:
            for a in availability:
                if a.room_type_id == item.room_type_id and a.date == target_date:
                    return a.available_rooms > 0
            return False

        first_unavailable = next(
            (d for d in dates if not _is_day_available(d)),
            dates[0] if dates else "",
        )
        return Left(
            {
                "code": "not_available",
                "message": f"Room type '{item.room_type_id}' is not available on date '{first_unavailable}'.",
                "date": first_unavailable,
                "room_type_id": item.room_type_id,
            }
        )

    return Right(item)


def validate_booking(
    booking: Booking,
    prices: tuple[Price, ...],
    availability: tuple[Availability, ...],
    rules: tuple[Rule, ...],
    room_types: tuple[RoomType, ...],
    rates: tuple[RatePlan, ...],
) -> Either[dict, Booking]:
    """Validate an entire Booking aggregation.

    Checks:
      1. Non-empty items.
      2. All items pass validate_cart_item (via functional reduce).
      3. Prices exist for every night of every item.
      4. Known cancellation policy.
      5. Non-refundable cancellation restrictions.
    """
    if not booking.items:
        return Left(
            {
                "code": "empty_booking",
                "message": "Booking contains no items.",
            }
        )

    def validate_folder(acc: Either[dict, None], it: CartItem) -> Either[dict, None]:
        return acc.bind(
            lambda _: validate_cart_item(
                it,
                availability=availability,
                rules=rules,
                room_types=room_types,
                rates=rates,
            ).map(lambda _: None)
        )

    item_check = functools.reduce(validate_folder, booking.items, Right(None))
    if isinstance(item_check, Left):
        return item_check

    # Verify prices exist for each night of each item
    for item in booking.items:
        dates_res = validate_dates(item.checkin, item.checkout)
        dates = dates_res.value
        available_price_dates = {p.date for p in prices if p.rate_id == item.rate_id}
        missing_dates = tuple(d for d in dates if d not in available_price_dates)
        if missing_dates:
            return Left(
                {
                    "code": "price_missing",
                    "message": (
                        f"Prices missing for rate '{item.rate_id}' on dates: "
                        f"{', '.join(missing_dates)}."
                    ),
                    "dates": missing_dates,
                    "rate_id": item.rate_id,
                }
            )

    # Verify cancellation policy is valid
    valid_policies = ("free", "standard", "non-refundable")
    for item in booking.items:
        rate = safe_rate(rates, item.rate_id).value
        if rate.cancellation not in valid_policies:
            return Left(
                {
                    "code": "unknown_cancellation_policy",
                    "message": f"Unknown cancellation policy: '{rate.cancellation}' for rate '{rate.id}'.",
                    "policy": rate.cancellation,
                    "rate_id": rate.id,
                }
            )

    # Check non-refundable cancellation restriction
    if booking.status == "cancelled":
        for item in booking.items:
            rate = safe_rate(rates, item.rate_id).value
            if rate.cancellation == "non-refundable":
                return Left(
                    {
                        "code": "non_refundable_cancel",
                        "message": (
                            f"Cancellation is prohibited for non-refundable rate plan '{rate.id}'."
                        ),
                        "rate_id": rate.id,
                    }
                )

    return Right(booking)


# ============================================================================
# SECTION 3: MONADIC PIPELINE (VALIDATE AND CALCULATE BOOKING)
# ============================================================================


def validate_and_calculate_booking(
    booking_id: str,
    guest: Guest,
    items: tuple[CartItem, ...],
    prices: tuple[Price, ...],
    availability: tuple[Availability, ...],
    rules: tuple[Rule, ...] = DEFAULT_RULES,
    room_types: tuple[RoomType, ...] = (),
    rates: tuple[RatePlan, ...] = (),
) -> Either[dict, Booking]:
    """Validate booking requirements and calculate final prices using quote_offer.

    Constructs a candidate Booking, performs end-to-end validation via validate_booking,
    and recalculates each item total via quote_offer (using the room type's hotel_id).
    VIP discount (is_vip) is not applied during quote_offer calculation because guest
    loyalty status is evaluated at the customer account level rather than in quote_offer.

    Composed strictly through monadic container methods (bind/map).
    """
    candidate_booking = Booking(
        id=booking_id,
        guest_id=guest.id,
        items=items,
        total=0,
        status="confirmed",
    )

    def calculate_booking(validated_booking: Booking) -> Either[dict, Booking]:
        def recalculate_item(item: CartItem) -> CartItem:
            rt = safe_room_type(room_types, item.room_type_id).value
            quoted_amount, _ = quote_offer(
                hotel_id=rt.hotel_id,
                room_type_id=item.room_type_id,
                rate_id=item.rate_id,
                checkin=item.checkin,
                checkout=item.checkout,
                prices_idx=prices,
                avail_idx=availability,
                rules=rules,
            )
            return dataclasses.replace(item, total_price=quoted_amount)

        recalculated_items = tuple(
            recalculate_item(it) for it in validated_booking.items
        )
        total_amount = functools.reduce(
            lambda acc, it: acc + it.total_price, recalculated_items, 0
        )
        return Right(
            Booking(
                id=booking_id,
                guest_id=guest.id,
                items=recalculated_items,
                total=total_amount,
                status="confirmed",
            )
        )

    return validate_booking(
        candidate_booking,
        prices=prices,
        availability=availability,
        rules=rules,
        room_types=room_types,
        rates=rates,
    ).bind(calculate_booking)
