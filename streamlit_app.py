"""Streamlit Web Application: Hotel & Room Booking System.

Coursework: Functional Programming in Python — Laboratory Works 1 & 2.
Paradigms: Immutability, Pure Functions, Higher-Order Functions (map/reduce),
           Closures & Function Factories, Lambdas, and Recursive Algorithms.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, timedelta
import subprocess
import sys
import pandas as pd
import streamlit as st

from core.filters import (
    filter_hotels_by_location,
    filter_hotels_by_min_rating,
    filter_rooms_by_capacity,
    filter_rooms_by_price,
)
from core.fp_tools import (
    make_amenity_filter,
    make_price_filter,
    recursive_aggregate_cities,
    recursive_aggregate_city,
    recursive_calculate_discount,
    recursive_find_cheapest_room,
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
    find_cheapest_room,
)
from data.mock_db import (
    get_sample_bookings,
    get_sample_cities,
    get_sample_discount_tree,
    get_sample_hotels,
    get_sample_reviews,
    get_sample_rooms,
)
from domain.models import Room

# Configure Streamlit page layout
st.set_page_config(
    page_title="Hotel & Room Booking System — Labs 1 & 2",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom UI styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .status-badge-ok {
        background-color: #ecfdf5;
        color: #047857;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
        border: 1px solid #a7f3d0;
        font-size: 0.85rem;
    }
    .tree-box {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-family: monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load domain collections
hotels = get_sample_hotels()
rooms = get_sample_rooms()
bookings = get_sample_bookings()
reviews = get_sample_reviews()
cities = get_sample_cities()
discount_tree = get_sample_discount_tree()

# Navigation menu options
MENU_OPTIONS = [
    "Overview",
    "Data",
    "Pricing & Pipelines",
    "Filters & Closures",
    "Recursive Algorithms",
    "Tests",
    "About",
]

# Sidebar Navigation
with st.sidebar:
    st.markdown("### 🏨 Navigation")
    current_section = st.radio(
        "Select Section",
        MENU_OPTIONS,
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("#### Status")
    st.markdown(
        '<span class="status-badge-ok">LAB 1 & LAB 2 ACTIVE</span>',
        unsafe_allow_html=True,
    )
    st.caption("• Lab 1: Immutability, Pure Functions, HOF")
    st.caption("• Lab 2: Closures, Lambdas, Recursion")

    st.markdown("---")
    st.markdown("#### System Metrics")
    st.caption(f"Hotels: **{len(hotels)}**")
    st.caption(f"Rooms: **{len(rooms)}**")
    st.caption(f"Cities (Tree): **{len(cities)}**")
    st.caption(f"Avg Rating: **{calculate_average_hotel_rating(hotels):.2f} / 5.0**")


# ============================================================================
# SECTION 1: OVERVIEW
# ============================================================================
if current_section == "Overview":
    st.markdown(
        '<div class="main-header">Hotel & Room Booking System</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Functional Programming Course Project — Laboratory Works 1 & 2</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        The **Hotel & Room Booking System** is an educational application implemented in **pure functional Python**.
        It demonstrates core functional paradigms through practical hotel reservation domain logic:

        - **Laboratory Work 1 (Pure Functions & HOF):**
          - Immutable domain models (`@dataclass(frozen=True)`).
          - Deterministic transformation functions (stay duration, pricing with seasonal multiplier, discounts).
          - Declarative `map`, `filter`, and `reduce` pipelines.
        - **Laboratory Work 2 (Closures, Lambdas, Recursion):**
          - Closure-based filter factories (`make_price_filter`, `make_amenity_filter`).
          - Pure lambda key extractors for sorting.
          - Recursive tree aggregation (City -> Hotels -> Rooms) without iterative loops.
          - Recursive search for the cheapest room and parsing of nested discount trees.
        """
    )

    st.markdown("### Architectural Principles")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <h4>🔒 Immutability</h4>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Domain entities cannot be mutated in place. All changes produce new instances.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <h4>✨ Pure Functions & Closures</h4>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Functions operate without side effects or hidden mutable state. Closures capture config scopes.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <h4>🔄 Pure Recursion</h4>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Hierarchies are processed via base cases and recursive steps without iterative for/while loops.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("System Baseline")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Hotels", len(hotels))
    s2.metric("Room Types", len(rooms))
    s3.metric("Bookings", len(bookings))
    s4.metric("Confirmed Revenue", f"${calculate_total_revenue(bookings):,.2f}")


# ============================================================================
# SECTION 2: DATA (IMMUTABLE DOMAIN ENTITIES)
# ============================================================================
elif current_section == "Data":
    st.markdown(
        '<div class="main-header">Domain Data & Immutability Contracts</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Immutable domain entities defined via @dataclass(frozen=True)</div>',
        unsafe_allow_html=True,
    )

    with st.expander("🛡️ Interactive Immutability Verification", expanded=True):
        st.markdown(
            "Click the button below to attempt modifying `base_price` on an active `Room` instance in memory:"
        )
        sample_room = rooms[0]
        st.code(
            f"# Target instance:\nroom = Room(id='{sample_room.id}', room_type='{sample_room.room_type}', base_price={sample_room.base_price})\n\n# Attempting mutation:\nroom.base_price = 999.0",
            language="python",
        )
        if st.button("Execute Mutation Attempt"):
            try:
                sample_room.base_price = 999.0  # type: ignore
                st.error("Error: Mutation succeeded, entity is not immutable!")
            except FrozenInstanceError as err:
                st.success(
                    f"Contract Enforced! Python intercepted the mutation and raised: `FrozenInstanceError: {err}`."
                )

    st.markdown("### Domain Collections Explorer")
    data_tab1, data_tab2, data_tab3, data_tab4 = st.tabs(
        ["Hotels", "Rooms", "Bookings", "Reviews"]
    )

    with data_tab1:
        st.caption("Immutable `Hotel` records loaded from the domain repository:")
        hotels_df = pd.DataFrame(
            [
                {
                    "ID": h.id,
                    "Name": h.name,
                    "Location": h.location,
                    "Rating": f"{h.rating} ⭐",
                    "Amenities": ", ".join(h.amenities),
                    "Room IDs": ", ".join(h.room_ids),
                }
                for h in hotels
            ]
        )
        st.dataframe(hotels_df, use_container_width=True, hide_index=True)

    with data_tab2:
        st.caption("Immutable `Room` records with base nightly rates and capacity:")
        rooms_df = pd.DataFrame(
            [
                {
                    "ID": r.id,
                    "Hotel ID": r.hotel_id,
                    "Room Type": r.room_type,
                    "Base Price ($/night)": f"${r.base_price:.2f}",
                    "Max Capacity": f"{r.capacity} guest(s)",
                    "Amenities": ", ".join(r.amenities),
                }
                for r in rooms
            ]
        )
        st.dataframe(rooms_df, use_container_width=True, hide_index=True)

    with data_tab3:
        st.caption("Immutable `Booking` customer reservation records:")
        bookings_df = pd.DataFrame(
            [
                {
                    "Booking ID": b.id,
                    "Room ID": b.room_id,
                    "Guest Name": b.guest_name,
                    "Check-In": str(b.check_in),
                    "Check-Out": str(b.check_out),
                    "Total Price": f"${b.total_price:.2f}",
                    "Status": b.status,
                }
                for b in bookings
            ]
        )
        st.dataframe(bookings_df, use_container_width=True, hide_index=True)

    with data_tab4:
        st.caption("Immutable `Review` guest feedback records:")
        reviews_df = pd.DataFrame(
            [
                {
                    "Review ID": rev.id,
                    "Hotel ID": rev.hotel_id,
                    "Rating": f"{rev.rating} ⭐",
                    "Comment": rev.comment,
                    "Timestamp": rev.timestamp.strftime("%Y-%m-%d %H:%M"),
                }
                for rev in reviews
            ]
        )
        st.dataframe(reviews_df, use_container_width=True, hide_index=True)


# ============================================================================
# SECTION 3: PRICING & PIPELINES (LAB 1)
# ============================================================================
elif current_section == "Pricing & Pipelines":
    st.markdown(
        '<div class="main-header">Pricing & Stay Calculator Pipelines</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Laboratory Work 1: Pure pricing functions and map/reduce aggregations (core/pricing.py)</div>',
        unsafe_allow_html=True,
    )

    calc_col1, calc_col2 = st.columns([1, 1])

    with calc_col1:
        st.subheader("Stay Inputs")
        room_dict = {
            f"[{r.id}] {r.room_type} — ${r.base_price:.2f}/night (Cap: {r.capacity})": r
            for r in rooms
        }
        chosen_room_label = st.selectbox("Select Room:", list(room_dict.keys()))
        selected_room: Room = room_dict[chosen_room_label]

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            check_in_date = st.date_input(
                "Check-In Date:", value=date.today() + timedelta(days=7)
            )
        with d_col2:
            check_out_date = st.date_input(
                "Check-Out Date:", value=date.today() + timedelta(days=11)
            )

        multiplier_presets = {
            "Standard Season (1.00x)": 1.00,
            "Low Season (0.85x, -15%)": 0.85,
            "High Season (1.20x, +20%)": 1.20,
            "Peak Holiday Season (1.40x, +40%)": 1.40,
        }
        chosen_preset = st.selectbox(
            "Seasonal Multiplier:", list(multiplier_presets.keys()), index=0
        )
        seasonal_mult = multiplier_presets[chosen_preset]

        discount_val = st.slider(
            "Promotional Discount (%):", min_value=0, max_value=50, value=0, step=5
        )

    with calc_col2:
        st.subheader("Quotation Calculation")
        nights_count = calculate_nights(check_in_date, check_out_date)

        if nights_count <= 0:
            st.error("Invalid stay dates: Check-Out must occur after Check-In.")
        else:
            base_subtotal = calculate_total_price(
                selected_room.base_price, nights_count, 1.00
            )
            seasonal_total = calculate_total_price(
                selected_room.base_price, nights_count, seasonal_mult
            )
            final_quote = calculate_stay_quote(
                selected_room,
                check_in_date,
                check_out_date,
                seasonal_multiplier=seasonal_mult,
                discount_percent=float(discount_val),
            )

            q1, q2 = st.columns(2)
            q1.metric("Stay Duration", f"{nights_count} night(s)")
            q2.metric("Base Rate", f"${selected_room.base_price:.2f} / night")

            q3, q4 = st.columns(2)
            q3.metric("Seasonal Factor", f"{seasonal_mult:.2f}x")
            q4.metric("Final Quote", f"${final_quote:.2f}")

            st.markdown("#### Pure Calculation Trace")
            st.code(
                f"""# 1. calculate_nights({check_in_date}, {check_out_date}) -> {nights_count} nights
# 2. calculate_total_price({selected_room.base_price}, {nights_count}, seasonal_multiplier={seasonal_mult}) -> ${seasonal_total:.2f}
# 3. apply_discount(${seasonal_total:.2f}, discount_percent={discount_val}%) -> ${final_quote:.2f}
""",
                language="python",
            )

    st.markdown("---")
    st.subheader("Map / Reduce Aggregations (Lab 1)")
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("Total Confirmed Revenue (reduce)", f"${calculate_total_revenue(bookings):,.2f}")
    with m_col2:
        st.metric("Average Hotel Rating (reduce)", f"{calculate_average_hotel_rating(hotels):.2f} / 5.0 ⭐")
    with m_col3:
        cheapest_found = find_cheapest_room(rooms)
        if cheapest_found:
            st.metric("Cheapest Room (reduce)", f"${cheapest_found.base_price:.2f}", cheapest_found.room_type)


# ============================================================================
# SECTION 4: FILTERS & CLOSURES (LAB 1 & LAB 2)
# ============================================================================
elif current_section == "Filters & Closures":
    st.markdown(
        '<div class="main-header">Filters & Closures</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Laboratory Work 1 (Predicates) & Laboratory Work 2 (Closure Factories & Lambdas)</div>',
        unsafe_allow_html=True,
    )

    tab_predicates, tab_closures, tab_lambdas = st.tabs(
        ["1. Pure Predicates (Lab 1)", "2. Closure Factories (Lab 2)", "3. Lambdas & Sorting (Lab 2)"]
    )

    with tab_predicates:
        st.subheader("Pure Filtering Predicates (core/filters.py)")
        st.markdown(
            "Filtering functions accept a sequence and return a newly constructed list matching the predicate."
        )

        p_c1, p_c2 = st.columns(2)
        with p_c1:
            p_range = st.slider("Price Range ($/night):", 50.0, 600.0, (100.0, 300.0), 10.0)
        with p_c2:
            p_cap = st.selectbox("Minimum Guest Capacity:", [1, 2, 3, 4, 5], index=1)

        matched_p = filter_rooms_by_price(rooms, p_range[0], p_range[1])
        matched_p = filter_rooms_by_capacity(matched_p, p_cap)

        st.caption(f"Matched {len(matched_p)} of {len(rooms)} available rooms.")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": r.id,
                        "Room Type": r.room_type,
                        "Price": f"${r.base_price:.2f}",
                        "Capacity": r.capacity,
                        "Amenities": ", ".join(r.amenities),
                    }
                    for r in matched_p
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    with tab_closures:
        st.subheader("Closure-Based Filter Factories (core/fp_tools.py)")
        st.markdown(
            """
            `make_price_filter(min_p, max_p)` and `make_amenity_filter(required)` return predicate functions
            that capture their configuration inside **lexical closure scopes**, avoiding global variables.
            """
        )

        cf_c1, cf_c2 = st.columns(2)
        with cf_c1:
            cl_min = st.number_input("Closure Min Price ($):", value=80.0, step=10.0)
            cl_max = st.number_input("Closure Max Price ($):", value=250.0, step=10.0)
            price_closure = make_price_filter(cl_min, cl_max)

        with cf_c2:
            all_amenities = sorted(list({a for r in rooms for a in r.amenities}))
            cl_amenity = st.selectbox("Closure Required Amenity:", ["None"] + all_amenities)

        # Apply closures
        closure_filtered = list(filter(price_closure, rooms))
        if cl_amenity != "None":
            amenity_closure = make_amenity_filter(cl_amenity)
            closure_filtered = list(filter(amenity_closure, closure_filtered))

        st.success(f"Closure pipeline matched **{len(closure_filtered)}** rooms.")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": r.id,
                        "Room Type": r.room_type,
                        "Price": f"${r.base_price:.2f}",
                        "Capacity": r.capacity,
                        "Amenities": ", ".join(r.amenities),
                    }
                    for r in closure_filtered
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.code(
            f"""# Closure factory execution:
price_filter = make_price_filter({cl_min}, {cl_max})
matched = list(filter(price_filter, rooms))
""",
            language="python",
        )

    with tab_lambdas:
        st.subheader("Lambdas in Sorting & Transformations (Lab 2)")
        sort_order = st.radio("Sort Rooms by Price:", ["Ascending (Lowest First)", "Descending (Highest First)"])
        is_desc = sort_order.startswith("Descending")

        sorted_rooms = sort_rooms_by_price(rooms, descending=is_desc)
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "ID": r.id,
                        "Room Type": r.room_type,
                        "Price": f"${r.base_price:.2f}",
                        "Capacity": r.capacity,
                    }
                    for r in sorted_rooms
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.code("sorted_rooms = sorted(rooms, key=lambda r: r.base_price, reverse=descending)", language="python")


# ============================================================================
# SECTION 5: RECURSIVE ALGORITHMS (LAB 2)
# ============================================================================
elif current_section == "Recursive Algorithms":
    st.markdown(
        '<div class="main-header">Recursive Algorithms</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Laboratory Work 2: Recursive hierarchy processing without iterative loops</div>',
        unsafe_allow_html=True,
    )

    tab_rec1, tab_rec2 = st.tabs(
        ["Algorithm 1: Hierarchy Aggregation", "Algorithm 2: Recursive Search & Discounts"]
    )

    with tab_rec1:
        st.subheader("Recursive City -> Hotels -> Rooms Aggregation")
        st.markdown(
            """
            This algorithm aggregates the total number of rooms and guest capacities across a nested
            **City -> Hotels -> Rooms** tree structure using pure recursion (head/tail decomposition) with **no loops**.
            """
        )

        for city in cities:
            agg = recursive_aggregate_city(city)
            st.markdown(
                f'<div class="tree-box">🏙️ <b>{city.name}</b>: {agg["room_count"]} rooms | {agg["total_capacity"]} total guest capacity</div>',
                unsafe_allow_html=True,
            )

        all_cities_agg = recursive_aggregate_cities(cities)
        st.info(
            f"🌐 **All Cities Combined (Recursive Aggregation):** {all_cities_agg['room_count']} rooms, "
            f"{all_cities_agg['total_capacity']} total capacity."
        )

        st.code(
            """def recursive_count_rooms(node):
    if not node:
        return 0
    if isinstance(node, Room):
        return 1
    if isinstance(node, HotelNode):
        return recursive_count_rooms(node.rooms)
    if isinstance(node, City):
        return recursive_count_rooms(node.hotels)
    if isinstance(node, tuple):
        return recursive_count_rooms(node[0]) + recursive_count_rooms(node[1:])
    return 0
""",
            language="python",
        )

    with tab_rec2:
        st.subheader("Recursive Search & Nested Discount Evaluation")

        st.markdown("#### 1. Recursive Search for Cheapest Room")
        cheapest_in_tree = recursive_find_cheapest_room(cities)
        if cheapest_in_tree:
            st.success(
                f"Cheapest room across the entire hierarchical tree: "
                f"**[{cheapest_in_tree.id}] {cheapest_in_tree.room_type}** at **${cheapest_in_tree.base_price:.2f}**/night."
            )

        st.markdown("#### 2. Recursive Nested Discount Tree Parsing")
        st.markdown(
            "Evaluates multi-tier discount trees recursively without loops by reusing Lab 1 `apply_discount`."
        )

        base_val = st.number_input("Baseline Price ($):", min_value=10.0, max_value=5000.0, value=1000.0, step=100.0)
        discounted_val = recursive_calculate_discount(base_val, discount_tree)

        d1, d2, d3 = st.columns(3)
        d1.metric("Original Price", f"${base_val:.2f}")
        d2.metric("Discounted Price", f"${discounted_val:.2f}")
        d3.metric("Total Saved", f"${base_val - discounted_val:.2f}")

        st.code(
            f"""# Evaluates: Holiday Promotion (10%) -> Loyalty Tier (5%) -> Early Bird (2%)
# Base: ${base_val:.2f} -> Final: ${discounted_val:.2f}
discounted = recursive_calculate_discount({base_val}, discount_tree)
""",
            language="python",
        )


# ============================================================================
# SECTION 6: TESTS (PYTEST RUNNER)
# ============================================================================
elif current_section == "Tests":
    st.markdown(
        '<div class="main-header">Pytest Automated Test Suite</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Independent test suites for Laboratory Work 1 and Laboratory Work 2</div>',
        unsafe_allow_html=True,
    )

    t_col1, t_col2 = st.columns([1, 2])

    with t_col1:
        st.markdown("#### Test Execution Controls")
        suite_choice = st.selectbox(
            "Select Test Suite:",
            ["All Labs (Lab 1 + Lab 2)", "Lab 1 Only (test_lab1.py)", "Lab 2 Only (test_lab2.py)"],
        )
        run_button = st.button("🚀 Run Pytest Suite", type="primary", use_container_width=True)

        if suite_choice.startswith("All"):
            cmd = ["pytest", "-v", "tests/"]
        elif "Lab 1" in suite_choice:
            cmd = ["pytest", "-v", "tests/test_lab1.py"]
        else:
            cmd = ["pytest", "-v", "tests/test_lab2.py"]

        st.code(" ".join(cmd), language="bash")

    with t_col2:
        st.markdown("#### Test Output")
        if run_button:
            with st.spinner("Running tests..."):
                try:
                    result = subprocess.run(
                        [sys.executable, "-m"] + cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0:
                        st.success("All automated tests passed successfully!")
                    else:
                        st.error(f"Tests finished with return code {result.returncode}")

                    st.code(result.stdout or "No standard output.", language="text")
                    if result.stderr:
                        st.code(result.stderr, language="text")
                except Exception as ex:
                    st.error(f"Failed to execute pytest: {ex}")
        else:
            st.info("Click 'Run Pytest Suite' to execute unit and functional tests.")


# ============================================================================
# SECTION 7: ABOUT
# ============================================================================
elif current_section == "About":
    st.markdown('<div class="main-header">About Project</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Functional Programming Coursework Project Specification — Labs 1 & 2</div>',
        unsafe_allow_html=True,
    )

    about_col1, about_col2 = st.columns([2, 1])

    with about_col1:
        st.markdown("### Coursework Specifications")
        st.markdown(
            """
            - **Domain**: Hotel & Room Booking System
            - **Course**: Pure Functional Programming in Python
            - **Delivered Labs**:
              - **Lab 1**: Pure transformation functions, immutable dataclasses, map/reduce pipelines.
              - **Lab 2**: Closures, function factories, lambdas, and 2 recursive algorithms.
            - **Interfaces**: Streamlit Web UI + Terminal CLI (`python cli.py`).
            - **Testing**: `pytest` test suites in `tests/test_lab1.py` and `tests/test_lab2.py`.
            """
        )

    with about_col2:
        st.markdown("### Architecture Status")
        st.markdown(
            """
            <div class="metric-card" style="text-align: left;">
                <p><strong>Language:</strong> Python 3.11</p>
                <p><strong>Lab 1:</strong> Completed (7 tests)</p>
                <p><strong>Lab 2:</strong> Completed (7 tests)</p>
                <p><strong>Code Quality:</strong> Black / Ruff clean</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
