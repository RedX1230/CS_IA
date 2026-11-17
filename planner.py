from __future__ import annotations

from math import floor

from models import Allocation, ScoredSubject, Subject


class SubjectValidator:
    def __init__(self, subjects: list[Subject], total_available_hours: float):
        self.subjects = subjects
        self.total_available_hours = total_available_hours

    def validate(self) -> list[str]:
        errors: list[str] = []

        if self.total_available_hours <= 0:
            errors.append("Total available study time must be greater than zero.")
        if not self.subjects:
            errors.append("At least one subject is required.")

        seen_names: set[str] = set()
        for index, subject in enumerate(self.subjects, start=1):
            errors.extend(subject.validate(index))
            if subject.clean_name:
                lowered = subject.clean_name.lower()
                if lowered in seen_names:
                    errors.append(f"Subject name '{subject.name}' is duplicated.")
                seen_names.add(lowered)

        return errors


class PriorityScorer:
    def __init__(
        self,
        difficulty_weight: float = 1.0,
        urgency_weight: float = 10.0,
        estimate_weight: float = 0.15,
    ):
        self.difficulty_weight = difficulty_weight
        self.urgency_weight = urgency_weight
        self.estimate_weight = estimate_weight

    def difficulty_component(self, subject: Subject) -> float:
        return self.difficulty_weight * subject.difficulty

    def urgency_component(self, subject: Subject) -> float:
        return self.urgency_weight * (1 / subject.days_until_exam)

    def estimate_component(self, subject: Subject) -> float:
        estimate_pressure = subject.estimated_hours / max(subject.days_until_exam, 1)
        return self.estimate_weight * estimate_pressure

    def score(self, subject: Subject) -> float:
        return (
            self.difficulty_component(subject)
            + self.urgency_component(subject)
            + self.estimate_component(subject)
        )


class StudyPlan:
    def __init__(
        self,
        subjects: list[Subject],
        total_available_hours: float,
        scorer: PriorityScorer | None = None,
    ):
        self.subjects = subjects
        self.total_available_hours = total_available_hours
        self.scorer = scorer or PriorityScorer()

    def validate(self) -> list[str]:
        return SubjectValidator(self.subjects, self.total_available_hours).validate()

    def scored_subjects(self) -> list[ScoredSubject]:
        scored = [
            ScoredSubject(subject=subject, priority_score=self.scorer.score(subject))
            for subject in self.subjects
        ]
        return sorted(scored, key=lambda item: item.priority_score, reverse=True)

    def equal_allocations(self) -> dict[str, float]:
        if not self.subjects:
            return {}

        raw_values = [self.total_available_hours / len(self.subjects)] * len(self.subjects)
        corrected = self.correct_rounding_difference(raw_values, self.total_available_hours)
        return {
            subject.clean_name: hours
            for subject, hours in zip(self.subjects, corrected)
        }

    def weighted_allocations(self, scored_subjects: list[ScoredSubject]) -> list[float]:
        if not scored_subjects:
            return []

        total_priority = sum(item.priority_score for item in scored_subjects)
        if total_priority <= 0:
            raw_values = [self.total_available_hours / len(scored_subjects)] * len(scored_subjects)
        else:
            raw_values = [
                self.total_available_hours * item.priority_score / total_priority
                for item in scored_subjects
            ]

        return self.correct_rounding_difference(raw_values, self.total_available_hours)

    def allocations(self) -> list[Allocation]:
        scored = self.scored_subjects()
        weighted_hours = self.weighted_allocations(scored)
        equal_by_name = self.equal_allocations()

        return [
            Allocation(
                subject=item.subject,
                priority_score=item.priority_score,
                equal_hours=equal_by_name[item.subject.clean_name],
                weighted_hours=weighted,
            )
            for item, weighted in zip(scored, weighted_hours)
        ]

    def allocation_rows(self) -> list[dict]:
        return [allocation.to_row() for allocation in self.allocations()]

    @staticmethod
    def correct_rounding_difference(raw_values: list[float], target_total: float) -> list[float]:
        if not raw_values:
            return []

        target_cents = int(round(target_total * 100))
        floored_cents = [floor(value * 100) for value in raw_values]
        remainder = target_cents - sum(floored_cents)
        fractional_order = sorted(
            range(len(raw_values)),
            key=lambda index: (raw_values[index] * 100) - floored_cents[index],
            reverse=True,
        )

        corrected = floored_cents[:]
        for index in fractional_order[:remainder]:
            corrected[index] += 1

        return [value / 100 for value in corrected]
