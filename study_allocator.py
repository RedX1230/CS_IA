from __future__ import annotations

from models import Subject
from code.planner import PriorityScorer, StudyPlan


def validate_inputs(subjects: list[Subject], total_available_hours: float) -> list[str]:
    return StudyPlan(subjects, total_available_hours).validate()


def calculate_priority_score(
    subject: Subject,
    difficulty_weight: float = 1.0,
    urgency_weight: float = 10.0,
    estimate_weight: float = 0.15,
) -> float:
    return PriorityScorer(
        difficulty_weight=difficulty_weight,
        urgency_weight=urgency_weight,
        estimate_weight=estimate_weight,
    ).score(subject)


def build_scored_subjects(
    subjects: list[Subject],
    difficulty_weight: float = 1.0,
    urgency_weight: float = 10.0,
    estimate_weight: float = 0.15,
) -> list[dict]:
    plan = StudyPlan(
        subjects,
        1,
        PriorityScorer(
            difficulty_weight=difficulty_weight,
            urgency_weight=urgency_weight,
            estimate_weight=estimate_weight,
        ),
    )
    return [item.to_row() for item in plan.scored_subjects()]


def sort_subjects_by_priority(scored_subjects: list[dict]) -> list[dict]:
    return sorted(scored_subjects, key=lambda item: item["priority_score"], reverse=True)


def calculate_equal_allocation(subjects: list[Subject], total_available_hours: float) -> list[float]:
    return list(StudyPlan(subjects, total_available_hours).equal_allocations().values())


def allocate_weighted_time(scored_subjects: list[dict], total_available_hours: float) -> list[float]:
    if not scored_subjects:
        return []

    total_priority = sum(item["priority_score"] for item in scored_subjects)
    if total_priority <= 0:
        raw_values = [total_available_hours / len(scored_subjects)] * len(scored_subjects)
    else:
        raw_values = [
            total_available_hours * item["priority_score"] / total_priority
            for item in scored_subjects
        ]
    return StudyPlan.correct_rounding_difference(raw_values, total_available_hours)


def correct_rounding_difference(raw_values: list[float], target_total: float) -> list[float]:
    return StudyPlan.correct_rounding_difference(raw_values, target_total)


def create_allocation_table(
    subjects: list[Subject],
    total_available_hours: float,
    difficulty_weight: float = 1.0,
    urgency_weight: float = 10.0,
    estimate_weight: float = 0.15,
) -> list[dict]:
    return StudyPlan(
        subjects,
        total_available_hours,
        PriorityScorer(
            difficulty_weight=difficulty_weight,
            urgency_weight=urgency_weight,
            estimate_weight=estimate_weight,
        ),
    ).allocation_rows()
