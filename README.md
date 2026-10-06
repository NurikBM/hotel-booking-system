# Hotel & Room Booking System (Pure Functional Python)

Курсовой проект по дисциплине «Функциональное программирование».  
Предметная область: **Система бронирования отелей и номеров (фильтры, цены, доступность, мемоизация)**.  
Реализованы: **Лабораторная работа 1**, **Лабораторная работа 2** и **Лабораторная работа 3**.

---

## Архитектура проекта

```
app/main.py          # Веб-интерфейс на Streamlit (8 вкладок по ТЗ)
core/domain.py       # Доменные неизменяемые сущности (Hotel, RoomType, RatePlan, Price, Availability, Guest, CartItem, Booking, Payment, Event, Rule)
core/transforms.py   # Lab 1 & 2: загрузка seed.json, корзина, nightly_sum (reduce), замыкания by_city, by_capacity, by_features, lambdas
core/recursion.py    # Lab 2: рекурсивный поиск предложений (Hotels -> Rooms -> Rates), рекурсивные скидки и поиск минимума
core/memo.py         # Lab 3: чистый мемоизатор @memoize (LRU, stats, clear), memoized_nightly_sum, бенчмарк ускорения
core/ftypes.py       # Lab 4 (заглушка)
core/compose.py      # Lab 5 (заглушка)
core/lazy.py         # Lab 6 (заглушка)
core/service.py      # Lab 7 (заглушка)
core/frp.py          # Lab 8 (заглушка)
core/report.py       # Lab 8 (заглушка)
data/seed.json       # Реалистичный датасет: 6 отелей, 24 типа номеров, 48 тарифов, 2880 цен (60 дней), 50 гостей
cli.py               # Консольное интерактивное меню
streamlit_app.py     # Точка входа для запуска Streamlit (проксирует в app.main)
tests/test_lab1.py   # 7 тестов Lab 1 (модели, seed, hold/remove, nightly_sum)
tests/test_lab2.py   # 7 тестов Lab 2 (замыкания, лямбды, 2 рекурсивных алгоритма)
tests/test_lab3.py   # 6 тестов Lab 3 (мемоизация, LRU-вытеснение, бенчмарк 250+ итераций)
```

---

## Реализованные лабораторные работы

### Лабораторная работа 1: Доменная модель, неизменяемость, трансформации
- **Неизменяемые сущности (`core/domain.py`):** `@dataclass(frozen=True)` для `Hotel`, `RoomType`, `RatePlan`, `Price`, `Availability`, `Guest`, `CartItem`, `Booking`, `Payment`, `Event`, `Rule`.
- **Все суммы в целых числах (`int`):** Цены хранятся в тиынах/копейках/центах без `float` для предотвращения ошибок округления.
- **Даты в стандарте ISO-8601:** Строки `"YYYY-MM-DD"`.
- **Чистые функции трансформации (`core/transforms.py`):**
  - `load_seed(path)`: чистая загрузка `data/seed.json` в кортежи доменных объектов.
  - `calculate_nights(checkin, checkout)` и `generate_date_range(checkin, checkout)`.
  - `nightly_sum(prices, checkin, checkout, rate_id) -> int`: расчёт суммы за период через `functools.reduce` по датам.
  - `hold_item(cart, item)` и `remove_hold(cart, item_id)`: чистые операции над корзиной без мутаций.
  - `apply_discount(amount, discount_percent)`: чистый целочисленный расчёт скидок.

### Лабораторная работа 2: Замыкания, лямбды и чистая рекурсия
- **Фабрики замыканий-предикатов (`core/transforms.py`):**
  - `by_city(city)`: предикат для отеля с регистронезависимым сравнением.
  - `by_capacity(guests)`: предикат для типов номеров (`capacity >= guests`).
  - `by_features(required)`: предикат проверки наличия набора удобств.
- **Лямбда-комбинаторы:** `sort_hotels_by_stars`, `sort_rooms_by_capacity`, `sort_prices_by_amount`.
- **Рекурсивные алгоритмы (`core/recursion.py`):**
  - `recursive_search_available_quotes`: рекурсивный обход дерева Отели → Типы номеров → Тарифы → Доступность без циклов `for` / `while`.
  - `recursive_apply_rules`: рекурсивный движок применения цепочки бизнес-правил и скидок.
  - `recursive_find_cheapest_quote`: хвостовая рекурсия для поиска лучшей цены без `min()`.

### Лабораторная работа 3: Чистая мемоизация и оптимизация производительности
- **Функциональный декоратор мемоизации (`core/memo.py`):**
  - `@memoize(maxsize=1024)`: чистый кэш с LRU-вытеснением при превышении лимита.
  - Нормализация составных аргументов (кортежи, словари, frozen-dataclasses) в детерминированные ключи.
  - Метрики кэша `cache_info()`: количество попаданий (`hits`), промахов (`misses`), текущий размер (`currsize`), процент попаданий (`hit_ratio`).
  - Чистый сброс кэша: `cache_clear()`.
- **Специализированные функции:** `memoized_nightly_sum`, `memoized_calculate_quote_with_loyalty`.
- **Бенчмарк ускорения (`benchmark_speedup`):**
  - Замер времени выполнения 200–500 запросов из `seed.json` без мемоизации и с мемоизацией.
  - Вычисление коэффициента ускорения (Speedup Factor: 10x–50x) и hit ratio (>95%).

---

## Инструкции по запуску

### 1. Запуск консольного приложения (CLI)
```bash
python3 cli.py
```
Интерактивное консольное меню предоставляет:
1. Статистику по загруженному `data/seed.json`.
2. Демонстрацию замыканий и лямбд (Lab 2).
3. Рекурсивный поиск предложений (Lab 2).
4. Рекурсивный движок правил (Lab 2).
5. Мемоизацию и 300-итерационный бенчмарк ускорения (Lab 3).
6. Запуск тестов `pytest`.
0. Выход.

### 2. Запуск веб-интерфейса Streamlit (8 вкладок)
```bash
streamlit run streamlit_app.py --server.port 3000
```
Или через npm:
```bash
npm run dev
```
Интерфейс содержит ровно 8 вкладок по ТЗ:
- **Overview:** архитектура, инварианты, ключевые метрики.
- **Data:** просмотр сущностей `data/seed.json`.
- **Functional Core:** замыкания, рекурсивный поиск и правила (Lab 2).
- **Pipelines:** корзина (Lab 1), мемоизация и бенчмарк 250+ итераций (Lab 3).
- **Async/FRP:** заглушка и обзор архитектуры для Lab 6 и Lab 8.
- **Reports:** статистические сводки и агрегации.
- **Tests:** запуск pytest прямо из браузера в один клик.
- **About:** академическое описание и инварианты курса.

### 3. Запуск автоматических тестов
Все 20 тестов (Lab 1 + Lab 2 + Lab 3):
```bash
pytest -v tests/
```
Или:
```bash
npm test
```

Запуск тестов по отдельным лабораторным:
```bash
pytest -v tests/test_lab1.py
pytest -v tests/test_lab2.py
pytest -v tests/test_lab3.py
```

### 4. Проверка стиля кода
```bash
black --check .
ruff check .
```
Кодовая база полностью соответствует стандартам Black и Ruff (0 ошибок и предупреждений).
