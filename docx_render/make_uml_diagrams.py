from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path("C:/Users/saad2/OneDrive/Documents/CS IA/docx_render")
BLUE = "#2E74B5"
LIGHT = "#E8EEF5"
DARK = "#17365D"
INK = "#1F2937"
LINE = "#64748B"


def font(size: int, bold: bool = False):
    candidates = ["C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf"]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def text_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, lines: list[str]) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=14, fill="white", outline=BLUE, width=3)
    draw.rounded_rectangle((x1, y1, x2, y1 + 42), radius=14, fill=BLUE)
    draw.rectangle((x1, y1 + 25, x2, y1 + 42), fill=BLUE)
    title_font = font(20, True)
    body_font = font(15)
    width = draw.textbbox((0, 0), title, font=title_font)[2]
    draw.text((x1 + (x2 - x1 - width) / 2, y1 + 9), title, font=title_font, fill="white")
    y = y1 + 55
    for line in lines:
        draw.text((x1 + 15, y), line, font=body_font, fill=INK)
        y += 22


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], label: str = "") -> None:
    draw.line([start, end], fill=LINE, width=3)
    ex, ey = end
    draw.polygon([(ex, ey), (ex - 12, ey - 6), (ex - 12, ey + 6)], fill=LINE)
    if label:
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        draw.text((mx + 5, my - 20), label, font=font(14), fill=DARK)


def class_diagram() -> None:
    image = Image.new("RGB", (1800, 1120), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 30), "UML Class Diagram — Smart Study Time Allocator", font=font(30, True), fill=DARK)
    boxes = {
        "subject": (60, 140, 430, 330),
        "scorer": (610, 140, 990, 330),
        "study": (1190, 120, 1700, 370),
        "allocation": (60, 610, 430, 790),
        "timetable": (610, 580, 1010, 800),
        "database": (1190, 570, 1700, 800),
        "feedback": (1190, 890, 1700, 1060),
    }
    text_box(draw, boxes["subject"], "Subject", ["+ name: str", "+ difficulty: int", "+ days_until_exam: int", "+ estimated_hours: float", "+ validate(position): list[str]"])
    text_box(draw, boxes["scorer"], "PriorityScorer", ["+ difficulty_weight: float", "+ urgency_weight: float", "+ estimate_weight: float", "+ score(subject): float"])
    text_box(draw, boxes["study"], "StudyPlan", ["+ subjects: list[Subject]", "+ total_available_hours: float", "+ scorer: PriorityScorer", "+ validate(): list[str]", "+ allocations(): list[Allocation]", "+ correct_rounding_difference(...)"])
    text_box(draw, boxes["allocation"], "Allocation", ["+ subject: Subject", "+ priority_score: float", "+ equal_hours: float", "+ weighted_hours: float", "+ difference_hours: float"])
    text_box(draw, boxes["timetable"], "WeeklyTimetable", ["+ allocation_rows: list[dict]", "+ block_length_hours: float", "+ generate_blocks(): list[TimetableBlock]", "+ grouped_blocks(): dict"])
    text_box(draw, boxes["database"], "DatabaseManager", ["+ db_path: Path", "+ init_database()", "+ save_plan(...) → int", "+ save_feedback(...)", "+ fetch_*() → rows"])
    text_box(draw, boxes["feedback"], "FeedbackModel", ["+ database: DatabaseManager", "+ adjusted_estimate(name, estimate)", "  → float"])
    arrow(draw, (430, 235), (1190, 235), "uses Subject")
    arrow(draw, (990, 235), (1190, 260), "scores")
    arrow(draw, (1370, 370), (250, 610), "creates")
    arrow(draw, (1430, 370), (810, 580), "provides allocation rows")
    arrow(draw, (1450, 370), (1450, 570), "saves plan")
    arrow(draw, (1450, 800), (1450, 890), "provides history")
    image.save(OUT / "uml_class_diagram.png")


def use_case_diagram() -> None:
    image = Image.new("RGB", (1800, 860), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 30), "UML Use-Case Diagram — Student Workflow", font=font(30, True), fill=DARK)
    # Actor
    draw.ellipse((90, 315, 150, 375), outline=DARK, width=4)
    draw.line((120, 375, 120, 485), fill=DARK, width=4)
    draw.line((65, 420, 175, 420), fill=DARK, width=4)
    draw.line((120, 485, 70, 545), fill=DARK, width=4)
    draw.line((120, 485, 170, 545), fill=DARK, width=4)
    draw.text((75, 565), "Student", font=font(20, True), fill=DARK)
    # System boundary
    draw.rounded_rectangle((310, 115, 1710, 760), radius=18, outline=BLUE, width=4)
    draw.text((345, 135), "Smart Study Time Allocator", font=font(22, True), fill=BLUE)
    cases = [
        ("Enter subject details", (450, 225, 830, 300)),
        ("Generate weighted study plan", (1040, 225, 1510, 300)),
        ("Create weekly timetable", (450, 415, 830, 490)),
        ("Save plan and timetable", (1040, 415, 1510, 490)),
        ("Submit actual-hours feedback", (450, 605, 830, 680)),
        ("View history and adjusted estimates", (1040, 605, 1510, 680)),
    ]
    for title, box in cases:
        draw.rounded_rectangle(box, radius=38, fill=LIGHT, outline=BLUE, width=3)
        w = draw.textbbox((0, 0), title, font=font(18))[2]
        draw.text((box[0] + (box[2] - box[0] - w) / 2, box[1] + 24), title, font=font(18), fill=INK)
        arrow(draw, (175, 430), (box[0], (box[1] + box[3]) // 2))
    draw.line((830, 262, 1040, 262), fill=LINE, width=3)
    draw.text((865, 235), "uses", font=font(14), fill=DARK)
    draw.line((830, 452, 1040, 452), fill=LINE, width=3)
    draw.text((858, 425), "can save", font=font(14), fill=DARK)
    draw.line((830, 642, 1040, 642), fill=LINE, width=3)
    draw.text((853, 615), "updates", font=font(14), fill=DARK)
    image.save(OUT / "uml_use_case_diagram.png")


OUT.mkdir(exist_ok=True)
class_diagram()
use_case_diagram()
