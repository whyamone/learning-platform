"""Тесты алгоритма SM-2. Это чистые расчёты — база данных здесь не нужна."""

import pytest

from app.services.sm2 import DEFAULT_EASE_FACTOR, MIN_EASE_FACTOR, Grade, Schedule, next_schedule


def test_first_success_comes_back_tomorrow():
    schedule = next_schedule(Schedule(), quality=4)

    assert schedule.repetitions == 1
    assert schedule.interval_days == 1


def test_second_success_comes_back_in_six_days():
    schedule = next_schedule(Schedule(repetitions=1, interval_days=1), quality=4)

    assert schedule.repetitions == 2
    assert schedule.interval_days == 6


def test_later_intervals_are_multiplied_by_ease_factor():
    schedule = next_schedule(Schedule(repetitions=2, interval_days=6, ease_factor=2.5), quality=4)

    assert schedule.interval_days == 15  # 6 × 2,5
    assert schedule.repetitions == 3


def test_intervals_grow_with_every_success():
    schedule = Schedule()
    intervals = []
    for _ in range(5):
        schedule = next_schedule(schedule, quality=4)
        intervals.append(schedule.interval_days)

    assert intervals == [1, 6, 15, 38, 95]


def test_failure_resets_progress():
    learned = Schedule(repetitions=5, interval_days=95, ease_factor=2.5)

    schedule = next_schedule(learned, quality=1)

    assert schedule.repetitions == 0
    assert schedule.interval_days == 1
    assert schedule.ease_factor < learned.ease_factor  # карточка стала «труднее»


@pytest.mark.parametrize(
    ("quality", "expected_ease"),
    [(5, 2.6), (4, 2.5), (3, 2.36), (1, 1.96)],
)
def test_ease_factor_changes_with_quality(quality, expected_ease):
    schedule = next_schedule(Schedule(ease_factor=DEFAULT_EASE_FACTOR), quality)

    # approx — сравнение дробных чисел с допуском (вспомни 0.1 + 0.2).
    assert schedule.ease_factor == pytest.approx(expected_ease)


def test_ease_factor_never_drops_below_minimum():
    schedule = Schedule()
    for _ in range(20):
        schedule = next_schedule(schedule, quality=0)

    assert schedule.ease_factor == MIN_EASE_FACTOR


@pytest.mark.parametrize("quality", [-1, 6])
def test_quality_out_of_range_is_rejected(quality):
    with pytest.raises(ValueError):
        next_schedule(Schedule(), quality)


def test_buttons_map_to_sm2_qualities():
    assert [grade.quality for grade in Grade] == [1, 3, 4, 5]
    # «С трудом» — всё ещё успех: серия не обнуляется.
    assert (
        next_schedule(Schedule(repetitions=1, interval_days=1), Grade.HARD.quality).repetitions == 2
    )
    assert (
        next_schedule(Schedule(repetitions=1, interval_days=1), Grade.AGAIN.quality).repetitions
        == 0
    )
