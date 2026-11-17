from models import Subject
from code.planner import PriorityScorer, StudyPlan


def test_valid_inputs_generate_no_errors():
    plan = StudyPlan(
        [
            Subject("Math", 5, 7, 8),
            Subject("English", 2, 20, 3),
        ],
        10,
    )

    assert plan.validate() == []


def test_invalid_inputs_are_reported():
    plan = StudyPlan(
        [
            Subject("", 0, 0, -1),
            Subject("Math", 3, 10, 2),
            Subject("math", 4, 12, 2),
        ],
        0,
    )

    errors = plan.validate()

    assert "Total available study time must be greater than zero." in errors
    assert any("must have a name" in error for error in errors)
    assert any("difficulty must be between 1 and 5" in error for error in errors)
    assert any("days until exam must be greater than zero" in error for error in errors)
    assert any("estimated hours cannot be negative" in error for error in errors)
    assert any("duplicated" in error for error in errors)


def test_priority_increases_with_difficulty_and_urgency():
    scorer = PriorityScorer()
    low_priority = Subject("Easy Later", 1, 30, 1)
    urgent_hard = Subject("Hard Soon", 5, 3, 1)

    assert scorer.score(urgent_hard) > scorer.score(low_priority)


def test_weighted_allocation_total_matches_available_time():
    plan = StudyPlan(
        [
            Subject("Math", 5, 7, 8),
            Subject("Biology", 4, 14, 5),
            Subject("History", 2, 30, 3),
        ],
        17.35,
    )
    rows = plan.allocation_rows()

    assert round(sum(row["weighted_allocation_hours"] for row in rows), 2) == 17.35


def test_equal_allocation_total_matches_available_time():
    plan = StudyPlan(
        [
            Subject("Math", 5, 7, 8),
            Subject("Biology", 4, 14, 5),
            Subject("History", 2, 30, 3),
        ],
        10,
    )

    assert sum(plan.equal_allocations().values()) == 10


def test_higher_priority_subject_receives_more_weighted_time():
    plan = StudyPlan(
        [
            Subject("Math", 5, 3, 8),
            Subject("English", 1, 60, 2),
        ],
        10,
    )
    rows = plan.allocation_rows()

    math = next(row for row in rows if row["name"] == "Math")
    english = next(row for row in rows if row["name"] == "English")

    assert math["priority_score"] > english["priority_score"]
    assert math["weighted_allocation_hours"] > english["weighted_allocation_hours"]


def test_zero_total_priority_falls_back_to_equal_allocation():
    plan = StudyPlan(
        [
            Subject("A", 1, 10, 0),
            Subject("B", 1, 10, 0),
        ],
        5,
        PriorityScorer(difficulty_weight=0, urgency_weight=0, estimate_weight=0),
    )

    assert [row["weighted_allocation_hours"] for row in plan.allocation_rows()] == [2.5, 2.5]
