"""Pricing Module: Pure calculation functions for stay durations and rates.

Coursework Lab 1: Pure transformation functions.
All functions in this module are strictly pure:
  1. Deterministic: the same inputs will ALWAYS produce the exact same output.
  2. Side-effect free: no mutation of parameters, no network/file I/O, no global state.
"""

from __future__ import annotations

from datetime import date
from domain.models import Room


def calculate_nights(check_in: date, check_out: date) -> int:
    """Calculate the number of nights between check-in and check-out dates.

    OVERVIEW:
    A pure date-difference calculation. The duration in nights is defined as
    (check_out - check_in).days. If the check_out date is before or equal to
    check_in, it returns 0 nights rather than negative numbers, ensuring safety.

    Args:
        check_in: Guest arrival date.
        check_out: Guest departure date.

    Returns:
        Non-negative integer representing the total nights of the stay.
    """
    delta_days = (check_out - check_in).days
    return max(0, delta_days)


def calculate_total_price(
    base_price: float,
    nights: int,
    seasonal_multiplier: float = 1.0,
) -> float:
    """Calculate the total price for a stay with a seasonal pricing multiplier.

    OVERVIEW:
    Pure mathematical transformation:
      Total = base_price * nights * seasonal_multiplier
    Rounded to 2 decimal places to model financial precision.

    Args:
        base_price: Nightly base rate for the room.
        nights: Number of nights.
        seasonal_multiplier: Factor reflecting demand/season (e.g., 1.25 for peak, 0.85 for low).

    Returns:
        Total price rounded to two decimal places.
    """
    if nights <= 0 or base_price <= 0.0 or seasonal_multiplier < 0.0:
        return 0.0
    raw_total = base_price * float(nights) * float(seasonal_multiplier)
    return round(raw_total, 2)


def apply_discount(total_price: float, discount_percent: float) -> float:
    """Apply a percentage discount to an existing total price.

    OVERVIEW:
    Pure calculation: produces a new discounted float without altering the input.
    Guarantees that the final price cannot be negative or exceed the original total.

    Args:
        total_price: The baseline cost.
        discount_percent: Discount between 0 and 100 percent.

    Returns:
        Discounted total price rounded to 2 decimal places.
    """
    if total_price <= 0.0:
        return 0.0
    clamped_discount = max(0.0, min(100.0, discount_percent))
    discount_amount = total_price * (clamped_discount / 100.0)
    return round(total_price - discount_amount, 2)


def calculate_stay_quote(
    room: Room,
    check_in: date,
    check_out: date,
    seasonal_multiplier: float = 1.0,
) -> float:
    """Calculate the complete stay quote for an immutable Room entity.

    OVERVIEW:
    Higher-level pure combination of `calculate_nights` and `calculate_total_price`.
    Extracts room.base_price and evaluates the full stay cost.

    Args:
        room: Immutable Room instance.
        check_in: Check-in date.
        check_out: Check-out date.
        seasonal_multiplier: Seasonal demand factor.

    Returns:
        Total calculated quote for the reservation.
    """
    nights = calculate_nights(check_in, check_out)
    return calculate_total_price(room.base_price, nights, seasonal_multiplier)
