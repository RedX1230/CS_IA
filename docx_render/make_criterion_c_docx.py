from __future__ import annotations

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = "C:/Users/saad2/OneDrive/Documents/CS IA/Criterion_C_System_Overview_Smart_Study_Time_Allocator.docx"
ASSETS = "C:/Users/saad2/OneDrive/Documents/CS IA/docx_render"
BLUE = "2E74B5"


def shade(cell, fill: str) -> None:
    props = cell._tc.get_or_add_tcPr()
    node = OxmlElement("w:shd")
    node.set(qn("w:fill"), fill)
    props.append(node)


def cell(cell, text: str, bold: bool = False, white: bool = False) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Calibri"
    r.font.size = Pt(9)
    if white:
        r.font.color.rgb = RGBColor(255, 255, 255)


def table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False
    for i, head in enumerate(headers):
        cell(t.rows[0].cells[i], head, True, True)
        shade(t.rows[0].cells[i], BLUE)
    for n, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cell(cells[i], value)
            if n % 2:
                shade(cells[i], "F2F4F7")
    for row in t.rows:
        for i, width in enumerate(widths):
            row.cells[i].width = Inches(width)
    doc.add_paragraph()


def heading(doc: Document, text: str, level: int = 1) -> None:
    doc.add_paragraph(text, style=f"Heading {level}")


def body(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.1


def code(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    r.font.name = "Consolas"
    r.font.size = Pt(8.5)


doc = Document()
section = doc.sections[0]
for side in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
    setattr(section, side, Inches(1))
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
for level, size in [(1, 16), (2, 13), (3, 12)]:
    style = doc.styles[f"Heading {level}"]
    style.font.name = "Calibri"
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor.from_string(BLUE)

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run("Criterion C: System Overview")
r.bold = True
r.font.size = Pt(22)
r.font.color.rgb = RGBColor.from_string(BLUE)
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle.add_run("Smart Study Time Allocator").italic = True

heading(doc, "1. System model")
body(doc, "The system is a local Python application. A student enters study requirements in the Streamlit interface. The application validates the data, applies the priority and allocation algorithms, creates a weekly timetable, and can save the result to SQLite. Feedback from a completed plan can adjust a future time estimate for the same subject.")
table(doc, ["External actor / component", "Input or responsibility", "Output / connection"], [
    ["Student", "Enters subject name, difficulty, days until exam, estimated hours, total available hours and optional feedback.", "Receives an allocation table, weekly timetable, history and validation messages."],
    ["Streamlit interface (app.py)", "Collects inputs in Plan, Timetable, Feedback and History tabs; displays results.", "Creates Subject objects; calls StudyPlan, WeeklyTimetable, DatabaseManager and FeedbackModel."],
    ["Planning module (planner.py)", "Validates subjects, calculates scores and divides available time.", "Returns allocation rows sorted by priority."],
    ["Timetable module (timetable.py)", "Converts weighted hours to fixed blocks and balances blocks across Monday-Sunday.", "Returns TimetableBlock objects and a rounding summary."],
    ["SQLite database (database.py)", "Stores plans, allocations, timetable blocks and feedback.", "Returns saved plans and feedback history to the interface."],
], [1.75, 2.85, 1.9])

heading(doc, "2. Component interaction")
code(doc, "Student → Streamlit UI → Subject / StudyPlan → PriorityScorer → Allocation rows\n"
          "                                   ↓                         ↓\n"
          "                           SubjectValidator          WeeklyTimetable → TimetableBlock\n"
          "                                   ↓                         ↓\n"
          "                           Error messages          DatabaseManager → SQLite\n"
          "                                                              ↓\n"
          "                                              FeedbackModel → adjusted future estimate")
body(doc, "This model relates directly to the decomposition in Criterion B. Each module has one main responsibility, and the interface only coordinates objects instead of containing the scoring or database algorithms itself.")

heading(doc, "3. UML use-case diagram")
body(doc, "The Student is the only external actor. The arrows show the features the student can perform; the connecting labels indicate where one feature produces data needed by the next feature.")
doc.add_picture(f"{ASSETS}/uml_use_case_diagram.png", width=Inches(6.5))

heading(doc, "4. UML class diagram")
body(doc, "The diagram shows the key classes used by the solution. StudyPlan is the main coordinator: it uses Subject and PriorityScorer to create Allocation results, which WeeklyTimetable converts into scheduled blocks. DatabaseManager persists the result and FeedbackModel uses stored feedback to adjust later estimates.")
doc.add_picture(f"{ASSETS}/uml_class_diagram.png", width=Inches(6.5))

heading(doc, "5. Object-oriented design")
table(doc, ["Class", "Key fields", "Key methods / purpose"], [
    ["Subject", "name, difficulty, days_until_exam, estimated_hours", "clean_name; validate(position). Represents one item entered by the student."],
    ["ScoredSubject", "subject, priority_score", "to_row(). Keeps an original Subject together with its computed score."],
    ["Allocation", "subject, priority_score, equal_hours, weighted_hours", "difference_hours; to_row(). Represents the final allocation for one subject."],
    ["TimetableBlock", "weekday, block_number, subject_name, duration_hours", "to_row(). Represents one displayed/saved study block."],
    ["SubjectValidator", "subjects, total_available_hours", "validate(). Checks whole-plan and subject-level input constraints."],
    ["PriorityScorer", "difficulty_weight, urgency_weight, estimate_weight", "score(subject) and component methods. Calculates explainable priority."],
    ["StudyPlan", "subjects, total_available_hours, scorer", "scored_subjects; allocations; correct_rounding_difference. Coordinates planning."],
    ["WeeklyTimetable", "allocation_rows, block_length_hours", "subject_block_counts; generate_blocks; grouped_blocks. Balances weekly schedule."],
    ["DatabaseManager / FeedbackModel", "db_path / database", "Save and retrieve SQLite records; calculate feedback-adjusted estimates."],
], [1.45, 2.3, 2.75])

heading(doc, "6. Data design")
body(doc, "SQLite is suitable because the planner is a small, local application that needs persistent history but does not require a network server. The design avoids repeating plan-level information in every allocation record.")
table(doc, ["Table", "Primary / foreign keys", "Purpose"], [
    ["plans", "PK: id", "One record per saved plan, including total available hours and scoring weights."],
    ["allocations", "PK: id; FK: plan_id → plans.id", "One calculated result per subject in a saved plan."],
    ["timetable_blocks", "PK: id; FK: plan_id → plans.id", "One record per scheduled block, including weekday and duration."],
    ["feedback", "PK: id; FK: allocation_id → allocations.id", "Actual hours, rating and notes after a student follows a plan."],
], [1.45, 2.4, 2.65])
table(doc, ["Important field", "Type", "Validation / meaning"], [
    ["difficulty", "INTEGER", "Must be 1 to 5; represents perceived difficulty."],
    ["days_until_exam", "INTEGER", "Must be greater than 0; used to calculate urgency."],
    ["estimated_hours", "REAL", "Must not be negative; represents the student's expected effort."],
    ["priority_score", "REAL", "Calculated value; higher values receive more weighted time."],
    ["weighted_allocation_hours", "REAL", "Calculated and corrected to two decimal places."],
    ["duration_hours", "REAL", "Selected timetable block length, from 0.25 to 4 hours in the interface."],
], [2.25, 1.1, 3.15])

heading(doc, "7. Annotated interface design")
body(doc, "The interface uses four tabs to keep the workflow in the same order that a student uses the solution. The sketches below identify the important controls and outputs; the final interface uses Streamlit widgets with the same labels.")
heading(doc, "Plan tab", 2)
code(doc, "[Settings]                         [Subjects]\n"
          "Total available hours  [20.0]     Name | Difficulty | Days until exam | Estimated hours\n"
          "Number of subjects     [4]        Mathematics | 5 | 7 | 8.0\n"
          "Difficulty weight      [1.0]      Biology     | 4 | 14 | 5.0\n"
          "Urgency weight        [10.0]     ...\n"
          "[Generate study plan]             → allocation table + weighted total")
body(doc, "The left settings area controls the scoring calculation. The right subject grid makes the input requirements visible side-by-side. Generate study plan validates before displaying results, preventing invalid values from entering the algorithm.")
heading(doc, "Timetable, Feedback and History tabs", 2)
code(doc, "Timetable: [Block length] [Generate weekly timetable] → Monday–Sunday grid\n"
          "Feedback:  [Saved plan] [Subject allocation] [Actual hours] [Rating] [Save feedback]\n"
          "History:   Recent plans table | Feedback summary | Selected saved timetable")
body(doc, "Timetable is separated from the planning input because it depends on a valid generated allocation. Feedback chooses an existing allocation so that planned hours are not typed again. History retrieves stored records to demonstrate persistence.")

heading(doc, "8. Algorithms")
heading(doc, "8.1 Priority score and weighted allocation", 2)
body(doc, "The score deliberately combines three transparent factors. A subject becomes more important when it is difficult, its exam is sooner, or its estimated work is high relative to the time remaining.")
code(doc, "FOR each subject\n"
          "    urgency ← urgency_weight × (1 / days_until_exam)\n"
          "    estimate_pressure ← estimated_hours / max(days_until_exam, 1)\n"
          "    score ← (difficulty_weight × difficulty) + urgency + (estimate_weight × estimate_pressure)\n"
          "SORT subjects by score descending\n"
          "FOR each scored subject\n"
          "    raw_hours ← total_available_hours × score / total_score\n"
          "ROUND values down to cents; give remaining cents to the largest fractional values")
body(doc, "The last step prevents a common allocation fault: independently rounded values may no longer add to the entered total. If total_score is zero because all user weights are zero, the algorithm uses equal allocation instead.")
heading(doc, "8.2 Balanced timetable generation", 2)
code(doc, "CREATE day_loads for Monday to Sunday, initially 0\n"
          "CONVERT each weighted allocation to max(1, round(weighted_hours / block_length)) blocks\n"
          "SORT subjects by priority score descending\n"
          "WHILE a subject still has blocks remaining\n"
          "    FOR each subject with blocks remaining\n"
          "        weekday ← day with the lowest load (earliest weekday breaks ties)\n"
          "        add a TimetableBlock to weekday\n"
          "        increase weekday load and decrease subject blocks")
body(doc, "By repeatedly selecting the least-loaded day, the algorithm spreads higher-priority subjects across the week instead of placing all their blocks on the same day.")
heading(doc, "8.3 Feedback adjustment", 2)
code(doc, "GET up to five recent feedback rows for the selected subject\n"
          "IF no rows exist, RETURN current_estimate\n"
          "ratio_list ← actual_hours / planned_hours for each valid row\n"
          "RETURN max(current_estimate × average(ratio_list), 0), rounded to 2 decimals")

heading(doc, "9. Testing strategy")
table(doc, ["Success criterion", "Functional test", "Expected result"], [
    ["Inputs are valid and understandable", "Enter blank and duplicate names; difficulty 0, 1, 5 and 6; deadline 0; negative hours.", "Errors identify invalid values; valid boundary values are accepted."],
    ["Time is allocated accurately", "Use three subjects and 17.35 hours; compare priorities and sum output.", "Higher-priority subject gets more time; total weighted hours equals exactly 17.35."],
    ["Weekly timetable is balanced", "Generate blocks with 1-hour and 0.5-hour lengths, including more than seven blocks.", "Blocks have requested duration and are spread across weekdays."],
    ["Plan data persists", "Save a plan with timetable, reopen/retrieve it, then inspect allocations and blocks.", "Correct plan, allocations and timetable records are returned."],
    ["Feedback improves later estimate", "Save feedback where actual hours differ from planned hours, then request adjustment.", "New estimate follows the average actual/planned ratio; no feedback leaves estimate unchanged."],
], [1.7, 2.8, 2.0])
body(doc, "Structural tests also cover the empty-subject list, a zero total score, values that need rounding correction, a timetable without generated allocations, and feedback with no stored history. These cases correspond to the automated pytest tests in the project.")

doc.save(OUT)
print(OUT)
