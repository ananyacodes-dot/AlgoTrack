import json
import tkinter as tk
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import font as tkfont, messagebox

import customtkinter as ctk
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import MaxNLocator

import backend as db

# ------------------------------------------------------------------
# Theme
# ------------------------------------------------------------------
NAVY = "#090b12"          # sidebar
NAVY_HOVER = "#161b2c"
ACCENT = "#5b7cfa"
ACCENT_DARK = "#4a68e0"   # button hover
ACCENT_SOFT = "#1d2340"   # tinted backgrounds
ACCENT_TEXT = "#9db0ff"   # accent-coloured text on dark cards
BG = "#0e1119"
CARD = "#161a26"
INPUT_BG = "#10141f"
BORDER = "#252b3b"
INPUT_BORDER = "#2e3547"
TEXT = "#e6e9f2"
MUTED = "#8a91a8"
GRID = "#222839"
FONT_FAMILY = None

STATUSES = ["Todo", "Solved", "Revision"]
DIFFICULTIES = ["Easy", "Medium", "Hard"]
STATUS_LABEL = {"Todo": "To Do", "Solved": "Solved", "Revision": "Revision"}
STATUS_STYLE = {
    "Solved": ("#14301f", "#5fd38d"),
    "Todo": ("#3a1a22", "#f27a8f"),
    "Revision": ("#1d2547", "#8ea2ff"),
}
DIFF_STYLE = {
    "Easy": ("#14301f", "#5fd38d"),
    "Medium": ("#3a2e12", "#f0b84d"),
    "Hard": ("#3a1a22", "#f27a8f"),
}
CHART_DIFF = {"Easy": "#34c17b", "Medium": "#f0b84d", "Hard": "#f26b6b"}
PALETTE = ["#6b8afd", "#34c17b", "#f0b84d", "#e86f8c", "#4db3f0", "#5c6378"]

DEFAULT_TOPICS = [
    "Array", "String", "Hashing", "Two Pointers", "Sliding Window",
    "Binary Search", "Sorting", "Linked List", "Stack", "Queue", "Heap",
    "Recursion", "Backtracking", "Tree", "Graph", "Greedy", "DP",
    "Bit Manipulation", "Math",
]
DEFAULT_PATTERNS = [
    "Two Pointers", "Sliding Window", "Binary Search", "Hashing", "Prefix Sum",
    "Fast & Slow Pointers", "Monotonic Stack", "BFS", "DFS", "Union Find",
    "Backtracking", "DP", "Greedy", "Heap", "Tree Traversal", "Topological Sort",
]
WEEK_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

ENTRY = dict(height=36, fg_color=INPUT_BG, border_color=INPUT_BORDER, border_width=1,
             text_color=TEXT, placeholder_text_color="#6b7389")
COMBO = dict(height=36, fg_color=INPUT_BG, border_color=INPUT_BORDER, border_width=1,
             button_color=INPUT_BORDER, button_hover_color="#3a4258", text_color=TEXT,
             dropdown_fg_color=CARD, dropdown_text_color=TEXT,
             dropdown_hover_color=ACCENT_SOFT)

SETTINGS_FILE = Path(__file__).with_name("settings.json")


# ------------------------------------------------------------------
# Settings (name + daily goal, stored in settings.json)
# ------------------------------------------------------------------
def load_settings():
    defaults = {"name": "", "daily_goal": 5, "weekly_goal": 7, "monthly_goal": 30}
    data = dict(defaults)
    try:
        data.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
    except Exception:
        pass
    for key in ("daily_goal", "weekly_goal", "monthly_goal"):
        try:
            data[key] = max(1, int(data[key]))
        except (TypeError, ValueError):
            data[key] = defaults[key]
    return data


def save_settings(data):
    try:
        SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


# ------------------------------------------------------------------
# UI helpers
# ------------------------------------------------------------------
def font(size=13, bold=False, italic=False):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold" if bold else "normal",
                       slant="italic" if italic else "roman")


def card(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10,
                        border_width=1, border_color=BORDER, **kw)


def chip(parent, text, style, width=76):
    bg, fg = style
    return ctk.CTkLabel(parent, text=text, width=width, height=22, corner_radius=6,
                        fg_color=bg, text_color=fg, font=font(11, True))


def header(parent, title, subtitle=""):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(f, text=title, font=font(24, True), text_color=TEXT).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(f, text=subtitle, text_color=MUTED).pack(anchor="w")
    return f


def card_title(parent, text):
    ctk.CTkLabel(parent, text=text, font=font(15, True), text_color=TEXT).pack(
        anchor="w", padx=16, pady=(14, 6))


def primary_button(parent, text, command, **kw):
    return ctk.CTkButton(parent, text=text, command=command, fg_color=ACCENT,
                         hover_color=ACCENT_DARK, text_color="white",
                         corner_radius=8, height=36, font=font(13, True), **kw)


def outline_button(parent, text, command, **kw):
    return ctk.CTkButton(parent, text=text, command=command, fg_color=CARD,
                         hover_color=ACCENT_SOFT, text_color=TEXT, border_width=1,
                         border_color=INPUT_BORDER, corner_radius=8, height=36, **kw)


def short_date(s):
    if not s:
        return "-"
    d = date.fromisoformat(s)
    return f"{d.day} {d:%b}"


def friendly_date(s):
    if not s:
        return "-"
    d = date.fromisoformat(s)
    if d == date.today():
        return "Today"
    if d == date.today() - timedelta(days=1):
        return "Yesterday"
    return short_date(s)


def clip(text, n):
    return text if len(text) <= n else text[: n - 1] + "\u2026"


# ------------------------------------------------------------------
# matplotlib helpers (light theme)
# ------------------------------------------------------------------
def new_figure(w, h):
    return Figure(figsize=(w, h), dpi=100, facecolor=CARD, layout="constrained")


def style_axes(ax, grid=True):
    ax.set_facecolor(CARD)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(INPUT_BORDER)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    if grid:
        ax.yaxis.grid(True, color=GRID, linewidth=1)
        ax.set_axisbelow(True)


def empty_message(ax, msg):
    ax.set_axis_off()
    ax.text(0.5, 0.5, msg, ha="center", va="center", color=MUTED,
            fontsize=9, transform=ax.transAxes)


def embed(fig, parent):
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.configure(bg=CARD, highlightthickness=0)
    widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    return canvas


def goal_numbers():
    """Solved counts for today, this week (Mon-Sun) and this month."""
    solved = dict(db.stats_by_date())
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week = sum(solved.get(str(monday + timedelta(days=i)), 0) for i in range(7))
    prefix = f"{today:%Y-%m}"
    month = sum(c for d, c in solved.items() if d.startswith(prefix))
    return {"day": solved.get(str(today), 0), "week": week, "month": month}


def max_streak(date_strings):
    days = sorted({date.fromisoformat(d) for d in date_strings})
    best = run = 0
    prev = None
    for d in days:
        run = run + 1 if prev is not None and (d - prev).days == 1 else 1
        best = max(best, run)
        prev = d
    return best


CAL_COLORS = ["#1c2233", "#0e4429", "#26a641", "#39d353"]


def cal_level(n):
    return 0 if n == 0 else 1 if n <= 2 else 2 if n <= 4 else 3


def calendar_geometry():
    """Last 365 days laid out in Monday-based week columns."""
    today = date.today()
    start = today - timedelta(days=364)
    start -= timedelta(days=start.weekday())
    weeks = (today - start).days // 7 + 1
    return today, start, weeks


def yearly_calendar_figure(solved):
    today, start, weeks = calendar_geometry()
    fig = new_figure(5.4, 1.1)
    ax = fig.add_subplot(111)
    ax.set_facecolor(CARD)
    ax.axis("off")

    def square(x, y, color, size=0.84):
        off = (1 - size) / 2
        ax.add_patch(FancyBboxPatch(
            (x + off, y + off), size, size, boxstyle="round,pad=0,rounding_size=0.18",
            facecolor=color, edgecolor="none"))

    for offset in range((today - start).days + 1):
        d = start + timedelta(days=offset)
        col, row = divmod(offset, 7)
        square(col, row, CAL_COLORS[cal_level(solved.get(str(d), 0))])

    labels, prev = [], None
    for col in range(weeks):
        d0 = start + timedelta(days=col * 7)
        if d0.month != prev:
            labels.append((col, f"{d0:%b}"))
            prev = d0.month
    if len(labels) > 1 and labels[1][0] - labels[0][0] < 3:
        labels = labels[1:]
    for col, name in labels:
        ax.text(col, -0.55, name, fontsize=8, color=MUTED, ha="left", va="center")
    for r, name in ((0, "Mon"), (2, "Wed"), (4, "Fri")):
        ax.text(-0.4, r + 0.5, name, fontsize=7, color=MUTED, ha="right", va="center")

    # legend
    x0 = weeks - 9.5
    ax.text(x0, 8.5, "Less", fontsize=7, color=MUTED, ha="right", va="center")
    for i, c in enumerate(CAL_COLORS):
        square(x0 + 0.4 + i * 1.2, 8.0, c, 0.9)
    ax.text(x0 + 0.4 + 4 * 1.2 + 0.1, 8.5, "More", fontsize=7, color=MUTED,
            ha="left", va="center")

    ax.set_xlim(-2.4, weeks + 0.2)
    ax.set_ylim(9.2, -1.3)
    ax.set_aspect("equal")
    return fig


def activity_figure():
    data = db.get_last_30_days_data()
    counts = [d[1] for d in data]
    fig = new_figure(4.8, 2.2)
    ax = fig.add_subplot(111)
    style_axes(ax)
    if sum(counts) == 0:
        empty_message(ax, "No solved problems in the last 30 days")
        return fig
    xs = list(range(len(counts)))
    ax.plot(xs, counts, color=ACCENT, linewidth=2, marker="o", markersize=3)
    ax.fill_between(xs, counts, color=ACCENT, alpha=0.12)
    ticks = xs[::4]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(data[i][2]) for i in ticks])
    ax.set_xlim(0, len(xs) - 1)
    ax.set_ylim(0, max(counts) + 1)
    return fig


# ------------------------------------------------------------------
# Home
# ------------------------------------------------------------------
class HomePage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.columnconfigure(0, weight=1)
        self.body = None

    def refresh(self):
        if self.body is not None:
            self.body.destroy()
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=0, column=0, sticky="nsew")
        self.body.columnconfigure(0, weight=5)
        self.body.columnconfigure(1, weight=4)
        self._build()

    @staticmethod
    def _stat_card(parent, title, value, sub, sub_color, icon, icon_fg, icon_bg):
        c = card(parent)
        c.columnconfigure(0, weight=1)
        ctk.CTkLabel(c, text=title.upper(), text_color=MUTED, font=font(10, True)).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(c, text=icon, width=30, height=30, corner_radius=8,
                     fg_color=icon_bg, text_color=icon_fg, font=font(14, True)).grid(
            row=0, column=1, rowspan=2, padx=(0, 12), pady=(10, 0), sticky="n")
        ctk.CTkLabel(c, text=str(value), font=font(28, True), text_color=TEXT).grid(
            row=1, column=0, sticky="w", padx=14)
        ctk.CTkLabel(c, text=sub, text_color=sub_color, font=font(11)).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 12))
        return c

    def _build(self):
        b = self.body
        stats = db.get_dashboard_stats()
        streak = db.get_streak()
        today_count = db.get_todays_count()
        goal = self.app.settings["daily_goal"]
        week = db.get_weekly_progress()
        pct = round(stats["solved"] / stats["total"] * 100) if stats["total"] else 0

        # --- greeting row ---
        hour = datetime.now().hour
        greet = ("Good morning" if hour < 12 else
                 "Good afternoon" if hour < 17 else "Good evening")
        name = self.app.settings["name"].strip()
        title = f"{greet}, {name}" if name else greet

        top = ctk.CTkFrame(b, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        top.columnconfigure(0, weight=1)
        left = ctk.CTkFrame(top, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        line = ctk.CTkFrame(left, fg_color="transparent")
        line.pack(anchor="w")
        ctk.CTkLabel(line, text=title, font=font(26, True), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(left, text="Here is an overview of your practice.",
                     text_color=MUTED).pack(anchor="w")
        ctk.CTkLabel(top, text=f"{date.today():%a, %d %b %Y}", width=160, height=32,
                     corner_radius=8, fg_color=CARD, text_color=TEXT,
                     font=font(12)).grid(row=0, column=1, sticky="e")

        lc = ctk.CTkFrame(b, fg_color="transparent")
        lc.grid(row=1, column=0, sticky="new", padx=(0, 8))
        rc = ctk.CTkFrame(b, fg_color="transparent")
        rc.grid(row=1, column=1, sticky="new", padx=(8, 0))

        # --- stat cards ---
        row = ctk.CTkFrame(lc, fg_color="transparent")
        row.pack(fill="x")
        cards = [
            ("Total Problems", stats["total"], f"\u2191 {sum(week)} solved this week",
             "#5fd38d", "\u25A3", ACCENT, ACCENT_SOFT),
            ("Solved", stats["solved"], f"\u2713 {pct}% of total",
             "#5fd38d", "\u2713", "#5fd38d", "#14301f"),
            ("To Do", stats["todo"], "not started", MUTED,
             "\u25F7", "#f0b84d", "#3a2e12"),
            ("Revision", stats["revision"], "to review", MUTED,
             "\u27F3", ACCENT, "#1d2547"),
        ]
        for i, (t, v, sub, sc, ic, ifg, ibg) in enumerate(cards):
            row.columnconfigure(i, weight=1, uniform="stat")
            self._stat_card(row, t, v, sub, sc, ic, ifg, ibg).grid(
                row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))

        # --- streak / today ---
        row2 = ctk.CTkFrame(lc, fg_color="transparent")
        row2.pack(fill="x", pady=(16, 0))
        for i in range(2):
            row2.columnconfigure(i, weight=1, uniform="mid")

        sc = card(row2)
        sc.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(sc, text="Current Streak", font=font(13, True), text_color=TEXT).pack(
            anchor="w", padx=14, pady=(14, 6))
        line = ctk.CTkFrame(sc, fg_color="transparent")
        line.pack(anchor="w", padx=14)
        ctk.CTkLabel(line, text=f"{streak} day{'s' if streak != 1 else ''}",
                     font=font(20, True), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(sc, text="Keep it up" if streak else "Solve one today to start",
                     text_color=MUTED).pack(anchor="w", padx=14, pady=(2, 14))

        tc = card(row2)
        tc.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(tc, text="Today's Progress", font=font(13, True), text_color=TEXT).pack(
            anchor="w", padx=14, pady=(14, 10))
        bar = ctk.CTkProgressBar(tc, height=8, progress_color=ACCENT, fg_color="#262c3f")
        bar.pack(fill="x", padx=14)
        bar.set(min(today_count / goal, 1.0))
        info = ctk.CTkFrame(tc, fg_color="transparent")
        info.pack(fill="x", padx=14, pady=(8, 14))
        ctk.CTkLabel(info, text=f"{today_count} / {goal} problems", text_color=MUTED,
                     font=font(12)).pack(side="left")
        ctk.CTkLabel(info, text=f"{min(round(today_count / goal * 100), 100)}%",
                     text_color=MUTED, font=font(12)).pack(side="right")

        # --- weekly progress ---
        wc = card(rc)
        wc.pack(fill="x")
        card_title(wc, "Weekly Progress")
        fig = new_figure(4.2, 2.1)
        ax = fig.add_subplot(111)
        style_axes(ax)
        today_idx = date.today().weekday()
        colors = [ACCENT if i == today_idx else "#3d4f9c" for i in range(7)]
        ax.bar(WEEK_DAYS, week, color=colors, width=0.5)
        ax.set_ylim(0, max(max(week), 1) + 1)
        embed(fig, wc)

        legend = ctk.CTkFrame(wc, fg_color="transparent")
        legend.pack(fill="x", padx=16, pady=(0, 14))
        for i, (label, val, col) in enumerate([
            ("Solved", stats["solved"], "#34c17b"),
            ("To Do", stats["todo"], "#fbbf4a"),
            ("Revision", stats["revision"], "#9a7be0"),
        ]):
            legend.columnconfigure(i, weight=1, uniform="leg")
            g = ctk.CTkFrame(legend, fg_color="transparent")
            g.grid(row=0, column=i, sticky="ew")
            ctk.CTkLabel(g, text="\u25CF", text_color=col, font=font(10)).pack(side="left")
            ctk.CTkLabel(g, text=f" {label}", text_color=MUTED, font=font(11)).pack(side="left")
            ctk.CTkLabel(g, text=str(val), text_color=TEXT, font=font(11, True)).pack(side="right")

        # --- recent activity ---
        rcard = card(rc)
        rcard.pack(fill="x", pady=(16, 0))
        rh = ctk.CTkFrame(rcard, fg_color="transparent")
        rh.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(rh, text="Recent Activity", font=font(15, True),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(rh, text="See all \u2192", width=70, height=26, fg_color="transparent",
                      hover_color=ACCENT_SOFT, text_color=ACCENT,
                      command=lambda: self.app.show("Activity")).pack(side="right")
        recent = db.get_all_problems()[:4]
        if not recent:
            ctk.CTkLabel(rcard, text="No activity yet. Add your first problem.",
                         text_color=MUTED).pack(padx=16, pady=(0, 16))
        for p in recent:
            r = ctk.CTkFrame(rcard, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=4)
            r.columnconfigure(1, weight=1)
            ctk.CTkLabel(r, text=str(p["problem_id"]), width=26, height=22, corner_radius=6,
                         fg_color=ACCENT_SOFT, text_color=ACCENT, font=font(10, True)).grid(
                row=0, column=0, padx=(0, 8))
            nm = ctk.CTkFrame(r, fg_color="transparent")
            nm.grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(nm, text=clip(p["problem_name"], 24), text_color=TEXT,
                         font=font(12, True)).pack(side="left")
            ctk.CTkLabel(nm, text=f"  ({clip(p['topic'], 14)})", text_color=MUTED,
                         font=font(11)).pack(side="left")
            chip(r, STATUS_LABEL[p["status"]], STATUS_STYLE[p["status"]], 70).grid(
                row=0, column=2, padx=8)
            ctk.CTkLabel(r, text=friendly_date(p["date_solved"]), width=70, anchor="e",
                         text_color=MUTED, font=font(11)).grid(row=0, column=3)
        ctk.CTkLabel(rcard, text="").pack(pady=2)
        self._extra(b, lc)

    def _extra(self, b, lc):
        settings = self.app.settings
        nums = goal_numbers()
        solved = dict(db.stats_by_date())

        # --- 30-day activity | goal progress ---
        ac = card(b)
        ac.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(16, 0))
        card_title(ac, "30-day solving activity")
        embed(activity_figure(), ac)

        gc = card(b)
        gc.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(16, 0))
        card_title(gc, "Goal progress")
        for label, key, gkey in (("Weekly goal", "week", "weekly_goal"),
                                 ("Monthly goal", "month", "monthly_goal")):
            goal, val = settings[gkey], nums[key]
            line = ctk.CTkFrame(gc, fg_color="transparent")
            line.pack(fill="x", padx=16, pady=(6, 0))
            ctk.CTkLabel(line, text=label, font=font(13, True), text_color=TEXT).pack(side="left")
            ctk.CTkLabel(line, text=f"{val} / {goal} solved", text_color=MUTED,
                         font=font(11)).pack(side="right")
            bar = ctk.CTkProgressBar(gc, height=8, progress_color=ACCENT, fg_color="#262c3f")
            bar.pack(fill="x", padx=16, pady=(6, 12))
            bar.set(min(val / goal, 1.0))
        outline_button(gc, "Manage goals \u2192", lambda: self.app.show("Goals"),
                       width=140).pack(anchor="e", padx=16, pady=(6, 14))

        # --- smart insights | next week's focus ---
        ic = card(b)
        ic.grid(row=3, column=0, sticky="nsew", padx=(0, 8), pady=(16, 0))
        card_title(ic, "Smart insights")
        for line in db.get_insights():
            ctk.CTkLabel(ic, text=f"\u2022 {line}", text_color=MUTED, wraplength=440,
                         justify="left").pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(ic, text="").pack(pady=4)

        fc = card(b)
        fc.grid(row=3, column=1, sticky="nsew", padx=(8, 0), pady=(16, 0))
        card_title(fc, "Next week's focus")
        ctk.CTkLabel(fc, text=db.get_weekly_recommendation(), wraplength=380,
                     justify="left", text_color=ACCENT_TEXT, font=font(14)).pack(
            anchor="w", padx=16, pady=(0, 16))

        # --- yearly contribution calendar ---
        cc = card(lc)
        cc.pack(fill="x", pady=(16, 0))
        today, start, weeks = calendar_geometry()
        cutoff = today - timedelta(days=364)
        year = {d: c for d, c in solved.items()
                if cutoff <= date.fromisoformat(d) <= today}
        total = sum(year.values())

        card_title(cc, "Yearly contribution calendar")
        sub = ctk.CTkFrame(cc, fg_color="transparent")
        sub.pack(fill="x", padx=16, pady=(0, 2))
        default_hint = f"{total} submission{'s' if total != 1 else ''} in the past year"
        hint = ctk.CTkLabel(sub, text=default_hint, text_color=TEXT, font=font(12, True))
        hint.pack(side="left")
        ctk.CTkLabel(sub, text=f"Active days: {len(year)}   Max streak: {max_streak(year)}",
                     text_color=MUTED, font=font(11)).pack(side="right")

        canvas = embed(yearly_calendar_figure(solved), cc)
        widget = canvas.get_tk_widget()
      
        cc.bind("<Configure>", lambda e: widget.configure(
            height=max(110, int((e.width - 24) / 5.1))))

        def on_move(ev):
            text = default_hint
            if ev.inaxes is not None and ev.xdata is not None and ev.ydata is not None:
                col, row = int(ev.xdata // 1), int(ev.ydata // 1)
                if 0 <= col < weeks and 0 <= row < 7:
                    d = start + timedelta(days=col * 7 + row)
                    if d <= today:
                        text = f"{d.day} {d:%b %Y}: {solved.get(str(d), 0)} solved"
            hint.configure(text=text)

        canvas.mpl_connect("motion_notify_event", on_move)


# ------------------------------------------------------------------
# Add Problem
# ------------------------------------------------------------------
class AddPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.columnconfigure(0, weight=1)

        header(self, "Add a New Problem", "Log a problem you worked on").grid(
            row=0, column=0, sticky="w", pady=(0, 14))

        form = card(self)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure((0, 1), weight=1, uniform="f")

        def lbl(text, r, c, span=1):
            ctk.CTkLabel(form, text=text, text_color=MUTED, font=font(12)).grid(
                row=r, column=c, columnspan=span, sticky="w",
                padx=(20, 10) if c == 0 else (10, 20), pady=(16, 4))

        def pad(c):
            return (20, 10) if c == 0 else (10, 20)

        lbl("Problem Name *", 0, 0)
        self.name = ctk.CTkEntry(form, placeholder_text="e.g. Two Sum", **ENTRY)
        self.name.grid(row=1, column=0, sticky="ew", padx=pad(0))
        self.name.bind("<Return>", lambda e: self.submit())

        lbl("Link", 0, 1)
        self.link = ctk.CTkEntry(form, placeholder_text="https://...", **ENTRY)
        self.link.grid(row=1, column=1, sticky="ew", padx=pad(1))

        lbl("Topic *", 2, 0)
        self.topic = ctk.CTkComboBox(form, values=DEFAULT_TOPICS, **COMBO)
        self.topic.grid(row=3, column=0, sticky="ew", padx=pad(0))

        lbl("Difficulty *", 2, 1)
        self.difficulty = ctk.CTkComboBox(form, values=DIFFICULTIES, state="readonly", **COMBO)
        self.difficulty.grid(row=3, column=1, sticky="ew", padx=pad(1))

        lbl("Pattern (optional)", 4, 0)
        self.pattern = ctk.CTkComboBox(form, values=DEFAULT_PATTERNS, **COMBO)
        self.pattern.grid(row=5, column=0, sticky="ew", padx=pad(0))

        lbl("Status", 4, 1)
        self.status = ctk.CTkComboBox(form, values=STATUSES, state="readonly", **COMBO)
        self.status.grid(row=5, column=1, sticky="ew", padx=pad(1))

        lbl("Notes (optional)", 6, 0, 2)
        self.notes = ctk.CTkTextbox(form, height=110, fg_color=INPUT_BG, border_width=1,
                                    border_color=INPUT_BORDER, text_color=TEXT)
        self.notes.grid(row=7, column=0, columnspan=2, sticky="ew", padx=20)

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.grid(row=8, column=0, columnspan=2, sticky="e", padx=20, pady=(16, 6))
        outline_button(btns, "Cancel", self.cancel, width=100).pack(side="left", padx=(0, 10))
        primary_button(btns, "Save Problem", self.submit, width=130).pack(side="left")

        self.msg = ctk.CTkLabel(form, text="")
        self.msg.grid(row=9, column=0, columnspan=2, sticky="e", padx=20, pady=(0, 14))

        self.clear()

    def refresh(self):
        problems = db.get_all_problems()
        topics = sorted(set(DEFAULT_TOPICS) | {p["topic"] for p in problems})
        patterns = sorted(set(DEFAULT_PATTERNS) | {p["pattern"] for p in problems if p["pattern"]})
        self.topic.configure(values=topics)
        self.pattern.configure(values=patterns)

    def clear(self):
        self.name.delete(0, "end")
        self.link.delete(0, "end")
        self.notes.delete("1.0", "end")
        self.topic.set("")
        self.pattern.set("")
        self.difficulty.set("Easy")
        self.status.set("Todo")

    def cancel(self):
        self.clear()
        self.msg.configure(text="")
        self.app.show("Home")

    def submit(self):
        try:
            db.add_problem(
                self.name.get(),
                self.link.get().strip(),
                self.topic.get(),
                self.difficulty.get(),
                self.status.get(),
                self.pattern.get().strip(),
                self.notes.get("1.0", "end").strip(),
            )
        except ValueError as e:
            self.msg.configure(text=str(e), text_color="#f27a8f")
            return
        except Exception as e:
            self.msg.configure(text=f"Error: {e}", text_color="#f27a8f")
            return
        self.clear()
        self.refresh()
        self.msg.configure(text="Problem saved.", text_color="#5fd38d")
        self.app.update_streak()


# ------------------------------------------------------------------
# All Problems
# ------------------------------------------------------------------
class ProblemsPage(ctk.CTkFrame):
    # (heading, fixed width in px; 0 = flexible column)
    COLS = [("#", 44), ("Problem Name", 0), ("Topic", 130), ("Difficulty", 100),
            ("Status", 100), ("Date Solved", 100), ("Pattern", 150), ("", 44)]
    CHIPS = ["All", "Easy", "Medium", "Hard", "Todo", "Solved", "Revision"]

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.diff = "All"
        self.status = "All"
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        top.columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="All Problems", font=font(24, True), text_color=TEXT).grid(
            row=0, column=0, sticky="w")
        primary_button(top, "+ Add Problem", lambda: app.show("Add Problem"), width=130).grid(
            row=0, column=1, sticky="e")

        self.search = ctk.CTkEntry(self, placeholder_text="\u2315  Search problems...", **ENTRY)
        self.search.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.search.bind("<KeyRelease>", lambda e: self.load())

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.chip_btns = {}
        for name in self.CHIPS:
            btn = ctk.CTkButton(bar, text=name, width=70, height=30, corner_radius=15,
                                border_width=1, command=lambda n=name: self._chip_click(n))
            btn.pack(side="left", padx=(0, 8))
            self.chip_btns[name] = btn
        self.topic_box = ctk.CTkComboBox(bar, values=["All Topics"], state="readonly",
                                         width=160, command=lambda v: self.load(), **COMBO)
        self.topic_box.set("All Topics")
        self.topic_box.pack(side="right")
        self.count_label = ctk.CTkLabel(bar, text="", text_color=MUTED)
        self.count_label.pack(side="right", padx=14)
        self._style_chips()

        tbl = card(self)
        tbl.grid(row=3, column=0, sticky="nsew")
        tbl.columnconfigure(0, weight=1)
        tbl.rowconfigure(1, weight=1)

        head = ctk.CTkFrame(tbl, fg_color="#1b2030", corner_radius=10)
        head.grid(row=0, column=0, sticky="ew", padx=(8, 26), pady=(8, 0))
        self._configure_cols(head)
        for i, (text, _) in enumerate(self.COLS):
            ctk.CTkLabel(head, text=text.upper(), text_color=MUTED, font=font(10, True),
                         anchor="w").grid(row=0, column=i, sticky="w",
                                          padx=(14, 0) if i == 0 else 0, pady=9)

        self.list = ctk.CTkScrollableFrame(tbl, fg_color="transparent")
        self.list.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 6))
        self.list.columnconfigure(0, weight=1)

    def _configure_cols(self, frame):
        for i, (_, w) in enumerate(self.COLS):
            if w == 0:
                frame.columnconfigure(i, weight=1)
            else:
                frame.columnconfigure(i, minsize=w, weight=0)

    def _style_chips(self):
        for name, btn in self.chip_btns.items():
            active = ((name == "All" and self.diff == "All" and self.status == "All")
                      or name in (self.diff, self.status))
            btn.configure(
                fg_color=ACCENT if active else CARD,
                hover_color=ACCENT_DARK if active else ACCENT_SOFT,
                text_color="white" if active else TEXT,
                border_color=ACCENT if active else BORDER,
            )

    def _chip_click(self, name):
        if name == "All":
            self.diff = self.status = "All"
        elif name in DIFFICULTIES:
            self.diff = "All" if self.diff == name else name
        else:
            self.status = "All" if self.status == name else name
        self._style_chips()
        self.load()

    def refresh(self):
        topics = ["All Topics"] + sorted({p["topic"] for p in db.get_all_problems()})
        self.topic_box.configure(values=topics)
        if self.topic_box.get() not in topics:
            self.topic_box.set("All Topics")
        self.load()

    def load(self):
        for w in self.list.winfo_children():
            w.destroy()
        topic = self.topic_box.get()
        rows = db.filter_by_problems(
            topic="All" if topic == "All Topics" else topic,
            difficulty=self.diff,
            status=self.status,
        )
        q = self.search.get().strip().lower()
        if q:
            rows = [p for p in rows if q in p["problem_name"].lower()
                    or q in p["topic"].lower() or q in (p["pattern"] or "").lower()]
        self.count_label.configure(text=f"{len(rows)} problem(s)")
        if not rows:
            ctk.CTkLabel(self.list, text="No problems found.", text_color=MUTED).grid(
                row=0, column=0, pady=40)
            return
        for i, p in enumerate(rows):
            self._row(i, p)

    def _row(self, i, p):
        r = ctk.CTkFrame(self.list, fg_color="transparent")
        r.grid(row=i * 2, column=0, sticky="ew")
        self._configure_cols(r)

        ctk.CTkLabel(r, text=str(i + 1), text_color=MUTED, anchor="w").grid(
            row=0, column=0, sticky="w", padx=(14, 0), pady=10)
        ctk.CTkLabel(r, text=clip(p["problem_name"], 42), text_color=TEXT, anchor="w",
                     font=font(13, True)).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(r, text=clip(p["topic"], 16), text_color=MUTED, anchor="w").grid(
            row=0, column=2, sticky="w")
        chip(r, p["difficulty"], DIFF_STYLE[p["difficulty"]], 68).grid(
            row=0, column=3, sticky="w")
        st = chip(r, STATUS_LABEL[p["status"]], STATUS_STYLE[p["status"]], 72)
        st.grid(row=0, column=4, sticky="w")
        st.bind("<Button-1>", lambda e, p=p, w=st: self._menu(p, w))
        ctk.CTkLabel(r, text=short_date(p["date_solved"]), text_color=MUTED, anchor="w").grid(
            row=0, column=5, sticky="w")
        ctk.CTkLabel(r, text=clip(p["pattern"] or "-", 18), text_color=MUTED, anchor="w").grid(
            row=0, column=6, sticky="w")
        more = ctk.CTkButton(r, text="\u22EF", width=30, height=28, fg_color="transparent",
                             hover_color=ACCENT_SOFT, text_color=MUTED, font=font(16, True))
        more.configure(command=lambda p=p, w=more: self._menu(p, w))
        more.grid(row=0, column=7)

        ctk.CTkFrame(self.list, height=1, fg_color=GRID).grid(
            row=i * 2 + 1, column=0, sticky="ew", padx=8)

    # --- actions ---
    def _menu(self, p, widget):
        m = tk.Menu(self, tearoff=0, bg=CARD, fg=TEXT, activebackground=ACCENT,
                    activeforeground="white", bd=0, relief="flat")
        if p["problem_link"]:
            m.add_command(label="Open link", command=lambda: self._open(p["problem_link"]))
        m.add_command(label="View details", command=lambda: self._details(p))
        m.add_separator()
        for s in STATUSES:
            if s != p["status"]:
                m.add_command(label=f"Mark as {STATUS_LABEL[s]}",
                              command=lambda s=s: self._change_status(p["problem_id"], s))
        m.add_separator()
        m.add_command(label="Delete", command=lambda: self._delete(p))
        try:
            m.tk_popup(widget.winfo_rootx(), widget.winfo_rooty() + widget.winfo_height())
        finally:
            m.grab_release()

    def _change_status(self, pid, new_status):
        try:
            db.update_status(pid, new_status)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.after(10, self.load)
        self.app.update_streak()

    def _delete(self, p):
        if messagebox.askyesno("Delete", f"Delete '{p['problem_name']}'?"):
            db.delete_problem(p["problem_id"])
            self.after(10, self.refresh)
            self.app.update_streak()

    @staticmethod
    def _open(link):
        if not link.startswith(("http://", "https://")):
            link = "https://" + link
        webbrowser.open(link)

    def _details(self, p):
        win = ctk.CTkToplevel(self, fg_color=BG)
        win.title(p["problem_name"])
        win.geometry("480x380")
        ctk.CTkLabel(win, text=p["problem_name"], font=font(18, True), text_color=TEXT,
                     wraplength=440, justify="left").pack(anchor="w", padx=20, pady=(18, 8))
        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(anchor="w", padx=20)
        chip(row, p["difficulty"], DIFF_STYLE[p["difficulty"]], 68).pack(side="left")
        chip(row, STATUS_LABEL[p["status"]], STATUS_STYLE[p["status"]], 72).pack(side="left", padx=8)
        ctk.CTkLabel(row, text=f"{p['topic']}  |  {p['pattern'] or 'no pattern'}",
                     text_color=MUTED).pack(side="left", padx=4)
        ctk.CTkLabel(win, text="Notes", font=font(14, True), text_color=TEXT).pack(
            anchor="w", padx=20, pady=(14, 0))
        box = ctk.CTkTextbox(win, fg_color=INPUT_BG, border_width=1, border_color=INPUT_BORDER,
                             text_color=TEXT)
        box.pack(fill="both", expand=True, padx=20, pady=(4, 20))
        box.insert("1.0", p["notes"] or "No notes.")
        box.configure(state="disabled")
        win.after(100, win.focus)


# ------------------------------------------------------------------
# Analytics (all charts are matplotlib)
# ------------------------------------------------------------------
class AnalyticsPage(ctk.CTkScrollableFrame):
    RANGES = {"Last 7 Days": 7, "Last 14 Days": 14, "Last 30 Days": 30}
    INSIGHT_ICONS = [("!", "#f27a8f", "#3a1a22"), ("\u25CE", "#f27a8f", "#3a1a22"),
                     ("\u2197", "#f0b84d", "#3a2e12"), ("\u2606", ACCENT, "#1d2547")]

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.columnconfigure(0, weight=1)
        self.body = None
        self.daily_canvas = None
        self.daily_holder = None
        self.range_var = ctk.StringVar(value="Last 7 Days")

    def refresh(self):
        if self.body is not None:
            self.body.destroy()
        self.daily_canvas = None
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=0, column=0, sticky="nsew")
        self.body.columnconfigure((0, 1), weight=1, uniform="a")
        self._build()

    def _build(self):
        b = self.body
        header(b, "Analytics", "Visualize your weaknesses").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        problems = db.get_all_problems()

        c1 = card(b)
        c1.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 16))
        card_title(c1, "Solved by Topic")
        embed(self._topic_pie(), c1)

        c2 = card(b)
        c2.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 16))
        card_title(c2, "Solved by Difficulty")
        embed(self._difficulty_chart(), c2)

        c3 = card(b)
        c3.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 16))
        head = ctk.CTkFrame(c3, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(head, text="Daily Progress", font=font(15, True), text_color=TEXT).pack(side="left")
        ctk.CTkComboBox(head, values=list(self.RANGES), variable=self.range_var,
                        state="readonly", width=130, **{**COMBO, "height": 28},
                        command=lambda v: self._draw_daily()).pack(side="right")
        self.daily_holder = ctk.CTkFrame(c3, fg_color="transparent")
        self.daily_holder.pack(fill="both", expand=True)
        self._draw_daily()

        c4 = card(b)
        c4.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(0, 16))
        card_title(c4, "Topic-wise Progress")
        embed(self._topic_progress(problems), c4)

        self._strong_topics(b, problems)
        self._streak_and_insights(b)

    # --- charts ---
    def _topic_pie(self):
        data = sorted(db.stats_by_topic(), key=lambda t: t[1], reverse=True)
        fig = new_figure(4.2, 2.4)
        if not data:
            empty_message(fig.add_subplot(111), "No solved problems yet")
            return fig
        top, rest = data[:5], data[5:]
        if rest:
            top.append(("Others", sum(n for _, n in rest)))
        total = sum(n for _, n in top)
        colors = PALETTE[: len(top)]

        gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.25])
        ax = fig.add_subplot(gs[0])
        lg = fig.add_subplot(gs[1])
        lg.axis("off")
        ax.pie(
            [n for _, n in top], colors=colors, startangle=90, counterclock=False,
            wedgeprops=dict(edgecolor=CARD, linewidth=1.5),
            autopct=lambda p: f"{p:.0f}%" if p >= 8 else "", pctdistance=0.72,
            textprops=dict(color="white", fontsize=7, fontweight="bold"),
        )
        step = min(0.16, 0.9 / max(len(top), 1))
        for i, ((name, n), col) in enumerate(zip(top, colors)):
            y = 0.5 + (len(top) - 1) * step / 2 - i * step
            lg.text(0.0, y, "\u25CF", color=col, fontsize=9, va="center", transform=lg.transAxes)
            lg.text(0.1, y, clip(name, 14), color=TEXT, fontsize=8, va="center", transform=lg.transAxes)
            lg.text(1.0, y, f"{n} ({round(n / total * 100)}%)", color=MUTED, fontsize=8,
                    ha="right", va="center", transform=lg.transAxes)
        return fig

    def _difficulty_chart(self):
        counts = dict(db.stats_by_difficulty())
        vals = [counts.get(d, 0) for d in DIFFICULTIES]
        fig = new_figure(4.2, 2.4)
        ax = fig.add_subplot(111)
        style_axes(ax)
        if sum(vals) == 0:
            empty_message(ax, "No solved problems yet")
            return fig
        bars = ax.bar(DIFFICULTIES, vals, color=[CHART_DIFF[d] for d in DIFFICULTIES], width=0.5)
        ax.bar_label(bars, padding=3, color=TEXT, fontsize=9, fontweight="bold")
        ax.set_ylim(0, max(vals) * 1.2)
        ax.tick_params(axis="x", labelsize=9)
        return fig

    def _draw_daily(self):
        if self.daily_canvas is not None:
            self.daily_canvas.get_tk_widget().destroy()
        n = self.RANGES[self.range_var.get()]
        data = db.get_last_30_days_data()[-n:]
        counts = [d[1] for d in data]

        fig = new_figure(4.2, 2.1)
        ax = fig.add_subplot(111)
        style_axes(ax)
        if sum(counts) == 0:
            empty_message(ax, f"No solved problems in the {self.range_var.get().lower()}")
        else:
            labels, prev_month = [], None
            for d, _, day in data:
                dt = date.fromisoformat(d)
                labels.append(f"{dt:%b} {day}" if dt.month != prev_month else str(day))
                prev_month = dt.month
            step = 1 if n <= 7 else 2 if n <= 14 else 3
            ax.bar(range(n), counts, color="#5b7cfa", width=0.55)
            ax.set_xticks(range(0, n, step))
            ax.set_xticklabels(labels[::step])
        self.daily_canvas = embed(fig, self.daily_holder)

    def _topic_progress(self, problems):
        totals, solved = {}, {}
        for p in problems:
            totals[p["topic"]] = totals.get(p["topic"], 0) + 1
            if p["status"] == "Solved":
                solved[p["topic"]] = solved.get(p["topic"], 0) + 1
        rows = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]

        fig = new_figure(4.2, 2.4)
        ax = fig.add_subplot(111)
        if not rows:
            empty_message(ax, "No problems yet")
            return fig
        ax.set_facecolor(CARD)
        for s in ax.spines.values():
            s.set_visible(False)
        ys = list(range(len(rows)))
        names = [clip(t, 14) for t, _ in rows]
        ratios = [solved.get(t, 0) / n for t, n in rows]
        colors = [PALETTE[i % 5] for i in ys]
        ax.barh(ys, [1] * len(rows), color="#242a3c", height=0.36)
        ax.barh(ys, ratios, color=colors, height=0.36)
        ax.set_yticks(ys)
        ax.set_yticklabels(names, fontsize=8, color=TEXT)
        ax.set_xticks([])
        ax.tick_params(length=0)
        ax.invert_yaxis()
        ax.set_xlim(0, 1.6)
        for i, (t, n) in enumerate(rows):
            s = solved.get(t, 0)
            ax.text(1.05, i, f"{s}/{n}", va="center", fontsize=8, color=MUTED)
            ax.text(1.6, i, f"{round(ratios[i] * 100)}%", va="center", ha="right",
                    fontsize=8, color=colors[i], fontweight="bold")
        return fig

    # --- strong / developing topics ---
    def _strong_topics(self, b, problems):
        totals, solved = {}, {}
        for p in problems:
            totals[p["topic"]] = totals.get(p["topic"], 0) + 1
            if p["status"] == "Solved":
                solved[p["topic"]] = solved.get(p["topic"], 0) + 1
        box = card(b)
        box.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        card_title(box, "Strong and developing topics")
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 16))
        row.columnconfigure((0, 1), weight=1, uniform="st")
        if not totals:
            ctk.CTkLabel(row, text="Add some problems to see this.", text_color=MUTED).grid(
                row=0, column=0, sticky="w")
            return
        ratios = {t: solved.get(t, 0) / n for t, n in totals.items()}
        best = max(solved, key=solved.get) if solved else None
        weak = min(ratios, key=ratios.get)
        items = []
        if best:
            items.append(("MOST SOLVED", "#5fd38d", best))
        items.append(("NEEDS MORE PRACTICE", "#f0b84d", weak))
        for i, (tag, color, topic) in enumerate(items):
            c = ctk.CTkFrame(row, fg_color=ACCENT_SOFT, corner_radius=12)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            ctk.CTkLabel(c, text=tag, text_color=color, font=font(10, True)).pack(
                anchor="w", padx=16, pady=(14, 2))
            ctk.CTkLabel(c, text=topic, text_color=TEXT, font=font(18, True)).pack(
                anchor="w", padx=16)
            ctk.CTkLabel(
                c, text=f"{solved.get(topic, 0)} solved \u00B7 {totals[topic]} tracked \u00B7 "
                        f"{round(ratios[topic] * 100)}% completion",
                text_color=MUTED, font=font(11)).pack(anchor="w", padx=16, pady=(2, 14))

    # --- streak & insights ---
    def _streak_and_insights(self, b):
        streak = db.get_streak()

        banner = ctk.CTkFrame(b, fg_color=ACCENT_SOFT, corner_radius=14,
                              border_width=1, border_color="#2b3566")
        banner.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        ctk.CTkLabel(banner, text=str(streak), width=56, height=56, corner_radius=14,
                     fg_color=CARD, text_color=ACCENT, font=font(24, True)).pack(
            side="left", padx=18, pady=18)
        txt = ctk.CTkFrame(banner, fg_color="transparent")
        txt.pack(side="left", pady=14)
        ctk.CTkLabel(txt, text=f"{streak}-day streak" if streak else "No active streak",
                     font=font(20, True), text_color=TEXT).pack(anchor="w")
        msg = (f"You've solved at least 1 problem for {streak} consecutive day"
               f"{'s' if streak != 1 else ''}."
               if streak else "Solve a problem today to start your streak.")
        ctk.CTkLabel(txt, text=msg, text_color=MUTED).pack(anchor="w")

        ic = card(b)
        ic.grid(row=5, column=0, columnspan=2, sticky="ew")
        card_title(ic, "Insights")
        lines = db.get_insights() + [db.get_weekly_recommendation()]
        for i, line in enumerate(lines):
            sym, fg, bg = self.INSIGHT_ICONS[i % len(self.INSIGHT_ICONS)]
            r = ctk.CTkFrame(ic, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(r, text=sym, width=32, height=32, corner_radius=8, fg_color=bg,
                         text_color=fg, font=font(14, True)).pack(side="left")
            ctk.CTkLabel(r, text=line, text_color=TEXT, wraplength=800, justify="left").pack(
                side="left", padx=12)
        ctk.CTkLabel(ic, text="").pack(pady=2)


# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------
class GoalsPage(ctk.CTkScrollableFrame):
    SPEC = [
        ("Daily target", "day", "daily_goal", "today"),
        ("Weekly target", "week", "weekly_goal", "this week (Mon-Sun)"),
        ("Monthly target", "month", "monthly_goal", "this month"),
    ]

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.columnconfigure(0, weight=1)
        self.body = None
        self.msg = ctk.CTkLabel(self, text="")
        self.msg.grid(row=2, column=0, sticky="w", pady=(8, 0))

    def refresh(self):
        self.msg.configure(text="")
        self._build()

    def _build(self):
        if self.body is not None:
            self.body.destroy()
        b = self.body = ctk.CTkFrame(self, fg_color="transparent")
        b.grid(row=1, column=0, sticky="nsew")
        b.columnconfigure(0, weight=1)

        header(b, "Goal Tracker", "Turn consistency into measurable progress").grid(
            row=0, column=0, sticky="w", pady=(0, 14))
        nums = goal_numbers()
        row = ctk.CTkFrame(b, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew")
        for i, (title, key, gkey, span) in enumerate(self.SPEC):
            row.columnconfigure(i, weight=1, uniform="g")
            goal, val = self.app.settings[gkey], nums[key]
            c = card(row)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            ctk.CTkLabel(c, text=title, font=font(16, True), text_color=TEXT).pack(
                anchor="w", padx=18, pady=(16, 2))
            ctk.CTkLabel(c, text=f"{val} of {goal} problems solved {span}", text_color=MUTED,
                         font=font(11), wraplength=240, justify="left").pack(anchor="w", padx=18)
            bar = ctk.CTkProgressBar(c, height=10, progress_color=ACCENT, fg_color="#262c3f")
            bar.pack(fill="x", padx=18, pady=(12, 6))
            bar.set(min(val / goal, 1.0))
            ctk.CTkLabel(c, text=f"{min(round(val / goal * 100), 100)}% complete",
                         text_color=ACCENT, font=font(11, True)).pack(anchor="w", padx=18)
            entry = ctk.CTkEntry(c, **ENTRY)
            entry.pack(fill="x", padx=18, pady=(14, 8))
            entry.insert(0, str(goal))
            primary_button(c, "Save target",
                           lambda k=gkey, e=entry: self._save(k, e)).pack(
                fill="x", padx=18, pady=(0, 18))

        info = card(b)
        info.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        ctk.CTkLabel(info, text="How goal progress is calculated", font=font(14, True),
                     text_color=TEXT).pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(
            info, text="Only problems marked Solved count toward your goals. Weekly progress "
                       "runs Monday to Sunday and monthly progress covers the current calendar "
                       "month. Targets are saved in settings.json next to app.py.",
            text_color=MUTED, wraplength=820, justify="left").pack(
            anchor="w", padx=18, pady=(0, 14))

    def _save(self, key, entry):
        try:
            value = int(entry.get().strip())
            if not 1 <= value <= 1000:
                raise ValueError
        except ValueError:
            self.msg.configure(text="Enter a whole number between 1 and 1000.",
                               text_color="#f27a8f")
            return
        self.app.settings[key] = value
        ok = save_settings(self.app.settings)
        self._build()
        self.msg.configure(text="Target saved." if ok else "Could not write settings.json",
                           text_color="#5fd38d" if ok else "#f27a8f")


class ActivityPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.columnconfigure(0, weight=1)
        self.body = None

    def refresh(self):
        if self.body is not None:
            self.body.destroy()
        b = self.body = ctk.CTkFrame(self, fg_color="transparent")
        b.grid(row=0, column=0, sticky="nsew")
        b.columnconfigure(0, weight=1)

        top = ctk.CTkFrame(b, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        header(top, "All Activity", "Everything you've tracked, newest first").grid(
            row=0, column=0, sticky="w")
        outline_button(top, "\u2190 Back", lambda: self.app.show("Home"), width=90).grid(
            row=0, column=1, sticky="e")

        groups = {}
        for p in db.get_all_problems():
            groups.setdefault(p["date_solved"], []).append(p)
        order = sorted((d for d in groups if d), reverse=True)
        if None in groups:
            order.append(None)
        if not order:
            ctk.CTkLabel(b, text="No activity yet.", text_color=MUTED).grid(row=1, column=0, pady=40)
            return

        for r, key in enumerate(order, start=1):
            items = groups[key]
            c = card(b)
            c.grid(row=r, column=0, sticky="ew", pady=(14, 0))
            if key:
                d = date.fromisoformat(key)
                lead = friendly_date(key)
                title = (f"{lead} \u00B7 {d:%d %b %Y}" if lead in ("Today", "Yesterday")
                         else f"{d:%A, %d %b %Y}")
                count = f"{len(items)} solved"
            else:
                title, count = "Not solved yet", f"{len(items)} problem(s)"
            head = ctk.CTkFrame(c, fg_color="transparent")
            head.pack(fill="x", padx=16, pady=(12, 4))
            ctk.CTkLabel(head, text=title, font=font(14, True), text_color=TEXT).pack(side="left")
            ctk.CTkLabel(head, text=count, text_color=MUTED, font=font(11)).pack(side="right")
            for p in items:
                rw = ctk.CTkFrame(c, fg_color="transparent")
                rw.pack(fill="x", padx=16, pady=4)
                rw.columnconfigure(1, weight=1)
                ctk.CTkLabel(rw, text=str(p["problem_id"]), width=30, height=22, corner_radius=6,
                             fg_color=ACCENT_SOFT, text_color=ACCENT, font=font(10, True)).grid(
                    row=0, column=0, padx=(0, 10))
                nm = ctk.CTkFrame(rw, fg_color="transparent")
                nm.grid(row=0, column=1, sticky="w")
                ctk.CTkLabel(nm, text=clip(p["problem_name"], 40), text_color=TEXT,
                             font=font(12, True)).pack(side="left")
                ctk.CTkLabel(nm, text=f"  ({clip(p['topic'], 18)})", text_color=MUTED,
                             font=font(11)).pack(side="left")
                chip(rw, p["difficulty"], DIFF_STYLE[p["difficulty"]], 68).grid(
                    row=0, column=2, padx=6)
                chip(rw, STATUS_LABEL[p["status"]], STATUS_STYLE[p["status"]], 72).grid(
                    row=0, column=3)
            ctk.CTkLabel(c, text="").pack(pady=2)


class SettingsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.columnconfigure(0, weight=1)
        header(self, "Settings", "Preferences").grid(
            row=0, column=0, sticky="w", pady=(0, 14))

        box = card(self)
        box.grid(row=1, column=0, sticky="ew")
        box.columnconfigure(0, weight=1)

        ctk.CTkLabel(box, text="Your name", text_color=MUTED, font=font(12)).grid(
            row=0, column=0, sticky="w", padx=20, pady=(18, 4))
        self.name = ctk.CTkEntry(box, placeholder_text="Shown in the greeting", **ENTRY)
        self.name.grid(row=1, column=0, sticky="ew", padx=20)

        ctk.CTkLabel(box, text=f"Database file: {getattr(db, 'DB_NAME', 'algotrack.db')}",
                     text_color=MUTED, font=font(11)).grid(
            row=2, column=0, sticky="w", padx=20, pady=(16, 0))

        primary_button(box, "Save Settings", self.save, width=140).grid(
            row=3, column=0, sticky="w", padx=20, pady=(16, 6))
        self.msg = ctk.CTkLabel(box, text="")
        self.msg.grid(row=4, column=0, sticky="w", padx=20, pady=(0, 16))

    def refresh(self):
        self.name.delete(0, "end")
        self.name.insert(0, self.app.settings["name"])
        self.msg.configure(text="")

    def save(self):
        self.app.settings["name"] = self.name.get().strip()
        ok = save_settings(self.app.settings)
        self.msg.configure(text="Settings saved." if ok else "Could not write settings.json",
                           text_color="#5fd38d" if ok else "#f27a8f")


# ------------------------------------------------------------------
# Main window
# ------------------------------------------------------------------
class App(ctk.CTk):
    NAV = [("Home", "\u2302"), ("Add Problem", "+"), ("All Problems", "\u2261"),
           ("Analytics", "\u25A5"), ("Goals", "\u25CE"), ("Settings", "\u2699")]

    def __init__(self):
        super().__init__(fg_color=BG)
        global FONT_FAMILY
        available = set(tkfont.families(self))
        for name in ("Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Arial"):
            if name in available:
                FONT_FAMILY = name
                break
        try:
            ctk.ThemeManager.theme["CTkFont"]["family"] = FONT_FAMILY
        except Exception:
            pass
        rcParams["font.family"] = [FONT_FAMILY or "DejaVu Sans", "DejaVu Sans"]
        db.create_table()
        self.settings = load_settings()

        self.title("AlgoTrack - DSA Practice Tracker")
        self.geometry("1320x820")
        self.minsize(1180, 720)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # sidebar
        sb = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=NAVY)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.pack_propagate(False)

        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.pack(anchor="w", padx=20, pady=(26, 28))
        bars = ctk.CTkFrame(logo, fg_color="transparent", width=30, height=30)
        bars.pack(side="left")
        for i, (h, c) in enumerate([(14, "#8f9bf0"), (22, ACCENT), (30, "#aab3f5")]):
            ctk.CTkFrame(bars, width=7, height=h, corner_radius=3, fg_color=c).place(
                x=i * 10, y=30 - h)
        t = ctk.CTkFrame(logo, fg_color="transparent")
        t.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(t, text="AlgoTrack", font=font(18, True), text_color="white").pack(anchor="w")
        ctk.CTkLabel(t, text="DSA practice tracker", font=font(10),
                     text_color="#9aa0c8").pack(anchor="w")

        ctk.CTkLabel(sb, text="WORKSPACE", font=font(10, True), text_color="#7d84b3").pack(
            anchor="w", padx=22, pady=(0, 6))
        self.nav = {}
        for name, icon in self.NAV:
            btn = ctk.CTkButton(
                sb, text=f"  {icon}    {name}", anchor="w", height=40, corner_radius=8,
                fg_color="transparent", hover_color=NAVY_HOVER, text_color="white",
                font=font(13), command=lambda n=name: self.show(n))
            btn.pack(fill="x", padx=12, pady=3)
            self.nav[name] = btn

        foot = ctk.CTkFrame(sb, fg_color=NAVY_HOVER, corner_radius=10)
        foot.pack(side="bottom", fill="x", padx=12, pady=16)
        ctk.CTkLabel(foot, text="CURRENT STREAK", font=font(10, True),
                     text_color="#9aa0c8").pack(anchor="w", padx=14, pady=(10, 0))
        self.streak_label = ctk.CTkLabel(foot, text="", font=font(15, True), text_color="white")
        self.streak_label.pack(anchor="w", padx=14, pady=(0, 10))

        # pages
        content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew", padx=32, pady=28)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        self.pages = {
            "Home": HomePage(content, self),
            "Add Problem": AddPage(content, self),
            "All Problems": ProblemsPage(content, self),
            "Analytics": AnalyticsPage(content, self),
            "Goals": GoalsPage(content, self),
            "Activity": ActivityPage(content, self),
            "Settings": SettingsPage(content, self),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_remove()

        self.show("Home")

    def update_streak(self):
        n = db.get_streak()
        self.streak_label.configure(text=f"{n} day{'s' if n != 1 else ''}")

    def show(self, name):
        active = "Home" if name == "Activity" else name
        for n, page in self.pages.items():
            if n == name:
                page.grid()
            else:
                page.grid_remove()
        for n, btn in self.nav.items():
            btn.configure(fg_color=ACCENT if n == active else "transparent")
        self.pages[name].refresh()
        self.update_streak()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    App().mainloop()
