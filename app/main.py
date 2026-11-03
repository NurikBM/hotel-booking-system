"""Streamlit Web Application for Hotel / Room Booking System.

Pure Functional Programming Coursework:
Tabs:
1. Overview: Architecture, Lab 1–3 concepts & key dataset metrics.
2. Data: Interactive seed database viewer (seed.json).
3. Functional Core: Closures, lambdas & recursive algorithms (Lab 2).
4. Pipelines: Map/Reduce, cart holds & Lab 3 memoization / speedup benchmark.
5. Async/FRP: Architectural preview for Lab 6 & Lab 8.
6. Reports: Pure statistical summaries & distributions.
7. Tests: Interactive pytest execution across test_lab1, test_lab2, test_lab3.
8. About: Academic specification, course standards & invariants.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import streamlit as st

# Core functional imports
from core.domain import (
    Availability,
    CartItem,
    Guest,
    Hotel,
    Price,
    RatePlan,
    RoomType,
    Rule,
)
from core.ftypes import (
    DEFAULT_RULES,
    Left,
    Right,
    Some,
    safe_rate,
    validate_and_calculate_booking,
    validate_cart_item,
)
from core.lazy import (
    drop_lazy,
    lazy_calendar_stream,
    lazy_offers,
    take_lazy,
)
from core.memo import (
    benchmark_speedup,
    memoize,
    memoized_nightly_sum,
    quote_offer,
    quote_offer_unmemoized,
)
from core.recursion import (
    recursive_apply_rules,
    recursive_find_cheapest_quote,
    recursive_search_available_quotes,
)
from core.transforms import (
    by_city,
    calculate_cart_total,
    hold_item,
    load_seed,
    nightly_sum,
    remove_hold,
)


@st.cache_data
def get_seed_data() -> tuple[
    tuple[Hotel, ...],
    tuple[RoomType, ...],
    tuple[RatePlan, ...],
    tuple[Price, ...],
    tuple[Availability, ...],
    tuple[Guest, ...],
]:
    seed_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")
    return load_seed(seed_path)


def format_cents(cents: int) -> str:
    """Format integer cents/tiyn into readable currency string."""
    return f"{cents / 100:,.2f} KZT"


def main() -> None:
    st.set_page_config(
        page_title="Hotel FP System (Labs 1–5)",
        page_icon="🏨",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    # Header Banner
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid #334155; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 style="margin: 0; font-size: 1.8rem; font-weight: 700; color: #f8fafc;">🏨 Hotel Booking FP System</h1>
                    <p style="margin: 0.3rem 0 0 0; color: #94a3b8; font-size: 0.95rem;">
                        Pure Functional Architecture &middot; Immutable Domain &middot; Closures &middot; Recursion &middot; Memoization
                    </p>
                </div>
                <div style="text-align: right;">
                    <span style="background: #0369a1; color: #e0f2fe; padding: 0.35rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                        Lab 1 + Lab 2 + Lab 3 + Lab 4 + Lab 5
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hotels, room_types, rate_plans, prices, availabilities, guests = get_seed_data()

    # Session state for cart simulation
    if "cart" not in st.session_state:
        st.session_state.cart = ()

    # 8 Main Tabs according to spec
    tabs = st.tabs(
        [
            "Overview",
            "Data",
            "Functional Core",
            "Pipelines",
            "Async/FRP",
            "Reports",
            "Tests",
            "About",
        ]
    )

    # ========================================================================
    # TAB 1: OVERVIEW
    # ========================================================================
    with tabs[0]:
        st.subheader("System Architecture & Lab Status")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Hotels", len(hotels))
        with col2:
            st.metric("Room Types", len(room_types))
        with col3:
            st.metric("Rate Plans", len(rate_plans))
        with col4:
            st.metric("Price Records", len(prices))
        with col5:
            st.metric("Guests", len(guests))

        st.markdown("---")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown("""
                ### 🧱 Lab 1: Immutable Domain
                - **Pure Data Structures**: `@dataclass(frozen=True)` without mutation.
                - **Strict Money Math**: All amounts stored in integer cents/tiyn.
                - **ISO-8601 Dates**: Standardized `"YYYY-MM-DD"` string calendar.
                - **Functional Transforms**: `load_seed`, `hold_item`, `remove_hold`.
                - **Fold Aggregation**: `nightly_sum` implemented via `functools.reduce`.
                """)
        with c2:
            st.markdown("""
                ### 🔀 Lab 2: Closures & Recursion
                - **Closure Predicates**: `by_city`, `by_capacity`, `by_features`.
                - **First-Class Lambdas**: Functional sorters and combinators.
                - **Recursive Tree Search**: `recursive_search_available_quotes` navigates Hotels -> Rooms -> Rates without loops.
                - **Recursive Rules**: `recursive_apply_rules` applies business discounts sequentially.
                - **Recursive Extremum**: `recursive_find_cheapest_quote` finds minimum without loops.
                """)
        with c3:
            st.markdown("""
                ### ⚡ Lab 3: Pure Memoization
                - **Higher-Order Decorator**: `@memoize(maxsize)` with LRU eviction.
                - **Introspection**: `cache_info()` (hits, misses, currsize, hit ratio).
                - **Cache Eviction**: Configurable size bounds & pure `cache_clear()`.
                - **Specialized Pricing**: `memoized_nightly_sum` and quote calculators.
                - **Benchmark Suite**: Rigorous 250+ iteration performance test proving 10x–50x speedups.
                """)
        with c4:
            st.markdown("""
                ### 🛡️ Lab 4: Monadic Validation
                - **Pure Containers**: `Maybe[T]` (`Some`/`Nothing`) & `Either[E, T]` (`Right`/`Left`).
                - **Monadic Methods**: `map`, `bind`, `get_or_else` without exceptions.
                - **Pure Lookups**: `safe_room_type`, `safe_rate`, `maybe_to_either`.
                - **Validation Pipeline**: `validate_dates`, `validate_cart_item`, `validate_booking`.
                - **Pure Composition**: `validate_and_calculate_booking` returns `Right(Booking)` or `Left(error)`.
                """)
        with c5:
            st.markdown("""
                ### ⏳ Lab 5: Lazy Evaluation
                - **Pure Generators**: `yield`-based iterators evaluated on demand.
                - **Calendar Streams**: `lazy_calendar_stream` for continuous dates.
                - **Availability**: `iter_available_days` yields without list materialization.
                - **Deferred Offers**: `lazy_offers` streams matching offers.
                - **Stream Combinators**: `take_lazy` and `drop_lazy` for lazy pagination.
                """)

    # ========================================================================
    # TAB 2: DATA EXPLORER
    # ========================================================================
    with tabs[1]:
        st.subheader("Seed Dataset Explorer (`data/seed.json`)")

        subtab1, subtab2, subtab3, subtab4 = st.tabs(
            ["Hotels", "Room Types", "Rate Plans", "Guests"]
        )

        with subtab1:
            city_filter = st.selectbox(
                "Filter by City", ["All"] + sorted({h.city for h in hotels})
            )
            filtered_hotels = (
                hotels
                if city_filter == "All"
                else tuple(filter(by_city(city_filter), hotels))
            )

            for h in filtered_hotels:
                with st.expander(f"{'⭐' * h.stars} {h.name} ({h.city})"):
                    st.write(f"**Hotel ID:** `{h.id}`")
                    st.write(f"**City:** {h.city} &middot; **Stars:** {h.stars}")
                    st.write(f"**Features:** {', '.join(h.features)}")
                    hotel_rooms = tuple(r for r in room_types if r.hotel_id == h.id)
                    st.write(f"**Available Room Categories:** {len(hotel_rooms)}")

        with subtab2:
            st.write(f"Total room types defined: **{len(room_types)}**")
            table_rooms = [
                {
                    "ID": r.id,
                    "Hotel ID": r.hotel_id,
                    "Name": r.name,
                    "Capacity": r.capacity,
                    "Beds": r.beds,
                    "Features": ", ".join(r.features),
                }
                for r in room_types[:15]
            ]
            st.table(table_rooms)

        with subtab3:
            st.write(f"Total rate plans defined: **{len(rate_plans)}**")
            table_rates = [
                {
                    "ID": rp.id,
                    "Room Type ID": rp.room_type_id,
                    "Name": rp.name,
                    "Meals": rp.meals,
                    "Cancellation": rp.cancellation,
                    "Price Factor": rp.price_factor,
                }
                for rp in rate_plans[:15]
            ]
            st.table(table_rates)

        with subtab4:
            st.write(f"Sample guests registered: **{len(guests)}**")
            table_guests = [
                {
                    "ID": g.id,
                    "Name": g.name,
                    "Email": g.email,
                    "Phone": g.phone,
                    "Loyalty Tier": g.loyalty_status.upper(),
                }
                for g in guests[:12]
            ]
            st.table(table_guests)

    # ========================================================================
    # TAB 3: FUNCTIONAL CORE (LAB 2)
    # ========================================================================
    with tabs[2]:
        st.subheader("Functional Core: Closures, Lambdas & Pure Recursion")

        c_left, c_right = st.columns([1, 1])

        with c_left:
            st.markdown(
                "#### 1. Recursive Hierarchical Search (`recursive_search_available_quotes`)"
            )
            sel_city = st.selectbox(
                "Search City", sorted({h.city for h in hotels}), key="fc_city"
            )
            sel_guests = st.number_input(
                "Guests Count", min_value=1, max_value=6, value=2, key="fc_guests"
            )
            c_in = st.text_input(
                "Check-in Date (ISO)", value="2026-06-01", key="fc_cin"
            )
            c_out = st.text_input(
                "Check-out Date (ISO)", value="2026-06-05", key="fc_cout"
            )

            if st.button("🚀 Execute Pure Recursive Search", key="btn_rec_search"):
                try:
                    quotes = recursive_search_available_quotes(
                        hotels=hotels,
                        room_types=room_types,
                        rate_plans=rate_plans,
                        prices=prices,
                        availabilities=availabilities,
                        city=sel_city,
                        checkin=c_in,
                        checkout=c_out,
                        guests=sel_guests,
                    )
                    st.success(
                        f"Found {len(quotes)} valid offers purely via recursion (no loops)!"
                    )

                    if quotes:
                        cheapest = recursive_find_cheapest_quote(quotes)
                        if cheapest:
                            st.info(
                                f"🏆 **Cheapest Offer (Recursive Extremum):** {cheapest.hotel.name} - "
                                f"{cheapest.room_type.name} ({format_cents(cheapest.final_total)})"
                            )

                        for q in quotes[:4]:
                            st.markdown(
                                f"""
                                <div style="padding: 0.8rem; background: #0f172a; border-radius: 8px; margin-bottom: 0.5rem; border: 1px solid #1e293b;">
                                    <strong>{q.hotel.name}</strong> &middot; {q.room_type.name}<br>
                                    <small style="color: #94a3b8;">Rate: {q.rate_plan.name} | Meals: {q.rate_plan.meals}</small><br>
                                    <span style="color: #38bdf8; font-weight: 600;">{format_cents(q.final_total)}</span>
                                    <small style="color: #64748b;">({q.nights} nights)</small>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                except (ValueError, KeyError, RuntimeError) as e:
                    st.error(f"Error in search: {e}")

        with c_right:
            st.markdown("#### 2. Recursive Rule Engine (`recursive_apply_rules`)")
            st.write(
                "Sequential evaluation of discount and business rules through pure tail recursion."
            )

            base_val = st.number_input(
                "Base Amount (KZT)",
                min_value=10000,
                max_value=500000,
                value=100000,
                step=10000,
            )
            base_cents = int(base_val * 100)

            is_vip = st.checkbox("Guest is VIP (10% off)", value=True)
            is_early = st.checkbox(
                "Early Bird booking (>14 days, 5,000 KZT off)", value=True
            )
            is_long = st.checkbox("Long Stay (>5 nights, 5% off)", value=False)

            rules = (
                Rule(
                    id="rule_vip",
                    kind="vip_discount",
                    payload=(10,),
                ),
                Rule(
                    id="rule_early",
                    kind="early_bird",
                    payload=(14, 500000),
                ),
                Rule(
                    id="rule_long",
                    kind="long_stay",
                    payload=(5, 5),
                ),
            )

            context = {
                "is_vip": is_vip,
                "days_in_advance": 30 if is_early else 0,
                "nights": 7 if is_long else 1,
            }
            final_cents = recursive_apply_rules(base_cents, rules, context)

            st.write(f"**Starting Amount:** `{format_cents(base_cents)}`")
            st.write(
                f"**Final Amount after Recursive Rules:** `{format_cents(final_cents)}`"
            )
            st.write(f"**Total Savings:** `{format_cents(base_cents - final_cents)}`")

        st.markdown("---")
        st.markdown("### 3. Maybe / Either (Lab 4)")
        st.write(
            "Pure functional monad containers `Maybe[T]` (`Some` / `Nothing`) and "
            "`Either[E, T]` (`Right` / `Left`) for exception-free validation pipelines."
        )

        fc_l4_c1, fc_l4_c2 = st.columns([1, 1])
        with fc_l4_c1:
            st.markdown("#### Safe Rate Plan Lookup (`safe_rate`)")
            st.write(
                "Demonstration of the `Maybe` monad: returns `Some(RatePlan)` or `Nothing()`."
            )

            rate_search_opts = [
                f"(Existing) {rp.name} [{rp.id}]" for rp in rate_plans[:5]
            ] + ["(Non-existent) invalid_rate_999"]
            sel_rate_label = st.selectbox(
                "Select Rate Plan to Look Up",
                rate_search_opts,
                key="l4_fc_sel_rate_lookup",
            )

            if "invalid" in sel_rate_label:
                lookup_id = "invalid_rate_999"
            else:
                lookup_id = sel_rate_label.split("[")[-1].rstrip("]")

            res_maybe = safe_rate(rate_plans, lookup_id)
            if isinstance(res_maybe, Some):
                st.success(
                    f"✅ Result: `Some(RatePlan)` &mdash; **{res_maybe.value.name}**"
                )
                st.write(
                    f"• ID: `{res_maybe.value.id}` &middot; Meals: `{res_maybe.value.meals}` &middot; Cancellation: `{res_maybe.value.cancellation}`"
                )
                mapped = res_maybe.map(lambda r: f"Rate: {r.name} ({r.meals})")
                st.write(f"• `map(lambda ...)` &rarr; `{mapped}`")
            else:
                st.warning(
                    "⚠️ Result: `Nothing()` &mdash; rate plan not found (zero exceptions or KeyError)"
                )
                fallback = res_maybe.get_or_else("Default Fallback Rate")
                st.write(f"• `get_or_else('...')` &rarr; `'{fallback}'`")

        with fc_l4_c2:
            st.markdown("#### Cart Item Pure Validation (`validate_cart_item`)")
            st.write(
                "Demonstration of the `Either` monad: returns `Right(CartItem)` on success or `Left(dict)` on failure."
            )

            sel_rt = st.selectbox(
                "Room Type",
                room_types[:5],
                format_func=lambda rt: f"{rt.name} (Capacity: {rt.capacity})",
                key="l4_fc_val_room",
            )
            matching_rates = [rp for rp in rate_plans if rp.room_type_id == sel_rt.id]
            if not matching_rates:
                matching_rates = [rate_plans[0]]
            sel_rp = st.selectbox(
                "Rate Plan",
                matching_rates,
                format_func=lambda rp: f"{rp.name} ({rp.id})",
                key="l4_fc_val_rate",
            )

            v_cin = st.text_input(
                "Check-in Date (ISO-8601)", value="2026-06-01", key="l4_fc_cin"
            )
            v_cout = st.text_input(
                "Check-out Date (ISO-8601)", value="2026-06-04", key="l4_fc_cout"
            )
            v_guests = st.number_input(
                "Guests Count",
                min_value=1,
                max_value=10,
                value=sel_rt.capacity,
                key="l4_fc_guests_cnt",
            )

            if st.button(
                "🔍 Validate CartItem (Pure Either)",
                key="l4_fc_btn_validate_item",
            ):
                item_to_check = CartItem(
                    id="cart_l4_demo",
                    guest_id=guests[0].id,
                    room_type_id=sel_rt.id,
                    rate_id=sel_rp.id,
                    checkin=v_cin,
                    checkout=v_cout,
                    guests_count=int(v_guests),
                    total_price=0,
                )
                item_validation = validate_cart_item(
                    item_to_check,
                    room_types=room_types,
                    rates=rate_plans,
                    availability=availabilities,
                    rules=DEFAULT_RULES,
                )
                if isinstance(item_validation, Right):
                    st.success("✅ Validation Passed! Container: `Right(CartItem)`")
                    st.write(f"• ID: `{item_validation.value.id}`")
                    st.write(
                        f"• Room: `{item_validation.value.room_type_id}` &middot; Rate: `{item_validation.value.rate_id}`"
                    )
                elif isinstance(item_validation, Left):
                    st.error("❌ Validation Rejected! Container: `Left(error)`")
                    st.write(f"• Error Code: `{item_validation.error.get('code')}`")
                    st.write(f"• Message: {item_validation.error.get('message')}")
                    st.json(item_validation.error)

    # ========================================================================
    # TAB 4: PIPELINES & MEMOIZATION (LAB 1 & LAB 3)
    # ========================================================================
    with tabs[3]:
        st.subheader("Functional Pipelines & Memoization Engine")

        p_tab1, p_tab2, p_tab3, p_tab4 = st.tabs(
            [
                "Cart Hold Pipeline (Lab 1)",
                "Memoized Pricing (Lab 3)",
                "Speedup Benchmark (Lab 3)",
                "Lazy Evaluation Streams (Lab 5)",
            ]
        )

        with p_tab1:
            st.markdown("#### Immutable Cart Management (`hold_item`, `remove_hold`)")
            st.write(
                "Demonstrates pure immutable tuple updates without mutating existing collections."
            )

            c1, c2 = st.columns([1, 1])
            with c1:
                item_label = st.selectbox(
                    "Select Room to Hold",
                    [f"{r.name} ({r.id})" for r in room_types[:6]],
                )
                sel_room_id = item_label.split("(")[-1].rstrip(")")
                nights_cnt = st.slider("Nights", 1, 7, 3)

                if st.button("➕ Add Hold to Cart"):
                    new_item = CartItem(
                        id=f"hold_{int(time.time() * 1000)}",
                        guest_id=guests[0].id,
                        room_type_id=sel_room_id,
                        rate_id=f"rp_{sel_room_id}_standard",
                        checkin="2026-06-01",
                        checkout=f"2026-06-{1 + nights_cnt:02d}",
                        guests_count=2,
                        total_price=2500000 * nights_cnt,
                    )
                    st.session_state.cart = hold_item(st.session_state.cart, new_item)
                    st.success(f"Held item {new_item.id} added immutably!")

            with c2:
                st.write(f"**Cart Items count:** {len(st.session_state.cart)}")
                total_cart = calculate_cart_total(st.session_state.cart)
                st.metric("Total Cart Amount", format_cents(total_cart))

                for item in st.session_state.cart:
                    col_it, col_rm = st.columns([3, 1])
                    with col_it:
                        st.write(
                            f"• `{item.id}`: {item.room_type_id} &mdash; {format_cents(item.total_price)}"
                        )
                    with col_rm:
                        if st.button("❌ Remove", key=f"rm_{item.id}"):
                            st.session_state.cart = remove_hold(
                                st.session_state.cart, item.id
                            )
                            st.rerun()

        with p_tab2:
            st.markdown("#### Pure Memoization Decorator (`@memoize`)")
            st.write(
                "Transparent function caching with LRU capacity control and real-time hit/miss metrics."
            )

            col_test, col_stats = st.columns([1, 1])
            with col_test:
                test_rate = rate_plans[0].id
                st.write(f"Testing rate plan: `{test_rate}`")
                chk_in = st.selectbox(
                    "Check-in", ["2026-06-01", "2026-06-05", "2026-06-10"]
                )
                chk_out = st.selectbox(
                    "Check-out", ["2026-06-04", "2026-06-08", "2026-06-15"]
                )

                if st.button("Compute via memoized_nightly_sum"):
                    t0 = time.perf_counter()
                    total_amt = memoized_nightly_sum(prices, chk_in, chk_out, test_rate)
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    st.write(
                        f"Result: **{format_cents(total_amt)}** (computed in `{elapsed_ms:.4f} ms`)"
                    )

                if st.button("🧹 Clear Memo Cache"):
                    memoized_nightly_sum.cache_clear()
                    st.info("Cache reset successfully.")

            with col_stats:
                st.markdown("##### Real-Time Cache Statistics")
                info = memoized_nightly_sum.cache_info()
                s1, s2 = st.columns(2)
                with s1:
                    st.metric("Cache Hits", info.hits)
                    st.metric("Current Size", info.currsize)
                with s2:
                    st.metric("Cache Misses", info.misses)
                    st.metric("Hit Ratio", f"{info.hit_ratio * 100:.1f}%")

        with p_tab3:
            st.markdown("#### High-Volume Speedup Benchmark (Lab 3 Requirement)")
            st.write(
                "Runs 200–500 iterations over a realistic set of pricing queries from `seed.json` to verify "
                "pure memoization speedup factor and cache behavior."
            )

            rep_count = st.slider(
                "Benchmark Repetitions",
                min_value=100,
                max_value=500,
                value=300,
                step=50,
            )

            if st.button("⚡ Run Speedup Benchmark", key="btn_run_bench"):
                # Prepare query pool from seed rate plans
                query_pool = tuple(
                    (
                        rp.id,
                        "2026-06-01",
                        f"2026-06-{4 + (i % 5):02d}",
                    )
                    for i, rp in enumerate(rate_plans[:10])
                )

                def unmemoized_test(r_id: str, cin: str, cout: str) -> int:
                    return nightly_sum(prices, cin, cout, r_id)

                @memoize(maxsize=1024)
                def memoized_test(r_id: str, cin: str, cout: str) -> int:
                    return nightly_sum(prices, cin, cout, r_id)

                with st.spinner("Benchmarking..."):
                    bench_res = benchmark_speedup(
                        unmemoized_fn=unmemoized_test,
                        memoized_fn=memoized_test,
                        queries=query_pool,
                        repetitions=rep_count,
                    )

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric(
                        "Unmemoized Time",
                        f"{bench_res.unmemoized_time_sec * 1000:.2f} ms",
                    )
                with m2:
                    st.metric(
                        "Memoized Time", f"{bench_res.memoized_time_sec * 1000:.2f} ms"
                    )
                with m3:
                    st.metric("Speedup Factor", f"{bench_res.speedup_factor:.1f}x")
                with m4:
                    st.metric(
                        "Cache Hit Ratio",
                        f"{bench_res.cache_info.hit_ratio * 100:.1f}%",
                    )

                st.success(
                    f"Benchmark completed successfully! Memoization achieved a **{bench_res.speedup_factor:.1f}x speedup** "
                    f"with {bench_res.cache_info.hits} hits out of {bench_res.iterations} iterations."
                )
        with p_tab4:
            st.markdown(
                "#### ⏳ Lazy Offers Stream & Pipeline (`lazy_offers`, `take_lazy`)"
            )
            st.write(
                "Evaluates search offers on demand using pure generator streams (`yield`), "
                "terminating execution as soon as the requested quota is met."
            )
            lz_c1, lz_c2, lz_c3 = st.columns([1, 1, 1])
            with lz_c1:
                lz_budget = st.slider(
                    "Max Budget (KZT)",
                    min_value=20000,
                    max_value=200000,
                    value=80000,
                    step=10000,
                    key="l5_slider_budget",
                )
            with lz_c2:
                lz_k = st.slider(
                    "Take First K Offers",
                    min_value=1,
                    max_value=10,
                    value=4,
                    key="l5_slider_k",
                )
            with lz_c3:
                lz_skip = st.slider(
                    "Skip Initial Offers (drop_lazy)",
                    min_value=0,
                    max_value=5,
                    value=0,
                    key="l5_slider_skip",
                )

            if st.button(
                "🌊 Stream Matching Offers Lazily", key="l5_btn_stream_offers"
            ):
                budget_cents = lz_budget * 100
                offer_stream = lazy_offers(
                    hotels=hotels,
                    room_types=room_types,
                    rates=rate_plans,
                    prices=prices,
                    avail=availabilities,
                    predicate=lambda h, r, rt, p: p <= budget_cents,
                    checkin="2026-06-01",
                    checkout="2026-06-04",
                )
                if lz_skip > 0:
                    offer_stream = drop_lazy(offer_stream, lz_skip)

                collected_offers = tuple(take_lazy(offer_stream, lz_k))

                if collected_offers:
                    st.success(
                        f"Lazily materialized {len(collected_offers)} offer(s) without processing entire dataset!"
                    )
                    for idx, (h, r, rt, p) in enumerate(collected_offers, 1):
                        st.markdown(
                            f"**{idx}. {h.name}** ({h.city}) &mdash; *{r.name}* "
                            f"(Cap: {r.capacity}) &middot; Plan: `{rt.name or rt.title}` &middot; **Total: {format_cents(p)}**"
                        )
                else:
                    st.warning("No offers matched the lazy filter predicate.")

    # ========================================================================
    # TAB 5: ASYNC / FRP (LABS 5–8 ROADMAP)
    # ========================================================================
    with tabs[4]:
        st.subheader("Future Labs: Async, FRP, Composition & Reports (Labs 5–8)")
        st.markdown(
            """
            <div style="background: #1e293b; border-left: 4px solid #38bdf8; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
                <h4 style="margin: 0 0 0.5rem 0; color: #f8fafc;">🔮 Planned Architecture for Future Labs:</h4>
                <ul style="margin: 0; color: #cbd5e1; line-height: 1.8;">
                    <li><strong>Lab 5:</strong> Lazy infinite streams, date and pricing generators (<code>core/lazy.py</code>).</li>
                    <li><strong>Lab 6:</strong> Functional Reactive Programming (FRP), Observable event bus (<code>core/frp.py</code>).</li>
                    <li><strong>Lab 7:</strong> Function composition pipelines and service layer (<code>core/compose.py</code>, <code>core/service.py</code>).</li>
                    <li><strong>Lab 8:</strong> Analytical reports and metric aggregations (<code>core/report.py</code>).</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
                ##### Future Modules Architecture:
                - **Lab 5:** Infinite generators for date ranges and lazy price simulators.
                - **Lab 6:** Observable streams for real-time price updates and cart holds.
                - **Lab 7:** Currying, pipe combinators, and pure booking service layer.
                - **Lab 8:** Pure financial reports derived from immutable `Event` streams.
                """)
        with c2:
            st.markdown("""
                ##### Modules Status (Clean Stubs):
                - `core/lazy.py`: Lab 5 stub.
                - `core/frp.py`: Lab 6 stub.
                - `core/compose.py`: Lab 7 stub.
                - `core/service.py`: Lab 7 stub.
                - `core/report.py`: Lab 8 stub.
                """)

    # ========================================================================
    # TAB 6: REPORTS
    # ========================================================================
    with tabs[5]:
        st.subheader("Statistical Reports & Aggregations")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Hotel Distribution by City")
            city_counts = {}
            for h in hotels:
                city_counts[h.city] = city_counts.get(h.city, 0) + 1
            for city, count in city_counts.items():
                st.write(f"• **{city}:** {count} hotels")

        with c2:
            st.markdown("#### Room Types by Capacity")
            cap_counts = {}
            for r in room_types:
                cap_counts[r.capacity] = cap_counts.get(r.capacity, 0) + 1
            for cap, count in sorted(cap_counts.items()):
                st.write(f"• **{cap} Guests Capacity:** {count} room categories")

        st.markdown("---")
        st.write(
            f"Average price per night across calendar: "
            f"**{format_cents(sum(p.amount for p in prices) // len(prices))}**"
        )

        st.markdown("---")
        st.markdown("### ⚡ Quotes (cached)")
        st.write(
            "Benchmark of combined functional pricing `quote_offer` "
            "(`nightly_sum` + `recursive_apply_rules` + `check_dates_available_rec` under `@lru_cache`)."
        )

        n_req = st.slider(
            "Number of Queries for Benchmark",
            min_value=50,
            max_value=500,
            value=300,
            step=50,
            key="rep_quotes_cnt",
        )
        if st.button(
            "🚀 Run quote_offer Benchmark (cached vs uncached)",
            key="btn_rep_quote_offer",
        ):
            sample_rules = (
                Rule(id="rule_rep_vip", kind="vip_discount", payload=(10,)),
                Rule(id="rule_rep_early", kind="early_bird", payload=(14, 500000)),
            )

            rel_rate_ids = {rate_plans[i % len(rate_plans)].id for i in range(5)}
            rel_room_ids = {room_types[i % len(room_types)].id for i in range(5)}
            prices_idx = tuple(p for p in prices if p.rate_id in rel_rate_ids)
            avails_idx = tuple(
                a for a in availabilities if a.room_type_id in rel_room_ids
            )

            query_tuples = tuple(
                (
                    hotels[i % len(hotels)].id,
                    room_types[i % 5].id,
                    rate_plans[i % 5].id,
                    "2026-06-01",
                    "2026-06-10",
                    prices_idx,
                    avails_idx,
                    sample_rules,
                )
                for i in range(5)
            )

            # Uncached run
            t0 = time.perf_counter()
            for i in range(n_req):
                q = query_tuples[i % len(query_tuples)]
                sample_res = quote_offer_unmemoized(*q)
            t_uncached = time.perf_counter() - t0

            # Cached run
            quote_offer.cache_clear()
            t1 = time.perf_counter()
            for i in range(n_req):
                q = query_tuples[i % len(query_tuples)]
                sample_res = quote_offer(*q)
            t_cached = time.perf_counter() - t1

            speedup = (t_uncached / t_cached) if t_cached > 0 else 1.0
            info = quote_offer.cache_info()

            qc1, qc2, qc3, qc4 = st.columns(4)
            with qc1:
                st.metric("Uncached Time", f"{t_uncached * 1000:.2f} ms")
            with qc2:
                st.metric("Cached Time (LRU)", f"{t_cached * 1000:.2f} ms")
            with qc3:
                st.metric("Speedup Factor", f"{speedup:.1f}x")
            with qc4:
                st.metric("Cache Hits", f"{info.hits} / {n_req}")

            st.success(
                f"**Sample Result:** `(total_amount={format_cents(sample_res[0])}, is_available={sample_res[1]})` "
                f"&mdash; tuple: `({sample_res[0]}, {sample_res[1]})`"
            )

        st.markdown("---")
        st.markdown("### 🛡️ Validate & Calculate Booking (Lab 4)")
        st.write(
            "Pure monadic booking pipeline (`Either[dict, Booking]`) without `try`/`except`. "
            "Reuses `quote_offer` for price recalculation and strict validation."
        )

        scenario_name = st.selectbox(
            "Select validation scenario",
            [
                "1. Valid Booking (Right[Booking])",
                "2. Capacity Exceeded (Left: capacity_exceeded)",
                "3. Unavailable Dates (Left: date_unavailable)",
                "4. Invalid Date Range (Left: invalid_date_range)",
                "5. Empty Cart (Left: empty_booking)",
            ],
            key="l4_rep_sel_scenario",
        )

        if st.button(
            "🚀 Run Validation Scenario (Pure Either)",
            key="l4_rep_btn_run_scenario",
        ):
            guest_sample = guests[0]
            if "1. Valid" in scenario_name:
                item = CartItem(
                    id="cart_rep_valid",
                    guest_id=guest_sample.id,
                    room_type_id=room_types[0].id,
                    rate_id=rate_plans[0].id,
                    checkin="2026-06-01",
                    checkout="2026-06-04",
                    guests_count=1,
                    total_price=0,
                )
                items_tuple = (item,)
                avails_tuple = availabilities
            elif "2. Capacity" in scenario_name:
                item = CartItem(
                    id="cart_rep_overcap",
                    guest_id=guest_sample.id,
                    room_type_id=room_types[0].id,
                    rate_id=rate_plans[0].id,
                    checkin="2026-06-01",
                    checkout="2026-06-04",
                    guests_count=room_types[0].capacity + 5,
                    total_price=0,
                )
                items_tuple = (item,)
                avails_tuple = availabilities
            elif "3. Unavailable" in scenario_name:
                item = CartItem(
                    id="cart_rep_unavail",
                    guest_id=guest_sample.id,
                    room_type_id=room_types[0].id,
                    rate_id=rate_plans[0].id,
                    checkin="2026-06-01",
                    checkout="2026-06-04",
                    guests_count=1,
                    total_price=0,
                )
                items_tuple = (item,)
                avails_tuple = ()  # No availability
            elif "4. Invalid" in scenario_name:
                item = CartItem(
                    id="cart_rep_invdates",
                    guest_id=guest_sample.id,
                    room_type_id=room_types[0].id,
                    rate_id=rate_plans[0].id,
                    checkin="2026-06-08",
                    checkout="2026-06-02",  # Checkout before checkin
                    guests_count=1,
                    total_price=0,
                )
                items_tuple = (item,)
                avails_tuple = availabilities
            else:  # Empty cart
                items_tuple = ()
                avails_tuple = availabilities

            res_scenario = validate_and_calculate_booking(
                booking_id="bk_rep_l4",
                guest=guest_sample,
                items=items_tuple,
                prices=prices,
                availability=avails_tuple,
                rules=DEFAULT_RULES,
                room_types=room_types,
                rates=rate_plans,
            )

            if isinstance(res_scenario, Right):
                bk = res_scenario.value
                st.success("✅ Validation Succeeded! Container: `Right(Booking)`")
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.metric("Booking ID", bk.id)
                with sc2:
                    st.metric("Guest", guest_sample.name)
                with sc3:
                    st.metric("Total Amount", format_cents(bk.total))
                st.write(f"• Status: `{bk.status}` &middot; Items: `{len(bk.items)}`")
            elif isinstance(res_scenario, Left):
                err = res_scenario.error
                st.error("❌ Validation Rejected! Container: `Left(error)`")
                st.write(f"• **Error Code:** `{err.get('code')}`")
                st.write(f"• **Message:** {err.get('message')}")
                st.json(err)

        st.markdown("---")
        st.markdown("### ⏳ Lazy Stream Sampling & Top-K Offers (Lab 5)")
        st.write(
            "Lazy generator evaluation for Reports: sample continuous calendar dates "
            "or stream the top-K matching hotel offers on demand without materializing the full dataset."
        )

        r_lz_col1, r_lz_col2 = st.columns(2)
        with r_lz_col1:
            st.markdown("##### 📅 Lazy Infinite Calendar Stream")
            st.caption("Uses `lazy_calendar_stream` + `take_lazy`")
            sample_days_cnt = st.slider(
                "Number of Days to Sample", 3, 21, 7, key="l5_rep_slider_days"
            )
            if st.button("Generate Date Stream Sample", key="l5_rep_btn_stream_dates"):
                sampled_dates = tuple(
                    take_lazy(lazy_calendar_stream("2026-06-01"), sample_days_cnt)
                )
                st.success(f"Streamed {len(sampled_dates)} calendar days on demand:")
                st.code(" -> ".join(sampled_dates), language="text")

        with r_lz_col2:
            st.markdown("##### 🏆 First K Budget Offers (Lazy Stream)")
            st.caption("Uses `lazy_offers` + `take_lazy`")
            k_offers_cnt = st.slider("Top K Offers", 1, 8, 3, key="l5_rep_slider_k")
            if st.button("Sample Top K Offers Lazily", key="l5_rep_btn_sample_offers"):
                offer_gen = lazy_offers(
                    hotels=hotels,
                    room_types=room_types,
                    rates=rate_plans,
                    prices=prices,
                    avail=availabilities,
                    predicate=lambda h, r, rt, p: p <= 9000000,
                    checkin="2026-06-01",
                    checkout="2026-06-04",
                )
                sampled_offers = tuple(take_lazy(offer_gen, k_offers_cnt))
                st.success(
                    f"Yielded {len(sampled_offers)} offers lazily (budget ≤ 90,000 KZT):"
                )
                for i, (h, r, rt, p) in enumerate(sampled_offers, 1):
                    st.write(
                        f"**{i}. {h.name}** ({h.city}) &middot; *{r.name}* &middot; Plan: `{rt.name or rt.title}` &middot; **{format_cents(p)}**"
                    )

    # ========================================================================
    # TAB 7: TESTS RUNNER
    # ========================================================================
    with tabs[6]:
        st.subheader("Automated Test Suite Runner")
        st.write(
            "Run pytest against lab test suites (`tests/test_lab1.py`, `tests/test_lab2.py`, `tests/test_lab3.py`, `tests/test_lab4.py`)."
        )

        col_sel, col_btn = st.columns([2, 1])
        with col_sel:
            test_target = st.selectbox(
                "Select Test Suite",
                [
                    "All Labs (Labs 1–5)",
                    "Lab 1 (Domain & Transforms)",
                    "Lab 2 (Closures & Recursion)",
                    "Lab 3 (Memoization & Benchmarks)",
                    "Lab 4 (Monads & Pure Validation)",
                    "Lab 5 (Lazy Streams & Evaluation)",
                ],
            )

        with col_btn:
            st.write("")
            st.write("")
            run_tests = st.button("🧪 Run Selected Tests")

        if run_tests:
            target_file = "tests/"
            if "Lab 1" in test_target:
                target_file = "tests/test_lab1.py"
            elif "Lab 2" in test_target:
                target_file = "tests/test_lab2.py"
            elif "Lab 3" in test_target:
                target_file = "tests/test_lab3.py"
            elif "Lab 4" in test_target:
                target_file = "tests/test_lab4.py"
            elif "Lab 5" in test_target:
                target_file = "tests/test_lab5.py"

            with st.spinner(f"Running pytest {target_file}..."):
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "-v", target_file],
                    capture_output=True,
                    text=True,
                    check=False,
                )

            if proc.returncode == 0:
                st.success("✅ All unit tests PASSED!")
            else:
                st.error("❌ Some tests failed or returned non-zero code.")

            st.code(proc.stdout + proc.stderr, language="text")

    # ========================================================================
    # TAB 8: ABOUT
    # ========================================================================
    with tabs[7]:
        st.subheader("About the Coursework & Invariants")
        st.markdown("""
            ### Hotel / Room Booking Functional Programming System
            This project is built according to university coursework requirements in **Pure Functional Programming (Python 3.10+)**.

            #### Core Invariants Enforced:
            1. **No Shared Mutable State**: All domain entities are defined via `@dataclass(frozen=True)`.
            2. **Pure Money Math**: Monetary amounts are integers representing smallest currency units (cents/tiyn) to avoid floating-point drift.
            3. **Pure Date Types**: ISO-8601 strings (`"YYYY-MM-DD"`) everywhere, enabling hashability and deterministic cache keys.
            4. **Clean Code & Type Hints**: Full typing, black/ruff compliance, zero TODOs or stubs in active labs.
            5. **Lab Separation**:
               - `tests/test_lab1.py`: Tests for Lab 1 (Domain & Transforms)
               - `tests/test_lab2.py`: Tests for Lab 2 (Closures, Lambdas, Recursion)
               - `tests/test_lab3.py`: Tests for Lab 3 (Memoization & Benchmarks)
               - `tests/test_lab4.py`: Tests for Lab 4 (Monads & Pure Validation Pipelines)
            """)


if __name__ == "__main__":
    main()
