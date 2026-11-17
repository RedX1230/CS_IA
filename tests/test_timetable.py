from timetable import WeeklyTimetable


def allocation_rows():
    return [
        {
            "name": "Math",
            "priority_score": 10,
            "weighted_allocation_hours": 4,
        },
        {
            "name": "Biology",
            "priority_score": 6,
            "weighted_allocation_hours": 2,
        },
        {
            "name": "English",
            "priority_score": 3,
            "weighted_allocation_hours": 1,
        },
    ]


def test_weekly_timetable_creates_monday_to_sunday_output():
    timetable = WeeklyTimetable(allocation_rows(), block_length_hours=1)

    grouped = timetable.grouped_blocks()

    assert list(grouped.keys()) == WeeklyTimetable.WEEKDAYS


def test_timetable_uses_selected_block_length():
    timetable = WeeklyTimetable(allocation_rows(), block_length_hours=0.5)

    blocks = timetable.generate_blocks()

    assert all(block.duration_hours == 0.5 for block in blocks)


def test_high_priority_subject_is_rotated_across_days():
    timetable = WeeklyTimetable(allocation_rows(), block_length_hours=1)

    blocks = timetable.generate_blocks()
    math_days = {block.weekday for block in blocks if block.subject_name == "Math"}

    assert len(math_days) > 1


def test_timetable_reports_rounding_difference_from_block_size():
    timetable = WeeklyTimetable(
        [
            {
                "name": "Math",
                "priority_score": 10,
                "weighted_allocation_hours": 1.3,
            }
        ],
        block_length_hours=1,
    )

    summary = timetable.summary_rows()

    assert summary[0]["blocks"] == 1
    assert summary[0]["scheduled_hours"] == 1
    assert summary[0]["rounding_difference"] == -0.3


def test_block_counts_preserve_overall_rounded_study_load():
    timetable = WeeklyTimetable(
        [
            {
                "name": "Math",
                "priority_score": 10,
                "weighted_allocation_hours": 3.75,
            },
            {
                "name": "Biology",
                "priority_score": 7,
                "weighted_allocation_hours": 2.25,
            },
            {
                "name": "English",
                "priority_score": 4,
                "weighted_allocation_hours": 1.5,
            },
        ],
        block_length_hours=0.5,
    )

    summary = timetable.summary_rows()

    assert sum(row["blocks"] for row in summary) == 15
    assert sum(row["scheduled_hours"] for row in summary) == 7.5
