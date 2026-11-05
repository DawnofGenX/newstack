import pytest

from {{ package_name }} import model as subject


def test_a_star_field_covers_the_whole_range():
    field = subject.parse_field("minute", "*", 0, 59)
    assert field.star is True
    assert len(field.values) == 60
    assert field.accepts(0) and field.accepts(59)


def test_a_step_divides_the_range():
    field = subject.parse_field("minute", "*/15", 0, 59)
    assert sorted(field.values) == [0, 15, 30, 45]
    assert field.star is False


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("1-5", [1, 2, 3, 4, 5]),
        ("10-20/5", [10, 15, 20]),
        ("1,15,30", [1, 15, 30]),
        ("59", [59]),
        ("0-59", list(range(60))),
    ],
)
def test_forms_a_minute_field_can_take(text, want):
    assert sorted(subject.parse_field("minute", text, 0, 59).values) == want


def test_names_are_numbers_in_disguise():
    assert sorted(subject.parse_field("month", "jan,dec", 1, 12, subject.MONTH_NAMES).values) == [
        1,
        12,
    ]
    assert sorted(subject.parse_field("weekday", "mon-fri", 0, 7, subject.DAY_NAMES).values) == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_sunday_is_both_zero_and_seven():
    assert subject.parse_field("weekday", "7", 0, 7, subject.DAY_NAMES).values == {0}
    assert subject.parse_field("weekday", "0", 0, 7, subject.DAY_NAMES).values == {0}
    assert subject.parse_field("weekday", "6,7", 0, 7, subject.DAY_NAMES).values == {0, 6}


@pytest.mark.parametrize(
    ("name", "text", "low", "high", "fragment"),
    [
        ("minute", "60", 0, 59, "outside 0-59"),
        ("minute", "-1", 0, 59, "not a number"),
        ("minute", "", 0, 59, "the field is empty"),
        ("minute", "*/0", 0, 59, "step must be at least 1"),
        ("minute", "5-1", 0, 59, "runs backwards"),
        ("minute", "abc", 0, 59, "not a number"),
        ("hour", "1.5", 0, 23, "not a number"),
        ("month", "smarch", 1, 12, "not a number"),
    ],
)
def test_a_field_that_cannot_mean_anything(name, text, low, high, fragment):
    with pytest.raises(subject.CronError, match=fragment):
        subject.parse_field(name, text, low, high)


def test_a_field_of_zero_alone_is_still_valid():
    assert subject.parse_field("hour", "0", 0, 23).values == {0}
