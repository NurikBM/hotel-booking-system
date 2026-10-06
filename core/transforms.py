"""Data transformations, seed loading, predicates, and functional pricing pipelines.

Lab 1:
  - load_seed: Load normalized immutable seed data from JSON
  - hold_item / remove_hold: Immutable cart management
  - nightly_sum: Price aggregation using reduce over ISO date range
  - calculate_nights, generate_date_range: Pure date calculations
  - Pure map/filter/reduce pipelines

Lab 2:
  - by_city: Closure returning predicate for Hotel
  - by_capacity: Closure returning predicate for RoomType
  - by_features: Closure returning predicate for entities with features
  - Lambdas for sorting and combinators
"""

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from datetime import date
from typing import Any

from core.domain import (
    Availability,
    CartItem,
    Guest,
    Hotel,
    Price,
    RatePlan,
    RoomType,
)

# ============================================================================
# LAB 1: SEED LOADING & IMMUTABLE DATA PREPARATION
# ============================================================================


def load_seed(
    path: str,
) -> tuple[
    tuple[Hotel, ...],
    tuple[RoomType, ...],
    tuple[RatePlan, ...],
    tuple[Price, ...],
    tuple[Availability, ...],
    tuple[Guest, ...],
]:
    """Load JSON seed file into pure, immutable tuple domain models."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    hotels = tuple(
        Hotel(
            id=str(h["id"]),
            name=str(h["name"]),
            stars=int(h["stars"]),
            city=str(h["city"]),
            features=tuple(str(x) for x in h.get("features", ())),
        )
        for h in raw.get("hotels", ())
    )

    room_types = tuple(
        RoomType(
            id=str(r["id"]),
            hotel_id=str(r["hotel_id"]),
            name=str(r["name"]),
            capacity=int(r["capacity"]),
            beds=int(r["beds"]),
            features=tuple(str(x) for x in r.get("features", ())),
        )
        for r in raw.get("room_types", ())
    )

    rate_plans = tuple(
        RatePlan(
            id=str(rp["id"]),
            room_type_id=str(rp["room_type_id"]),
            name=str(rp["name"]),
            meals=str(rp.get("meals", "none")),
            cancellation=str(rp.get("cancellation", "standard")),
            price_factor=float(rp.get("price_factor", 1.0)),
        )
        for rp in raw.get("rate_plans", ())
    )

    prices = tuple(
        Price(
            date=str(p["date"]),
            rate_id=str(p["rate_id"]),
            amount=int(p["amount"]),
        )
        for p in raw.get("prices", ())
    )

    availabilities = tuple(
        Availability(
            date=str(a["date"]),
            room_type_id=str(a["room_type_id"]),
            available_rooms=int(a["available_rooms"]),
        )
        for a in raw.get("availability", ())
    )

    guests = tuple(
        Guest(
            id=str(g["id"]),
            name=str(g["name"]),
            email=str(g["email"]),
            phone=str(g["phone"]),
            loyalty_status=str(g.get("loyalty_status", "standard")),
        )
        for g in raw.get("guests", ())
    )

    return (hotels, room_types, rate_plans, prices, availabilities, guests)


# ============================================================================
# LAB 1: DATE & PRICING OPERATIONS (PURE FUNCTIONS, REDUCE)
# ============================================================================


def calculate_nights(checkin: str, checkout: str) -> int:
    """Calculate the number of nights between check-in and check-out dates."""
    d_in = date.fromisoformat(checkin)
    d_out = date.fromisoformat(checkout)
    delta = (d_out - d_in).days
    if delta <= 0:
        raise ValueError(
            f"checkout ({checkout}) must be strictly after checkin ({checkin})"
        )
    return delta


def generate_date_range(checkin: str, checkout: str) -> tuple[str, ...]:
    """Generate a tuple of ISO-8601 date strings for each night of the stay."""
    d_in = date.fromisoformat(checkin)
    nights = calculate_nights(checkin, checkout)
    from datetime import timedelta

    return tuple((d_in + timedelta(days=i)).isoformat() for i in range(nights))


def nightly_sum(
    prices: tuple[Price, ...],
    checkin: str,
    checkout: str,
    rate_id: str,
) -> int:
    """Calculate the total price across all nights for a rate_id using functools.reduce.

    Raises ValueError if price for any night is missing in prices calendar.
    """
    needed_dates = generate_date_range(checkin, checkout)
    # Build lookup mapping for O(1) date access during reduction
    lookup = {p.date: p.amount for p in prices if p.rate_id == rate_id}

    missing_dates = tuple(d for d in needed_dates if d not in lookup)
    if missing_dates:
        raise ValueError(
            f"Missing price records for rate_id={rate_id} on dates: {missing_dates}"
        )

    # Pure reduction summing nightly amounts
    night_costs = tuple(lookup[d] for d in needed_dates)
    return functools.reduce(lambda acc, price: acc + price, night_costs, 0)


def apply_discount(amount: int, discount_percent: int) -> int:
    """Apply discount percentage (0..100) to an integer monetary amount.

    Pure function. Rounds to nearest cent/tiyn.
    """
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("discount_percent must be between 0 and 100")
    if discount_percent == 0:
        return amount
    discounted = (amount * (100 - discount_percent)) // 100
    return max(0, discounted)


# ============================================================================
# LAB 1: IMMUTABLE CART MANAGEMENT
# ============================================================================


def hold_item(cart: tuple[CartItem, ...], item: CartItem) -> tuple[CartItem, ...]:
    """Add an item to the cart, returning a new immutable tuple."""
    return (*cart, item)


def remove_hold(cart: tuple[CartItem, ...], item_id: str) -> tuple[CartItem, ...]:
    """Remove an item by id from the cart, returning a new immutable tuple."""
    return tuple(i for i in cart if i.id != item_id)


def calculate_cart_total(cart: tuple[CartItem, ...]) -> int:
    """Sum total_price of all items in cart using reduce."""
    return functools.reduce(lambda acc, item: acc + item.total_price, cart, 0)


# ============================================================================
# LAB 2: CLOSURES & FUNCTION FACTORIES
# ============================================================================


def by_city(city: str) -> Callable[[Hotel], bool]:
    """Closure factory: predicate matching hotel city (case-insensitive)."""
    target = city.strip().casefold()

    def predicate(hotel: Hotel) -> bool:
        return hotel.city.strip().casefold() == target

    return predicate


def by_capacity(guests: int) -> Callable[[RoomType], bool]:
    """Closure factory: predicate matching room capacity >= guests."""
    if guests < 1:
        raise ValueError("guests count must be >= 1")

    def predicate(room: RoomType) -> bool:
        return room.capacity >= guests

    return predicate


def by_features(required: tuple[str, ...]) -> Callable[[Any], bool]:
    """Closure factory: predicate checking that entity features contain all required features."""
    req_set = {f.strip().casefold() for f in required}

    def predicate(entity: Any) -> bool:
        entity_feats = {f.strip().casefold() for f in getattr(entity, "features", ())}
        return req_set.issubset(entity_feats)

    return predicate


def by_price_range(
    min_amt: int, max_amt: int, currency: str = "KZT"
) -> Callable[[Price], bool]:
    """Closure factory: predicate filtering a single nightly Price within [min_amt, max_amt].

    Логичнее применять к отдельной цене за ночь, так как это базовый атомарный элемент тарифа в календаре цен.
    """
    if min_amt < 0 or max_amt < min_amt:
        raise ValueError(f"Invalid price bounds: min={min_amt}, max={max_amt}")

    def predicate(price: Price) -> bool:
        amt = price.amount if hasattr(price, "amount") else int(price)
        return min_amt <= amt <= max_amt

    return predicate


# ============================================================================
# LAB 2: LAMBDAS, COMBINATORS & SORTING
# ============================================================================

sort_hotels_by_stars: Callable[[tuple[Hotel, ...], bool], tuple[Hotel, ...]] = (
    lambda hotels, descending=True: tuple(
        sorted(hotels, key=lambda h: h.stars, reverse=descending)
    )
)

sort_rooms_by_capacity: Callable[[tuple[RoomType, ...], bool], tuple[RoomType, ...]] = (
    lambda rooms, descending=False: tuple(
        sorted(rooms, key=lambda r: (r.capacity, r.beds), reverse=descending)
    )
)

sort_prices_by_amount: Callable[[tuple[Price, ...], bool], tuple[Price, ...]] = (
    lambda prices, descending=False: tuple(
        sorted(prices, key=lambda p: p.amount, reverse=descending)
    )
)
