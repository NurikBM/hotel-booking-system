"""Core package for functional logic: Lab 1 (pricing, filters) and Lab 2 (fp_tools)."""

from core.filters import (
    filter_hotels_by_location,
    filter_hotels_by_min_rating,
    filter_rooms_by_capacity,
    filter_rooms_by_price,
    is_room_in_price_range,
)
from core.fp_tools import (
    make_amenity_filter,
    make_price_filter,
    recursive_aggregate_cities,
    recursive_aggregate_city,
    recursive_calculate_discount,
    recursive_count_rooms,
    recursive_find_cheapest_room,
    recursive_sum_capacity,
    sort_hotels_by_rating,
    sort_rooms_by_price,
)
from core.pricing import (
    apply_discount,
    calculate_average_hotel_rating,
    calculate_nights,
    calculate_stay_quote,
    calculate_total_price,
    calculate_total_revenue,
    extract_hotel_names,
    find_cheapest_room,
    transform_rooms_with_multiplier,
)

__all__ = [
    # Lab 1: pricing & transformations
    "calculate_nights",
    "calculate_total_price",
    "apply_discount",
    "calculate_stay_quote",
    "extract_hotel_names",
    "transform_rooms_with_multiplier",
    "calculate_total_revenue",
    "calculate_average_hotel_rating",
    "find_cheapest_room",
    # Lab 1: filters
    "is_room_in_price_range",
    "filter_rooms_by_price",
    "filter_rooms_by_capacity",
    "filter_hotels_by_min_rating",
    "filter_hotels_by_location",
    # Lab 2: closures & lambdas
    "make_price_filter",
    "make_amenity_filter",
    "sort_rooms_by_price",
    "sort_hotels_by_rating",
    # Lab 2: recursive algorithms
    "recursive_count_rooms",
    "recursive_sum_capacity",
    "recursive_aggregate_city",
    "recursive_aggregate_cities",
    "recursive_find_cheapest_room",
    "recursive_calculate_discount",
]
