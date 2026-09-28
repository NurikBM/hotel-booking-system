"""Domain Models: Hotel & Room Booking System.

Coursework Lab 1 & Lab 2: Immutable domain entities.
All domain entities are declared as `@dataclass(frozen=True)` without custom __init__.
Immutability guarantees thread safety, prevents unexpected side effects,
and enforces pure functional programming principles.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Hotel:
    """Immutable representation of a Hotel entity.

    Attributes:
        id: Unique hotel identifier.
        name: Name of the hotel.
        location: City or area location.
        rating: Average customer rating (0.0 - 5.0).
        amenities: Tuple of provided amenities.
        room_ids: Tuple of room identifiers belonging to this hotel.
    """

    id: str
    name: str
    location: str
    rating: float
    amenities: tuple[str, ...]
    room_ids: tuple[str, ...]


@dataclass(frozen=True)
class Room:
    """Immutable representation of a Room entity.

    Attributes:
        id: Unique room identifier.
        hotel_id: Foreign key to the parent hotel.
        room_type: Category (e.g. 'Standard', 'Deluxe', 'Suite').
        base_price: Nightly base rate in USD.
        capacity: Maximum guest capacity.
        amenities: Tuple of specific room amenities.
    """

    id: str
    hotel_id: str
    room_type: str
    base_price: float
    capacity: int
    amenities: tuple[str, ...]


@dataclass(frozen=True)
class Booking:
    """Immutable representation of a customer Booking.

    Attributes:
        id: Unique booking identifier.
        room_id: Identifier of the reserved room.
        guest_name: Full name of the primary guest.
        check_in: Reservation start date.
        check_out: Reservation departure date.
        total_price: Final calculated cost for the reservation.
        status: Current status (e.g. 'CONFIRMED', 'CANCELLED', 'PENDING').
    """

    id: str
    room_id: str
    guest_name: str
    check_in: date
    check_out: date
    total_price: float
    status: str


@dataclass(frozen=True)
class Review:
    """Immutable customer review and rating for a hotel.

    Attributes:
        id: Unique review identifier.
        hotel_id: Target hotel identifier.
        rating: Score given by guest (1.0 - 5.0).
        comment: Written feedback text.
        timestamp: Review submission date and time.
    """

    id: str
    hotel_id: str
    rating: float
    comment: str
    timestamp: datetime


@dataclass(frozen=True)
class HotelNode:
    """Hotel node holding nested rooms for recursive hierarchy processing."""

    id: str
    name: str
    rating: float
    rooms: tuple[Room, ...]


@dataclass(frozen=True)
class City:
    """City node holding nested hotels for recursive hierarchy processing."""

    name: str
    hotels: tuple[HotelNode, ...]


@dataclass(frozen=True)
class DiscountNode:
    """Recursive discount structure: discount percentage and possible sub-discounts."""

    name: str
    percentage: float
    sub_discounts: tuple[DiscountNode, ...] = ()
