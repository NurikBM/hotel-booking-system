# Hotel & Room Booking System (Pure Functional Python)

Course project in "Functional Programming".  
Domain: **Hotel & Room Booking System (filters, prices, availability, memoization, pure monadic validations, lazy streams)**.  
Implemented: **Lab 1**, **Lab 2**, **Lab 3**, **Lab 4**, and **Lab 5**.

---

## Project Architecture

```
app/main.py          # Streamlit Web UI (8 tabs per specification)
core/domain.py       # Domain immutable entities (Hotel, RoomType, RatePlan, Price, Availability, Guest, CartItem, Booking, Payment, Event, Rule)
core/transforms.py   # Lab 1 & 2: load seed.json, cart hold/remove, nightly_sum (reduce), closures by_city, by_capacity, by_features, by_price_range, lambdas
core/recursion.py    # Lab 2: recursive search for quotes (Hotels -> Rooms -> Rates), recursive discount rules and min price search
core/memo.py         # Lab 3: pure memoizer @memoize (LRU eviction, stats, clear), quote_offer (@lru_cache), memoized_nightly_sum, speedup benchmark
core/ftypes.py       # Lab 4: monads Maybe (Some/Nothing), Either (Right/Left), pure safe lookups, zero-exception booking validation
core/lazy.py         # Lab 5: lazy iterators: calendar stream, iter_available_days, lazy_offers, take_lazy, drop_lazy, LazySequence
core/frp.py          # Lab 6 (placeholder)
core/compose.py      # Lab 7 (placeholder)
core/service.py      # Lab 7 (placeholder)
core/report.py       # Lab 8 (placeholder)
data/seed.json       # Realistic dataset: 6 hotels, 24 room types, 48 rate plans, 2880 prices (60 days), 50 guests
cli.py               # Interactive CLI menu (Labs 1–5)
streamlit_app.py     # Streamlit entry adapter (from app.main import main; main())
tests/test_lab1.py   # 7 tests Lab 1 (models, seed, hold/remove, nightly_sum)
tests/test_lab2.py   # 8 tests Lab 2 (closures, by_price_range, lambdas, recursive algorithms)
tests/test_lab3.py   # 11 tests Lab 3 (memoization, quote_offer, LRU eviction, speedup benchmark)
tests/test_lab4.py   # 21 tests Lab 4 (Maybe/Either monad laws, Railway Oriented Validation, AST exception-free verification, Streamlit AppTest)
tests/test_lab5.py   # 7 tests Lab 5 (iter_available_days, lazy_offers, lazy_calendar_stream, take/drop_lazy, LazySequence chaining)
```

---

## Domain Model & Specification Compliance

The domain model (`core/domain.py`) strictly adheres to the course specification and reference dataset `data/seed.json`:
1. **Immutability (`frozen=True`):** all entities (`Hotel`, `RoomType`, `RatePlan`, `Price`, `Availability`, `Guest`, `CartItem`, `Booking`, `Payment`, `Event`, `Rule`) are immutable frozen dataclasses.
2. **Pure Integer Money (`int`):** monetary amounts are represented strictly in integer cents / kopecks / tiyn without `float` to avoid rounding artifacts.
3. **Strict ISO-8601 Dates:** all calendar dates are strings in `"YYYY-MM-DD"` format, guaranteeing deterministic hashability and compatibility with `@lru_cache`.
4. **Seed Compatibility:** `beds` in `RoomType` is represented as a tuple of bed type strings `tuple[str, ...]`, `Price` includes `id` and `currency="KZT"`, `Availability` includes `id`, `RatePlan` includes `hotel_id`, `title`, `refundable`, and `cancel_before_days`. `Rule(id, kind, payload)` is fully serializable and hashable.

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
  - `safe_rate`, `safe_room_type`, `validate_dates`, `validate_cart_item`, `validate_booking`.
  - `validate_and_calculate_booking(booking_id, guest, items, prices, availability, rules, room_types, rates) -> Either[dict, Booking]`.

### Lab 5: Lazy Evaluation & Infinite Streams
- **Lazy Generators (`core/lazy.py`):**
  - `iter_available_days(avail, room_type_id) -> Iterator[tuple[str, int]]`: yields availability tuples on demand.
  - `lazy_offers(hotels, room_types, rates, prices, avail, predicate, checkin, checkout) -> Iterator[tuple[Hotel, RoomType, RatePlan, int]]`: streams matching offers without evaluating unneeded records.
  - `lazy_calendar_stream(start_date, days=None) -> Iterator[str]`: infinite/finite generator of ISO calendar dates.
  - `take_lazy(iterable, n)` & `drop_lazy(iterable, n)`: stream combinators for lazy pagination.
  - `lazy_filter` & `lazy_map`: composable functional stream transformers.
  - `LazySequence[T]`: fluent immutable wrapper with deferred terminal execution (`to_tuple`, `head`).

---

## Web Interface Navigation (Streamlit)

1. **Overview:** Architectural summary for Labs 1–5 and dataset metrics from `data/seed.json`.
2. **Data:** Interactive inspection of hotels, room types, rate plans, and guests.
3. **Functional Core:**
   - Recursive quote search (Lab 2);
   - Recursive discount rules engine (Lab 2);
   - **Section "Maybe / Either (Lab 4)":** safe rate lookup via `safe_rate` and cart item validation via `validate_cart_item`.
4. **Pipelines:**
   - Cart hold pipeline `hold_item`/`remove_hold` (Lab 1);
   - Memoized nightly sum `memoized_nightly_sum` and benchmark (Lab 3);
   - **Section "Lazy Evaluation Streams (Lab 5)":** interactive slider to filter and lazily stream top K offers under budget without materializing the dataset.
5. **Async/FRP:** Roadmap for upcoming labs 6–8 (`frp.py`, `compose.py`, `service.py`, `report.py`).
6. **Reports:**
   - Hotel and room distribution analytics;
   - `quote_offer` caching latency measurements (Lab 3);
   - **Section "Validate & Calculate Booking (Lab 4)":** interactive runner for 5 booking validation scenarios.
7. **Tests:** In-browser automated test runner (`pytest`) covering Labs 1–5.
8. **About:** Domain invariants and functional programming purity rules.

---

## Instructions

### 1. Running the CLI
```bash
python3 cli.py
```
Menu options (Labs 1–5):
1. Statistics for `data/seed.json` (Lab 1)
2. Closures & Lambda Filters (Lab 2)
3. Recursive Quote Search (Lab 2)
4. Recursive Business Rules Engine (Lab 2)
5. Pure Memoization & Speedup Benchmark (Lab 3)
6. Monadic Validation Pipeline (Lab 4 Maybe/Either)
7. Lazy Streams & Deferred Evaluation (Lab 5)
8. Run Automated Test Suite (pytest)
0. Exit

### 2. Running the Streamlit Web Application
```bash
streamlit run streamlit_app.py --server.port 3000
```

### 3. Running Automated Tests (all 54 tests pass)
```bash
python -m pytest -q tests/
```
Running per-lab test suites:
```bash
pytest -v tests/test_lab1.py
pytest -v tests/test_lab2.py
pytest -v tests/test_lab3.py
pytest -v tests/test_lab4.py
pytest -v tests/test_lab5.py
```

### 4. Code Quality and Formatting Checks
```bash
black --check .
ruff check .
```
