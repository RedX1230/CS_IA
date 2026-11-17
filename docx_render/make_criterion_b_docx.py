from __future__ import annotations

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUT = "C:/Users/saad2/OneDrive/Documents/CS IA/Criterion_B_Planning_Smart_Study_Time_Allocator.docx"
BLUE = "2E74B5"
LIGHT_BLUE = "E8EEF5"
LIGHT_GRAY = "F2F4F7"
WHITE = "FFFFFF"
WIDTH = 9360


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_width(cell, dxa: int) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(dxa))
    tc_w.set(qn("w:type"), "dxa")


def set_table_geometry(table, widths: list[int]) -> None:
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(widths)))
    tbl_w.set(qn("w:type"), "dxa")
    indent = OxmlElement("w:tblInd")
    indent.set(qn("w:w"), "120")
    indent.set(qn("w:type"), "dxa")
    tbl_pr.append(indent)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)
    grid = table._tbl.tblGrid
    for column, width in zip(grid.gridCol_lst, widths):
        column.set(qn("w:w"), str(width))
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            set_cell_width(cell, width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_cell_margins(cell) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for side in ("top", "start", "bottom", "end"):
        node = tc_mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            tc_mar.append(node)
        node.set(qn("w:w"), "80" if side in {"top", "bottom"} else "120")
        node.set(qn("w:type"), "dxa")


def set_cell_text(cell, value: str, bold: bool = False, color: str | None = None, size: float = 9.5) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.1
    run = p.add_run(value)
    run.bold = bold
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    set_cell_margins(cell)


def add_table(doc, headers: list[str], rows: list[list[str]], widths: list[int]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for cell, header in zip(table.rows[0].cells, headers):
        set_cell_text(cell, header, bold=True, color=WHITE)
        set_cell_shading(cell, BLUE)
    for number, row in enumerate(rows):
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            set_cell_text(cell, value)
            if number % 2:
                set_cell_shading(cell, LIGHT_GRAY)
    set_table_geometry(table, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_heading(doc, text: str, level: int = 1) -> None:
    p = doc.add_paragraph(style=f"Heading {level}")
    p.add_run(text)


def add_body(doc, text: str) -> None:
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.1


def style(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.1
    for level, size, before, after, colour in [(1, 16, 16, 8, BLUE), (2, 13, 12, 6, BLUE), (3, 12, 8, 4, "1F4D78")]:
        s = doc.styles[f"Heading {level}"]
        s.font.name = "Calibri"
        s._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        s._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        s.font.size = Pt(size)
        s.font.color.rgb = RGBColor.from_string(colour)
        s.paragraph_format.space_before = Pt(before)
        s.paragraph_format.space_after = Pt(after)
        s.paragraph_format.line_spacing = 1.1


doc = Document()
style(doc)

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_after = Pt(4)
r = title.add_run("Criterion B: Planning")
r.bold = True
r.font.name = "Calibri"
r.font.size = Pt(22)
r.font.color.rgb = RGBColor.from_string(BLUE)
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle.paragraph_format.space_after = Pt(16)
sr = subtitle.add_run("Smart Study Time Allocator")
sr.italic = True
sr.font.size = Pt(12)

add_heading(doc, "1. Proposed solution", 1)
add_body(doc, "The proposed solution is a local Streamlit application for IB students who find it difficult to divide limited revision time fairly across several subjects. The student enters each subject's name, difficulty, exam deadline and estimated revision time. The system validates the data, calculates a transparent priority score, assigns the available study hours proportionally, and turns the result into a balanced Monday-to-Sunday timetable. SQLite stores saved plans and later feedback so future estimated hours can be adjusted from planned-versus-actual study time.")
add_body(doc, "The solution is deliberately rule-based rather than opaque: the user can change the difficulty, urgency and estimated-time weights and compare equal allocation with weighted allocation. This makes the recommendation explainable and gives the student control over the result.")

add_heading(doc, "2. Problem decomposition", 1)
add_body(doc, "The original problem was divided into independent, manageable components. Each component produces an output used by the next component, which reduces development risk and makes individual algorithms testable.")
add_table(doc, ["Component", "Subtasks", "Output / dependency"], [
    ["Input and validation", "Collect total hours and subject fields; reject blank or duplicate names, difficulty outside 1-5, non-positive deadlines and negative estimates.", "Validated Subject objects. Must finish before scoring."],
    ["Priority scoring", "Calculate difficulty, urgency and estimated-effort components; add components; order subjects from highest to lowest score.", "Ordered ScoredSubject records. Depends on valid input."],
    ["Time allocation", "Calculate equal baseline; distribute hours in proportion to score; correct two-decimal rounding difference.", "Allocation records whose weighted hours total exactly the user's available hours."],
    ["Timetable generation", "Convert weighted hours to fixed blocks; select the least-loaded weekday; create Monday-Sunday grid.", "TimetableBlock records. Depends on allocation rows."],
    ["Persistence and feedback", "Create SQLite tables; save plans, allocations and timetable blocks; record actual hours and ratings; calculate adjusted estimates.", "History and feedback-adjusted estimate. Depends on saved allocations."],
    ["User interface and evaluation", "Provide Plan, Timetable, Feedback and History tabs; present clear errors and results; compare behaviour with success criteria.", "Usable application and evaluation evidence. Integrates all other components."],
], [1800, 4500, 3060])

add_heading(doc, "3. Object decomposition and relationships", 1)
add_body(doc, "The application uses object-oriented programming because the key entities in the problem have clear state and behaviour. The model below identifies the objects before development and shows which components are responsible for processing them.")
add_table(doc, ["Object / module", "Responsibility", "Collaborates with"], [
    ["Subject", "Stores one subject's name, difficulty, days until exam and estimated hours; validates field-level data.", "SubjectValidator; PriorityScorer"],
    ["PriorityScorer", "Computes an explainable score from difficulty, urgency and estimate pressure.", "Subject; StudyPlan"],
    ["StudyPlan", "Coordinates validation, sorting, equal allocation, weighted allocation and rounding correction.", "SubjectValidator; PriorityScorer; Allocation"],
    ["WeeklyTimetable", "Turns allocation rows into balanced TimetableBlock objects.", "Allocation; TimetableBlock"],
    ["DatabaseManager", "Creates and queries SQLite tables for plans, allocations, timetable blocks and feedback.", "FeedbackModel; app UI"],
    ["FeedbackModel", "Uses previous planned/actual ratios to adjust an estimate for the same subject.", "DatabaseManager; Subject"],
], [2100, 4650, 2610])

add_heading(doc, "4. Main data flow", 1)
add_body(doc, "The following flow specifies the order of processing. Arrows represent a data dependency, not merely a screen-navigation choice.")
add_table(doc, ["Stage", "Data received", "Processing", "Data produced"], [
    ["1. Plan input", "Subject details, total available hours, user-selected weights", "Validate all values and report errors before calculation.", "Validated subjects and settings"],
    ["2. Calculate plan", "Validated subjects and settings", "Score, sort, allocate proportionally and correct rounding.", "Allocation rows and comparison with equal allocation"],
    ["3. Make timetable", "Allocation rows and block length", "Round hours to blocks and place each next block on the least-loaded weekday.", "Weekly timetable grid and block summary"],
    ["4. Save / retrieve", "Plan, allocations and timetable blocks", "Insert into or query the SQLite database using key relationships.", "Plan history and saved timetable"],
    ["5. Feedback loop", "Selected allocation, actual hours, rating and notes", "Store feedback; average planned-to-actual ratios for future estimates.", "Feedback summary and adjusted estimate"],
], [1350, 2200, 3300, 2510])

add_heading(doc, "5. Research and resources", 1)
add_table(doc, ["Research question", "Planned method / resource", "How it informs the solution"], [
    ["How should limited time be prioritised fairly?", "Compare a weighted priority formula with an equal-allocation baseline; discuss settings with intended student users.", "Defines the scoring factors and makes the result explainable."],
    ["How can a timetable avoid clustering work on one day?", "Prototype fixed-length blocks and evaluate a least-loaded-day placement rule with sample plans.", "Defines the balancing rule for WeeklyTimetable."],
    ["How should data persist locally?", "Review Python sqlite3 documentation and SQLite foreign-key design examples.", "Defines normalized plans, allocations, timetable_blocks and feedback tables."],
    ["How can the interface be kept simple?", "Review Streamlit documentation and collect feedback on a wireframe with four tabs.", "Defines the Plan, Timetable, Feedback and History workflow."],
], [2100, 3500, 3760])

add_heading(doc, "6. Development plan and dependencies", 1)
add_body(doc, "This is a chronological plan prepared before implementation. The testing and evaluation activities are interleaved with development so defects can be corrected early. The exact dates can be replaced with the student's own school-calendar dates before submission.")
add_table(doc, ["Week", "Planned task", "Dependency / evidence"], [
    ["1", "Confirm client requirements and success criteria; research Streamlit, SQLite and weighted allocation; produce paper UI sketches.", "No dependency. Evidence: interview notes, sources, initial sketches."],
    ["2", "Design Subject, Allocation and TimetableBlock data models; write validation and its unit tests.", "Depends on requirements. Evidence: class design and valid/extreme/invalid test cases."],
    ["3", "Implement scoring, equal/weighted allocation and rounding correction; test calculations with hand-worked examples.", "Depends on validated input. Evidence: test results proving total equals available hours."],
    ["4", "Implement timetable block conversion and least-loaded-day placement; test empty, small and high-load schedules.", "Depends on allocation rows. Evidence: generated timetable grids."],
    ["5", "Implement SQLite schema, save/retrieve functions and feedback adjustment; test table relationships.", "Depends on allocation and timetable objects. Evidence: database test results."],
    ["6", "Integrate Streamlit tabs; conduct usability testing with intended users; fix issues and record changes.", "Depends on completed modules. Evidence: screenshots and feedback log."],
    ["7", "Run final functional and structural tests against success criteria; collect client evaluation; write Criterion E.", "Depends on integrated application. Evidence: completed test table and evaluation."],
], [720, 5100, 3540])

add_heading(doc, "7. Testing strategy", 1)
add_body(doc, "Functional testing will check each requirement against the finished interface. Structural testing will check important algorithms with valid, extreme and invalid data. Automated pytest tests will be used for the non-UI modules, while user-interface checks will be recorded manually with screenshots.")
add_table(doc, ["Feature / success criterion", "Test approach", "Expected result"], [
    ["Input validation", "Try blank, duplicate and valid subject names; difficulty 0, 1, 5 and 6; deadline 0 and 1; negative and zero estimates.", "Invalid input produces a specific error; boundary values 1 and 5 for difficulty and 1 day are accepted."],
    ["Weighted allocation", "Use 1 subject, then several subjects with different difficulty/deadline values; compare a hand calculation.", "Higher score receives at least as much time; all allocated hours sum exactly to total available hours."],
    ["Rounding correction", "Use totals that create recurring decimals, for example 10 hours across three equal-priority subjects.", "Each value has two decimals and the final sum remains exactly 10.00 hours."],
    ["Timetable balancing", "Test 1 block, 7 blocks, more than 7 blocks, and a fractional block length.", "Blocks are placed Monday-Sunday in a load-balanced pattern; every block has the selected duration."],
    ["Database and feedback", "Save a plan with allocations and timetable; retrieve it; add feedback with planned and actual hours.", "Foreign-key records are retrievable for the correct plan and later estimate is adjusted only when feedback exists."],
], [2050, 4300, 3010])

add_heading(doc, "8. Limitations and risk control", 1)
add_table(doc, ["Risk / constraint", "Planned response"], [
    ["A student may enter unrealistic estimates or change priorities frequently.", "Keep inputs editable, show the underlying factors and retain equal allocation as a baseline comparison."],
    ["Fixed timetable blocks may slightly differ from exact weighted hours.", "Show a block-rounding summary so the difference is visible instead of hidden."],
    ["Feedback data may be too limited to be reliable at first.", "Use the original estimate when no feedback exists and average only recent valid planned/actual ratios."],
    ["The project must be achievable within the IA timeframe.", "Use Streamlit and SQLite, avoid online accounts and keep the adaptive feature rule-based rather than implementing machine learning."],
], [3100, 6260])

doc.save(OUT)
print(OUT)
