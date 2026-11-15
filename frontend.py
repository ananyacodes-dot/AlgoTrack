from __future__ import annotations

import importlib
import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime
from typing import Any

import customtkinter as ctk

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False


# ───────────────────────────── DESIGN SYSTEM ──────────────────────────────

APP_NAME = "AlgoTrack"
BACKEND_MODULE = "database"

C = {
    "bg": "#090A0F",
    "sidebar": "#101117",
    "panel": "#12141D",
    "panel_2": "#171A25",
    "panel_3": "#202333",
    "border": "#272A37",
    "green": "#8058F5",
    "green_hover": "#A18AFF",
    "mint": "#C4B6FF",
    "sage": "#9297AA",
    "text": "#F2F3FA",
    "muted": "#9297AA",
    "dim": "#666D82",
    "red": "#ED7184",
    "amber": "#E5B65B",
    "blue": "#27C4E7",
}

FONT = "Segoe UI"
MONO = "Consolas"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


# ───────────────────────────── BACKEND ADAPTER ────────────────────────────

class BackendAdapter:
    """Keep database-specific details in one place."""

    def __init__(self):
        self.db = importlib.import_module(BACKEND_MODULE)
        if hasattr(self.db, "create_table"):
            self.db.create_table()

    def call(self, name: str, *args, default=None, **kwargs):
        fn = getattr(self.db, name, None)
        if not callable(fn):
            return default
        try:
            result = fn(*args, **kwargs)
            return default if result is None and default is not None else result
        except Exception as exc:
            print(f"[AlgoTrack backend] {name}: {exc}")
            return default

    def stats(self):
        return self.call("get_dashboard_stats", default={}) or {}

    def problems(self):
        return self.call("get_all_problems", default=[]) or []

    def streak(self):
        return self.call("get_streak", default=0) or 0

    def today_count(self):
        return self.call("get_todays_count", default=0) or 0

    def weekly(self):
        return self.call("get_weekly_progress", default=[]) or []

    def add(self, name, topic, difficulty, status, link, pattern, notes):
        fn = getattr(self.db, "add_problem", None)
        if not callable(fn):
            raise AttributeError("backend.add_problem() was not found.")
        # database.py signature:
        # add_problem(problem_name, problem_link, topic, difficulty, status, pattern, notes)
        return fn(name, link, topic, difficulty, status, pattern, notes)

    def update_status(self, problem_id, status):
        fn = getattr(self.db, "update_status", None)
        if not callable(fn):
            raise AttributeError("backend.update_status() was not found.")
        return fn(problem_id, status)

    def delete(self, problem_id):
        fn = getattr(self.db, "delete_problem", None)
        if not callable(fn):
            raise AttributeError("backend.delete_problem() was not found.")
        return fn(problem_id)

    def topic_stats(self):
        return self.call("stats_by_topic", default=[]) or []

    def difficulty_stats(self):
        return self.call("stats_by_difficulty", default=[]) or []

    def last_30(self):
        return self.call("get_last_30_days_data", default=[]) or []

    def insights(self):
        return self.call("get_insights", default=[]) or []

    def recommendation(self):
        return self.call("get_weekly_recommendation", default="Keep showing up.") or "Keep showing up."


# ───────────────────────────── SMALL HELPERS ──────────────────────────────

def value(obj: Any, *keys, default=""):
    """Read a field from either a dict or sqlite Row."""
    for key in keys:
        try:
            result = obj[key] if isinstance(obj, dict) else getattr(obj, key)
            if result is not None:
                return result
        except (KeyError, IndexError, TypeError, AttributeError):
            pass
    return default


def safe_int(x, default=0):
    try:
        return int(x or 0)
    except (TypeError, ValueError):
        return default


def normalize_status(s):
    s = str(s or "Todo").strip().lower()
    if s in {"solved", "done", "completed"}:
        return "Solved"
    if s in {"revision", "revise", "review"}:
        return "Revision"
    return "Todo"


def normalize_difficulty(s):
    s = str(s or "Medium").strip().title()
    return s if s in {"Easy", "Medium", "Hard"} else "Medium"


def card(parent, **kwargs):
    return ctk.CTkFrame(
        parent, fg_color=kwargs.get("fg_color", C["panel"]),
        corner_radius=kwargs.get("corner_radius", 16),
        border_width=kwargs.get("border_width", 1),
        border_color=kwargs.get("border_color", C["border"]),
    )


# ───────────────────────────── MAIN APPLICATION ───────────────────────────

class AlgoTrackApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AlgoTrack — Your DSA Operating System")
        self.geometry("1440x900")
        self.minsize(1120, 720)
        self.configure(fg_color=C["bg"])

        try:
            self.db = BackendAdapter()
        except Exception as exc:
            messagebox.showerror(
                "Backend connection failed",
                f"Could not import '{BACKEND_MODULE}'.\n\n{exc}\n\n"
                "Place backend.py beside this file, or change BACKEND_MODULE at the top."
            )
            self.destroy()
            return

        self.current_page = "Dashboard"
        self.all_problems = []
        self.filtered_problems = []
        self.nav_buttons = {}
        self._build_shell()
        self.show_page("Dashboard")
        self.refresh_data()

    def _build_shell(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self, width=238, fg_color=C["sidebar"], corner_radius=0,
            border_width=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(8, weight=1)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=22, pady=(28, 30))
        mark = ctk.CTkFrame(brand, width=42, height=42, corner_radius=13, fg_color="#382A89")
        mark.pack(side="left")
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="A", font=(FONT, 23, "bold"), text_color=C["green"]).place(relx=.5, rely=.48, anchor="center")
        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left", padx=11)
        ctk.CTkLabel(brand_text, text="ALGOTRACK", font=(FONT, 17, "bold"), text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(brand_text, text="DSA WORKSPACE", font=(FONT, 9, "bold"), text_color=C["dim"]).pack(anchor="w", pady=(1, 0))

        ctk.CTkLabel(self.sidebar, text="WORKSPACE", font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=24, pady=(0, 10))

        nav_items = [
            ("Dashboard", "◫"),
            ("Problems", "▤"),
            ("Focus mode", "◎"),
            ("Revision room", "↻"),
            ("Analytics", "⌁"),
        ]
        for label, symbol in nav_items:
            self._nav_item(label, symbol)

        ctk.CTkFrame(self.sidebar, height=1, fg_color=C["border"]).pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(self.sidebar, text="YOUR SYSTEM", font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=24, pady=(0, 10))
        self._nav_item("Settings", "⚙")

        self.sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color=C["panel"], corner_radius=14)
        self.sidebar_footer.pack(side="bottom", fill="x", padx=15, pady=17)
        ctk.CTkLabel(self.sidebar_footer, text="BUILT FOR CONSISTENCY",
                     font=(FONT, 9, "bold"), text_color=C["dim"]).pack(anchor="w", padx=13, pady=(12, 4))
        ctk.CTkLabel(self.sidebar_footer, text="One problem at a time.",
                     font=(FONT, 12), text_color=C["mint"]).pack(anchor="w", padx=13, pady=(0, 12))

        self.main = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.topbar = ctk.CTkFrame(self.main, fg_color=C["bg"], corner_radius=0, height=76)
        self.topbar.grid(row=0, column=0, sticky="ew", padx=32)
        self.topbar.grid_columnconfigure(0, weight=1)
        self.page_title = ctk.CTkLabel(self.topbar, text="Dashboard",
                                       font=(FONT, 23, "bold"), text_color=C["text"])
        self.page_title.grid(row=0, column=0, sticky="w", pady=(22, 0))
        self.topbar_right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        self.topbar_right.grid(row=0, column=1, sticky="e", pady=(20, 0))
        self.date_label = ctk.CTkLabel(
            self.topbar_right, text=datetime.now().strftime("%A, %d %B"),
            font=(FONT, 11), text_color=C["muted"]
        )
        self.date_label.pack(side="left", padx=(0, 15))
        ctk.CTkButton(self.topbar_right, text="+ Add problem", width=132, height=37,
                      corner_radius=10, fg_color=C["green"], hover_color=C["green_hover"],
                      text_color="#FFFFFF", font=(FONT, 12, "bold"),
                      command=lambda: self.show_page("Problems", open_add=True)).pack(side="left")

        self.content = ctk.CTkFrame(self.main, fg_color=C["bg"], corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew", padx=32, pady=(8, 24))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _nav_item(self, label, symbol):
        btn = ctk.CTkButton(
            self.sidebar, text=f"  {symbol}     {label}", anchor="w",
            height=43, corner_radius=10, fg_color="transparent",
            hover_color=C["panel_2"], text_color=C["muted"],
            font=(FONT, 12), command=lambda name=label: self.show_page(name)
        )
        btn.pack(fill="x", padx=13, pady=3)
        self.nav_buttons[label] = btn

    def _set_active_nav(self, page):
        for label, btn in self.nav_buttons.items():
            active = label == page
            btn.configure(
                fg_color="#292044" if active else "transparent",
                text_color=C["green"] if active else C["muted"],
                font=(FONT, 12, "bold" if active else "normal")
            )

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_page(self, page, open_add=False):
        self.current_page = page
        self.page_title.configure(text=page)
        self._set_active_nav(page)
        self._clear_content()
        if page == "Dashboard":
            self._dashboard()
        elif page == "Problems":
            self._problems_page()
            if open_add:
                self._add_problem_dialog()
        elif page == "Focus mode":
            self._focus_page()
        elif page == "Revision room":
            self._revision_page()
        elif page == "Analytics":
            self._analytics_page()
        else:
            self._settings_page()

    def refresh_data(self):
        self.all_problems = list(self.db.problems())
        self._refresh_current()

    def _refresh_current(self):
        page = self.current_page
        self.show_page(page)

    # ───────────────────────────── DASHBOARD ──────────────────────────────

    def _dashboard(self):
        wrap = ctk.CTkScrollableFrame(self.content, fg_color="transparent",
                                      scrollbar_button_color=C["panel_3"])
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stats = self.db.stats()
        solved = safe_int(stats.get("solved", 0))
        total = safe_int(stats.get("total", len(self.all_problems)))
        todo = safe_int(stats.get("todo", 0))
        revision = safe_int(stats.get("revision", 0))
        streak = safe_int(self.db.streak())
        today = safe_int(self.db.today_count())

        hero = ctk.CTkFrame(wrap, fg_color="#171728", corner_radius=20,
                            border_width=1, border_color="#34305C")
        hero.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 18))
        hero.grid_columnconfigure(0, weight=1)
        left = ctk.CTkFrame(hero, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=25, pady=23)
        ctk.CTkLabel(left, text="YOUR DAILY PRACTICE", font=(FONT, 10, "bold"),
                     text_color="#BBAAFF").pack(anchor="w")
        ctk.CTkLabel(left, text="Build the habit. Master the patterns.",
                     font=(FONT, 23, "bold"), text_color=C["text"]).pack(anchor="w", pady=(8, 5))
        ctk.CTkLabel(left, text="Your next breakthrough is one focused session away.",
                     font=(FONT, 12), text_color=C["muted"]).pack(anchor="w")
        right = ctk.CTkFrame(hero, fg_color="#211D3D", corner_radius=15)
        right.grid(row=0, column=1, sticky="e", padx=25, pady=22)
        ctk.CTkLabel(right, text="✦  CURRENT STREAK", font=(FONT, 9, "bold"),
                     text_color="#BBAAFF").pack(padx=18, pady=(13, 2))
        ctk.CTkLabel(right, text=f"{streak} days", font=(FONT, 27, "bold"),
                     text_color=C["green"]).pack(padx=18)
        ctk.CTkLabel(right, text="Consistency compounds.", font=(FONT, 10),
                     text_color=C["sage"]).pack(padx=18, pady=(0, 13))

        metric_data = [
            ("PROBLEMS SOLVED", solved, "Lifetime progress", C["green"]),
            ("TOTAL TRACKED", total, "Your problem library", C["blue"]),
            ("TO DO", todo, "Waiting in your queue", C["amber"]),
            ("FOR REVISION", revision, "Reinforce your learning", "#C5A7E8"),
        ]
        for i, (label, number, sub, accent) in enumerate(metric_data):
            self._metric_card(wrap, i, label, number, sub, accent)

        section = ctk.CTkFrame(wrap, fg_color="transparent")
        section.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(22, 9))
        ctk.CTkLabel(section, text="Your momentum", font=(FONT, 17, "bold"),
                     text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(section, text="A quick look at your consistency",
                     font=(FONT, 10), text_color=C["dim"]).pack(side="left", padx=12, pady=(4, 0))

        progress_card = card(wrap)
        progress_card.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=(0, 8), pady=(0, 12))
        ctk.CTkLabel(progress_card, text="TODAY'S SESSION", font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=18, pady=(17, 8))
        ctk.CTkLabel(progress_card, text=f"{today} problems solved today",
                     font=(FONT, 19, "bold"), text_color=C["text"]).pack(anchor="w", padx=18)
        target = 3
        pct = min(today / target, 1) if target else 0
        bar = ctk.CTkProgressBar(progress_card, height=9, corner_radius=8,
                                 fg_color="#272A37", progress_color=C["green"])
        bar.pack(fill="x", padx=18, pady=(16, 7))
        bar.set(pct)
        ctk.CTkLabel(progress_card, text=f"{today} of {target} daily target  ·  {int(pct*100)}%",
                     font=(FONT, 10), text_color=C["muted"]).pack(anchor="w", padx=18, pady=(0, 17))

        weekly_card = card(wrap)
        weekly_card.grid(row=3, column=2, columnspan=2, sticky="nsew", padx=(8, 0), pady=(0, 12))
        ctk.CTkLabel(weekly_card, text="WEEKLY ACTIVITY", font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=18, pady=(17, 8))
        self._draw_weekly(weekly_card)

        bottom_left = card(wrap)
        bottom_left.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=(0, 8), pady=(0, 12))
        ctk.CTkLabel(bottom_left, text="RECENT PROBLEMS", font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=18, pady=(16, 9))
        recent = sorted(self.all_problems, key=lambda p: str(value(p, "date_solved", default="")), reverse=True)[:5]
        if not recent:
            self._empty(bottom_left, "Your problem journey starts here.", "Add your first problem to begin.")
        else:
            for p in recent:
                self._problem_row(bottom_left, p, compact=True)

        bottom_right = card(wrap)
        bottom_right.grid(row=4, column=2, columnspan=2, sticky="nsew", padx=(8, 0), pady=(0, 12))
        ctk.CTkLabel(bottom_right, text="A NOTE FOR THIS WEEK", font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=18, pady=(16, 9))
        recommendation = self.db.recommendation()
        ctk.CTkLabel(bottom_right, text=str(recommendation), font=(FONT, 14),
                     text_color=C["text"], wraplength=340, justify="left").pack(anchor="w", padx=18, pady=(3, 12))
        ctk.CTkButton(bottom_right, text="Open problem library  →", height=34,
                      fg_color=C["panel_3"], hover_color="#302A50", text_color=C["green"],
                      command=lambda: self.show_page("Problems")).pack(anchor="w", padx=18, pady=(0, 16))

    def _metric_card(self, parent, col, label, number, sub, accent):
        frame = card(parent)
        frame.grid(row=1, column=col, sticky="ew", padx=(0 if col == 0 else 6, 6 if col < 3 else 0), pady=(0, 8))
        ctk.CTkLabel(frame, text=label, font=(FONT, 9, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=15, pady=(14, 5))
        ctk.CTkLabel(frame, text=str(number), font=(FONT, 27, "bold"),
                     text_color=accent).pack(anchor="w", padx=15)
        ctk.CTkLabel(frame, text=sub, font=(FONT, 10),
                     text_color=C["muted"]).pack(anchor="w", padx=15, pady=(1, 14))

    def _draw_weekly(self, parent):
        data = self.db.weekly()
        if not MATPLOTLIB_AVAILABLE:
            ctk.CTkLabel(parent, text=str(data), text_color=C["muted"]).pack(padx=18, pady=15)
            return
        fig = Figure(figsize=(4.5, 1.65), dpi=100, facecolor=C["panel"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["panel"])
        labels, values = self._series(data, ("day", "date", "label"), ("count", "solved", "total", "value"))
        if not values:
            labels, values = ["M", "T", "W", "T", "F", "S", "S"], [0] * 7
        ax.bar(range(len(values)), values, color=C["green"], width=.52, alpha=.9)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels([str(x)[:3] for x in labels], color=C["sage"], fontsize=8)
        ax.tick_params(axis="y", left=False, labelleft=False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="y", color=C["border"], linewidth=.7)
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=(0, 5))

    # ───────────────────────────── PROBLEMS ───────────────────────────────

    def _problems_page(self):
        self.all_problems = list(self.db.problems())
        outer = ctk.CTkFrame(self.content, fg_color="transparent")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        ctk.CTkLabel(header, text="Your personal problem vault",
                     font=(FONT, 14), text_color=C["muted"]).pack(side="left")
        ctk.CTkButton(header, text="+ New problem", width=125, height=35,
                      fg_color=C["green"], hover_color=C["green_hover"],
                      text_color="#FFFFFF", font=(FONT, 11, "bold"),
                      command=self._add_problem_dialog).pack(side="right")

        filters = card(outer)
        filters.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        filters.grid_columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        search = ctk.CTkEntry(filters, textvariable=self.search_var, height=38,
                              placeholder_text="Search problems, topics or patterns...",
                              fg_color=C["bg"], border_color=C["border"],
                              text_color=C["text"])
        search.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        search.bind("<KeyRelease>", lambda _e: self._apply_filters())
        self.status_filter = ctk.CTkOptionMenu(
            filters, values=["All statuses", "Todo", "Solved", "Revision"],
            height=36, width=135, fg_color=C["panel_3"], button_color="#34305C",
            button_hover_color="#463777", command=lambda _v: self._apply_filters()
        )
        self.status_filter.grid(row=0, column=1, padx=(0, 8), pady=12)
        self.difficulty_filter = ctk.CTkOptionMenu(
            filters, values=["All levels", "Easy", "Medium", "Hard"],
            height=36, width=125, fg_color=C["panel_3"], button_color="#34305C",
            button_hover_color="#463777", command=lambda _v: self._apply_filters()
        )
        self.difficulty_filter.grid(row=0, column=2, padx=(0, 12), pady=12)

        self.problem_list = ctk.CTkScrollableFrame(outer, fg_color="transparent",
                                                  scrollbar_button_color=C["panel_3"])
        self.problem_list.grid(row=2, column=0, sticky="nsew")
        self._apply_filters()

    def _apply_filters(self):
        if not hasattr(self, "problem_list") or not self.problem_list.winfo_exists():
            return
        for w in self.problem_list.winfo_children():
            w.destroy()
        query = self.search_var.get().strip().lower()
        sf = self.status_filter.get()
        df = self.difficulty_filter.get()
        rows = []
        for p in self.all_problems:
            name = str(value(p, "problem_name", "name", default=""))
            topic = str(value(p, "topic", default=""))
            pattern = str(value(p, "pattern", default=""))
            status = normalize_status(value(p, "status", default="Todo"))
            difficulty = normalize_difficulty(value(p, "difficulty", default="Medium"))
            if query and query not in f"{name} {topic} {pattern}".lower():
                continue
            if sf != "All statuses" and status != sf:
                continue
            if df != "All levels" and difficulty != df:
                continue
            rows.append(p)
        if not rows:
            self._empty(self.problem_list, "No matching problems.", "Try changing your filters or add a new problem.")
            return
        for p in rows:
            self._problem_row(self.problem_list, p, compact=False, actions=True)

    def _problem_row(self, parent, p, compact=False, actions=False):
        name = str(value(p, "problem_name", "name", default="Untitled problem"))
        topic = str(value(p, "topic", default="General"))
        difficulty = normalize_difficulty(value(p, "difficulty", default="Medium"))
        status = normalize_status(value(p, "status", default="Todo"))
        pid = value(p, "problem_id", "id", default=None)
        frame = ctk.CTkFrame(parent, fg_color=C["panel"], corner_radius=12,
                             border_width=1, border_color=C["border"])
        frame.pack(fill="x", padx=2, pady=4)
        frame.grid_columnconfigure(0, weight=1)
        info = ctk.CTkFrame(frame, fg_color="transparent")
        info.grid(row=0, column=0, sticky="w", padx=14, pady=11)
        ctk.CTkLabel(info, text=name, font=(FONT, 12, "bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(info, text=f"{topic}  ·  {difficulty}  ·  {status}",
                     font=(FONT, 10), text_color=C["muted"]).pack(anchor="w", pady=(3, 0))
        if actions:
            right = ctk.CTkFrame(frame, fg_color="transparent")
            right.grid(row=0, column=1, sticky="e", padx=10)
            next_status = "Solved" if status != "Solved" else "Revision"
            ctk.CTkButton(right, text=next_status, width=82, height=29,
                          fg_color=C["panel_3"], hover_color="#302A50",
                          text_color=C["green"], font=(FONT, 10),
                          command=lambda i=pid, s=next_status: self._change_status(i, s)).pack(side="left", padx=3)
            ctk.CTkButton(right, text="Delete", width=58, height=29,
                          fg_color="#35212A", hover_color="#56303F",
                          text_color=C["red"], font=(FONT, 10),
                          command=lambda i=pid: self._delete_problem(i)).pack(side="left", padx=3)

    def _add_problem_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add a problem")
        dialog.geometry("420x750")
        dialog.resizable(True, True)
        dialog.configure(fg_color=C["bg"])
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Add to your problem vault",
                     font=(FONT, 21, "bold"), text_color=C["text"]).pack(anchor="w", padx=25, pady=(24, 4))
        ctk.CTkLabel(dialog, text="Capture the problem. Learn the pattern.",
                     font=(FONT, 11), text_color=C["muted"]).pack(anchor="w", padx=25, pady=(0, 18))

        fields = {}
        def add_entry(label, placeholder="", default=""):
            ctk.CTkLabel(dialog, text=label.upper(), font=(FONT, 9, "bold"),
                         text_color=C["dim"]).pack(anchor="w", padx=25, pady=(9, 5))
            ent = ctk.CTkEntry(dialog, height=38, placeholder_text=placeholder,
                               fg_color=C["panel"], border_color=C["border"],
                               text_color=C["text"])
            ent.pack(fill="x", padx=25)
            if default:
                ent.insert(0, default)
            fields[label] = ent
            return ent

        add_entry("Problem name", "e.g. Two Sum")
        add_entry("Topic", "e.g. Arrays")
        add_entry("Problem link", "https://...")
        add_entry("Pattern", "e.g. Hash map")
        ctk.CTkLabel(dialog, text="DIFFICULTY", font=(FONT, 9, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=25, pady=(12, 5))
        difficulty = ctk.CTkOptionMenu(dialog, values=["Easy", "Medium", "Hard"],
                                       fg_color=C["panel_2"], button_color="#34305C",
                                       button_hover_color="#463777", height=36)
        difficulty.pack(fill="x", padx=25)
        ctk.CTkLabel(dialog, text="STATUS", font=(FONT, 9, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=25, pady=(12, 5))
        status = ctk.CTkOptionMenu(dialog, values=["Todo", "Solved", "Revision"],
                                   fg_color=C["panel_2"], button_color="#34305C",
                                   button_hover_color="#463777", height=36)
        status.pack(fill="x", padx=25)
        ctk.CTkLabel(dialog, text="NOTES", font=(FONT, 9, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=25, pady=(12, 5))
        notes = ctk.CTkTextbox(dialog, height=75, fg_color=C["panel"],
                               border_width=1, border_color=C["border"],
                               text_color=C["text"], corner_radius=9)
        notes.pack(fill="x", padx=25)

        def save():
            name = fields["Problem name"].get().strip()
            topic = fields["Topic"].get().strip()
            if not name or not topic:
                messagebox.showwarning("Missing information", "Please enter at least a problem name and topic.", parent=dialog)
                return
            try:
                self.db.add(
                    name, topic, difficulty.get(), status.get(),
                    fields["Problem link"].get().strip(),
                    fields["Pattern"].get().strip(), notes.get("1.0", "end").strip()
                )
                dialog.destroy()
                self.refresh_data()
            except Exception as exc:
                messagebox.showerror("Could not save problem", str(exc), parent=dialog)

        ctk.CTkButton(dialog, text="Save problem  →", height=42,
                      fg_color=C["green"], hover_color=C["green_hover"],
                      text_color="#FFFFFF", font=(FONT, 12, "bold"),
                      command=save).pack(fill="x", padx=25, pady=20)

    def _change_status(self, pid, status):
        if pid is None:
            messagebox.showerror("Missing problem ID", "This row has no problem_id/id field.")
            return
        try:
            self.db.update_status(pid, status)
            self.refresh_data()
        except Exception as exc:
            messagebox.showerror("Update failed", str(exc))

    def _delete_problem(self, pid):
        if pid is None:
            messagebox.showerror("Missing problem ID", "This row has no problem_id/id field.")
            return
        if messagebox.askyesno("Delete problem", "Delete this problem from your tracker? This cannot be undone."):
            try:
                self.db.delete(pid)
                self.refresh_data()
            except Exception as exc:
                messagebox.showerror("Delete failed", str(exc))

    # ───────────────────────────── FOCUS MODE ─────────────────────────────

    def _focus_page(self):
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        hero = ctk.CTkFrame(frame, fg_color="#171728", corner_radius=20,
                            border_width=1, border_color="#34305C")
        hero.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(hero, text="FOCUS MODE", font=(FONT, 10, "bold"),
                     text_color="#BBAAFF").pack(pady=(25, 7))
        ctk.CTkLabel(hero, text="One problem. One clear mind.",
                     font=(FONT, 25, "bold"), text_color=C["text"]).pack()
        ctk.CTkLabel(hero, text="Set a small intention and give it your full attention.",
                     font=(FONT, 12), text_color=C["muted"]).pack(pady=(7, 22))

        timer_card = card(frame)
        timer_card.pack(fill="x", pady=8)
        ctk.CTkLabel(timer_card, text="POMODORO SESSION", font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(pady=(22, 4))
        self.timer_label = ctk.CTkLabel(timer_card, text="25:00",
                                        font=(MONO, 54, "bold"), text_color=C["green"])
        self.timer_label.pack(pady=5)
        self.timer_running = False
        self.timer_seconds = 25 * 60
        self.timer_job = None
        controls = ctk.CTkFrame(timer_card, fg_color="transparent")
        controls.pack(pady=(7, 22))
        ctk.CTkButton(controls, text="Start focus", width=120, height=38,
                      fg_color=C["green"], hover_color=C["green_hover"],
                      text_color="#FFFFFF", command=self._timer_start).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="Pause", width=90, height=38,
                      fg_color=C["panel_3"], hover_color="#302A50",
                      text_color=C["text"], command=self._timer_pause).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="Reset", width=90, height=38,
                      fg_color=C["panel_3"], hover_color="#302A50",
                      text_color=C["text"], command=self._timer_reset).pack(side="left", padx=5)

        intention = card(frame)
        intention.pack(fill="x", pady=8)
        ctk.CTkLabel(intention, text="TODAY'S INTENTION", font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=18, pady=(16, 7))
        self.intention_entry = ctk.CTkEntry(intention, height=40,
                                            placeholder_text="e.g. Solve two array problems without looking at hints",
                                            fg_color=C["bg"], border_color=C["border"])
        self.intention_entry.pack(fill="x", padx=18, pady=(0, 17))

    def _timer_start(self):
        if not self.timer_running:
            self.timer_running = True
            self._timer_tick()

    def _timer_pause(self):
        self.timer_running = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None

    def _timer_reset(self):
        self._timer_pause()
        self.timer_seconds = 25 * 60
        if hasattr(self, "timer_label") and self.timer_label.winfo_exists():
            self.timer_label.configure(text="25:00")

    def _timer_tick(self):
        if not self.timer_running:
            return
        if self.timer_seconds <= 0:
            self.timer_running = False
            self.timer_label.configure(text="00:00")
            messagebox.showinfo("Focus session complete", "Nice work. Take a short break.")
            return
        mins, secs = divmod(self.timer_seconds, 60)
        self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
        self.timer_seconds -= 1
        self.timer_job = self.after(1000, self._timer_tick)

    # ───────────────────────────── REVISION ───────────────────────────────

    def _revision_page(self):
        outer = ctk.CTkFrame(self.content, fg_color="transparent")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(outer, text="Turn solved problems into lasting knowledge.",
                     font=(FONT, 13), text_color=C["muted"]).pack(anchor="w", pady=(0, 15))
        rows = [p for p in self.all_problems if normalize_status(value(p, "status")) == "Revision"]
        if not rows:
            panel = card(outer)
            panel.pack(fill="x")
            self._empty(panel, "Your revision queue is clear.", "Mark a problem as Revision when you want to revisit it.")
        else:
            for p in rows:
                self._problem_row(outer, p, actions=True)

    # ───────────────────────────── ANALYTICS ──────────────────────────────

    def _analytics_page(self):
        outer = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(outer, text="Understand your patterns, not just your numbers.",
                     font=(FONT, 13), text_color=C["muted"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        self._chart_card(outer, 1, 0, "TOPIC DISTRIBUTION", self.db.topic_stats(), "topic")
        self._chart_card(outer, 1, 1, "DIFFICULTY BREAKDOWN", self.db.difficulty_stats(), "difficulty")
        self._chart_card(outer, 2, 0, "LAST 30 DAYS", self.db.last_30(), "trend", span=2)

        insight_card = card(outer)
        insight_card.grid(row=3, column=0, columnspan=2, sticky="ew", pady=8)
        ctk.CTkLabel(insight_card, text="LEARNING INSIGHTS", font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=17, pady=(15, 8))
        insights = self.db.insights()
        if not insights:
            ctk.CTkLabel(insight_card, text="Keep logging your practice. Your insights will appear here.",
                         font=(FONT, 11), text_color=C["muted"]).pack(anchor="w", padx=17, pady=(0, 15))
        else:
            for item in insights[:6] if isinstance(insights, (list, tuple)) else [insights]:
                ctk.CTkLabel(insight_card, text=f"•  {item}", font=(FONT, 11),
                             text_color=C["text"], wraplength=800, justify="left").pack(anchor="w", padx=17, pady=3)
            ctk.CTkFrame(insight_card, height=10, fg_color="transparent").pack()

    def _chart_card(self, parent, row, col, title, data, kind, span=1):
        panel = card(parent)
        panel.grid(row=row, column=col, columnspan=span, sticky="nsew",
                   padx=(0, 7) if col == 0 else (7, 0), pady=7)
        ctk.CTkLabel(panel, text=title, font=(FONT, 10, "bold"),
                     text_color=C["dim"]).pack(anchor="w", padx=16, pady=(15, 5))
        if not data:
            ctk.CTkLabel(panel, text="Not enough data yet.",
                         font=(FONT, 11), text_color=C["muted"]).pack(padx=16, pady=35)
            return
        if not MATPLOTLIB_AVAILABLE:
            ctk.CTkLabel(panel, text=str(data), text_color=C["muted"]).pack(padx=16, pady=20)
            return
        labels, vals = self._series(data, ("topic", "difficulty", "date", "day", "label", "name"),
                                    ("count", "solved", "total", "value"))
        if not labels or not vals:
            ctk.CTkLabel(panel, text="Data format not recognized. Check backend return values.",
                         text_color=C["muted"], wraplength=300).pack(padx=16, pady=25)
            return
        width = 5.0 if span == 2 else 3.2
        fig = Figure(figsize=(width, 2.15), dpi=100, facecolor=C["panel"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(C["panel"])
        if kind == "trend":
            ax.plot(range(len(vals)), vals, color=C["green"], linewidth=2.2, marker="o", markersize=4)
            ax.fill_between(range(len(vals)), vals, color=C["green"], alpha=.12)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels([str(x)[-5:] for x in labels], fontsize=7, color=C["sage"], rotation=0)
        else:
            ax.barh(range(len(vals)), vals, color=C["green"], alpha=.85, height=.58)
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels([str(x)[:16] for x in labels], fontsize=8, color=C["sage"])
            ax.invert_yaxis()
            ax.tick_params(axis="x", labelbottom=False, bottom=False)
        ax.tick_params(axis="y", length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="x" if kind != "trend" else "y", color=C["border"], linewidth=.6)
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1.1)
        canvas = FigureCanvasTkAgg(fig, master=panel)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _series(self, data, label_keys, value_keys):
        labels, vals = [], []
        if isinstance(data, dict):
            # Some backends return {label: count}.
            labels = list(data.keys())
            vals = [safe_int(v) for v in data.values()]
            return labels, vals
        if not isinstance(data, (list, tuple)):
            return [], []
        for item in data:
            if isinstance(item, (int, float)):
                labels.append(str(len(labels) + 1))
                vals.append(safe_int(item))
                continue

            # database.py returns tuples:
            # stats_by_topic/difficulty -> (label, count)
            # get_last_30_days_data -> (ISO date, count, day_number)
            if isinstance(item, (list, tuple)):
                if len(item) >= 2:
                    lab, val = item[0], item[1]
                    labels.append(str(lab))
                    vals.append(safe_int(val))
                continue

            lab = value(item, *label_keys, default=None)
            val = value(item, *value_keys, default=None)
            if lab is not None and val is not None:
                labels.append(str(lab))
                vals.append(safe_int(val))
        return labels, vals

    # ───────────────────────────── SETTINGS / EMPTY ───────────────────────

    def _settings_page(self):
        panel = card(self.content)
        panel.grid(row=0, column=0, sticky="new")
        ctk.CTkLabel(panel, text="Workspace preferences", font=(FONT, 17, "bold"),
                     text_color=C["text"]).pack(anchor="w", padx=20, pady=(20, 8))
        ctk.CTkLabel(panel, text="AlgoTrack Midnight Edition · Dark theme",
                     font=(FONT, 12), text_color=C["muted"]).pack(anchor="w", padx=20, pady=(0, 5))
        ctk.CTkLabel(panel, text=f"Database module: {BACKEND_MODULE}",
                     font=(FONT, 11), text_color=C["dim"]).pack(anchor="w", padx=20, pady=(0, 20))
        ctk.CTkButton(panel, text="Refresh data", width=120, height=35,
                      fg_color=C["panel_3"], hover_color="#302A50",
                      text_color=C["green"], command=self.refresh_data).pack(anchor="w", padx=20, pady=(0, 20))

    def _empty(self, parent, title, subtitle):
        ctk.CTkLabel(parent, text="✧", font=(FONT, 28), text_color=C["green"]).pack(pady=(20, 3))
        ctk.CTkLabel(parent, text=title, font=(FONT, 13, "bold"),
                     text_color=C["text"]).pack()
        ctk.CTkLabel(parent, text=subtitle, font=(FONT, 10),
                     text_color=C["muted"]).pack(pady=(4, 18))


if __name__ == "__main__":
    app = AlgoTrackApp()
    if app.winfo_exists():
        app.mainloop()
