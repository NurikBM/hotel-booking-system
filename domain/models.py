"""Domain Models: Hotel & Room Booking System.

Coursework Lab 1: Pure functional domain entities.
All domain entities are strictly immutable (@dataclass(frozen=True)).
Immutability guarantees thread safety, prevents unexpected side-effects,
and supports pure functional transformations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Sequence


@dataclass(frozen=True)
class Hotel:
    """Immutable representation of a Hotel entity.

    Attributes:
        id: Unique hotel identifier.
        name: Name of the hotel.
        location: City or area location.
        rating: Average customer rating (0.0 - 5.0).
        amenities: Tuple of provided amenities (e.g. 'WiFi', 'Pool').
        room_ids: Tuple of room identifiers belonging to this hotel.
    """

    id: str
    name: str
    location: str
    rating: float
    amenities: tuple[str, ...]
    room_ids: tuple[str, ...]

    def __init__(
        self,
        id: str,
        name: str,
        location: str,
        rating: float,
        amenities: Sequence[str] = (),
        room_ids: Sequence[str] = (),
    ) -> None:
        """Initialize Hotel and enforce tuple conversion for deep immutability."""
        object.__setattr__(self, "id", str(id))
        object.__setattr__(self, "name", str(name))
        object.__setattr__(self, "location", str(location))
        object.__setattr__(self, "rating", float(rating))
        object.__setattr__(self, "amenities", tuple(amenities))
        object.__setattr__(self, "room_ids", tuple(room_ids))


@dataclass(frozen=True)
class Room:
    """Immutable representation of a Room entity.

    Attributes:
        id: Unique room identifier.
        hotel_id: Foreign key to the parent hotel.
        room_type: Category (e.g. 'Standard', 'Deluxe', 'Suite').
        base_price: Nightly base rate in USD.
        capacity: Maximum guest capacity.
        amenities: Tuple of specific room amenities (e.g. 'Balcony', 'AC').
    """

    id: str
    hotel_id: str
    room_type: str
    base_price: float
    capacity: int
    amenities: tuple[str, ...]

    def __init__(
        self,
        id: str,
        hotel_id: str,
        room_type: str,
        base_price: float,
        capacity: int,
        amenities: Sequence[str] = (),
    ) -> None:
        """Initialize Room and enforce tuple conversion for deep immutability."""
        object.__setattr__(self, "id", str(id))
        object.__setattr__(self, "hotel_id", str(hotel_id))
        object.__setattr__(self, "room_type", str(room_type))
        object.__setattr__(self, "base_price", float(base_price))
        object.__setattr__(self, "capacity", int(capacity))
        object.__setattr__(self, "amenities", tuple(amenities))


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
