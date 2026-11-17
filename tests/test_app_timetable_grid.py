from app import build_timetable_grid
from models import TimetableBlock


def test_timetable_grid_uses_weekdays_as_columns():
    blocks = [
        TimetableBlock("Monday", 1, "Math", 1),
        TimetableBlock("Wednesday", 1, "Biology", 1),
        TimetableBlock("Monday", 2, "English", 1),
    ]

    grid = build_timetable_grid(blocks)

    assert grid[0]["Block"] == 1
    assert grid[0]["Monday"] == "Math (1 h)"
    assert grid[0]["Tuesday"] == ""
    assert grid[0]["Wednesday"] == "Biology (1 h)"
    assert grid[1]["Block"] == 2
    assert grid[1]["Monday"] == "English (1 h)"
