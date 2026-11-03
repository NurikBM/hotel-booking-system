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
    beds: tuple[str, ...] | int = ()
    features: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.beds, int):
            object.__setattr__(self, "beds", tuple("single" for _ in range(self.beds)))
        elif isinstance(self.beds, (list, tuple)):
            object.__setattr__(self, "beds", tuple(str(b) for b in self.beds))


@dataclass(frozen=True)
class RatePlan:
    """Rate plan associated with a room type."""

    id: str
    room_type_id: str
    name: str = ""
    meals: str = "none"  # "none", "breakfast", "half-board", "all-inclusive"
    cancellation: str = "standard"  # "free", "non-refundable", "standard"
    price_factor: float = 1.0
    hotel_id: str = ""
    title: str = ""
    refundable: bool = True
    cancel_before_days: int = 1

    def __post_init__(self) -> None:
        if not self.title and self.name:
            object.__setattr__(self, "title", self.name)
        elif not self.name and self.title:
            object.__setattr__(self, "name", self.title)
        if self.cancellation == "non-refundable":
            object.__setattr__(self, "refundable", False)
            object.__setattr__(self, "cancel_before_days", 0)


@dataclass(frozen=True)
class Price:
    """Price for a specific rate plan on a specific calendar date.

    Amount is strictly an integer in cents / tiyn.
    """

    date: str  # YYYY-MM-DD
    rate_id: str
    amount: int  # in cents / tiyn
    id: str = ""
    currency: str = "KZT"

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"pr_{self.rate_id}_{self.date}")


@dataclass(frozen=True)
class Availability:
    """Number of available rooms of a given type on a date.

    Supports both spec name `available` and legacy alias `available_rooms`.
    """

    date: str  # YYYY-MM-DD
    room_type_id: str
    available_rooms: int = 0
    id: str = ""
    available: int = 0

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"av_{self.room_type_id}_{self.date}")
        if self.available == 0 and self.available_rooms != 0:
            object.__setattr__(self, "available", self.available_rooms)
        elif self.available_rooms == 0 and self.available != 0:
            object.__setattr__(self, "available_rooms", self.available)


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
