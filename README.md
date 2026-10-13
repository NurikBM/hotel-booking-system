# Hotel & Room Booking System (Pure Functional Python)

Course project in "Functional Programming".  
Domain: **Hotel & Room Booking System (filters, prices, availability, memoization, pure monadic validations)**.  
Implemented: **Lab 1**, **Lab 2**, **Lab 3**, and **Lab 4**.

---

## Project Architecture

```
app/main.py          # Streamlit Web UI (8 tabs per specification)
core/domain.py       # Domain immutable entities (Hotel, RoomType, RatePlan, Price, Availability, Guest, CartItem, Booking, Payment, Event, Rule)
core/transforms.py   # Lab 1 & 2: load seed.json, cart hold/remove, nightly_sum (reduce), closures by_city, by_capacity, by_features, by_price_range, lambdas
core/recursion.py    # Lab 2: recursive search for quotes (Hotels -> Rooms -> Rates), recursive discount rules and min price search
core/memo.py         # Lab 3: pure memoizer @memoize (LRU eviction, stats, clear), quote_offer (@lru_cache), memoized_nightly_sum, speedup benchmark
core/ftypes.py       # Lab 4: monads Maybe (Some/Nothing), Either (Right/Left), pure safe lookups, zero-exception booking validation
core/lazy.py         # Lab 5 (placeholder)
core/frp.py          # Lab 6 (placeholder)
core/compose.py      # Lab 7 (placeholder)
core/service.py      # Lab 7 (placeholder)
core/report.py       # Lab 8 (placeholder)
data/seed.json       # Realistic dataset: 6 hotels, 24 room types, 48 rate plans, 2880 prices (60 days), 50 guests
cli.py               # Interactive CLI menu (Labs 1–4)
streamlit_app.py     # Streamlit entry adapter (from app.main import main; main())
tests/test_lab1.py   # 7 tests Lab 1 (models, seed, hold/remove, nightly_sum)
tests/test_lab2.py   # 8 tests Lab 2 (closures, by_price_range, lambdas, recursive algorithms)
tests/test_lab3.py   # 11 tests Lab 3 (memoization, quote_offer, LRU eviction, speedup benchmark)
tests/test_lab4.py   # 21 tests Lab 4 (Maybe/Either monad laws, Railway Oriented Validation, AST exception-free verification, Streamlit AppTest)
```

---

## Domain Model & Specification Compliance

The domain model (`core/domain.py`) strictly adheres to the course specification and reference dataset `data/seed.json`:
1. **Immutability (`frozen=True`):** all entities (`Hotel`, `RoomType`, `RatePlan`, `Price`, `Availability`, `Guest`, `CartItem`, `Booking`, `Payment`, `Event`, `Rule`) are immutable frozen dataclasses.
2. **Pure Integer Money (`int`):** monetary amounts are represented strictly in integer cents / kopecks / tiyn without `float` to avoid rounding artifacts.
3. **Strict ISO-8601 Dates:** all calendar dates are strings in `"YYYY-MM-DD"` format, guaranteeing deterministic hashability and compatibility with `@lru_cache`.
4. **Seed Compatibility:** `beds` in `RoomType` is represented as a tuple of bed type strings `tuple[str, ...]` (with automatic tuple conversion if initialized from integer bed counts), `Price` includes `id` and `currency="KZT"`, `Availability` includes `id`, `RatePlan` includes `hotel_id`, `title`, `refundable`, and `cancel_before_days`. `Rule(id, kind, payload)` is fully serializable and hashable.

---

## Implemented Laboratories

### Lab 1: Domain Model, Immutability, Transformations
- Immutable structures `@dataclass(frozen=True)` for all domain entities.
- Pure functions: `load_seed`, `calculate_nights`, `generate_date_range`.
- Fold-based calculation `nightly_sum(prices, checkin, checkout, rate_id) -> int` via `functools.reduce`.
- Pure shopping cart operations: `hold_item`, `remove_hold`, `calculate_cart_total`.

### Lab 2: Closures, Lambdas, and Pure Recursion
- Higher-order predicate factories: `by_city`, `by_capacity`, `by_features`, `by_price_range`.
- Lambda sorters: `sort_hotels_by_stars`, `sort_rooms_by_capacity`, `sort_prices_by_amount`.
- Recursive quote search `recursive_search_available_quotes` without loops.
- Recursive rule interpreter `recursive_apply_rules` and minimum search `recursive_find_cheapest_quote`.

### Lab 3: Pure Memoization and Performance Optimization
- Decorator `@memoize(maxsize=1024)` with cache introspection `cache_info()` and clean reset `cache_clear()`.
- Combined quote function `@lru_cache def quote_offer(...) -> tuple[int, bool]`, reusing `nightly_sum`, `recursive_apply_rules`, and recursive date check `check_dates_available_rec`.
- Speedup benchmark `benchmark_speedup` over 250+ iterations demonstrating 10x–50x speedup.

### Lab 4: Functional Monads and Pure Validation (Railway Oriented Programming)
- **Monad Containers (`core/ftypes.py`):**
  - `Maybe[T]`: `Some[T]` / `Nothing` with `map`, `bind`, `get_or_else`.
  - `Either[E, T]`: `Right[T]` / `Left[E]` with `map`, `bind`, `get_or_else`.
  - Monad bridge `maybe_to_either(maybe, error_dict) -> Either`.
- **Zero-Exception Pure Validators (zero `try`/`except`/`raise` in `core/ftypes.py`):**
  - `safe_rate(rates: tuple[RatePlan, ...], rate_id: str) -> Maybe[RatePlan]`
  - `safe_room_type(room_types: tuple[RoomType, ...], room_type_id: str) -> Maybe[RoomType]`
  - `validate_dates(checkin: str, checkout: str) -> Either[dict, tuple[str, str]]`
  - `validate_cart_item(item: CartItem, room_types: tuple[RoomType, ...], rates: tuple[RatePlan, ...], availability: tuple[Availability, ...], rules: tuple[Rule, ...]) -> Either[dict, CartItem]`
  - `validate_booking(booking: Booking, prices: tuple[Price, ...], availability: tuple[Availability, ...], rules: tuple[Rule, ...], room_types: tuple[RoomType, ...], rates: tuple[RatePlan, ...]) -> Either[dict, Booking]`
- **End-to-End Booking Validation Pipeline:**
  ```python
  validate_and_calculate_booking(
      booking_id: str,
      guest: Guest,
      items: tuple[CartItem, ...],
      prices: tuple[Price, ...],
      availability: tuple[Availability, ...],
      rules: tuple[Rule, ...] = DEFAULT_RULES,
      room_types: tuple[RoomType, ...] = (),
      rates: tuple[RatePlan, ...] = (),
  ) -> Either[dict, Booking]
  ```

---

## Web Interface Navigation (Streamlit)

1. **Overview:** Architectural summary for Labs 1–4 and dataset metrics from `data/seed.json`.
2. **Data:** Interactive inspection of hotels, room types, rate plans, and guests.
3. **Functional Core:**
   - Recursive quote search (Lab 2);
   - Recursive discount rules engine (Lab 2);
   - **Section "Maybe / Either (Lab 4)":** safe rate lookup via `safe_rate` (`Some`/`Nothing`) and cart item validation via `validate_cart_item` (`Right`/`Left`).
4. **Pipelines:** cart hold pipeline `hold_item`/`remove_hold` (Lab 1), memoized nightly sum `memoized_nightly_sum`, and memoization speedup benchmark (Lab 3).
5. **Async/FRP:** Roadmap for upcoming labs 5–8 (`lazy.py`, `frp.py`, `compose.py`, `service.py`, `report.py`).
6. **Reports:**
   - Hotel and room distribution analytics;
   - `quote_offer` caching latency measurements (Lab 3);
   - **Section "Validate & Calculate Booking (Lab 4)":** interactive runner for 5 booking validation scenarios (Valid Booking, Capacity Exceeded, Unavailable Dates, Invalid Date Range, Empty Cart).
7. **Tests:** In-browser automated test runner (`pytest`) covering all labs.
8. **About:** Domain invariants and functional programming purity rules.

---

## Instructions

### 1. Running the CLI
```bash
python3 cli.py
```
Menu options (Labs 1–4):
1. Statistics for `data/seed.json` (Lab 1)
2. Closures & Lambda Filters (Lab 2)
3. Recursive Quote Search (Lab 2)
4. Recursive Business Rules Engine (Lab 2)
5. Pure Memoization & Speedup Benchmark (Lab 3)
6. Monadic Validation Pipeline (Lab 4): safe lookups and 5 validation scenarios
7. Run pytest test suite
0. Exit

### 2. Running the Streamlit Web Application
```bash
streamlit run streamlit_app.py --server.port 3000
```
Or:
```bash
npm run dev
```

### 3. Running Automated Tests (all 47 tests pass)
```bash
python -m pytest -q tests/
```
Running per-lab test suites:
```bash
pytest -v tests/test_lab1.py
pytest -v tests/test_lab2.py
pytest -v tests/test_lab3.py
pytest -v tests/test_lab4.py
```

### 4. Code Quality and Formatting Checks
```bash
black --check .
ruff check .
```
The codebase conforms 100% to Black and Ruff checks (0 warnings, 0 errors).
