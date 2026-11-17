# Smart Study Time Allocator

A Python + Streamlit application for an IB Computer Science IA. The app helps students divide available study time between subjects using an explainable priority algorithm, then improves future estimated time using feedback history stored in SQLite.

Full documentation is available in [documentation.md](./documentation.md).

## Features

- Input subjects, difficulty, days until exam, and estimated time needed.
- Calculate priority scores from difficulty and urgency.
- Compare equal allocation with weighted algorithm allocation.
- Correct rounding so allocated time exactly matches the available time.
- Generate a Monday-Sunday weekly timetable from weighted allocations.
- Split study into adjustable fixed-length blocks.
- Save plans, subjects, allocations, and feedback in SQLite.
- Save timetable blocks with each plan.
- Use feedback from planned vs actual study time to adjust later estimates.
- Run repeated scenarios for sensitivity analysis.

## Run The App

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Run Tests

```powershell
pytest
```

## Algorithm Summary

Priority is calculated with:

```text
priority = (difficulty_weight * difficulty) + (urgency_weight * (1 / days_until_exam))
```

Weighted time is then allocated proportionally:

```text
allocated_time = total_available_time * subject_priority / total_priority
```

After rounding, the app corrects the largest rounding differences so the final total exactly equals the user's available study time.

## OOP Structure

- `models.py`: `Subject`, `ScoredSubject`, `Allocation`, and `TimetableBlock` data classes.
- `planner.py`: `SubjectValidator`, `PriorityScorer`, and `StudyPlan`.
- `timetable.py`: `WeeklyTimetable` for Monday-Sunday block generation.
- `database.py`: `DatabaseManager` and `FeedbackModel`.
- `app.py`: Streamlit user interface.
