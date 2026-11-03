# Role & Objective
You are a Python Software Engineer implementing a university lab project in
**pure functional-style Python**. The domain is "Hotel / Room Booking
(filters, prices)" — a single-page web app (Streamlit) simulating hotel
search and booking: hotels, room types, rate plans/prices, availability
calendar, filters, booking cart (hold), payments, cancellation rules, and
reports.

This spec is derived directly from the official assignment PDF
("Hotel_Room_Booking_English.pdf"). It supersedes any earlier version of
this file. If anything here conflicts with an earlier draft, this file wins.

The project must be implemented in a functional programming style: pure
functions, immutability, composition, recursion, laziness, FRP, async.
Keep it simple and readable — this is coursework, not a production system.

Team: 2-3 students. Language: Python 3.11+.
Submission: one PR per lab (`lab-0N`) + a 2-minute screencast describing
what was implemented and where to click in the UI.

---

# IMPORTANT: Retrofit needed before Lab 3

Labs 1-2 were previously implemented against an earlier, incorrect draft of
this spec, using a simplified domain model (`Hotel(location, rating,
amenities)`, `Room(base_price, capacity)` with price baked into the room,
float prices, `datetime.date` objects). That model does **not** match the
PDF's domain model and is missing entities Lab 3 depends on (`RatePlan`,
`Price`, `Availability`, `Rule`). Lab 3's `quote_offer` cannot be written
without them.

Before starting Lab 3, do the following retrofit:

1. Replace/extend `domain/models.py` (or move to `core/domain.py` per the
   structure below) with the entities in "Domain Model" below — this
   replaces the old `Hotel`/`Room`/`Booking`/`Review` set.
2. Switch all monetary amounts from `float` to `int` (kopecks/tiyn). Round
   only at the very end of a calculation chain.
3. Switch all dates from `datetime.date` to ISO strings (`"YYYY-MM-DD"`).
   Do not mix `datetime` objects and strings in cache keys (this matters a
   lot for Lab 3's `@lru_cache`).
4. Create `data/seed.json` with realistic volume (see Lab 1 below).
5. Rename modules to match the PDF's file structure (see below) so a
   grader can map "this file = this lab" using the PDF's own names.
6. Rebuild the Streamlit menu to the exact 8 required tabs (see below).
7. Backfill Lab 1 with the cart/hold functions the PDF requires
   (`hold_item`, `remove_hold`, `nightly_sum`) — the old Lab 1 only had
   price/nights calculations, not cart logic.
8. Keep the existing closures and recursive algorithms from the old Lab 2
   conceptually (closures + 2 recursive functions is still correct), but
   rename/rewrite them to operate on the new domain model and match the
   PDF's suggested signatures (`by_city`, `by_capacity`, `by_features`,
   `by_price_range`, `split_date_range`, etc.).

Do not start Lab 3 until steps 1-4 are done — `quote_offer` needs
`RatePlan`, `Price`, `Availability`, and `Rule` to exist.

---

# Domain Model (core/domain.py)

All entities are immutable (`@dataclass(frozen=True)` or `NamedTuple`). All
operations return new collections (`tuple`, `frozenset`); input values are
never mutated.

- `Hotel(id, name, stars: int, city: str, features: tuple[str, ...])`
- `RoomType(id, hotel_id, name, capacity: int, beds: tuple[str, ...], features: tuple[str, ...])`
- `RatePlan(id, hotel_id, room_type_id, title: str, meal: str, refundable: bool, cancel_before_days: int | None)`
- `Price(id, rate_id, date: str, amount: int, currency: str)` — nightly price, one row per date, `amount` in integer kopecks/tiyn
- `Availability(id, room_type_id, date: str, available: int)`
- `Guest(id, name, email: str)`
- `CartItem(id, hotel_id, room_type_id, rate_id, checkin: str, checkout: str, guests: int)` — pre-booking/hold
- `Booking(id, guest_id, items: tuple[CartItem, ...], total: int, status: str)` — status: held/confirmed/cancelled
- `Payment(id, booking_id, amount: int, ts: str, method: str)`
- `Event(id, ts: str, name: str, payload: dict)` — SEARCH, HOLD, BOOKED, CANCELLED, PRICE_CHANGED
- `Rule(id, kind: str, payload: dict)` — min_stay, max_stay, weekend_markup, city_tax, ...

---

# Constraints

1. Python 3.11+.
2. Business logic is pure (no I/O, no mutation) where reasonably possible.
3. Type hints on function signatures.
4. `pytest`, minimum 5 tests per lab (≥40 total across all 8 labs).
5. `black` and `ruff` (or `flake8`) must pass with no issues.
6. No TODOs / placeholders in submitted code.
7. UI: Streamlit (recommended) or Gradio / FastAPI+HTML.
8. Required menu, exactly these 8 tabs:
   **Overview · Data · Functional Core · Pipelines · Async/FRP · Reports · Tests · About**
9. Money stored as integers (kopecks/tiyn); tax/surcharges applied to
   integers, rounded only at the very end.
10. Dates stored as ISO strings (`YYYY-MM-DD`); never mix `datetime`
    objects and strings in the same cache key.
11. Availability must be checked for every day in a stay interval.
12. Refundability: if `refundable=False`, cancellation is only allowed
    before `cancel_before_days` (or is prohibited entirely if that field
    is `None`).

---

# File Structure

```
project/
  app/
    main.py                # Streamlit entry point, 8-tab menu
  core/
    domain.py               # immutable models (see Domain Model above)
    transforms.py            # pure transformations, predicates, HOF (Lab 1)
    recursion.py             # rate/policy hierarchies, date ranges (Lab 2)
    memo.py                  # cache for expensive price/availability (Lab 3)
    ftypes.py                # Maybe / Either (Lab 4)
    lazy.py                  # lazy iterators: calendar, offers (Lab 5)
    frp.py                   # event bus: SEARCH, HOLD, BOOKED, CANCELLED, PRICE_CHANGED (Lab 6)
    compose.py                # compose / pipe (Lab 7)
    service.py               # SearchService / QuoteService / BookingService (Lab 7)
    report.py                 # revenue, occupancy, cancellation reports (Lab 8)
  data/
    seed.json                # sample dataset (see Lab 1)
  tests/
    test_lab1.py
    test_lab2.py
    test_lab3.py
    ...                      # one file per lab, ≥5 tests each
  README.md                  # launch instructions, navigation, signatures, team contributions
  requirements.txt
  ruff.toml / pyproject.toml
```

Each lab's code stays in its own module (per the mapping above) so a
grader can point to "this file = this lab."

Run commands (Streamlit):
```
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/main.py
pytest -q
ruff check .
black --check .
```

`requirements.txt` (minimum): `streamlit`, `pytest`, `black`, `ruff`.

---

# Lab Work Requirements

## Lab 1 (4 pts) — Pure Functions + Immutability + HOF
**Menu:** Overview · Data · Functional Core

- `data/seed.json`: 5-8 hotels in 2-3 cities; 20-30 room types; 40-60 rate
  plans; 60-day price calendars (one nightly price per date); room
  availability; 50 guests.
- In `core/transforms.py`:
  ```python
  def load_seed(path: str) -> tuple[...]: ...

  def hold_item(cart: tuple[CartItem, ...], item: CartItem) -> tuple[CartItem, ...]: ...

  def remove_hold(cart: tuple[CartItem, ...], item_id: str) -> tuple[CartItem, ...]: ...

  def nightly_sum(
      prices: tuple[Price, ...], checkin: str, checkout: str, rate_id: str
  ) -> int:
      # reduce over dates
      ...
  ```
- UI (Overview tab): aggregates (#hotels, #room_types, #rates, days in
  price calendar), average price by city/stars.
- Acceptance: immutable models, new collections returned; uses
  `map`/`filter`/`reduce`; ≥5 tests.

## Lab 2 (4 pts) — Lambdas and Closures + Recursion
**Menu:** Functional Core · Pipelines

1. Closure filters for search, in `core/transforms.py` or a dedicated
   module:
   ```python
   def by_city(city: str): ...
   def by_capacity(guests: int): ...
   def by_features(required: tuple[str, ...]): ...
   def by_price_range(min_amt: int, max_amt: int, currency: str): ...
   ```
2. Two recursive functions (pick 2) in `core/recursion.py`:
   ```python
   def split_date_range(checkin: str, checkout: str) -> tuple[str, ...]: ...

   def apply_rate_inheritance(rate: RatePlan, rules: tuple[Rule, ...]) -> RatePlan: ...

   def build_policy_tree(rate: RatePlan) -> tuple[dict, ...]: ...
   ```
3. UI: combine filters (city, capacity, features, budget) and show
   matching offers.
- Acceptance: ≥1 closure + ≥2 recursive functions; ≥5 tests.

## Lab 3 (4 pts) — Advanced Recursion + Memoization
**Menu:** Pipelines · Reports

- An "expensive" function in `core/memo.py` or `core/service.py`: quote an
  offer (price for the period + taxes + rule-based surcharges +
  availability check):
  ```python
  from functools import lru_cache

  @lru_cache
  def quote_offer(
      hotel_id: str,
      room_type_id: str,
      rate_id: str,
      checkin: str,
      checkout: str,
      prices_idx: tuple[Price, ...],
      avail_idx: tuple[Availability, ...],
      rules: tuple[Rule, ...],
  ) -> tuple[int, bool]:
      # -> (total_amount, is_available)
      ...
  ```
- All arguments must be hashable and immutable (tuples, not lists; ISO
  date strings, not `datetime`).
- Measure execution time before/after caching (ms) on 200-500 requests.
- UI: Reports → "Quotes (cached)".
- Acceptance: immutable cache keys; pure function; performance
  measurement shown; ≥5 tests.

## Lab 4 (4 pts) — Functional Patterns: Maybe/Either
**Menu:** Functional Core · Reports

- Implement `Maybe`/`Either` in `core/ftypes.py` (`map`, `bind`,
  `get_or_else`).
- Wrap risky operations:
  ```python
  def safe_rate(rates, rate_id) -> Maybe[RatePlan]: ...

  def validate_cart_item(
      item: CartItem, availability: tuple[Availability, ...], rules: tuple[Rule, ...]
  ) -> Either[dict, CartItem]: ...

  def validate_booking(
      booking: Booking, prices, availability, rules
  ) -> Either[dict, Booking]:
      # checks: min/max stay, capacity, availability for every day,
      # valid dates, cancellation policy
      ...
  ```
- UI: Functional Core/Reports — "validate and calculate booking" pipeline
  without try/except (container compositions only).
- Acceptance: errors/empty values handled through containers; ≥5 tests.

**Independent work (4 pts per block, Labs 1-4):** ≥5 tests per lab
(≥20 total for Labs 1-4), plus README with UI navigation.

## Lab 5 (4 pts) — Lazy Evaluation
**Menu:** Pipelines · Reports

- Lazy generators in `core/lazy.py`:
  ```python
  def iter_available_days(
      avail: tuple[Availability, ...], room_type_id: str
  ) -> Iterator[tuple[str, int]]: ...

  def lazy_offers(
      hotels, room_types, rates, prices, avail, predicate
  ) -> Iterator[tuple[Hotel, RoomType, RatePlan, int]]:
      """Stream (hotel, room, rate, price for period) for offers
      satisfying the condition."""
      ...
  ```
- Demonstration: filter the first k matching offers without full
  materialization.
- Acceptance: uses `yield` generators; materialization only at the final
  step; ≥5 tests.

## Lab 6 (4 pts) — FRP / Event Processing
**Menu:** Async/FRP

- Booking event bus in `core/frp.py`:
  ```python
  class Event(NamedTuple):
      name: str
      ts: str
      payload: dict

  class EventBus:
      def subscribe(self, name: str, handler: Callable[[Event, dict], dict]): ...
      def publish(self, name: str, payload: dict): ...
  ```
  Event names: SEARCH, HOLD, BOOKED, CANCELLED, PRICE_CHANGED.
- Pure subscriber functions build views: active holds, latest bookings,
  price changes, occupancy by dates.
- UI: event generation buttons; "live" panels.
- Acceptance: ≥2 event types; handlers pure (state-in → state-out);
  ≥5 tests.

## Lab 7 (4 pts) — Composition/Modularity + OOP Integration
**Menu:** Functional Core · Pipelines · Reports

1. Composition utilities in `core/compose.py`:
   ```python
   def compose(*funcs): ...
   def pipe(x, *funcs): ...
   ```
2. Facades in `core/service.py` (only compositions of pure functions; no
   business logic inside the class bodies):
   ```python
   class SearchService:
       def __init__(self, filters, scorers): ...
       def search(self, req: dict) -> tuple[tuple[str, ...], ...]: ...

   class QuoteService:
       def __init__(self, quoter): ...
       def quote(self, item: CartItem) -> int: ...

   class BookingService:
       def __init__(self, validators, quoter, finalizer): ...
       def confirm(self, guest: Guest, cart: tuple[CartItem, ...]) -> Either[dict, Booking]: ...
   ```
3. UI: "Search → Quote → Confirmation" showing intermediate steps.
- Acceptance: facade methods are compositions of pure functions;
  dependencies injected externally (constructor/factory, no global
  state); ≥5 tests.

## Lab 8 (4 pts) — Parallelism/Async + Final Integration
**Menu:** Async/FRP · Reports

1. Async quoting/search across multiple hotels/dates, in `core/service.py`
   or `app/main.py`:
   ```python
   async def quote_batch(items: list[CartItem]) -> dict[str, int]: ...

   async def search_parallel(reqs: list[dict]) -> list[tuple[str, ...]]:
       # asyncio.gather / executors
       ...
   ```
2. End-to-end: loading → filters → lazy offers → quote cache → validation
   pipeline → booking confirmation → report.
- Acceptance: actual async/parallel execution; a "one-click" report
  (sales totals, occupancy by dates/hotels) in `core/report.py`; ≥5 tests.

**Independent work (4 pts per block, Labs 5-8):** ≥5 additional tests per
lab (≥20 total for Labs 5-8).

---

# Mini-checklist for each submission

- Functions are implemented and linked to the corresponding menu item.
- No mutation of input structures (new values/projections are returned).
- ≥5 tests per lab; `pytest -q` passes.
- `black` + `ruff`/`flake8` pass without issues.
- README: launch instructions, navigation, function signatures, and team
  member contributions.
- Each lab submitted as its own PR (`lab-0N`) with a 2-minute screencast.

---

# Pricing and rules hints

- Money: store monetary amounts as integers (tiyn/kopecks). Apply
  taxes/surcharges to integers and round only at the very end.
- Rules: min/max stay, closed-to-arrival, closed-to-departure, weekend
  markup, city_tax per night — implement as separate pure functions and
  compose them.
- Availability: check availability for every day in the interval.
- Refundability: if `refundable=False`, allow cancellation only before
  `cancel_before_days` (or prohibit cancellation entirely if that field is
  `None`).
- Time zones/dates: store dates in ISO format `YYYY-MM-DD`; do not mix
  `datetime` objects and strings in cache keys.

---

# Notes for the coding agent

- This is the authoritative spec (derived from the official PDF). An
  earlier draft of this file used a different, simpler domain model and
  file layout — do not follow that older model; use the one above.
- Before touching Lab 3, complete the retrofit listed at the top of this
  file (domain model, int money, ISO date strings, seed.json, module
  names, Streamlit's 8-tab menu, Lab 1's cart/hold functions).
- Reuse the existing closures and recursive-algorithm *logic* from the
  prior Lab 2 implementation where it still fits conceptually (closures +
  2 recursive functions) — just rewire it to the new domain entities and
  the PDF's suggested function names.
- Keep each lab's code in its own module per the "File Structure" mapping
  so a grader can point to "this file = this lab."
- Prefer clarity over cleverness — a grader should be able to read each
  function and see the concept it's demonstrating.
