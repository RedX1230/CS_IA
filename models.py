from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Subject:
    name: str
    difficulty: int
    days_until_exam: int
    estimated_hours: float = 0.0

    @property
    def clean_name(self) -> str:
        return self.name.strip()

    def validate(self, position: int) -> list[str]:
        errors: list[str] = []
        label = self.clean_name or f"subject {position}"

        if not self.clean_name:
            errors.append(f"Subject {position} must have a name.")
        if self.difficulty < 1 or self.difficulty > 5:
            errors.append(f"{label}: difficulty must be between 1 and 5.")
        if self.days_until_exam <= 0:
            errors.append(f"{label}: days until exam must be greater than zero.")
        if self.estimated_hours < 0:
            errors.append(f"{label}: estimated hours cannot be negative.")

        return errors


@dataclass(frozen=True)
class ScoredSubject:
    subject: Subject
    priority_score: float

    def to_row(self) -> dict:
        return {
            "name": self.subject.clean_name,
            "difficulty": self.subject.difficulty,
            "days_until_exam": self.subject.days_until_exam,
            "estimated_hours": round(self.subject.estimated_hours, 2),
            "priority_score": round(self.priority_score, 4),
        }


@dataclass(frozen=True)
class Allocation:
    subject: Subject
    priority_score: float
    equal_hours: float
    weighted_hours: float

    @property
    def difference_hours(self) -> float:
        return round(self.weighted_hours - self.equal_hours, 2)

    def to_row(self) -> dict:
        return {
            "name": self.subject.clean_name,
            "difficulty": self.subject.difficulty,
            "days_until_exam": self.subject.days_until_exam,
            "estimated_hours": round(self.subject.estimated_hours, 2),
            "priority_score": round(self.priority_score, 4),
            "equal_allocation_hours": round(self.equal_hours, 2),
            "weighted_allocation_hours": round(self.weighted_hours, 2),
            "difference_hours": self.difference_hours,
        }


@dataclass(frozen=True)
class TimetableBlock:
    weekday: str
    block_number: int
    subject_name: str
    duration_hours: float

    def to_row(self) -> dict:
        return {
            "weekday": self.weekday,
            "block_number": self.block_number,
            "subject_name": self.subject_name,
            "duration_hours": round(self.duration_hours, 2),
        }
