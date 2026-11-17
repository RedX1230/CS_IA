from pathlib import Path

from database import DatabaseManager, FeedbackModel
from models import TimetableBlock


def test_plan_feedback_and_timetable_are_persisted(tmp_path: Path):
    db_path = tmp_path / "test.db"
    database = DatabaseManager(db_path)
    database.init_database()

    allocation_rows = [
        {
            "name": "Math",
            "difficulty": 5,
            "days_until_exam": 7,
            "estimated_hours": 8,
            "priority_score": 6.5,
            "equal_allocation_hours": 5,
            "weighted_allocation_hours": 7,
            "difference_hours": 2,
        }
    ]
    timetable_blocks = [
        TimetableBlock("Monday", 1, "Math", 1),
        TimetableBlock("Tuesday", 1, "Math", 1),
    ]

    plan_id = database.save_plan(
        allocation_rows,
        total_available_hours=10,
        difficulty_weight=1,
        urgency_weight=10,
        estimate_weight=0.15,
        timetable_blocks=timetable_blocks,
    )
    allocations = database.fetch_allocations_for_plan(plan_id)
    saved_blocks = database.fetch_timetable_blocks_for_plan(plan_id)

    assert len(allocations) == 1
    assert allocations[0]["subject_name"] == "Math"
    assert len(saved_blocks) == 2
    assert saved_blocks[0]["weekday"] == "Monday"

    database.save_feedback(
        allocation_id=allocations[0]["id"],
        subject_name="Math",
        planned_hours=7,
        actual_hours=8.4,
        rating=4,
        notes="Needed more practice",
    )

    adjusted = FeedbackModel(database).adjusted_estimate("Math", 10)
    summary = database.fetch_feedback_summary()

    assert adjusted == 12
    assert summary[0]["feedback_count"] == 1
