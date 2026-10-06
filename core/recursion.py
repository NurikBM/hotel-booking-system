"""Recursive Algorithms for Hotel / Room Booking System.

Coursework Lab 2:
  1. Recursive Hierarchical Traversal:
     `recursive_find_available_offers`: Recursively navigates
     Hotels -> RoomTypes -> RatePlans to discover matching available bookings
     purely through recursion (no `for` / `while` loops).
  2. Recursive Discount / Rule Engine:
     `recursive_apply_rules`: Recursively evaluates a sequence of business / discount
     rules on a price accumulator.
  3. Recursive Extremum Search:
     `recursive_find_cheapest_quote`: Pure tail-recursive minimum search over quotes
     without loops or builtin `min()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.domain import Availability, Hotel, Price, RatePlan, RoomType, Rule
from core.transforms import by_capacity, by_city, by_features, generate_date_range


@dataclass(frozen=True)
class BookingQuote:
    """Calculated quote for a prospective booking."""

    hotel: Hotel
    room_type: RoomType
    rate_plan: RatePlan
    checkin: str
    checkout: str
    nights: int
    base_total: int
    final_total: int


# ============================================================================
# 1. RECURSIVE HIERARCHICAL SEARCH (HOTELS -> ROOMS -> RATES)
# ============================================================================


def check_dates_available_rec(
    availabilities: tuple[Availability, ...],
    room_type_id: str,
    dates: tuple[str, ...],
    index: int = 0,
) -> bool:
    """Recursive check that room_type_id has availability > 0 for all dates.

    Base case: index == len(dates) -> True
    Recursive step: check dates[index], then recurse for index + 1.
    """
    if index >= len(dates):
        return True

    target_date = dates[index]

    # Check if this date has available rooms > 0
    # Recursive search within availabilities tuple for target_date and room_type_id
    def find_slot(slots: tuple[Availability, ...], s_idx: int) -> int | None:
        if s_idx >= len(slots):
            return None
        if (
            slots[s_idx].room_type_id == room_type_id
            and slots[s_idx].date == target_date
        ):
            return slots[s_idx].available_rooms
        return find_slot(slots, s_idx + 1)

    available = find_slot(availabilities, 0)
    if available is None or available <= 0:
        return False

    return check_dates_available_rec(availabilities, room_type_id, dates, index + 1)


# Alias for backward compatibility
_check_dates_available_rec = check_dates_available_rec


def _calc_rate_total_rec(
    prices: tuple[Price, ...],
    rate_id: str,
    dates: tuple[str, ...],
    d_idx: int = 0,
    acc: int = 0,
) -> int | None:
    """Recursively sum price for rate_id across needed dates.

    Returns None if any date has missing price.
    """
    if d_idx >= len(dates):
        return acc

    target_date = dates[d_idx]

    def find_price(ps: tuple[Price, ...], p_idx: int) -> int | None:
        if p_idx >= len(ps):
            return None
        if ps[p_idx].rate_id == rate_id and ps[p_idx].date == target_date:
            return ps[p_idx].amount
        return find_price(ps, p_idx + 1)

    daily_amt = find_price(prices, 0)
    if daily_amt is None:
        return None

    return _calc_rate_total_rec(prices, rate_id, dates, d_idx + 1, acc + daily_amt)


def _traverse_rate_plans_rec(
    hotel: Hotel,
    room: RoomType,
    rate_plans: tuple[RatePlan, ...],
    prices: tuple[Price, ...],
    dates: tuple[str, ...],
    rp_idx: int = 0,
    acc: tuple[BookingQuote, ...] = (),
) -> tuple[BookingQuote, ...]:
    """Recursively process rate plans for a room type."""
    if rp_idx >= len(rate_plans):
        return acc

    rp = rate_plans[rp_idx]
    new_acc = acc
    if rp.room_type_id == room.id:
        total = _calc_rate_total_rec(prices, rp.id, dates, 0, 0)
        if total is not None:
            quote = BookingQuote(
                hotel=hotel,
                room_type=room,
                rate_plan=rp,
                checkin=dates[0],
                checkout=dates[-1],
                nights=len(dates),
                base_total=total,
                final_total=total,
            )
            new_acc = (*acc, quote)

    return _traverse_rate_plans_rec(
        hotel, room, rate_plans, prices, dates, rp_idx + 1, new_acc
    )


def _traverse_rooms_rec(
    hotel: Hotel,
    rooms: tuple[RoomType, ...],
    rate_plans: tuple[RatePlan, ...],
    prices: tuple[Price, ...],
    availabilities: tuple[Availability, ...],
    dates: tuple[str, ...],
    guests: int,
    required_features: tuple[str, ...],
    r_idx: int = 0,
    acc: tuple[BookingQuote, ...] = (),
) -> tuple[BookingQuote, ...]:
    """Recursively process room types of a hotel."""
    if r_idx >= len(rooms):
        return acc

    room = rooms[r_idx]
    new_acc = acc
    if room.hotel_id == hotel.id:
        # Check capacity & features
        cap_ok = by_capacity(guests)(room)
        feat_ok = by_features(required_features)(room) if required_features else True
        avail_ok = _check_dates_available_rec(availabilities, room.id, dates, 0)

        if cap_ok and feat_ok and avail_ok:
            quotes = _traverse_rate_plans_rec(
                hotel, room, rate_plans, prices, dates, 0, ()
            )
            new_acc = (*acc, *quotes)

    return _traverse_rooms_rec(
        hotel,
        rooms,
        rate_plans,
        prices,
        availabilities,
        dates,
        guests,
        required_features,
        r_idx + 1,
        new_acc,
    )


def recursive_search_available_quotes(
    hotels: tuple[Hotel, ...],
    room_types: tuple[RoomType, ...],
    rate_plans: tuple[RatePlan, ...],
    prices: tuple[Price, ...],
    availabilities: tuple[Availability, ...],
    city: str,
    checkin: str,
    checkout: str,
    guests: int = 1,
    required_features: tuple[str, ...] = (),
    h_idx: int = 0,
    acc: tuple[BookingQuote, ...] = (),
) -> tuple[BookingQuote, ...]:
    """Pure recursive traversal of the Hotel -> Room -> RatePlan hierarchy.

    Finds all valid booking quotes without while or for loops.
    """
    if h_idx >= len(hotels):
        return acc

    hotel = hotels[h_idx]
    new_acc = acc
    if by_city(city)(hotel):
        dates = generate_date_range(checkin, checkout)
        hotel_quotes = _traverse_rooms_rec(
            hotel,
            room_types,
            rate_plans,
            prices,
            availabilities,
            dates,
            guests,
            required_features,
            0,
            (),
        )
        new_acc = (*acc, *hotel_quotes)

    return recursive_search_available_quotes(
        hotels,
        room_types,
        rate_plans,
        prices,
        availabilities,
        city,
        checkin,
        checkout,
        guests,
        required_features,
        h_idx + 1,
        new_acc,
    )


# ============================================================================
# 2. RECURSIVE RULE / DISCOUNT APPLICATION ENGINE
# ============================================================================


def recursive_apply_rules(
    current_amount: int,
    rules: tuple[Rule, ...],
    context: Any = None,
    r_idx: int = 0,
) -> int:
    """Recursively applies a sequence of serializable Rule(id, kind, payload) objects.

    Interprets rule kind and payload:
      - 'discount_pct': payload=(pct,) -> reduces amount by pct %
      - 'fixed_discount': payload=(amt,) -> reduces amount by amt
      - 'vip_discount': payload=(pct,) -> if context and context.get('is_vip'): reduces by pct %
      - 'early_bird': payload=(min_days, discount) -> if context.get('days_in_advance', 0) > min_days: reduces
      - 'long_stay': payload=(min_nights, pct) -> if context.get('nights', 0) >= min_nights: reduces by pct %
    """
    if r_idx >= len(rules):
        return current_amount

    rule = rules[r_idx]
    kind = rule.kind
    payload = rule.payload
    ctx = context if isinstance(context, dict) else {}

    new_amount = current_amount

    if kind == "discount_pct":
        pct = payload[0] if payload else 0
        new_amount = (current_amount * (100 - pct)) // 100
    elif kind == "fixed_discount":
        fixed = payload[0] if payload else 0
        new_amount = max(0, current_amount - fixed)
    elif kind == "vip_discount":
        if ctx.get("is_vip", False):
            pct = payload[0] if payload else 10
            new_amount = (current_amount * (100 - pct)) // 100
    elif kind == "early_bird":
        min_days = payload[0] if len(payload) > 0 else 14
        discount = payload[1] if len(payload) > 1 else 500000
        if (
            ctx.get("days_in_advance", 0) > min_days
            or ctx.get("days_ahead", 0) > min_days
        ):
            new_amount = max(0, current_amount - discount)
    elif kind == "long_stay":
        min_nights = payload[0] if len(payload) > 0 else 5
        pct = payload[1] if len(payload) > 1 else 5
        if ctx.get("nights", 0) >= min_nights:
            new_amount = (current_amount * (100 - pct)) // 100
    elif hasattr(rule, "action") and callable(rule.action):
        predicate_matches = (
            rule.predicate(context) if getattr(rule, "predicate", None) else True
        )
        if predicate_matches:
            new_amount = rule.action(current_amount)

    return recursive_apply_rules(new_amount, rules, context, r_idx + 1)


# ============================================================================
# 3. RECURSIVE EXTREMUM SEARCH (MINIMUM QUOTE)
# ============================================================================


def recursive_find_cheapest_quote(
    quotes: tuple[BookingQuote, ...],
    idx: int = 0,
    current_min: BookingQuote | None = None,
) -> BookingQuote | None:
    """Recursively finds the quote with minimum final_total without min() or loops."""
    if idx >= len(quotes):
        return current_min

    item = quotes[idx]
    next_min = (
        item
        if current_min is None or item.final_total < current_min.final_total
        else current_min
    )

    return recursive_find_cheapest_quote(quotes, idx + 1, next_min)
