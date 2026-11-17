# Smart Study Time Allocator Documentation

## 1. Project Overview

Smart Study Time Allocator is a Python and Streamlit application designed for IB students who need help distributing study time across multiple subjects. The application accepts subject data, calculates a weighted priority score for each subject, allocates study time proportionally, and generates a weekly timetable.

The project also stores plans and feedback in SQLite so that later study plans can be adjusted using previous user feedback. This makes the system suitable for demonstrating both rule-based processing and basic adaptive behaviour in an IB Computer Science IA.

## 2. System Architecture

The codebase is sectionalized into separate modules so each part of the system has a clear responsibility.

- `models.py` contains the data classes used throughout the project.
- `planner.py` contains validation, priority scoring, and study allocation logic.
- `timetable.py` contains weekly timetable generation logic.
- `database.py` contains database access and feedback adjustment logic.
- `app.py` contains the Streamlit user interface.

This separation improves readability, testing, and maintainability. It also makes the project easier to explain in the IA because each module performs one main task.

## 3. Object-Oriented Design

The application uses OOP to represent the main concepts in the problem domain.

### Subject

`Subject` stores the subject name, difficulty, days until exam, and estimated study hours.

Key behaviour:

- `clean_name`: returns the trimmed subject name.
- `validate(position)`: checks for missing names, invalid difficulty, invalid days until exam, and negative estimated hours.

### ScoredSubject

`ScoredSubject` combines a `Subject` with its calculated priority score.

This class is used after scoring so the plan can keep the original subject data together with the computed score.

### Allocation

`Allocation` represents the final result for one subject after the study time has been distributed.

It stores:

- the original subject
- the priority score
- the equal allocation
- the weighted allocation

It also calculates the difference between equal and weighted allocation.

### TimetableBlock

`TimetableBlock` represents one scheduled block in the timetable.

It stores:

- weekday
- block number
- subject name
- duration in hours

This class is used by the timetable generator and database save logic.

### SubjectValidator

`SubjectValidator` checks that the full set of subjects and total study time are valid before allocation begins.

### PriorityScorer

`PriorityScorer` calculates a subject priority score using three factors:

- difficulty
- urgency, based on `1 / days_until_exam`
- estimated effort pressure

The scoring formula is intentionally transparent so it can be justified in the IA.

### StudyPlan

`StudyPlan` manages the entire scheduling process.

Responsibilities:

- validate all input data
- score all subjects
- calculate equal allocation
- calculate weighted allocation
- correct rounding so the total exactly matches the available study time
- produce allocation rows for display and storage

### WeeklyTimetable

`WeeklyTimetable` converts weighted study allocations into a Monday-to-Sunday block schedule.

Responsibilities:

- validate timetable inputs
- convert hours into fixed-length study blocks
- distribute blocks across the week
- balance blocks across days instead of placing them all together
- return timetable blocks and summary rows

### DatabaseManager

`DatabaseManager` handles all database operations.

Responsibilities:

- create the tables if they do not exist
- save plans
- save allocations
- save timetable blocks
- save feedback
- fetch saved plans, allocations, timetable blocks, and feedback summaries

### FeedbackModel

`FeedbackModel` uses previous planned-vs-actual study data to adjust future estimated hours.

This gives the project a lightweight adaptive feature without turning it into a full machine learning system.

## 4. Priority and Allocation Logic

The priority score is calculated as:

```text
priority = (difficulty_weight * difficulty) + (urgency_weight * (1 / days_until_exam)) + (estimate_weight * estimated_pressure)
```

After subjects are scored, the system:

1. sorts the subjects by priority score
2. calculates the weighted share of the total study time
3. rounds values to two decimal places
4. corrects rounding differences so the total matches the available time exactly

The application also calculates equal allocation so the user can compare the algorithmic result against a simple baseline.

## 5. Timetable Logic

The timetable generator works with fixed block sizes, such as 1 hour.

Process:

1. Convert each subject's weighted allocation into a number of timetable blocks.
2. Sort the subjects by priority.
3. Place each next block into the weekday with the lightest current load.
4. Repeat until all blocks are placed.

This creates a weekly timetable that is balanced across days while still respecting priority.

## 6. Database Schema

The project uses SQLite with four tables.

### plans

Stores one record for each generated study plan.

| Field | Type | Description |
| --- | --- | --- |
| `id` | INTEGER PK | Unique plan identifier |
| `created_at` | TEXT | Timestamp when the plan was saved |
| `total_available_hours` | REAL | Total study time entered by the user |
| `difficulty_weight` | REAL | Weight used for the difficulty part of the score |
| `urgency_weight` | REAL | Weight used for the urgency part of the score |
| `estimate_weight` | REAL | Weight used for estimated effort pressure |

### allocations

Stores the subject-level allocation results for each plan.

| Field | Type | Description |
| --- | --- | --- |
| `id` | INTEGER PK | Unique allocation identifier |
| `plan_id` | INTEGER FK | Links to `plans.id` |
| `subject_name` | TEXT | Subject name |
| `difficulty` | INTEGER | Subject difficulty score |
| `days_until_exam` | INTEGER | Days until exam |
| `estimated_hours` | REAL | Estimated hours for the subject |
| `priority_score` | REAL | Calculated priority score |
| `equal_allocation_hours` | REAL | Equal share of time |
| `weighted_allocation_hours` | REAL | Weighted share of time |
| `difference_hours` | REAL | Difference between equal and weighted allocation |

### feedback

Stores user feedback after studying.

| Field | Type | Description |
| --- | --- | --- |
| `id` | INTEGER PK | Unique feedback identifier |
| `allocation_id` | INTEGER FK | Links to `allocations.id` |
| `subject_name` | TEXT | Subject name |
| `planned_hours` | REAL | Hours originally allocated |
| `actual_hours` | REAL | Hours actually spent |
| `rating` | INTEGER | User rating from 1 to 5 |
| `notes` | TEXT | Optional comment |
| `created_at` | TEXT | Timestamp when feedback was saved |

### timetable_blocks

Stores timetable blocks for each saved plan.

| Field | Type | Description |
| --- | --- | --- |
| `id` | INTEGER PK | Unique timetable block identifier |
| `plan_id` | INTEGER FK | Links to `plans.id` |
| `weekday` | TEXT | Day of the week |
| `block_number` | INTEGER | Position of the block within the day grid |
| `subject_name` | TEXT | Subject assigned to the block |
| `duration_hours` | REAL | Duration of the block |

## 7. User Interface

The Streamlit app is divided into four tabs:

- `Plan`: enter subjects, weights, and available study time, then generate and save a plan
- `Timetable`: generate and view a weekly timetable as a table
- `Feedback`: save actual study hours and notes
- `History`: review previously saved plans, feedback, and timetable blocks

This layout keeps the interface simple and makes the application easier to demonstrate during the IA presentation.

## 8. Testing

The project includes automated tests for:

- input validation
- priority scoring
- equal and weighted allocation
- rounding correction
- timetable grid generation
- timetable block distribution
- database save and fetch behaviour
- feedback-based estimate adjustment

These tests support the reliability of the implementation and provide evidence for the IA development process.

## 9. Suggested IA Write-Up Points

- The project solves a real student problem: time management and study prioritization.
- The design uses OOP to model real-world entities.
- The algorithm is explainable, which is important for the IA.
- SQLite provides persistence so the app can use historical feedback.
- The timetable feature turns abstract allocations into something a student can actually follow.
