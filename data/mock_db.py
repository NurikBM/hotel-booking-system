"""Mock In-Memory Database: Sample immutable data for development and testing.

Coursework Lab 1: Sample domain instances.
All records are instantiated as immutable dataclasses.
Returns immutable tuples or deep copies to protect against unexpected mutations.
"""

from __future__ import annotations

from datetime import date, datetime
from domain.models import Booking, Hotel, Review, Room

# Sample Hotels
SAMPLE_HOTELS: tuple[Hotel, ...] = (
    Hotel(
        id="h1",
        name="Grand Azure Palace",
        location="Nice",
        rating=4.8,
        amenities=("WiFi", "Pool", "Spa", "Ocean View", "Restaurant"),
        room_ids=("r101", "r102"),
    ),
    Hotel(
        id="h2",
        name="Alpine Pine Retreat",
        location="Chamonix",
        rating=4.6,
        amenities=("WiFi", "Sauna", "Ski Storage", "Fireplace"),
        room_ids=("r201", "r202"),
    ),
    Hotel(
        id="h3",
        name="Lumiere City Center Hotel",
        location="Paris",
        rating=4.2,
        amenities=("WiFi", "Gym", "Breakfast Buffet", "Business Center"),
        room_ids=("r301", "r302"),
    ),
)

# Sample Rooms
SAMPLE_ROOMS: tuple[Room, ...] = (
    Room(
        id="r101",
        hotel_id="h1",
        room_type="Deluxe Sea View",
        base_price=220.0,
        capacity=2,
        amenities=("Balcony", "King Bed", "Minibar", "AC"),
    ),
    Room(
        id="r102",
        hotel_id="h1",
        room_type="Presidential Suite",
        base_price=550.0,
        capacity=4,
        amenities=("Jacuzzi", "Balcony", "Kitchenette", "Butler Service"),
    ),
    Room(
        id="r201",
        hotel_id="h2",
        room_type="Standard Mountain Chalet",
        base_price=130.0,
        capacity=2,
        amenities=("Heated Floors", "Mountain View", "Tea Maker"),
    ),
    Room(
        id="r202",
        hotel_id="h2",
        room_type="Family Ski Suite",
        base_price=310.0,
        capacity=5,
        amenities=("Fireplace", "Bunk Beds", "Balcony", "Kitchenette"),
    ),
    Room(
        id="r301",
        hotel_id="h3",
        room_type="Standard Single",
        base_price=85.0,
        capacity=1,
        amenities=("Desk", "Coffee Maker", "AC"),
    ),
    Room(
        id="r302",
        hotel_id="h3",
        room_type="Superior Double",
        base_price=145.0,
        capacity=2,
        amenities=("Queen Bed", "Desk", "City View", "AC"),
    ),
)

# Sample Bookings
SAMPLE_BOOKINGS: tuple[Booking, ...] = (
    Booking(
        id="b1",
        room_id="r101",
        guest_name="Alice Martin",
        check_in=date(2026, 6, 1),
        check_out=date(2026, 6, 5),
        total_price=880.0,
        status="CONFIRMED",
    ),
    Booking(
        id="b2",
        room_id="r201",
        guest_name="Bob Henderson",
        check_in=date(2026, 7, 10),
        check_out=date(2026, 7, 15),
        total_price=650.0,
        status="CONFIRMED",
    ),
    Booking(
        id="b3",
        room_id="r301",
        guest_name="Claire Dubois",
        check_in=date(2026, 8, 2),
        check_out=date(2026, 8, 4),
        total_price=170.0,
        status="CONFIRMED",
    ),
    Booking(
        id="b4",
        room_id="r102",
        guest_name="Daniel Craig",
        check_in=date(2026, 6, 20),
        check_out=date(2026, 6, 23),
        total_price=1650.0,
        status="CANCELLED",
    ),
    Booking(
        id="b5",
        room_id="r302",
        guest_name="Emma Watson",
        check_in=date(2026, 9, 1),
        check_out=date(2026, 9, 7),
        total_price=870.0,
        status="CONFIRMED",
    ),
)

# Sample Reviews
SAMPLE_REVIEWS: tuple[Review, ...] = (
    Review(
        id="rev1",
        hotel_id="h1",
        rating=5.0,
        comment="Breathtaking ocean views and impeccable service.",
        timestamp=datetime(2026, 6, 6, 10, 30),
    ),
    Review(
        id="rev2",
        hotel_id="h1",
        rating=4.5,
        comment="Lovely pool and spa. Breakfast was slightly crowded.",
        timestamp=datetime(2026, 6, 12, 14, 15),
    ),
    Review(
        id="rev3",
        hotel_id="h2",
        rating=4.7,
        comment="Perfect ski-in ski-out location. Cozy fireplace!",
        timestamp=datetime(2026, 7, 16, 9, 0),
    ),
    Review(
        id="rev4",
        hotel_id="h3",
        rating=4.0,
        comment="Very central and convenient for sightseeing in Paris.",
        timestamp=datetime(2026, 8, 5, 11, 45),
    ),
)


def get_sample_hotels() -> list[Hotel]:
    """Return a fresh list of sample Hotel records."""
    return list(SAMPLE_HOTELS)


def get_sample_rooms() -> list[Room]:
    """Return a fresh list of sample Room records."""
    return list(SAMPLE_ROOMS)


def get_sample_bookings() -> list[Booking]:
    """Return a fresh list of sample Booking records."""
    return list(SAMPLE_BOOKINGS)


def get_sample_reviews() -> list[Review]:
    """Return a fresh list of sample Review records."""
    return list(SAMPLE_REVIEWS)
