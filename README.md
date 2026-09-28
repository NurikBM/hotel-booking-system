# Hotel & Room Booking System (Pure Functional Python)

Курсовой проект по дисциплине «Функциональное программирование».
Предметная область: **Система бронирования отелей и номеров (фильтры, цены, доступность)**.
Реализованы **Лабораторная работа 1** и **Лабораторная работа 2**.

---

## Архитектура проекта

```
domain/models.py     # Lab 1: неизменяемые сущности (Hotel, Room, Booking, Review, City, HotelNode, DiscountNode)
core/pricing.py      # Lab 1: чистый расчёт цен, ночей, скидок и map/reduce-пайплайны
core/filters.py      # Lab 1: чистые предикаты и функции фильтрации
core/fp_tools.py     # Lab 2: фабрики замыканий (make_price_filter, make_amenity_filter), лямбды, 2 рекурсивных алгоритма
data/mock_db.py      # Неизменяемые тестовые данные (+ иерархия Город -> Отели -> Номера для рекурсии)
cli.py               # Консольное интерактивное меню
streamlit_app.py     # Веб-интерфейс на Streamlit (только Lab 1 и Lab 2)
tests/test_lab1.py   # Набор тестов для Lab 1 (7 тестов)
tests/test_lab2.py   # Набор тестов для Lab 2 (7 тестов)
```

---

## Реализованные лабораторные работы

### Лабораторная работа 1: Чистые функции, неизменяемость, функции высшего порядка
- **Неизменяемые сущности:** `@dataclass(frozen=True)` для `Hotel`, `Room`, `Booking`, `Review` с коллекциями `tuple[str, ...]`. Попытка мутации вызывает `FrozenInstanceError`.
- **Чистые функции трансформации:**
  - `calculate_nights(check_in, check_out) -> int` — расчёт длительности проживания без отрицательных значений.
  - `calculate_total_price(base_price, nights, seasonal_multiplier) -> float` — детерминированный расчёт стоимости.
  - `apply_discount(total_price, discount_percent) -> float` — расчёт скидки.
  - `calculate_stay_quote(room, check_in, check_out, seasonal_multiplier, discount_percent) -> float` — полный расчёт без скрытых наценок.
- **Предикаты фильтрации (`core/filters.py`):** фильтрация по диапазону цен, вместимости, рейтингу и локации.
- **Пайплайны `map` и `reduce` (`core/pricing.py`):**
  - `extract_hotel_names`: проекция через `map`.
  - `transform_rooms_with_multiplier`: создание новых комнат с изменёнными ценами через `map`.
  - `calculate_total_revenue`: сворачивание подтверждённого дохода через `reduce`.
  - `calculate_average_hotel_rating`: вычисление среднего рейтинга через `reduce`.
  - `find_cheapest_room`: поиск самой дешёвой комнаты через `reduce`.

### Лабораторная работа 2: Замыкания, лямбды и рекурсивные алгоритмы
- **Фабрики замыканий (`core/fp_tools.py`):**
  - `make_price_filter(min_p, max_p)`: возвращает предикат `Callable[[Room], bool]`, захватывая границы цен в лексической области видимости и переиспользуя `is_room_in_price_range` из Lab 1.
  - `make_amenity_filter(required)`: возвращает предикат проверки удобств.
- **Лямбда-функции:**
  - `sort_rooms_by_price`: сортировка с лямбда-ключом `lambda r: r.base_price`.
  - `sort_hotels_by_rating`: сортировка с лямбда-ключом `lambda h: h.rating`.
- **Рекурсивный алгоритм 1 (Агрегация иерархии):**
  - `recursive_count_rooms(node)` и `recursive_sum_capacity(node)` — рекурсивный обход структуры Город → Отели → Номера без циклов (явные базовые случаи и рекурсивные шаги декомпозиции головы и хвоста кортежей).
  - `recursive_aggregate_city` и `recursive_aggregate_cities`.
- **Рекурсивный алгоритм 2 (Рекурсивный поиск и разбор):**
  - `recursive_find_cheapest_room`: рекурсивный поиск самого дешёвого номера в дереве.
  - `recursive_calculate_discount`: рекурсивный разбор и применение вложенного дерева скидок (`DiscountNode`) поверх чистой `apply_discount` из Lab 1.

---

## Инструкции по запуску

### 1. Запуск консольного приложения (CLI)
```bash
python3 cli.py
```
Меню CLI поддерживает:
1. Загрузку и отображение сущностей (Hotels, Rooms).
2. Фильтрацию комнат через замыкания-предикаты.
3. Демонстрацию обоих рекурсивных алгоритмов.
4. Запуск тестов `pytest`.
0. Выход.

### 2. Запуск веб-интерфейса Streamlit
```bash
streamlit run streamlit_app.py --server.port 3000
```
Или:
```bash
npm run dev
```

### 3. Запуск автоматических тестов
Запуск всех тестов:
```bash
pytest -v tests/
```
Или через npm:
```bash
npm test
```
Запуск тестов конкретной лабораторной:
```bash
pytest -v tests/test_lab1.py
pytest -v tests/test_lab2.py
```
