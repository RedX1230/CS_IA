from __future__ import annotations

import sqlite3
from pathlib import Path

from models import TimetableBlock

DB_PATH = Path("study_allocator.db")


class DatabaseManager:
    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_database(self) -> None:
        with self.get_connection() as connection:
            connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total_available_hours REAL NOT NULL,
                difficulty_weight REAL NOT NULL,
                urgency_weight REAL NOT NULL,
                estimate_weight REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                days_until_exam INTEGER NOT NULL,
                estimated_hours REAL NOT NULL,
                priority_score REAL NOT NULL,
                equal_allocation_hours REAL NOT NULL,
                weighted_allocation_hours REAL NOT NULL,
                difference_hours REAL NOT NULL,
                FOREIGN KEY (plan_id) REFERENCES plans(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                allocation_id INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                planned_hours REAL NOT NULL,
                actual_hours REAL NOT NULL,
                rating INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (allocation_id) REFERENCES allocations(id)
            );

            CREATE TABLE IF NOT EXISTS timetable_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                weekday TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                duration_hours REAL NOT NULL,
                FOREIGN KEY (plan_id) REFERENCES plans(id)
            );
            """
            )

    def save_plan(
        self,
        allocation_rows: list[dict],
        total_available_hours: float,
        difficulty_weight: float,
        urgency_weight: float,
        estimate_weight: float,
        timetable_blocks: list[TimetableBlock] | None = None,
    ) -> int:
        with self.get_connection() as connection:
            cursor = connection.execute(
            """
            INSERT INTO plans (
                total_available_hours,
                difficulty_weight,
                urgency_weight,
                estimate_weight
            )
            VALUES (?, ?, ?, ?)
            """,
                (total_available_hours, difficulty_weight, urgency_weight, estimate_weight),
            )
            plan_id = int(cursor.lastrowid)

            connection.executemany(
            """
            INSERT INTO allocations (
                plan_id,
                subject_name,
                difficulty,
                days_until_exam,
                estimated_hours,
                priority_score,
                equal_allocation_hours,
                weighted_allocation_hours,
                difference_hours
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    (
                        plan_id,
                        row["name"],
                        row["difficulty"],
                        row["days_until_exam"],
                        row["estimated_hours"],
                        row["priority_score"],
                        row["equal_allocation_hours"],
                        row["weighted_allocation_hours"],
                        row["difference_hours"],
                    )
                    for row in allocation_rows
                ],
            )

            if timetable_blocks:
                self._save_timetable_blocks(connection, plan_id, timetable_blocks)

            return plan_id

    def _save_timetable_blocks(
        self,
        connection: sqlite3.Connection,
        plan_id: int,
        timetable_blocks: list[TimetableBlock],
    ) -> None:
        connection.executemany(
            """
            INSERT INTO timetable_blocks (
                plan_id,
                weekday,
                block_number,
                subject_name,
                duration_hours
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    plan_id,
                    block.weekday,
                    block.block_number,
                    block.subject_name,
                    block.duration_hours,
                )
                for block in timetable_blocks
            ],
        )

    def fetch_recent_plans(self, limit: int = 10) -> list[sqlite3.Row]:
        with self.get_connection() as connection:
            return connection.execute(
            """
            SELECT
                plans.id,
                plans.created_at,
                plans.total_available_hours,
                COUNT(allocations.id) AS subject_count
            FROM plans
            LEFT JOIN allocations ON allocations.plan_id = plans.id
            GROUP BY plans.id
            ORDER BY plans.created_at DESC, plans.id DESC
            LIMIT ?
            """,
                (limit,),
            ).fetchall()

    def fetch_allocations_for_plan(self, plan_id: int) -> list[sqlite3.Row]:
        with self.get_connection() as connection:
            return connection.execute(
            """
            SELECT *
            FROM allocations
            WHERE plan_id = ?
            ORDER BY priority_score DESC
            """,
                (plan_id,),
            ).fetchall()

    def fetch_timetable_blocks_for_plan(self, plan_id: int) -> list[sqlite3.Row]:
        with self.get_connection() as connection:
            return connection.execute(
                """
                SELECT *
                FROM timetable_blocks
                WHERE plan_id = ?
                ORDER BY
                    CASE weekday
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END,
                    block_number
                """,
                (plan_id,),
            ).fetchall()

    def save_feedback(
        self,
        allocation_id: int,
        subject_name: str,
        planned_hours: float,
        actual_hours: float,
        rating: int,
        notes: str = "",
    ) -> None:
        with self.get_connection() as connection:
            connection.execute(
            """
            INSERT INTO feedback (
                allocation_id,
                subject_name,
                planned_hours,
                actual_hours,
                rating,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
                (allocation_id, subject_name, planned_hours, actual_hours, rating, notes),
            )

    def fetch_feedback_for_subject(self, subject_name: str, limit: int = 5) -> list[sqlite3.Row]:
        with self.get_connection() as connection:
            return connection.execute(
            """
            SELECT planned_hours, actual_hours
            FROM feedback
            WHERE LOWER(subject_name) = LOWER(?)
                AND planned_hours > 0
                AND actual_hours >= 0
            ORDER BY created_at DESC, id DESC
            LIMIT 5
            """,
                (subject_name,),
            ).fetchall()

    def fetch_feedback_summary(self) -> list[sqlite3.Row]:
        with self.get_connection() as connection:
            return connection.execute(
            """
            SELECT
                subject_name,
                COUNT(*) AS feedback_count,
                ROUND(AVG(planned_hours), 2) AS average_planned_hours,
                ROUND(AVG(actual_hours), 2) AS average_actual_hours,
                ROUND(AVG(actual_hours - planned_hours), 2) AS average_difference,
                ROUND(AVG(rating), 2) AS average_rating
            FROM feedback
            GROUP BY LOWER(subject_name)
            ORDER BY feedback_count DESC, subject_name
            """
            ).fetchall()


class FeedbackModel:
    def __init__(self, database: DatabaseManager):
        self.database = database

    def adjusted_estimate(self, subject_name: str, current_estimate: float) -> float:
        rows = self.database.fetch_feedback_for_subject(subject_name)

        if not rows:
            return current_estimate

        ratios = [row["actual_hours"] / row["planned_hours"] for row in rows]
        average_ratio = sum(ratios) / len(ratios)
        adjusted = current_estimate * average_ratio
        return round(max(adjusted, 0), 2)


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    return DatabaseManager(db_path).get_connection()


def init_database(db_path: Path | str = DB_PATH) -> None:
    DatabaseManager(db_path).init_database()


def save_plan_to_database(
    allocation_rows: list[dict],
    total_available_hours: float,
    difficulty_weight: float,
    urgency_weight: float,
    estimate_weight: float,
    db_path: Path | str = DB_PATH,
) -> int:
    return DatabaseManager(db_path).save_plan(
        allocation_rows,
        total_available_hours,
        difficulty_weight,
        urgency_weight,
        estimate_weight,
    )


def fetch_recent_plans(limit: int = 10, db_path: Path | str = DB_PATH) -> list[sqlite3.Row]:
    return DatabaseManager(db_path).fetch_recent_plans(limit)


def fetch_allocations_for_plan(plan_id: int, db_path: Path | str = DB_PATH) -> list[sqlite3.Row]:
    return DatabaseManager(db_path).fetch_allocations_for_plan(plan_id)


def save_feedback(
    allocation_id: int,
    subject_name: str,
    planned_hours: float,
    actual_hours: float,
    rating: int,
    notes: str = "",
    db_path: Path | str = DB_PATH,
) -> None:
    DatabaseManager(db_path).save_feedback(
        allocation_id,
        subject_name,
        planned_hours,
        actual_hours,
        rating,
        notes,
    )


def update_estimated_time_from_feedback(
    subject_name: str,
    current_estimate: float,
    db_path: Path | str = DB_PATH,
) -> float:
    return FeedbackModel(DatabaseManager(db_path)).adjusted_estimate(subject_name, current_estimate)


def fetch_feedback_summary(db_path: Path | str = DB_PATH) -> list[sqlite3.Row]:
    return DatabaseManager(db_path).fetch_feedback_summary()
