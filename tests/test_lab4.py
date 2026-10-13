"""Unit tests for Lab 4: Functional Monads (Maybe/Either) & Pure Booking Validation.

Covers:
  - Maybe monad: Some and Nothing with map, bind, get_or_else
  - Either monad: Right and Left with map, bind, get_or_else
  - maybe_to_either monad bridge
  - safe_rate and safe_room_type lookups
  - validate_dates without exceptions across invalid, out-of-range, and malformed inputs
  - validate_cart_item: capacity, rate mismatch, min/max stay, availability
  - validate_booking: empty bookings, missing prices, cancellation policies
  - validate_and_calculate_booking monadic composition & price equivalence
  - Static AST inspection verifying absence of try/except/raise in core/ftypes.py
  - Part 0 regression: recursive_apply_rules ignoring min_stay/max_stay
"""

from __future__ import annotations

import ast
import os

import pytest

from core.domain import (
    Availability,
    Booking,
    CartItem,
    Price,
    RatePlan,
    Rule,
)
from core.ftypes import (
    DEFAULT_RULES,
    Left,
    Nothing,
    Right,
    Some,
    maybe_to_either,
    safe_rate,
    safe_room_type,
    validate_and_calculate_booking,
    validate_booking,
    validate_cart_item,
    validate_dates,
)
from core.memo import quote_offer
from core.recursion import recursive_apply_rules
from core.transforms import load_seed


@pytest.fixture(scope="module")
def seed_data():
    seed_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")
    return load_seed(seed_path)


def test_maybe_monad_laws_and_operations():
    """Verify Some and Nothing support map, bind, get_or_else and short-circuit on Nothing."""
    # Some operations
    some_val = Some(42)
    assert some_val.value == 42
    assert some_val.map(lambda x: x * 2) == Some(84)
    assert some_val.bind(lambda x: Some(f"val-{x}")) == Some("val-42")
    assert some_val.bind(lambda x: Nothing()) == Nothing()
    assert some_val.get_or_else(0) == 42

    # Nothing operations: function must not be invoked
    invoked = False

    def explode(x):
        nonlocal invoked
        invoked = True
        return x + 1

    nothing_val = Nothing()
    assert nothing_val.map(explode) == Nothing()
    assert not invoked
    assert nothing_val.bind(explode) == Nothing()
    assert not invoked
    assert nothing_val.get_or_else(100) == 100

    # maybe_to_either bridge
    err_dict = {"code": "not_found", "message": "Item missing"}
    assert maybe_to_either(Some("found"), err_dict) == Right("found")
    assert maybe_to_either(Nothing(), err_dict) == Left(err_dict)


def test_either_monad_laws_and_operations():
    """Verify Right and Left support map, bind, get_or_else and preserve errors on Left."""
    # Right operations
    right_val = Right(100)
    assert right_val.value == 100
    assert right_val.map(lambda x: x + 50) == Right(150)
    assert right_val.bind(lambda x: Right(x * 2)) == Right(200)
    assert right_val.bind(lambda x: Left({"code": "err"})) == Left({"code": "err"})
    assert right_val.get_or_else(0) == 100

    # Left operations: short-circuiting
    invoked = False

    def explode(x):
        nonlocal invoked
        invoked = True
        return x + 1

    err_payload = {"code": "initial_error", "message": "Failed"}
    left_val = Left(err_payload)
    assert left_val.error == err_payload
    assert left_val.map(explode) == Left(err_payload)
    assert not invoked
    assert left_val.bind(explode) == Left(err_payload)
    assert not invoked
    assert left_val.get_or_else(999) == 999


def test_safe_lookups(seed_data):
    """Verify safe_rate and safe_room_type return Some when found and Nothing when absent."""
    _, rooms, rates, _, _, _ = seed_data

    # Valid lookups
    valid_rate_id = rates[0].id
    rate_res = safe_rate(rates, valid_rate_id)
    assert isinstance(rate_res, Some)
    assert rate_res.value.id == valid_rate_id

    valid_room_id = rooms[0].id
    room_res = safe_room_type(rooms, valid_room_id)
    assert isinstance(room_res, Some)
    assert room_res.value.id == valid_room_id

    # Non-existent lookups
    assert safe_rate(rates, "non_existent_rate_999") == Nothing()
    assert safe_room_type(rooms, "non_existent_room_999") == Nothing()


@pytest.mark.parametrize(
    "cin,cout,expected_code",
    [
        ("", "2026-06-05", "invalid_date"),
        ("2026-6-1", "2026-06-05", "invalid_date"),
        ("2026-02-30", "2026-06-05", "invalid_date"),
        ("2026-13-01", "2026-06-05", "invalid_date"),
        ("0000-01-01", "2026-06-05", "invalid_date"),
        ("2026-06-05", "2026-06-05", "invalid_date_range"),
        ("2026-06-10", "2026-06-05", "invalid_date_range"),
        ("2026-06-01", "not-a-date", "invalid_date"),
    ],
)
def test_validate_dates_invalid_inputs_no_exceptions(cin, cout, expected_code):
    """Verify validate_dates safely catches all malformed and illogical inputs without raising."""
    res = validate_dates(cin, cout)
    assert isinstance(res, Left)
    assert res.error["code"] == expected_code


def test_validate_dates_valid():
    """Verify validate_dates returns Right with tuple of nights for valid ranges."""
    res = validate_dates("2026-06-01", "2026-06-04")
    assert isinstance(res, Right)
    assert res.value == ("2026-06-01", "2026-06-02", "2026-06-03")


def test_validate_cart_item_success(seed_data):
    """Verify validate_cart_item accepts a legitimate cart item from seed data."""
    _, rooms, rates, _, avails, _ = seed_data

    item = CartItem(
        id="cart_001",
        guest_id="guest_001",
        room_type_id="rt_h_almaty_rixos_1",
        rate_id="rp_rt_h_almaty_rixos_1_standard",
        checkin="2026-06-01",
        checkout="2026-06-05",
        guests_count=1,
        total_price=0,
    )

    res = validate_cart_item(
        item,
        availability=avails,
        rules=DEFAULT_RULES,
        room_types=rooms,
        rates=rates,
    )
    assert isinstance(res, Right)
    assert res.value == item


def test_validate_cart_item_capacity_exceeded(seed_data):
    """Verify validate_cart_item detects capacity violation."""
    _, rooms, rates, _, avails, _ = seed_data

    # Room capacity is 1, requesting 5 guests
    item = CartItem(
        id="cart_cap",
        guest_id="guest_001",
        room_type_id="rt_h_almaty_rixos_1",
        rate_id="rp_rt_h_almaty_rixos_1_standard",
        checkin="2026-06-01",
        checkout="2026-06-03",
        guests_count=5,
        total_price=0,
    )

    res = validate_cart_item(
        item,
        availability=avails,
        rules=DEFAULT_RULES,
        room_types=rooms,
        rates=rates,
    )
    assert isinstance(res, Left)
    assert res.error["code"] == "capacity_exceeded"
    assert res.error["capacity"] == 1


def test_validate_cart_item_stay_duration_limits(seed_data):
    """Verify validate_cart_item enforces min_stay and max_stay rules."""
    _, rooms, rates, _, avails, _ = seed_data

    item_short = CartItem(
        id="cart_short",
        guest_id="guest_001",
        room_type_id="rt_h_almaty_rixos_1",
        rate_id="rp_rt_h_almaty_rixos_1_standard",
        checkin="2026-06-01",
        checkout="2026-06-03",  # 2 nights
        guests_count=1,
        total_price=0,
    )

    # Rule requiring min 5 nights
    rules_min5 = (Rule(id="r_min5", kind="min_stay", payload=(5,)),)
    res_min = validate_cart_item(
        item_short,
        availability=avails,
        rules=rules_min5,
        room_types=rooms,
        rates=rates,
    )
    assert isinstance(res_min, Left)
    assert res_min.error["code"] == "min_stay_violation"

    # Rule restricting max to 1 night
    rules_max1 = (Rule(id="r_max1", kind="max_stay", payload=(1,)),)
    res_max = validate_cart_item(
        item_short,
        availability=avails,
        rules=rules_max1,
        room_types=rooms,
        rates=rates,
    )
    assert isinstance(res_max, Left)
    assert res_max.error["code"] == "max_stay_violation"


def test_validate_cart_item_unavailable_date(seed_data):
    """Verify validate_cart_item returns not_available with specific unavailable date."""
    _, rooms, rates, _, _, _ = seed_data

    # Create artificial availability with 0 rooms on 2026-06-03
    custom_avails = (
        Availability(
            date="2026-06-01", room_type_id="rt_h_almaty_rixos_1", available_rooms=2
        ),
        Availability(
            date="2026-06-02", room_type_id="rt_h_almaty_rixos_1", available_rooms=2
        ),
        Availability(
            date="2026-06-03", room_type_id="rt_h_almaty_rixos_1", available_rooms=0
        ),  # sold out!
        Availability(
            date="2026-06-04", room_type_id="rt_h_almaty_rixos_1", available_rooms=2
        ),
    )

    item = CartItem(
        id="cart_unavail",
        guest_id="guest_001",
        room_type_id="rt_h_almaty_rixos_1",
        rate_id="rp_rt_h_almaty_rixos_1_standard",
        checkin="2026-06-01",
        checkout="2026-06-05",
        guests_count=1,
        total_price=0,
    )

    res = validate_cart_item(
        item,
        availability=custom_avails,
        rules=(),
        room_types=rooms,
        rates=rates,
    )
    assert isinstance(res, Left)
    assert res.error["code"] == "not_available"
    assert res.error["date"] == "2026-06-03"


def test_validate_booking_empty_and_failures(seed_data):
    """Verify validate_booking validates items, price holes, and cancellation policies."""
    _, rooms, rates, prices, avails, _ = seed_data

    # 1. Empty booking
    empty_b = Booking(id="b_empty", guest_id="g1", items=(), total=0)
    res_empty = validate_booking(empty_b, prices, avails, (), rooms, rates)
    assert isinstance(res_empty, Left)
    assert res_empty.error["code"] == "empty_booking"

    # 2. Missing prices outside seed calendar (after 2026-07-30)
    future_item = CartItem(
        id="cart_future",
        guest_id="g1",
        room_type_id="rt_h_almaty_rixos_1",
        rate_id="rp_rt_h_almaty_rixos_1_standard",
        checkin="2026-08-01",
        checkout="2026-08-05",
        guests_count=1,
        total_price=0,
    )
    # Give future availability so availability passes
    future_avails = tuple(
        Availability(
            date=f"2026-08-0{i}", room_type_id="rt_h_almaty_rixos_1", available_rooms=5
        )
        for i in range(1, 6)
    )
    future_booking = Booking(
        id="b_future", guest_id="g1", items=(future_item,), total=0
    )
    res_price = validate_booking(
        future_booking, prices, future_avails, (), rooms, rates
    )
    assert isinstance(res_price, Left)
    assert res_price.error["code"] == "price_missing"
    assert "dates" in res_price.error

    # 3. Non-refundable cancellation check
    non_ref_rate = RatePlan(
        id="rp_non_ref",
        room_type_id="rt_h_almaty_rixos_1",
        name="Non Refundable Promo",
        cancellation="non-refundable",
    )
    custom_rates = (*rates, non_ref_rate)
    custom_prices = (
        *prices,
        Price(date="2026-06-01", rate_id="rp_non_ref", amount=2000000),
        Price(date="2026-06-02", rate_id="rp_non_ref", amount=2000000),
    )
    cancelled_item = CartItem(
        id="cart_nonref",
        guest_id="g1",
        room_type_id="rt_h_almaty_rixos_1",
        rate_id="rp_non_ref",
        checkin="2026-06-01",
        checkout="2026-06-03",
        guests_count=1,
        total_price=0,
    )
    cancelled_booking = Booking(
        id="b_cancel",
        guest_id="g1",
        items=(cancelled_item,),
        total=0,
        status="cancelled",
    )
    res_cancel = validate_booking(
        cancelled_booking, custom_prices, avails, (), rooms, custom_rates
    )
    assert isinstance(res_cancel, Left)
    assert res_cancel.error["code"] == "non_refundable_cancel"


def test_validate_and_calculate_booking_end_to_end(seed_data):
    """Verify validate_and_calculate_booking produces exact recalculated prices matching pure domain."""
    _hotels, rooms, rates, prices, avails, guests = seed_data

    guest = guests[0]
    item1 = CartItem(
        id="cart_e2e_1",
        guest_id=guest.id,
        room_type_id="rt_h_almaty_rixos_1",
        rate_id="rp_rt_h_almaty_rixos_1_standard",
        checkin="2026-06-01",
        checkout="2026-06-05",  # 4 nights
        guests_count=1,
        total_price=0,
    )

    items = (item1,)
    rules = DEFAULT_RULES

    res = validate_and_calculate_booking(
        booking_id="booking_confirmed_101",
        guest=guest,
        items=items,
        prices=prices,
        availability=avails,
        rules=rules,
        room_types=rooms,
        rates=rates,
    )

    assert isinstance(res, Right)
    final_booking = res.value
    assert final_booking.id == "booking_confirmed_101"
    assert final_booking.guest_id == guest.id
    assert final_booking.status == "confirmed"
    assert len(final_booking.items) == 1

    # Verify immutability of input item
    assert item1.total_price == 0
    recalculated_item = final_booking.items[0]
    assert recalculated_item.total_price > 0
    assert final_booking.total == recalculated_item.total_price

    # Verify price calculation equals independent quote_offer
    expected_price, is_avail = quote_offer(
        hotel_id="h_almaty_rixos",
        room_type_id="rt_h_almaty_rixos_1",
        rate_id="rp_rt_h_almaty_rixos_1_standard",
        checkin="2026-06-01",
        checkout="2026-06-05",
        prices_idx=prices,
        avail_idx=avails,
        rules=rules,
    )
    assert is_avail is True
    assert final_booking.total == expected_price


def test_ast_no_try_except_raise_in_core_ftypes():
    """Verify core/ftypes.py contains no try/except statements or raise keywords via AST."""
    ftypes_path = os.path.join(os.path.dirname(__file__), "..", "core", "ftypes.py")
    with open(ftypes_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename="core/ftypes.py")

    disallowed_nodes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Try, ast.Raise)):
            disallowed_nodes.append((type(node).__name__, getattr(node, "lineno", 0)))
        # Python 3.11+ ast.TryStar
        if hasattr(ast, "TryStar") and isinstance(node, ast.TryStar):
            disallowed_nodes.append((type(node).__name__, getattr(node, "lineno", 0)))

    assert (
        not disallowed_nodes
    ), f"Forbidden AST nodes found in core/ftypes.py: {disallowed_nodes}"


def test_regression_part0_recursive_apply_rules():
    """Verify recursive_apply_rules ignores min_stay and max_stay validation rules."""
    rules = (
        Rule(id="r1", kind="min_stay", payload=(3,)),
        Rule(id="r2", kind="max_stay", payload=(10,)),
    )
    base_price = 5000000
    res = recursive_apply_rules(base_price, rules)
    assert (
        res == base_price
    ), "recursive_apply_rules must ignore validation rules min_stay and max_stay"


def test_streamlit_app_apptest_first_render_and_lab4():
    """Verify Streamlit AppTest performs clean first render and interactive Lab 4 clicks with no exceptions."""
    from streamlit.testing.v1 import AppTest

    app_path = os.path.join(os.path.dirname(__file__), "..", "streamlit_app.py")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()
    assert not at.exception, f"First render error: {at.exception}"

    # Verify clicking Lab 4 button in Functional Core
    btn_val_item = at.button(key="l4_fc_btn_validate_item")
    assert btn_val_item is not None
    btn_val_item.click().run()
    assert not at.exception, f"Click error: {at.exception}"

    # Verify clicking Lab 4 button in Reports
    btn_val_booking = at.button(key="l4_rep_btn_run_scenario")
    assert btn_val_booking is not None
    btn_val_booking.click().run()
    assert not at.exception, f"Click error: {at.exception}"
