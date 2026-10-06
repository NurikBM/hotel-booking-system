"""Domain Model for Hotel / Room Booking System.

Pure functional immutable domain entities using frozen dataclasses.
All monetary amounts are integers (kopecks/cents).
All dates are ISO-8601 strings (YYYY-MM-DD).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Hotel:
    """Hotel entity."""

    id: str
    name: str
    stars: int
    city: str
    features: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoomType:
    """Room type belonging to a hotel."""

    id: str
    hotel_id: str
    name: str
    capacity: int
    beds: int
    features: tuple[str, ...] = ()


@dataclass(frozen=True)
class RatePlan:
    """Rate plan associated with a room type."""

    id: str
    room_type_id: str
    name: str
    meals: str = "none"  # "none", "breakfast", "half-board", "all-inclusive"
    cancellation: str = "standard"  # "free", "non-refundable", "standard"
    price_factor: float = 1.0


@dataclass(frozen=True)
class Price:
    """Price for a specific rate plan on a specific calendar date.

    Amount is strictly an integer in cents/kopecks.
    """

    date: str  # YYYY-MM-DD
    rate_id: str
    amount: int  # in cents / kopecks


@dataclass(frozen=True)
class Availability:
    """Number of available rooms of a given type on a date."""

    date: str  # YYYY-MM-DD
    room_type_id: str
    available_rooms: int


@dataclass(frozen=True)
class Guest:
    """Customer profile."""

    id: str
    name: str
    email: str
    phone: str
    loyalty_status: str = "standard"  # "standard", "silver", "gold", "platinum"


@dataclass(frozen=True)
class CartItem:
    """An item placed on hold or in cart."""

    id: str
    guest_id: str
    room_type_id: str
    rate_id: str
    checkin: str  # YYYY-MM-DD
    checkout: str  # YYYY-MM-DD
    guests_count: int
    total_price: int  # in cents / kopecks


@dataclass(frozen=True)
class Booking:
    """Confirmed booking containing one or more booked items."""

    id: str
    guest_id: str
    items: tuple[CartItem, ...]
    total: int  # in cents / kopecks
    status: str = "confirmed"  # "confirmed", "cancelled", "completed"


@dataclass(frozen=True)
class Payment:
    """Payment record."""

    id: str
    booking_id: str
    amount: int  # in cents / kopecks
    status: str = "succeeded"  # "pending", "succeeded", "failed", "refunded"
    timestamp: str = ""


@dataclass(frozen=True)
class Event:
    """Domain event for event sourcing / audit log."""

    id: str
    timestamp: str
    event_type: str
    payload: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True)
class Rule:
    """Serializable business / discount rule as defined in PDF spec.

    Fields:
      id: Unique rule identifier
      kind: Rule type (e.g. 'discount_pct', 'fixed_discount', 'vip_discount', 'early_bird')
      payload: Hashable tuple of rule parameters, e.g. (10,) or (500000,)
    """

    id: str
    kind: str
    payload: tuple[Any, ...] = ()
