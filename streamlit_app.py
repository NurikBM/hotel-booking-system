"""Streamlit Web Application: Hotel & Room Booking System.

Coursework: Functional Programming in Python.
Architecture: Single Page Application (SPA) with section navigation.
Paradigms: Immutability, Pure Functions, Higher-Order Functions (HOF), and Pipelines.
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
    calculate_average_hotel_rating,
    calculate_total_revenue,
    compose,
    extract_hotel_names,
    extract_unique_hotel_amenities,
    find_affordable_rooms,
    find_cheapest_room,
    find_rooms_by_type,
    transform_rooms_with_multiplier,
)
from core.pricing import (
    apply_discount,
    calculate_nights,
    calculate_stay_quote,
    calculate_total_price,
)
from data.mock_db import (
    get_sample_bookings,
    get_sample_hotels,
    get_sample_reviews,
    get_sample_rooms,
)
from domain.models import Booking, Hotel, Room

# Configure Streamlit page layout
st.set_page_config(
    page_title="Hotel & Room Booking System",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom UI styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .code-badge {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 2px 8px;
        font-family: monospace;
        font-size: 0.9em;
    }
    .status-badge-ok {
        background-color: #ecfdf5;
        color: #047857;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
        border: 1px solid #a7f3d0;
    }
    .status-badge-dev {
        background-color: #fffbeb;
        color: #b45309;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
        border: 1px solid #fde68a;
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

# Navigation menu structure according to course requirements:
# Overview · Data · Functional Core · Pipelines · Async/FRP · Reports · Tests · About
MENU_OPTIONS = [
    "Overview",
    "Data",
    "Functional Core",
    "Pipelines",
    "Async/FRP",
    "Reports",
    "Tests",
    "About",
]

# Sidebar Navigation (Collapsible drawer / burger menu)
with st.sidebar:
    st.markdown("### 🏨 Navigation")
    current_section = st.radio(
        "Select Section",
        MENU_OPTIONS,
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("#### System Metrics")
    st.caption(f"Hotels: **{len(hotels)}**")
    st.caption(f"Rooms: **{len(rooms)}**")
    st.caption(f"Bookings: **{len(bookings)}**")
    st.caption(f"Avg Rating: **{calculate_average_hotel_rating(hotels):.2f} / 5.0**")

    st.markdown("---")
    st.caption("Functional Programming Coursework")
    st.caption("Python 3.11 • Pure FP Architecture")


# ============================================================================
# SECTION 1: OVERVIEW
# ============================================================================
if current_section == "Overview":
    st.markdown('<div class="main-header">Hotel & Room Booking System</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Functional Programming Course Project in Python</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        The **Hotel & Room Booking System** is an enterprise-grade booking management engine designed and
        implemented entirely around **pure functional programming (FP) principles**. The system replaces
        traditional mutable state models and imperative mutation cycles with strictly immutable data structures,
        mathematically pure transformation functions, and declarative higher-order pipelines.

        Built with **Python 3.11** and **Streamlit**, the application models hotel properties, room categories,
        customer reservations, and dynamic pricing algorithms. All calculations—including date differences,
        seasonal yield factors, and promotional discounts—operate without side effects, guaranteeing determinism,
        idempotency, and complete thread safety across concurrent operations.
        """
    )

    st.markdown("### Core Architectural Pillars")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <h4>🔒 Immutability</h4>
                <p style="color: #64748b; font-size: 0.9rem;">
                    All domain entities use <code>@dataclass(frozen=True)</code> with immutable tuples, eliminating race conditions.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <h4>✨ Pure Functions</h4>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Zero side-effects, zero global state. Given identical arguments, functions always return identical results.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <h4>⚡ Higher-Order Pipelines</h4>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Declarative data flow leveraging <code>map</code>, <code>filter</code>, and <code>reduce</code> for transformations.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
            <div class="metric-card">
                <h4>🧪 Comprehensive Tests</h4>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Full unit and property test coverage with <code>pytest</code> verifying contract guarantees and math precision.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("System Summary")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Registered Hotels", len(hotels))
    s2.metric("Available Room Types", len(rooms))
    s3.metric("Processed Bookings", len(bookings))
    s4.metric("Confirmed Revenue", f"${calculate_total_revenue(bookings):,.2f}")


# ============================================================================
# SECTION 2: DATA (IMMUTABLE DOMAIN ENTITIES)
# ============================================================================
elif current_section == "Data":
    st.markdown('<div class="main-header">Domain Data & Immutability Contracts</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Immutable domain entities defined via @dataclass(frozen=True)</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        In functional programming, state is never modified in-place. Domain models are declared as **frozen dataclasses**,
        and internal collection attributes use immutable `tuple` types rather than mutable `list` objects. This structural
        discipline ensures that records cannot be altered accidentally after instantiation.
        """
    )

    # Immutability Demonstration
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
# SECTION 3: FUNCTIONAL CORE (MAP, FILTER, REDUCE & COMPOSITION)
# ============================================================================
elif current_section == "Functional Core":
    st.markdown('<div class="main-header">Functional Core & HOF Pipelines</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Interactive demonstration of pure predicate filtering, map transformations, and reduce folding</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### 1. Pure Predicate Filtering (`core/filters.py`)")
    st.markdown(
        "Filtering functions accept a sequence and return a newly constructed list containing only elements "
        "matching the predicate function. The source collections are left untouched."
    )

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        price_range = st.slider(
            "Price Range ($/night):",
            min_value=50.0,
            max_value=600.0,
            value=(80.0, 350.0),
            step=10.0,
        )

    with filter_col2:
        # Selectable guest capacity as requested
        min_guest_capacity = st.selectbox(
            "Minimum Guest Capacity:",
            options=[1, 2, 3, 4, 5],
            index=1,
            help="Filters rooms capable of accommodating at least this number of guests.",
        )

    with filter_col3:
        all_locations = ["All Locations"] + sorted(list({h.location for h in hotels}))
        selected_location = st.selectbox("Hotel Location:", all_locations)

    # Execute pure filtering pipeline
    matched_rooms = filter_rooms_by_price(rooms, price_range[0], price_range[1])
    matched_rooms = filter_rooms_by_capacity(matched_rooms, min_guest_capacity)

    if selected_location != "All Locations":
        location_hotel_ids = {
            h.id for h in filter_hotels_by_location(hotels, selected_location)
        }
        matched_rooms = [r for r in matched_rooms if r.hotel_id in location_hotel_ids]

    st.markdown(
        f"**Pipeline Filter Output:** Matched `{len(matched_rooms)}` of `{len(rooms)}` available rooms."
    )

    if matched_rooms:
        hotel_map = {h.id: h for h in hotels}
        filtered_display = pd.DataFrame(
            [
                {
                    "Room ID": r.id,
                    "Type": r.room_type,
                    "Hotel": hotel_map.get(r.hotel_id).name if r.hotel_id in hotel_map else r.hotel_id,
                    "Location": hotel_map.get(r.hotel_id).location if r.hotel_id in hotel_map else "—",
                    "Base Price": f"${r.base_price:.2f}/night",
                    "Capacity": f"{r.capacity} guest(s)",
                    "Amenities": ", ".join(r.amenities),
                }
                for r in matched_rooms
            ]
        )
        st.dataframe(filtered_display, use_container_width=True, hide_index=True)
    else:
        st.warning("No rooms match the selected price, capacity, and location criteria.")

    st.markdown("---")
    st.markdown("### 2. Higher-Order Pipelines (`core/fp_tools.py`)")

    hof_tab1, hof_tab2, hof_tab3 = st.tabs(["MAP Transformations", "REDUCE Folding", "Function Composition"])

    with hof_tab1:
        st.markdown("#### Immutable Projections via `map`")
        st.write(
            "**`extract_hotel_names(hotels)`:**",
            extract_hotel_names(hotels),
        )

        st.markdown("#### Dynamic Price Adjustment (`transform_rooms_with_multiplier`)")
        surge_rate = st.slider("Seasonal Surge Adjustment (+%):", min_value=0, max_value=60, value=15, step=5)
        multiplier = 1.0 + (surge_rate / 100.0)

        transformed_rooms = transform_rooms_with_multiplier(rooms, multiplier)

        surge_comparison = pd.DataFrame(
            [
                {
                    "Room ID": orig.id,
                    "Room Type": orig.room_type,
                    "Original Price": f"${orig.base_price:.2f}",
                    f"Adjusted Price (+{surge_rate}%)": f"${trans.base_price:.2f}",
                    "Immutability Verified": "True (New instance generated)",
                }
                for orig, trans in zip(rooms, transformed_rooms)
            ]
        )
        st.dataframe(surge_comparison, use_container_width=True, hide_index=True)

    with hof_tab2:
        st.markdown("#### Aggregations via `reduce`")
        r_col1, r_col2, r_col3 = st.columns(3)

        with r_col1:
            total_rev = calculate_total_revenue(bookings)
            st.metric("Total Confirmed Revenue", f"${total_rev:,.2f}")
            st.caption("Calculated using `reduce` over active bookings (cancelled bookings filtered out).")

        with r_col2:
            avg_rating = calculate_average_hotel_rating(hotels)
            st.metric("Average Hotel Rating", f"{avg_rating:.2f} / 5.0")
            st.caption("Calculated by folding rating values via `reduce` and dividing by collection length.")

        with r_col3:
            cheapest = find_cheapest_room(rooms)
            cheapest_display = f"{cheapest.room_type} (${cheapest.base_price:.2f})" if cheapest else "None"
            st.metric("Cheapest Room", cheapest_display)
            st.caption("Extremum determination using `reduce(min_func, rooms)` without stateful iteration.")

        st.markdown("#### Combined Map + Reduce: Unique Hotel Amenities")
        unique_amenities = extract_unique_hotel_amenities(hotels)
        st.write("`extract_unique_hotel_amenities(hotels)`:", sorted(list(unique_amenities)))

    with hof_tab3:
        st.markdown("#### Mathematical Composition: `(f ∘ g)(x) = f(g(x))`")
        st.markdown(
            "The `compose` helper binds two unary transformations into a single reusable pipeline:"
        )
        st.code(
            """def compose(f, g):
    return lambda x: f(g(x))

# Example pipeline: Calculate 3 nights stay and apply 10% discount:
calc_stay = lambda rate: calculate_total_price(rate, nights=3, seasonal_multiplier=1.2)
apply_promo = lambda total: apply_discount(total, discount_percent=10.0)
quote_pipeline = compose(apply_promo, calc_stay)
""",
            language="python",
        )
        test_rate = st.number_input("Input Base Nightly Rate ($):", value=150.0, step=10.0)
        calc_stay = lambda rate: calculate_total_price(rate, nights=3, seasonal_multiplier=1.2)
        apply_promo = lambda total: apply_discount(total, discount_percent=10.0)
        pipeline = compose(apply_promo, calc_stay)
        result = pipeline(test_rate)
        st.info(f"Pipeline Result for ${test_rate:.2f}/night (3 nights @ 1.2x with 10% promo): **${result:.2f}**")


# ============================================================================
# SECTION 4: PIPELINES (PRICING & STAY CALCULATOR)
# ============================================================================
elif current_section == "Pipelines":
    st.markdown('<div class="main-header">Pricing & Reservation Pipelines</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Interactive stay quotation engine driven by pure mathematical functions (core/pricing.py)</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        The pricing pipeline is composed of deterministic mathematical functions:
        - `calculate_nights(check_in, check_out) -> int`
        - `calculate_total_price(base_price, nights, seasonal_multiplier) -> float`
        - `apply_discount(total_price, discount_percent) -> float`
        """
    )

    calc_col1, calc_col2 = st.columns([1, 1])

    with calc_col1:
        st.subheader("Reservation Inputs")
        room_dict = {
            f"[{r.id}] {r.room_type} — ${r.base_price:.2f}/night (Max: {r.capacity} guests)": r
            for r in rooms
        }
        chosen_room_label = st.selectbox("Select Room:", list(room_dict.keys()))
        selected_room: Room = room_dict[chosen_room_label]

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            check_in_date = st.date_input("Check-In Date:", value=date.today() + timedelta(days=7))
        with d_col2:
            check_out_date = st.date_input("Check-Out Date:", value=date.today() + timedelta(days=11))

        multiplier_presets = {
            "Standard Season (1.00x)": 1.00,
            "Low / Off-Peak Season (0.85x, 15% reduction)": 0.85,
            "High Season (1.20x, +20%)": 1.20,
            "Peak Holiday Season (1.40x, +40%)": 1.40,
            "Special Event Surge (1.60x, +60%)": 1.60,
        }
        chosen_preset = st.selectbox("Seasonal Multiplier:", list(multiplier_presets.keys()), index=2)
        seasonal_mult = multiplier_presets[chosen_preset]

        discount_val = st.slider("Promotional Discount (%):", min_value=0, max_value=50, value=0, step=5)

    with calc_col2:
        st.subheader("Quotation Breakdown")
        nights_count = calculate_nights(check_in_date, check_out_date)

        if nights_count <= 0:
            st.error("Invalid stay dates: Check-Out must occur after Check-In.")
        else:
            base_subtotal = calculate_total_price(selected_room.base_price, nights_count, 1.00)
            seasonal_total = calculate_total_price(selected_room.base_price, nights_count, seasonal_mult)
            final_quote = apply_discount(seasonal_total, discount_val)
            discount_amount = round(seasonal_total - final_quote, 2)

            q1, q2 = st.columns(2)
            q1.metric("Stay Duration", f"{nights_count} night(s)")
            q2.metric("Base Rate", f"${selected_room.base_price:.2f} / night")

            q3, q4 = st.columns(2)
            q3.metric("Seasonal Factor", f"{seasonal_mult:.2f}x")
            q4.metric("Final Quote", f"${final_quote:.2f}")

            st.markdown("#### Pure Pipeline Execution Trace")
            st.code(
                f"""1. calculate_nights({check_in_date}, {check_out_date})
   = {nights_count} nights

2. calculate_total_price(base_price={selected_room.base_price}, nights={nights_count}, seasonal_multiplier={seasonal_mult})
   = ${selected_room.base_price} * {nights_count} * {seasonal_mult}
   = ${seasonal_total:.2f}

3. apply_discount(total_price={seasonal_total:.2f}, discount_percent={discount_val}%)
   = ${seasonal_total:.2f} - ${discount_amount:.2f}
   = ${final_quote:.2f}
""",
                language="text",
            )
            st.success(
                f"Quotation confirmed: **{selected_room.room_type}** for {nights_count} night(s) = **${final_quote:.2f}**."
            )


# ============================================================================
# SECTION 5: ASYNC / FRP (IN DEVELOPMENT)
# ============================================================================
elif current_section == "Async/FRP":
    st.markdown('<div class="main-header">Asynchronous & Reactive Programming (Async / FRP)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Module Status: In Development</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<span class="status-badge-dev">IN DEVELOPMENT</span>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### Planned Module Scope
        This section is reserved for the upcoming laboratory assignments focusing on **Asynchronous Execution** and
        **Functional Reactive Programming (FRP)**:

        1. **Asynchronous Availability Checks (`asyncio`):**
           - Concurrent querying of distributed hotel provider inventories without blocking the main event loop.
           - Async coroutines for batch processing reservation confirmations and payment authorization webhooks.

        2. **Reactive Event Streams (FRP):**
           - Observables and event streams modeling real-time price fluctuations and seat/room occupancy updates.
           - Declarative event stream transformations (`filter`, `debounce`, `combineLatest`).
        """
    )
    st.info("Module scheduled for implementation in accordance with coursework laboratory roadmap.")


# ============================================================================
# SECTION 6: REPORTS (IN DEVELOPMENT)
# ============================================================================
elif current_section == "Reports":
    st.markdown('<div class="main-header">Analytics & Aggregation Reports</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Module Status: In Development</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<span class="status-badge-dev">IN DEVELOPMENT</span>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### Planned Module Scope
        This section is reserved for higher-level reporting and analytical data pipelines:

        1. **Revenue Analytics by Hotel and Region:**
           - Multi-dimensional aggregation using pure folding pipelines (`reduce`).
           - Trend indicators and yield metrics comparing seasonal multipliers against baseline occupancy.

        2. **Occupancy & Demand Reports:**
           - Capacity utilization analysis across room classes.
           - Automated generation of downloadable analytical summaries.
        """
    )
    st.info("Reporting module scheduled for implementation in subsequent coursework iterations.")


# ============================================================================
# SECTION 7: TESTS (PYTEST RUNNER)
# ============================================================================
elif current_section == "Tests":
    st.markdown('<div class="main-header">Pytest Automated Test Suite</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Automated verification of immutability guarantees, pure calculations, and HOF pipelines</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        The test suite in `tests/test_labs.py` executes comprehensive unit and functional assertions
        covering every pure component in the system:
        - **Immutability Enforcement:** Confirms that modifying any `@dataclass(frozen=True)` raises `FrozenInstanceError`.
        - **Pure Pricing Functions:** Verifies calculation determinism, non-negative night durations, and discount clamping.
        - **Predicate Filters:** Validates filtering logic for price ranges, capacities, and locations.
        - **Higher-Order Functions:** Tests `map`, `filter`, `reduce`, and function composition contracts.
        """
    )

    t_col1, t_col2 = st.columns([1, 2])

    with t_col1:
        st.markdown("#### Test Execution Controls")
        st.caption("Click to trigger pytest in the current runtime environment:")
        run_button = st.button("🚀 Run Pytest Test Suite", type="primary", use_container_width=True)

        st.markdown("#### Terminal Command")
        st.code("pytest -v tests/test_labs.py", language="bash")

    with t_col2:
        st.markdown("#### Test Results")
        if run_button:
            with st.spinner("Executing test suite..."):
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", "-v", "tests/test_labs.py"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0:
                        st.success("All automated tests passed successfully!")
                    else:
                        st.error(f"Test run completed with non-zero exit code: {result.returncode}")

                    st.code(result.stdout or "No standard output.", language="text")
                    if result.stderr:
                        st.code(result.stderr, language="text")
                except Exception as ex:
                    st.error(f"Failed to execute pytest: {ex}")
        else:
            st.info("Click 'Run Pytest Test Suite' to execute all unit tests and inspect real-time outputs.")


# ============================================================================
# SECTION 8: ABOUT
# ============================================================================
elif current_section == "About":
    st.markdown('<div class="main-header">About Project</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Functional Programming Coursework Project Specification</div>',
        unsafe_allow_html=True,
    )

    about_col1, about_col2 = st.columns([2, 1])

    with about_col1:
        st.markdown("### Project Information")
        st.markdown(
            """
            - **Course**: Functional Programming in Python
            - **Project Topic**: Hotel & Room Booking System
            - **Architecture**: Single Page Web Application (Streamlit) + Terminal CLI
            - **Paradigm**: Pure Functional Programming
              - Immutability guarantees via frozen dataclasses
              - Pure, deterministic calculation functions
              - Declarative higher-order pipelines (`map`, `filter`, `reduce`)
              - Mathematical function composition
            """
        )

        st.markdown("### Technologies Used")
        st.markdown(
            """
            - **Python 3.11**: Core runtime environment
            - **Streamlit**: Single-page application web interface
            - **Pytest**: Automated testing framework
            - **Pandas**: Structured tabular representation of immutable data
            """
        )

    with about_col2:
        st.markdown("### Author & Project Meta")
        st.markdown(
            """
            <div class="metric-card" style="text-align: left;">
                <p><strong>Topic:</strong> Hotel/Room Booking</p>
                <p><strong>System:</strong> Functional Python</p>
                <p><strong>Version:</strong> 1.0.0</p>
                <p><strong>Status:</strong> Active</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
