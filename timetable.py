from __future__ import annotations

from collections import defaultdict
from math import floor

from models import TimetableBlock


class WeeklyTimetable:
    WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def __init__(self, allocation_rows: list[dict], block_length_hours: float = 1.0):
        self.allocation_rows = allocation_rows
        self.block_length_hours = block_length_hours

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.block_length_hours <= 0:
            errors.append("Block length must be greater than zero.")
        if not self.allocation_rows:
            errors.append("Generate a study plan before creating a timetable.")
        return errors

    def subject_block_counts(self) -> list[dict]:
        total_weighted_hours = sum(float(row["weighted_allocation_hours"]) for row in self.allocation_rows)
        positive_subjects = sum(
            1 for row in self.allocation_rows if float(row["weighted_allocation_hours"]) > 0
        )
        total_blocks = max(positive_subjects, round(total_weighted_hours / self.block_length_hours))
        raw_counts = [
            {
                "subject_name": row["name"],
                "priority_score": row["priority_score"],
                "weighted_hours": float(row["weighted_allocation_hours"]),
                "raw_blocks": float(row["weighted_allocation_hours"]) / self.block_length_hours,
            }
            for row in self.allocation_rows
        ]

        base_counts = [floor(item["raw_blocks"]) for item in raw_counts]
        for index, item in enumerate(raw_counts):
            if item["weighted_hours"] > 0 and base_counts[index] == 0:
                base_counts[index] = 1

        difference = total_blocks - sum(base_counts)
        fractional_order = sorted(
            range(len(raw_counts)),
            key=lambda index: (
                raw_counts[index]["raw_blocks"] - floor(raw_counts[index]["raw_blocks"]),
                raw_counts[index]["priority_score"],
            ),
            reverse=True,
        )

        if difference > 0:
            for index in fractional_order[:difference]:
                base_counts[index] += 1
        elif difference < 0:
            removable_order = sorted(
                range(len(raw_counts)),
                key=lambda index: (
                    raw_counts[index]["raw_blocks"] - floor(raw_counts[index]["raw_blocks"]),
                    raw_counts[index]["priority_score"],
                ),
            )
            for index in removable_order:
                if difference == 0:
                    break
                if base_counts[index] > 1:
                    base_counts[index] -= 1
                    difference += 1

        block_counts = []
        for row, blocks in zip(raw_counts, base_counts):
            weighted_hours = row["weighted_hours"]
            scheduled_hours = round(blocks * self.block_length_hours, 2)
            block_counts.append(
                {
                    "subject_name": row["subject_name"],
                    "priority_score": row["priority_score"],
                    "weighted_hours": weighted_hours,
                    "blocks": blocks,
                    "scheduled_hours": scheduled_hours,
                    "rounding_difference": round(scheduled_hours - weighted_hours, 2),
                }
            )
        return sorted(block_counts, key=lambda item: item["priority_score"], reverse=True)

    def generate_blocks(self) -> list[TimetableBlock]:
        errors = self.validate()
        if errors:
            raise ValueError("; ".join(errors))

        remaining = self.subject_block_counts()
        blocks_by_day: dict[str, list[TimetableBlock]] = defaultdict(list)
        day_loads = {weekday: 0.0 for weekday in self.WEEKDAYS}

        while any(item["blocks"] > 0 for item in remaining):
            for subject in remaining:
                if subject["blocks"] <= 0:
                    continue

                weekday = self._best_weekday(subject["subject_name"], blocks_by_day, day_loads)
                block = TimetableBlock(
                    weekday=weekday,
                    block_number=len(blocks_by_day[weekday]) + 1,
                    subject_name=subject["subject_name"],
                    duration_hours=self.block_length_hours,
                )
                blocks_by_day[weekday].append(block)
                day_loads[weekday] = round(day_loads[weekday] + self.block_length_hours, 2)
                subject["blocks"] -= 1

        return [
            block
            for weekday in self.WEEKDAYS
            for block in blocks_by_day[weekday]
        ]

    def _best_weekday(
        self,
        subject_name: str,
        blocks_by_day: dict[str, list[TimetableBlock]],
        day_loads: dict[str, float],
    ) -> str:
        def score_day(weekday: str) -> tuple[float, int, int]:
            subject_already_on_day = any(
                block.subject_name == subject_name for block in blocks_by_day[weekday]
            )
            repeated_previous_block = (
                bool(blocks_by_day[weekday])
                and blocks_by_day[weekday][-1].subject_name == subject_name
            )
            return (
                day_loads[weekday],
                1 if subject_already_on_day else 0,
                1 if repeated_previous_block else 0,
            )

        return min(self.WEEKDAYS, key=lambda day: (*score_day(day), self.WEEKDAYS.index(day)))

    def grouped_blocks(self) -> dict[str, list[TimetableBlock]]:
        grouped = {weekday: [] for weekday in self.WEEKDAYS}
        for block in self.generate_blocks():
            grouped[block.weekday].append(block)
        return grouped

    def summary_rows(self) -> list[dict]:
        return self.subject_block_counts()
