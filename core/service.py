"""Service facades for Lab 7: Search, Quote and Booking services.

Facades contain NO business logic. Every method is a composition of pure functions that
are injected through the constructor (dependency injection). The default dependency
factories at the bottom of this module only adapt existing pure functions from
``core.transforms``, ``core.memo`` and ``core.ftypes`` to the injected signatures.

Types:
    Offer      = (Hotel, RoomType, RatePlan, total_price)  -- as streamed by lazy_offers
    OfferId    = (hotel_id, room_type_id, rate_id)
    Filter     = request dict -> predicate over Offer       (filter factory)
    Scorer     = Offer -> sortable key (lower is better)
    Quoter     = CartItem -> int (total amount in cents)
    Validator  = CartItem -> Either[dict, CartItem]
    Finalizer  = (Guest, tuple[CartItem, ...]) -> Either[dict, Booking]
"""

from __future__ import annotations

import dataclasses
import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from core.compose import all_of, pipe, rank_by
from core.domain import (
    Availability,
    Booking,
    CartItem,
    Guest,
    Hotel,
    Price,
    RatePlan,
    RoomType,
    Rule,
)
from core.ftypes import Either, Left, Right, safe_room_type, validate_booking
from core.ftypes import validate_cart_item as _validate_cart_item
from core.lazy import lazy_filter, lazy_map, take_lazy
from core.memo import quote_offer
from core.transforms import by_capacity, by_city, by_features, calculate_cart_total

Offer = tuple[Hotel, RoomType, RatePlan, int]
OfferId = tuple[str, str, str]
Filter = Callable[[dict], Callable[[Offer], bool]]
Scorer = Callable[[Offer], Any]
Quoter = Callable[[CartItem], int]
Validator = Callable[[CartItem], Either]
Finalizer = Callable[[Guest, tuple[CartItem, ...]], Either]


# ============================================================================
# PURE COMPOSITION HELPERS (wiring only)
# ============================================================================


def offer_id(offer: Offer) -> OfferId:
    """Project an offer onto its identifying triple."""
    hotel, room, rate, _price = offer
    return (hotel.id, room.id, rate.id)


def requote(quoter: Quoter) -> Callable[[CartItem], CartItem]:
    """Lift a quoter into a function returning a NEW CartItem carrying the quoted price."""
    return lambda item: dataclasses.replace(item, total_price=quoter(item))


def validate_all(
    validators: tuple[Validator, ...],
) -> Callable[[tuple[CartItem, ...]], Either]:
    """Run every validator over every cart item; stop at the first Left (railway fold)."""

    def check_item(item: CartItem) -> Either:
        return functools.reduce(lambda acc, v: acc.bind(v), validators, Right(item))

    def check_cart(cart: tuple[CartItem, ...]) -> Either:
        if not cart:
            return Left(
                {"code": "empty_cart", "message": "Cart contains no items to confirm."}
            )
        return functools.reduce(
            lambda acc, item: acc.bind(
                lambda items: check_item(item).map(lambda ok: (*items, ok))
            ),
            cart,
            Right(()),
        )

    return check_cart


# ============================================================================
# FACADES
# ============================================================================


@dataclass(frozen=True)
class SearchService:
    """Search facade: filters + scorers injected, offers streamed lazily.

    ``req`` keys:
        offers : iterable of Offer (e.g. the lazy_offers stream; consumed lazily)
        limit  : optional max number of results
        plus whatever keys the injected filter factories read (city, guests, ...).
    """

    filters: tuple[Filter, ...]
    scorers: tuple[Scorer, ...] = ()

    def search(self, req: dict) -> tuple[OfferId, ...]:
        predicate = all_of(*(make_filter(req) for make_filter in self.filters))
        limit = req.get("limit")
        take = (lambda s: take_lazy(s, limit)) if limit is not None else (lambda s: s)
        return pipe(
            req["offers"],
            lambda offers: lazy_filter(predicate, offers),
            rank_by(self.scorers),
            take,
            lambda offers: lazy_map(offer_id, offers),
            tuple,
        )


@dataclass(frozen=True)
class QuoteService:
    """Quote facade: delegates to the injected quoter."""

    quoter: Quoter

    def quote(self, item: CartItem) -> int:
        return pipe(item, self.quoter)


@dataclass(frozen=True)
class BookingService:
    """Booking facade: validate -> requote -> finalize, all injected."""

    validators: tuple[Validator, ...]
    quoter: Quoter
    finalizer: Finalizer

    def confirm(self, guest: Guest, cart: tuple[CartItem, ...]) -> Either:
        return (
            validate_all(self.validators)(cart)
            .map(lambda items: tuple(map(requote(self.quoter), items)))
            .bind(lambda quoted: self.finalizer(guest, quoted))
        )


# ============================================================================
# DEFAULT DEPENDENCY FACTORIES (adapters over existing pure functions)
# ============================================================================


def _always(_offer: Offer) -> bool:
    return True


def city_filter(req: dict) -> Callable[[Offer], bool]:
    if not req.get("city"):
        return _always
    pred = by_city(req["city"])
    return lambda offer: pred(offer[0])


def capacity_filter(req: dict) -> Callable[[Offer], bool]:
    if not req.get("guests"):
        return _always
    pred = by_capacity(req["guests"])
    return lambda offer: pred(offer[1])


def features_filter(req: dict) -> Callable[[Offer], bool]:
    if not req.get("features"):
        return _always
    pred = by_features(tuple(req["features"]))
    return lambda offer: pred(offer[0]) or pred(offer[1])


def budget_filter(req: dict) -> Callable[[Offer], bool]:
    if req.get("max_total") is None:
        return _always
    cap = req["max_total"]
    return lambda offer: offer[3] <= cap


DEFAULT_FILTERS: tuple[Filter, ...] = (
    city_filter,
    capacity_filter,
    features_filter,
    budget_filter,
)


def price_scorer(offer: Offer) -> int:
    return offer[3]


def stars_scorer(offer: Offer) -> int:
    return -offer[0].stars


DEFAULT_SCORERS: tuple[Scorer, ...] = (price_scorer,)


def make_quoter(
    room_types: tuple[RoomType, ...],
    prices: tuple[Price, ...],
    availability: tuple[Availability, ...],
    rules: tuple[Rule, ...],
) -> Quoter:
    """Quoter backed by the memoized ``quote_offer`` (Lab 3). Unknown room type -> 0."""

    def quoter(item: CartItem) -> int:
        return (
            safe_room_type(room_types, item.room_type_id)
            .map(
                lambda rt: quote_offer(
                    hotel_id=rt.hotel_id,
                    room_type_id=item.room_type_id,
                    rate_id=item.rate_id,
                    checkin=item.checkin,
                    checkout=item.checkout,
                    prices_idx=prices,
                    avail_idx=availability,
                    rules=rules,
                )[0]
            )
            .get_or_else(0)
        )

    return quoter


def make_item_validator(
    availability: tuple[Availability, ...],
    rules: tuple[Rule, ...],
    room_types: tuple[RoomType, ...],
    rates: tuple[RatePlan, ...],
) -> Validator:
    """CartItem validator backed by Lab 4 ``validate_cart_item``."""
    return lambda item: _validate_cart_item(
        item, availability, rules, room_types, rates
    )


def make_finalizer(
    prices: tuple[Price, ...],
    availability: tuple[Availability, ...],
    rules: tuple[Rule, ...],
    room_types: tuple[RoomType, ...],
    rates: tuple[RatePlan, ...],
) -> Finalizer:
    """Finalizer: build a Booking from quoted items, then run Lab 4 ``validate_booking``."""

    def finalize(guest: Guest, items: tuple[CartItem, ...]) -> Either:
        booking = Booking(
            id=f"bk_{guest.id}_{items[0].id}",
            guest_id=guest.id,
            items=items,
            total=calculate_cart_total(items),
            status="confirmed",
        )
        return validate_booking(booking, prices, availability, rules, room_types, rates)

    return finalize


def build_services(
    room_types: tuple[RoomType, ...],
    rates: tuple[RatePlan, ...],
    prices: tuple[Price, ...],
    availability: tuple[Availability, ...],
    rules: tuple[Rule, ...],
) -> tuple[SearchService, QuoteService, BookingService]:
    """Composition root: the one place where concrete dependencies are wired in."""
    quoter = make_quoter(room_types, prices, availability, rules)
    return (
        SearchService(DEFAULT_FILTERS, DEFAULT_SCORERS),
        QuoteService(quoter),
        BookingService(
            validators=(make_item_validator(availability, rules, room_types, rates),),
            quoter=quoter,
            finalizer=make_finalizer(prices, availability, rules, room_types, rates),
        ),
    )


__all__: list[str] = [
    "BookingService",
    "QuoteService",
    "SearchService",
    "DEFAULT_FILTERS",
    "DEFAULT_SCORERS",
    "build_services",
    "make_finalizer",
    "make_item_validator",
    "make_quoter",
    "offer_id",
    "requote",
    "validate_all",
]
