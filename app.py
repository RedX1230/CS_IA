from __future__ import annotations

from dataclasses import asdict
from html import escape
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from database import DatabaseManager, FeedbackModel
from models import Subject, TimetableBlock
from planner import PriorityScorer, StudyPlan
from timetable import WeeklyTimetable


HOST = "127.0.0.1"
PORT = 8501

database = DatabaseManager()
database.init_database()
feedback_model = FeedbackModel(database)

STATE = {
    "subject_count": 4,
    "latest_plan_id": None,
    "latest_allocations": [],
    "latest_timetable_blocks": [],
    "latest_timetable_summary": [],
    "latest_settings": {
        "total_available_hours": 20.0,
        "difficulty_weight": 1.0,
        "urgency_weight": 10.0,
        "estimate_weight": 0.15,
        "use_feedback_estimates": True,
        "block_length": 1.0,
    },
    "draft_subjects": [],
    "errors": [],
    "save_message": "",
    "feedback_message": "",
    "view": "plan",
    "feedback_plan_id": None,
}


def default_subjects(count: int) -> list[dict]:
    return [
        {
            "name": f"Subject {index + 1}",
            "difficulty": 3,
            "days_until_exam": 14,
            "estimated_hours": 5.0,
        }
        for index in range(count)
    ]


def initialise_state() -> None:
    if not STATE["draft_subjects"]:
        STATE["draft_subjects"] = default_subjects(STATE["subject_count"])


def sync_draft_subject_count() -> None:
    count = int(STATE["subject_count"])
    draft = list(STATE.get("draft_subjects") or [])
    if len(draft) < count:
        draft.extend(default_subjects(count - len(draft)))
    elif len(draft) > count:
        draft = draft[:count]
    STATE["draft_subjects"] = draft


def read_subjects_from_form(form: dict[str, list[str]], count: int, use_feedback_estimates: bool) -> list[Subject]:
    subjects: list[Subject] = []
    for index in range(count):
        name = form.get(f"name_{index}", [""])[0].strip()
        difficulty = int(form.get(f"difficulty_{index}", ["3"])[0])
        days_until_exam = int(form.get(f"days_{index}", ["14"])[0])
        estimated_hours = float(form.get(f"estimate_{index}", ["5.0"])[0])
        if use_feedback_estimates and name:
            estimated_hours = feedback_model.adjusted_estimate(name, estimated_hours)
        subjects.append(
            Subject(
                name=name,
                difficulty=difficulty,
                days_until_exam=days_until_exam,
                estimated_hours=estimated_hours,
            )
        )
    return subjects


def serialise_subjects(subjects: list[Subject]) -> list[dict]:
    return [asdict(subject) for subject in subjects]


def human_hours(hours: float) -> str:
    rounded_minutes = int(round(abs(float(hours)) * 60 / 15) * 15)
    hours_part = rounded_minutes // 60
    minutes_part = rounded_minutes % 60
    sign = "-" if float(hours) < 0 and rounded_minutes else ""
    if hours_part and minutes_part:
        return f"{sign}{hours_part} h {minutes_part} min"
    if hours_part:
        return f"{sign}{hours_part} h"
    return f"{sign}{minutes_part} min"


def build_allocation_rows(allocation_rows: list[dict]) -> list[list[str]]:
    return [
        [
            row["name"],
            str(row["difficulty"]),
            str(row["days_until_exam"]),
            human_hours(row["estimated_hours"]),
            f'{row["priority_score"]:.4f}',
            human_hours(row["equal_allocation_hours"]),
            human_hours(row["weighted_allocation_hours"]),
            human_hours(row["difference_hours"]),
        ]
        for row in allocation_rows
    ]


def build_timetable_grid(blocks: list[TimetableBlock]) -> list[dict]:
    grouped = {weekday: [] for weekday in WeeklyTimetable.WEEKDAYS}
    for block in blocks:
        grouped[block.weekday].append(block)

    largest_day = max((len(day_blocks) for day_blocks in grouped.values()), default=0)
    rows = []
    for block_index in range(largest_day):
        row = {"Block": block_index + 1}
        for weekday in WeeklyTimetable.WEEKDAYS:
            day_blocks = grouped[weekday]
            if block_index < len(day_blocks):
                block = day_blocks[block_index]
                row[weekday] = f"{block.subject_name} ({human_hours(block.duration_hours)})"
            else:
                row[weekday] = ""
        rows.append(row)
    return rows


def timetable_grid_rows(blocks: list[TimetableBlock]) -> list[list[str]]:
    grid = build_timetable_grid(blocks)
    return [
        [str(row["Block"])] + [row[weekday] for weekday in WeeklyTimetable.WEEKDAYS]
        for row in grid
    ]


def html_table(headers: list[str], rows: list[list[str]]) -> str:
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    if rows:
        body_html = "".join(
            "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
            for row in rows
        )
    else:
        body_html = f'<tr><td colspan="{len(headers)}">No data yet</td></tr>'
    return f"""
    <table class="wf-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{body_html}</tbody>
    </table>
    """


def nav_link(key: str, label: str, active: bool) -> str:
    cls = "nav-link active" if active else "nav-link"
    return f'<a class="{cls}" href="/?view={key}">{label}</a>'


def messages_html() -> str:
    parts = []
    for key in ("errors", "save_message", "feedback_message"):
        value = STATE.get(key)
        if not value:
            continue
        if isinstance(value, list):
            parts.extend(f'<div class="message error">{escape(item)}</div>' for item in value)
        else:
            kind = "success" if key != "errors" else "error"
            parts.append(f'<div class="message {kind}">{escape(str(value))}</div>')
        STATE[key] = [] if key == "errors" else ""
    return "".join(parts)


def render_shell(content: str, view: str) -> str:
    nav_links = "".join(
        [
            nav_link("plan", "Plan", view == "plan"),
            nav_link("timetable", "Timetable", view == "timetable"),
            nav_link("feedback", "Feedback", view == "feedback"),
            nav_link("history", "History", view == "history"),
        ]
    )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart Study Time Allocator</title>
  <style>
    :root {{
      --bg: #f1ebdf;
      --panel: #ddd6c7;
      --panel-2: #e7dfcf;
      --line: #4d463f;
      --line-soft: rgba(77, 70, 63, 0.35);
      --ink: #5a4634;
      --muted: #7b6756;
      --accent: #c94b3b;
      --field-bg: #f8f3e9;
      --field-text: #5a4634;
      --field-border: #6a5a49;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Courier New", Courier, monospace;
      color: var(--ink);
      background:
        radial-gradient(circle at 1px 1px, rgba(77, 70, 63, 0.08) 1px, transparent 0) 0 0 / 14px 14px,
        var(--bg);
    }}
    .topbar {{
      height: 42px;
      background: #221f1c;
      border-bottom: 1px solid var(--line);
      color: #f0e8d8;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 14px;
      letter-spacing: 0.12em;
      font-size: 0.72rem;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 245px 1fr;
      min-height: calc(100vh - 42px);
    }}
    .sidebar {{
      border-right: 1px solid var(--line);
      background: var(--panel-2);
      padding: 14px;
    }}
    .brand {{
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.2);
      padding: 14px;
      margin-bottom: 14px;
    }}
    .brand h1 {{ margin: 0; font-size: 1.15rem; line-height: 1; }}
    .brand p {{ margin: 6px 0 0; font-size: 0.8rem; color: var(--muted); }}
    .sidebar h3 {{
      margin: 18px 0 8px;
      font-size: 0.72rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    .nav-link {{
      display: block;
      text-decoration: none;
      color: var(--ink);
      border: 1px solid transparent;
      padding: 8px 10px;
      margin-bottom: 6px;
    }}
    .nav-link.active {{
      border-color: var(--line);
      background: rgba(255,255,255,0.3);
    }}
    .quick-card {{
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.18);
      padding: 12px;
      margin-top: 10px;
      font-size: 0.86rem;
      color: var(--muted);
    }}
    .main {{ padding: 18px; }}
    .shell {{
      border: 1px solid var(--line);
      background: rgba(241, 235, 223, 0.88);
      box-shadow: 0 0 0 1px rgba(255,255,255,0.35) inset;
      padding: 14px;
    }}
    .titlebar {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 10px 12px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }}
    .titlebar h2 {{ margin: 0; font-size: 1.15rem; }}
    .block {{
      border: 1px solid var(--line-soft);
      background: rgba(255,255,255,0.22);
      padding: 12px;
      margin-bottom: 12px;
    }}
    .block-label {{
      font-size: 0.72rem;
      letter-spacing: 0.16em;
      color: var(--muted);
      text-transform: uppercase;
      margin-bottom: 8px;
    }}
    .form-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 10px;
    }}
    .field label {{
      display: block;
      margin-bottom: 4px;
      font-size: 0.82rem;
    }}
    .field input, .field select, .field textarea {{
      width: 100%;
      padding: 8px 9px;
      border: 1px solid var(--field-border);
      background: var(--field-bg);
      color: var(--field-text);
      font: inherit;
      outline: none;
    }}
    .field input::placeholder, .field textarea::placeholder {{ color: #8d7a69; }}
    .field.full {{ grid-column: 1 / -1; }}
    .action-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }}
    button, .btn {{
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      padding: 8px 12px;
      cursor: pointer;
      font: inherit;
      text-decoration: none;
    }}
    .primary {{
      background: var(--accent);
      border-color: #6b241c;
      color: #fff;
    }}
    .message {{
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.28);
      padding: 10px 12px;
      margin-bottom: 10px;
    }}
    .error {{ color: #7e231c; }}
    .success {{ color: #265d31; }}
    .wf-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      background: rgba(255,255,255,0.35);
    }}
    .wf-table th, .wf-table td {{
      border: 1px solid var(--line);
      padding: 8px 9px;
      vertical-align: top;
      text-align: left;
      font-size: 0.9rem;
    }}
    .wf-table th {{ background: var(--panel); }}
    .two-col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    @media (max-width: 1100px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .sidebar {{ border-right: 0; border-bottom: 1px solid var(--line); }}
      .form-grid {{ grid-template-columns: 1fr 1fr; }}
      .two-col {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 700px) {{
      .form-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="topbar">
    <div>SMART STUDY TIME ALLOCATOR | PLANNING INTERFACE</div>
    <div>IBDP CS IA</div>
  </div>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <h1>Smart Study Time Allocator</h1>
        <p>IB Computer Science IA</p>
      </div>
      <h3>Navigation</h3>
      {nav_links}
      <h3>Quick Actions</h3>
      <div class="quick-card">Generate a weighted study plan, build a weekly timetable, then save feedback and history.</div>
    </aside>
    <main class="main">
      <div class="shell">
        <div class="titlebar">
          <h2>Smart Study Time Allocator</h2>
        </div>
        {content}
      </div>
    </main>
  </div>
</body>
</html>"""


def render_plan_view() -> str:
    sync_draft_subject_count()
    count = int(STATE["subject_count"])
    draft = STATE["draft_subjects"]
    allocations = STATE["latest_allocations"]
    settings = STATE["latest_settings"]
    fields = []
    for index in range(count):
        subject = draft[index]
        fields.append(
            f"""
            <div class="form-grid">
              <div class="field"><label>Name</label><input name="name_{index}" value="{escape(subject['name'])}" placeholder="Mathematics"></div>
              <div class="field"><label>Difficulty</label><input type="number" min="1" max="5" name="difficulty_{index}" value="{subject['difficulty']}"></div>
              <div class="field"><label>Days until exam</label><input type="number" min="1" name="days_{index}" value="{subject['days_until_exam']}"></div>
              <div class="field"><label>Estimated hours</label><input type="number" step="0.5" min="0" name="estimate_{index}" value="{subject['estimated_hours']}"></div>
            </div>
            """
        )

    allocation_html = ""
    if allocations:
        allocation_html = f"""
        <div class="block">
          <div class="block-label">Generated Allocation</div>
          {html_table(["Subject", "Difficulty", "Days Until Exam", "Estimated Hours", "Priority Score", "Equal Allocation", "Weighted Allocation", "Difference"], build_allocation_rows(allocations))}
          <div style="margin-top:10px;"><strong>Weighted allocation total:</strong> {human_hours(sum(row['weighted_allocation_hours'] for row in allocations))}</div>
        </div>
        """

    return f"""
    {messages_html()}
    <div class="block">
      <div class="block-label">Settings and Subjects</div>
      <form method="post" action="/action">
        <input type="hidden" name="action" value="generate_plan">
        <div class="form-grid">
          <div class="field"><label>Total available study hours</label><input type="number" step="0.5" min="0" name="total_available_hours" value="{settings.get('total_available_hours', 20.0)}"></div>
          <div class="field"><label>Number of subjects</label><input type="number" min="1" max="12" name="subject_count" value="{count}"></div>
          <div class="field"><label>Difficulty weight</label><input type="number" step="0.1" min="0" name="difficulty_weight" value="{settings.get('difficulty_weight', 1.0)}"></div>
          <div class="field"><label>Urgency weight</label><input type="number" step="0.5" min="0" name="urgency_weight" value="{settings.get('urgency_weight', 10.0)}"></div>
          <div class="field"><label>Estimated-time weight</label><input type="number" step="0.05" min="0" name="estimate_weight" value="{settings.get('estimate_weight', 0.15)}"></div>
          <div class="field" style="display:flex;align-items:end;"><label style="display:flex;align-items:center;gap:8px;margin:0;"><input type="checkbox" name="use_feedback_estimates" {"checked" if settings.get("use_feedback_estimates", True) else ""}>Use feedback-adjusted estimated hours</label></div>
        </div>
        <div class="block-label" style="margin-top:10px;">Subjects</div>
        {''.join(fields)}
        <div class="action-row"><button class="primary" type="submit">Generate Study Plan</button></div>
      </form>
    </div>
    {allocation_html}
    """


def render_timetable_view() -> str:
    allocations = STATE["latest_allocations"]
    blocks = STATE["latest_timetable_blocks"]
    summary = STATE["latest_timetable_summary"]
    if not allocations:
        return messages_html() + '<div class="block">Generate a study plan first, then create a weekly timetable from it.</div>'

    table_html = ""
    if blocks:
        table_html = f"""
        <div class="block">
          <div class="block-label">Timetable</div>
          {html_table(["Block"] + WeeklyTimetable.WEEKDAYS, timetable_grid_rows([TimetableBlock(**block) for block in blocks]))}
        </div>
        <div class="block">
          <div class="block-label">Block Rounding Summary</div>
          {html_table(["Subject", "Weighted Hours", "Blocks", "Scheduled Hours", "Rounding Difference"], [[row["subject_name"], human_hours(row["weighted_hours"]), str(row["blocks"]), human_hours(row["scheduled_hours"]), human_hours(row["rounding_difference"])] for row in summary])}
        </div>
        <div class="block">
          <form method="post" action="/action">
            <input type="hidden" name="action" value="save_plan">
            <div class="action-row"><button class="primary" type="submit">Save Plan With Timetable</button></div>
          </form>
        </div>
        """

    return f"""
    {messages_html()}
    <div class="block">
      <div class="block-label">Weekly Timetable Maker</div>
      <form method="post" action="/action">
        <input type="hidden" name="action" value="generate_timetable">
        <div class="form-grid">
          <div class="field"><label>Study block length in hours</label><input type="number" step="0.25" min="0.25" max="4" name="block_length" value="{STATE['latest_settings'].get('block_length', 1.0)}"></div>
        </div>
        <div class="action-row"><button class="primary" type="submit">Generate Weekly Timetable</button></div>
      </form>
    </div>
    {table_html}
    """


def render_feedback_view() -> str:
    plans = database.fetch_recent_plans(limit=20)
    if not plans:
        return messages_html() + '<div class="block">Generate and save a plan before entering feedback.</div>'
    selected_plan = int(STATE.get("feedback_plan_id") or plans[0]["id"])
    allocations = database.fetch_allocations_for_plan(selected_plan)
    plan_options = "".join(
        f'<option value="{plan["id"]}" {"selected" if plan["id"] == selected_plan else ""}>Plan {plan["id"]} - {plan["created_at"]} ({plan["subject_count"]} subjects)</option>'
        for plan in plans
    )
    allocation_options = "".join(
        f'<option value="{allocation["id"]}">{escape(allocation["subject_name"])} - planned {human_hours(allocation["weighted_allocation_hours"])}</option>'
        for allocation in allocations
    )
    return f"""
    {messages_html()}
    <div class="block">
      <div class="block-label">Feedback</div>
      <form method="get" action="/">
        <input type="hidden" name="view" value="feedback">
        <div class="form-grid">
          <div class="field">
            <label>Plan</label>
            <select name="plan_id">{plan_options}</select>
          </div>
        </div>
        <div class="action-row"><button type="submit">Load Plan</button></div>
      </form>
      <form method="post" action="/action">
        <input type="hidden" name="action" value="save_feedback">
        <input type="hidden" name="plan_id" value="{selected_plan}">
        <div class="form-grid">
          <div class="field"><label>Subject allocation</label><select name="allocation_id">{allocation_options}</select></div>
          <div class="field"><label>Actual hours studied</label><input type="number" min="0" step="0.25" name="actual_hours" value="0"></div>
          <div class="field"><label>Plan usefulness (1-5)</label><input type="number" min="1" max="5" step="1" name="rating" value="3"></div>
          <div class="field full"><label>Notes</label><textarea name="notes" rows="4" placeholder="Too little time for Paper 2 revision"></textarea></div>
        </div>
        <div class="action-row"><button class="primary" type="submit">Save Feedback</button></div>
      </form>
    </div>
    """


def render_history_view() -> str:
    plans = database.fetch_recent_plans(limit=10)
    feedback_summary = database.fetch_feedback_summary()
    selected_plan = int(STATE.get("history_plan_id") or (plans[0]["id"] if plans else 0))
    saved_blocks = database.fetch_timetable_blocks_for_plan(selected_plan) if selected_plan else []
    plan_options = "".join(
        f'<option value="{plan["id"]}" {"selected" if plan["id"] == selected_plan else ""}>Plan {plan["id"]}</option>'
        for plan in plans
    )
    return f"""
    <div class="two-col">
      <div class="block">
        <div class="block-label">Recent Saved Plans</div>
        {html_table(["Plan ID", "Created", "Total Hours", "Subjects"], [[str(plan["id"]), plan["created_at"], human_hours(plan["total_available_hours"]), str(plan["subject_count"])] for plan in plans])}
      </div>
      <div class="block">
        <div class="block-label">Feedback Summary</div>
        {html_table(["Subject", "Entries", "Avg Planned", "Avg Actual", "Avg Difference", "Avg Rating"], [[row["subject_name"], str(row["feedback_count"]), human_hours(row["average_planned_hours"]), human_hours(row["average_actual_hours"]), human_hours(row["average_difference"]), f"{row['average_rating']:.1f}"] for row in feedback_summary])}
      </div>
    </div>
    <div class="block">
      <div class="block-label">Saved Timetable</div>
      <form method="get" action="/">
        <input type="hidden" name="view" value="history">
        <div class="form-grid">
          <div class="field">
            <label>View saved timetable for plan</label>
            <select name="plan_id">{plan_options}</select>
          </div>
        </div>
        <div class="action-row"><button type="submit">Load Saved Timetable</button></div>
      </form>
      {html_table(["Weekday", "Block", "Subject", "Duration"], [[row["weekday"], str(row["block_number"]), row["subject_name"], human_hours(row["duration_hours"])] for row in saved_blocks])}
    </div>
    """


def render_view(view: str) -> str:
    if view == "plan":
        return render_plan_view()
    if view == "timetable":
        return render_timetable_view()
    if view == "feedback":
        return render_feedback_view()
    return render_history_view()


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        initialise_state()
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        view = params.get("view", [STATE["view"]])[0].lower()
        if view not in {"plan", "timetable", "feedback", "history"}:
            view = "plan"
        STATE["view"] = view
        if "plan_id" in params:
            STATE["feedback_plan_id"] = params["plan_id"][0]
            STATE["history_plan_id"] = params["plan_id"][0]
        content = render_view(view)
        body = render_shell(content, view).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        initialise_state()
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length).decode("utf-8")
        form = parse_qs(data)
        action = form.get("action", [""])[0]

        if action == "generate_plan":
            subject_count = max(1, min(12, int(form.get("subject_count", ["4"])[0])))
            STATE["subject_count"] = subject_count
            use_feedback_estimates = form.get("use_feedback_estimates", ["off"])[0] == "on"
            subjects = read_subjects_from_form(form, subject_count, use_feedback_estimates)
            plan = StudyPlan(
                subjects,
                float(form.get("total_available_hours", ["20.0"])[0]),
                PriorityScorer(
                    difficulty_weight=float(form.get("difficulty_weight", ["1.0"])[0]),
                    urgency_weight=float(form.get("urgency_weight", ["10.0"])[0]),
                    estimate_weight=float(form.get("estimate_weight", ["0.15"])[0]),
                ),
            )
            errors = plan.validate()
            STATE["draft_subjects"] = serialise_subjects(subjects)
            STATE["latest_settings"] = {
                "total_available_hours": float(form.get("total_available_hours", ["20.0"])[0]),
                "difficulty_weight": float(form.get("difficulty_weight", ["1.0"])[0]),
                "urgency_weight": float(form.get("urgency_weight", ["10.0"])[0]),
                "estimate_weight": float(form.get("estimate_weight", ["0.15"])[0]),
                "use_feedback_estimates": use_feedback_estimates,
                "block_length": STATE["latest_settings"].get("block_length", 1.0),
            }
            if errors:
                STATE["errors"] = errors
                STATE["latest_allocations"] = []
            else:
                STATE["errors"] = []
                STATE["latest_allocations"] = plan.allocation_rows()
                STATE["latest_timetable_blocks"] = []
                STATE["latest_timetable_summary"] = []
            self._redirect("/?view=plan")
            return

        if action == "generate_timetable":
            block_length = float(form.get("block_length", ["1.0"])[0])
            timetable = WeeklyTimetable(STATE.get("latest_allocations", []), block_length_hours=block_length)
            errors = timetable.validate()
            STATE["latest_settings"]["block_length"] = block_length
            if errors:
                STATE["errors"] = errors
            else:
                STATE["errors"] = []
                STATE["latest_timetable_blocks"] = [block.to_row() for block in timetable.generate_blocks()]
                STATE["latest_timetable_summary"] = timetable.summary_rows()
            self._redirect("/?view=timetable")
            return

        if action == "save_feedback":
            plan_id = int(form.get("plan_id", ["0"])[0])
            allocation_id = int(form.get("allocation_id", ["0"])[0])
            allocations = database.fetch_allocations_for_plan(plan_id)
            allocation = next(row for row in allocations if row["id"] == allocation_id)
            database.save_feedback(
                allocation_id=allocation_id,
                subject_name=allocation["subject_name"],
                planned_hours=float(allocation["weighted_allocation_hours"]),
                actual_hours=float(form.get("actual_hours", ["0"])[0]),
                rating=int(form.get("rating", ["3"])[0]),
                notes=form.get("notes", [""])[0],
            )
            STATE["feedback_message"] = "Feedback saved. Future estimates for this subject can now adapt."
            self._redirect(f"/?view=feedback&plan_id={plan_id}")
            return

        if action == "save_plan":
            settings = STATE.get("latest_settings", {})
            blocks = [TimetableBlock(**row) for row in STATE.get("latest_timetable_blocks", [])]
            plan_id = database.save_plan(
                STATE.get("latest_allocations", []),
                total_available_hours=settings.get("total_available_hours", 20.0),
                difficulty_weight=settings.get("difficulty_weight", 1.0),
                urgency_weight=settings.get("urgency_weight", 10.0),
                estimate_weight=settings.get("estimate_weight", 0.15),
                timetable_blocks=blocks,
            )
            STATE["latest_plan_id"] = plan_id
            STATE["save_message"] = f"Plan {plan_id} and timetable saved to SQLite."
            self._redirect("/?view=timetable")
            return

        self._redirect("/")

    def _redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        return


def run() -> None:
    initialise_state()
    server = ThreadingHTTPServer((HOST, PORT), RequestHandler)
    print(f"Serving on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
