from __future__ import annotations

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text: str, bold: bool = False) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(9.5)


def style_document(doc: Document) -> None:
    sec = doc.sections[0]
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11)
    sec.top_margin = Inches(1)
    sec.bottom_margin = Inches(1)
    sec.left_margin = Inches(1)
    sec.right_margin = Inches(1)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10.5)

    for name, size in [("Title", 18), ("Heading 1", 14), ("Heading 2", 12)]:
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)


def add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(text)
    run.font.size = Pt(10.5)


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    p = doc.add_paragraph()
    if level == 1:
        p.style = doc.styles["Heading 1"]
    else:
        p.style = doc.styles["Heading 2"]
    p.add_run(text)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    for i, width in enumerate(widths):
        for cell in table.columns[i].cells:
            cell.width = Inches(width)
    hdr = table.rows[0].cells
    for idx, header in enumerate(headers):
        set_cell_text(hdr[idx], header, bold=True)
        set_cell_shading(hdr[idx], "D9EAF7")
    for row in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            set_cell_text(cells[idx], value)


doc = Document()
style_document(doc)

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("Smart Study Time Allocator")
run.bold = True
run.font.name = "Arial"
run.font.size = Pt(18)

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run("IB Computer Science IA Documentation")
run.italic = True
run.font.name = "Arial"
run.font.size = Pt(11)

doc.add_paragraph("")

add_heading(doc, "1. Project Overview", 1)
doc.add_paragraph(
    "Smart Study Time Allocator is a Python and Streamlit application designed to help IB students divide available study time across subjects. "
    "The application accepts subject information, calculates a weighted priority score, allocates study time proportionally, and generates a weekly timetable. "
    "SQLite is used to store plans and feedback so the system can improve later estimates using previous study data."
)

add_heading(doc, "2. System Architecture", 1)
for text in [
    "`models.py` contains the main data classes used across the project.",
    "`planner.py` contains validation, scoring, and allocation logic.",
    "`timetable.py` contains the weekly timetable generator.",
    "`database.py` contains SQLite access and feedback adjustment logic.",
    "`app.py` contains the Streamlit interface.",
]:
    add_bullet(doc, text)

add_heading(doc, "3. Object-Oriented Design", 1)
doc.add_paragraph(
    "The project uses object-oriented programming to represent the problem domain clearly. "
    "Each class has one main responsibility, which makes the logic easier to explain, test, and maintain."
)

add_heading(doc, "Core Classes", 2)
core_rows = [
    ["Subject", "Stores subject name, difficulty, days until exam, and estimated hours; validates subject-level input."],
    ["ScoredSubject", "Combines a Subject with its calculated priority score."],
    ["Allocation", "Stores equal and weighted allocations for one subject and calculates the difference."],
    ["TimetableBlock", "Represents one scheduled block in the weekly timetable."],
    ["SubjectValidator", "Checks the full subject list and total study time before allocation."],
    ["PriorityScorer", "Calculates the weighted priority score using difficulty, urgency, and estimated effort."],
    ["StudyPlan", "Manages scoring, sorting, allocation, rounding correction, and row generation."],
    ["WeeklyTimetable", "Turns weighted allocations into Monday-Sunday study blocks."],
    ["DatabaseManager", "Creates tables and handles saving and fetching plans, allocations, timetable blocks, and feedback."],
    ["FeedbackModel", "Adjusts future estimated hours using planned-versus-actual feedback history."],
]
add_table(doc, ["Class", "Role"], core_rows, [1.5, 5.8])

add_heading(doc, "4. Allocation Algorithm", 1)
doc.add_paragraph(
    "The priority score is calculated with an explainable rule-based formula:"
)
doc.add_paragraph(
    "priority = (difficulty_weight * difficulty) + (urgency_weight * (1 / days_until_exam)) + (estimate_weight * estimated_pressure)"
)
for text in [
    "Subjects are sorted by priority score from highest to lowest.",
    "Weighted study time is allocated proportionally to the priority score.",
    "Equal allocation is also calculated so the user can compare the algorithm against a simple baseline.",
    "Rounding is corrected so the final total exactly matches the available study time.",
]:
    add_bullet(doc, text)

add_heading(doc, "5. Weekly Timetable Logic", 1)
for text in [
    "The user chooses a fixed block length, such as 1 hour.",
    "Weighted hours are converted into a number of study blocks.",
    "Blocks are distributed across Monday to Sunday.",
    "The next block is placed into the weekday with the lightest load so the timetable stays balanced.",
    "The timetable is shown as a grid with blocks as rows and weekdays as columns.",
]:
    add_bullet(doc, text)

add_heading(doc, "6. Database Design", 1)
doc.add_paragraph(
    "SQLite is used because the application is a small local system and does not need a separate database server. "
    "The database stores each plan, the detailed allocations produced by the algorithm, timetable blocks, and user feedback. "
    "This allows the application to reuse previous results and adapt future study estimates from historical behaviour."
)

add_heading(doc, "6.1 Why a Database Is Needed", 2)
for text in [
    "To keep generated study plans available after the session ends.",
    "To store timetable blocks so a saved plan can be reviewed later.",
    "To record feedback and compare planned hours against actual study time.",
    "To support the feedback-based estimate update used in later plans.",
]:
    add_bullet(doc, text)

add_heading(doc, "6.2 Database Structure", 2)
doc.add_paragraph(
    "The schema is normalized so each table stores one type of information. A plan can have many allocations, many timetable blocks, and many feedback records."
)

schema_tables = [
    (
        "plans",
        "Stores one record per generated study plan.",
        [
            ["id", "INTEGER PK", "Unique plan identifier"],
            ["created_at", "TEXT", "Timestamp when the plan was saved"],
            ["total_available_hours", "REAL", "Total study time entered by the user"],
            ["difficulty_weight", "REAL", "Difficulty weight used in scoring"],
            ["urgency_weight", "REAL", "Urgency weight used in scoring"],
            ["estimate_weight", "REAL", "Estimated effort weight used in scoring"],
        ],
    ),
    (
        "allocations",
        "Stores the calculated allocation for each subject in a plan.",
        [
            ["id", "INTEGER PK", "Unique allocation identifier"],
            ["plan_id", "INTEGER FK", "Links to plans.id"],
            ["subject_name", "TEXT", "Subject name"],
            ["difficulty", "INTEGER", "Difficulty level"],
            ["days_until_exam", "INTEGER", "Days until exam"],
            ["estimated_hours", "REAL", "Estimated hours"],
            ["priority_score", "REAL", "Calculated priority score"],
            ["equal_allocation_hours", "REAL", "Equal share of time"],
            ["weighted_allocation_hours", "REAL", "Weighted share of time"],
            ["difference_hours", "REAL", "Difference between equal and weighted allocation"],
        ],
    ),
    (
        "feedback",
        "Stores post-study feedback so the system can adjust later estimates.",
        [
            ["id", "INTEGER PK", "Unique feedback identifier"],
            ["allocation_id", "INTEGER FK", "Links to allocations.id"],
            ["subject_name", "TEXT", "Subject name"],
            ["planned_hours", "REAL", "Hours originally allocated"],
            ["actual_hours", "REAL", "Hours actually spent"],
            ["rating", "INTEGER", "User rating from 1 to 5"],
            ["notes", "TEXT", "Optional comment"],
            ["created_at", "TEXT", "Timestamp when feedback was saved"],
        ],
    ),
    (
        "timetable_blocks",
        "Stores the weekly timetable generated from the weighted plan.",
        [
            ["id", "INTEGER PK", "Unique timetable block identifier"],
            ["plan_id", "INTEGER FK", "Links to plans.id"],
            ["weekday", "TEXT", "Day of the week"],
            ["block_number", "INTEGER", "Block position in the day grid"],
            ["subject_name", "TEXT", "Subject assigned to the block"],
            ["duration_hours", "REAL", "Duration of the block"],
        ],
    ),
]

for table_name, purpose, rows in schema_tables:
    add_heading(doc, table_name, 3)
    doc.add_paragraph(purpose)
    add_table(doc, ["Field", "Type", "Description"], rows, [1.6, 1.2, 4.5])

add_heading(doc, "6.3 Relationships Between Tables", 2)
for text in [
    "`plans.id` is the parent key for both `allocations.plan_id` and `timetable_blocks.plan_id`.",
    "`allocations.id` is the parent key for `feedback.allocation_id`.",
    "This structure lets one saved plan link to all of its subject allocations, timetable blocks, and feedback records.",
]:
    add_bullet(doc, text)

add_heading(doc, "6.4 Example Use of the Database", 2)
doc.add_paragraph(
    "When the student generates a plan, the application saves the plan settings in `plans`, one row per subject in `allocations`, and any timetable blocks in `timetable_blocks`. "
    "After studying, the student can record actual study time in `feedback`. The `FeedbackModel` then uses these records to adjust future estimates for the same subject."
)

add_heading(doc, "7. User Interface", 1)
for text in [
    "Plan tab: enter subjects, weights, and available study hours, then generate a weighted plan.",
    "Timetable tab: generate a weekly timetable and view it as a table.",
    "Feedback tab: save actual study time and notes for a subject allocation.",
    "History tab: review previous plans, feedback summaries, and saved timetable blocks.",
]:
    add_bullet(doc, text)

add_heading(doc, "8. Testing", 1)
for text in [
    "Input validation",
    "Priority scoring",
    "Equal and weighted allocation",
    "Rounding correction",
    "Timetable generation",
    "Database persistence",
    "Feedback-based estimate adjustment",
]:
    add_bullet(doc, text)

add_heading(doc, "9. IA Evaluation Points", 1)
for text in [
    "The project solves a realistic student time-management problem.",
    "The design uses OOP to model real-world entities clearly.",
    "The scoring algorithm is explainable and easy to justify.",
    "SQLite adds persistence and supports adaptive behaviour.",
    "The timetable feature turns abstract time allocations into a practical weekly plan.",
]:
    add_bullet(doc, text)

doc.save("C:/Users/saad2/OneDrive/Documents/CS IA/Smart_Study_Time_Allocator_Documentation.docx")
