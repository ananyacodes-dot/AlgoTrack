from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime, timedelta
from typing import Any

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import backend


# ============================================================
# THEME AND CONFIGURATION
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_TITLE = "AlgoTrack"
WINDOW_SIZE = "1440x900"

COLORS = {
    "background": "#0B1120",
    "sidebar": "#101827",
    "surface": "#151F30",
    "surface_2": "#1B2940",
    "border": "#26364F",
    "text": "#F1F5F9",
    "muted": "#94A3B8",
    "blue": "#60A5FA",
    "blue_dark": "#2563EB",
    "green": "#34D399",
    "yellow": "#FBBF24",
    "red": "#FB7185",
    "purple": "#A78BFA",
    "cyan": "#22D3EE",
}

FONT = "Segoe UI"


# ============================================================
# SMALL REUSABLE UI COMPONENTS
# ============================================================

class StatCard(ctk.CTkFrame):
    """Compact dashboard metric card."""

    def __init__(
        self,
        master,
        title: str,
        value: str = "0",
        subtitle: str = "",
        accent: str = COLORS["blue"],
    ):
        super().__init__(
            master,
            fg_color=COLORS["surface"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title.upper(),
            font=ctk.CTkFont(FONT, 11, "bold"),
            text_color=COLORS["muted"],
        ).grid(row=0, column=0, sticky="w", padx=17, pady=(15, 4))

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(FONT, 29, "bold"),
            text_color=accent,
        )
        self.value_label.grid(row=1, column=0, sticky="w", padx=17)

        self.subtitle_label = ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(FONT, 11),
            text_color=COLORS["muted"],
        )
        self.subtitle_label.grid(
            row=2, column=0, sticky="w", padx=17, pady=(2, 15)
        )

    def set_values(self, value: Any, subtitle: str | None = None):
        self.value_label.configure(text=str(value))
        if subtitle is not None:
            self.subtitle_label.configure(text=subtitle)


class SectionHeader(ctk.CTkFrame):
    def __init__(self, master, title: str, description: str = ""):
        super().__init__(master, fg_color="transparent")

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(FONT, 25, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")

        if description:
            ctk.CTkLabel(
                self,
                text=description,
                font=ctk.CTkFont(FONT, 12),
                text_color=COLORS["muted"],
            ).pack(anchor="w", pady=(4, 0))


# ============================================================
# MAIN APPLICATION
# ============================================================

class AlgoTrackApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(1100, 720)
        self.configure(fg_color=COLORS["background"])

        self.current_page = "Dashboard"
        self.problem_rows: list[dict[str, Any]] = []
        self._chart_canvases = []

        try:
            backend.initialize_database()
        except Exception as error:
            messagebox.showerror(
                "Database error",
                f"AlgoTrack could not initialize its database:\n\n{error}",
            )
            self.destroy()
            return

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        self.content = ctk.CTkFrame(
            self,
            fg_color=COLORS["background"],
            corner_radius=0,
        )
        self.content.grid(
            row=0, column=1, sticky="nsew", padx=0, pady=0
        )
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.show_dashboard()

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=235,
            corner_radius=0,
            fg_color=COLORS["sidebar"],
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(8, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(27, 30))

        ctk.CTkLabel(
            brand,
            text="◈",
            font=ctk.CTkFont(FONT, 28, "bold"),
            text_color=COLORS["blue"],
        ).pack(side="left")

        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left", padx=(9, 0))

        ctk.CTkLabel(
            brand_text,
            text="AlgoTrack",
            font=ctk.CTkFont(FONT, 20, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_text,
            text="YOUR DSA WORKSPACE",
            font=ctk.CTkFont(FONT, 9, "bold"),
            text_color=COLORS["muted"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            sidebar,
            text="WORKSPACE",
            font=ctk.CTkFont(FONT, 10, "bold"),
            text_color="#64748B",
        ).pack(anchor="w", padx=22, pady=(0, 9))

        self.nav_buttons = {}

        navigation = [
            ("Dashboard", "⌂", self.show_dashboard),
            ("Problems", "▤", self.show_problems),
            ("Analytics", "◫", self.show_analytics),
            ("Revisions", "↻", self.show_revisions),
            ("Goals", "◎", self.show_goals),
        ]

        for label, symbol, command in navigation:
            button = ctk.CTkButton(
                sidebar,
                text=f"  {symbol}     {label}",
                anchor="w",
                height=43,
                corner_radius=9,
                fg_color="transparent",
                hover_color=COLORS["surface_2"],
                text_color=COLORS["muted"],
                font=ctk.CTkFont(FONT, 13, "bold"),
                command=command,
            )
            button.pack(fill="x", padx=13, pady=3)
            self.nav_buttons[label] = button

        footer = ctk.CTkFrame(
            sidebar,
            fg_color=COLORS["surface"],
            corner_radius=12,
        )
        footer.pack(side="bottom", fill="x", padx=13, pady=17)

        ctk.CTkLabel(
            footer,
            text="BUILD CONSISTENCY",
            font=ctk.CTkFont(FONT, 10, "bold"),
            text_color=COLORS["muted"],
        ).pack(anchor="w", padx=13, pady=(12, 3))

        self.sidebar_streak = ctk.CTkLabel(
            footer,
            text="🔥 0 day streak",
            font=ctk.CTkFont(FONT, 14, "bold"),
            text_color=COLORS["text"],
        )
        self.sidebar_streak.pack(anchor="w", padx=13, pady=(0, 12))

    def _set_active_nav(self, page: str):
        for name, button in self.nav_buttons.items():
            if name == page:
                button.configure(
                    fg_color=COLORS["blue_dark"],
                    text_color="#FFFFFF",
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=COLORS["muted"],
                )

        self.current_page = page

    # --------------------------------------------------------
    # PAGE UTILITIES
    # --------------------------------------------------------

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()
        self._chart_canvases.clear()

    def _page_container(self):
        container = ctk.CTkScrollableFrame(
            self.content,
            fg_color=COLORS["background"],
            corner_radius=0,
        )
        container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        container.grid_columnconfigure(0, weight=1)
        return container

    def _page_topbar(self, parent, page_title: str):
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=30, pady=(24, 12))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text=page_title,
            font=ctk.CTkFont(FONT, 13, "bold"),
            text_color=COLORS["muted"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top,
            text=date.today().strftime("%A, %d %B %Y"),
            font=ctk.CTkFont(FONT, 11),
            text_color=COLORS["muted"],
        ).grid(row=0, column=1, sticky="e")

    def _panel(self, parent, title: str, row: int, column: int,
               columnspan: int = 1):
        panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["surface"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="nsew",
            padx=7,
            pady=7,
        )

        ctk.CTkLabel(
            panel,
            text=title,
            font=ctk.CTkFont(FONT, 14, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=17, pady=(15, 7))

        return panel

    def _show_error(self, title: str, error: Exception):
        messagebox.showerror(title, str(error))

    def _refresh_sidebar(self):
        try:
            self.sidebar_streak.configure(
                text=f"🔥 {backend.get_streak()} day streak"
            )
        except Exception:
            self.sidebar_streak.configure(text="🔥 0 day streak")

    # ========================================================
    # DASHBOARD
    # ========================================================

    def show_dashboard(self):
        self._set_active_nav("Dashboard")
        self._clear_content()

        page = self._page_container()
        self._page_topbar(page, "OVERVIEW")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=1, column=0, sticky="ew", padx=30, pady=(7, 17))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Your progress, in focus.",
            font=ctk.CTkFont(FONT, 27, "bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Track your consistency. Identify gaps. Keep improving.",
            font=ctk.CTkFont(FONT, 12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        ctk.CTkButton(
            header,
            text="+ Add problem",
            width=145,
            height=38,
            corner_radius=9,
            fg_color=COLORS["blue_dark"],
            hover_color="#1D4ED8",
            command=self.open_add_problem,
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        try:
            stats = backend.get_dashboard_stats()
            streak = backend.get_streak()
            today_count = backend.get_todays_count()
        except Exception as error:
            self._show_error("Could not load dashboard", error)
            return

        cards = ctk.CTkFrame(page, fg_color="transparent")
        cards.grid(row=2, column=0, sticky="ew", padx=23, pady=2)

        for column in range(4):
            cards.grid_columnconfigure(column, weight=1, uniform="stat")

        card_data = [
            ("Total problems", stats["total"], "In your tracker", COLORS["blue"]),
            ("Solved", stats["solved"], "Completed problems", COLORS["green"]),
            ("To do", stats["todo"], "Waiting to be solved", COLORS["yellow"]),
            ("Current streak", f"{streak} days", f"{today_count} solved today", COLORS["purple"]),
        ]

        for index, (title, value, subtitle, accent) in enumerate(card_data):
            card = StatCard(cards, title, value, subtitle, accent)
            card.grid(
                row=0, column=index, sticky="ew", padx=7, pady=7
            )

        # Main charts row.
        charts = ctk.CTkFrame(page, fg_color="transparent")
        charts.grid(row=3, column=0, sticky="ew", padx=23, pady=5)
        charts.grid_columnconfigure((0, 1), weight=1, uniform="chart")

        activity_panel = self._panel(
            charts, "30-day solving activity", 0, 0
        )
        topic_panel = self._panel(
            charts, "Solved problems by topic", 0, 1
        )

        self._draw_activity_chart(activity_panel)
        self._draw_topic_chart(topic_panel)

        # Bottom row.
        bottom = ctk.CTkFrame(page, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="ew", padx=23, pady=(3, 20))
        bottom.grid_columnconfigure((0, 1), weight=1, uniform="bottom")

        insight_panel = self._panel(
            bottom, "Smart insights", 0, 0
        )
        recommendation_panel = self._panel(
            bottom, "Next week's focus", 0, 1
        )

        try:
            insights = backend.get_insights()
            recommendation = backend.get_weekly_recommendation()
        except Exception as error:
            insights = [f"Unable to generate insights: {error}"]
            recommendation = "Try again after adding some problems."

        for insight in insights:
            ctk.CTkLabel(
                insight_panel,
                text=f"•  {insight}",
                font=ctk.CTkFont(FONT, 12),
                text_color=COLORS["muted"],
                wraplength=440,
                justify="left",
            ).pack(anchor="w", padx=17, pady=5)

        ctk.CTkLabel(
            recommendation_panel,
            text=recommendation,
            font=ctk.CTkFont(FONT, 13),
            text_color=COLORS["text"],
            wraplength=420,
            justify="left",
        ).pack(anchor="w", padx=17, pady=(7, 18))

        # Contribution calendar and goal progress.
        activity_goals = ctk.CTkFrame(page, fg_color="transparent")
        activity_goals.grid(
            row=5, column=0, sticky="ew", padx=23, pady=(0, 20)
        )
        activity_goals.grid_columnconfigure((0, 1), weight=1, uniform="activity")

        calendar_panel = self._panel(
            activity_goals, "Contribution calendar — last 30 days", 0, 0
        )
        goals_panel = self._panel(
            activity_goals, "Goal progress", 0, 1
        )
        self._render_contribution_calendar(calendar_panel)
        self._render_goal_summary(goals_panel)

        self._refresh_sidebar()

    # ========================================================
    # MATPLOTLIB CHART HELPERS
    # ========================================================

    def _create_figure(self, width=5.2, height=2.5):
        figure = Figure(figsize=(width, height), dpi=95)
        figure.patch.set_facecolor(COLORS["surface"])
        axis = figure.add_subplot(111)
        axis.set_facecolor(COLORS["surface"])

        axis.tick_params(colors=COLORS["muted"], labelsize=8)

        for spine in axis.spines.values():
            spine.set_color(COLORS["border"])

        axis.grid(
            True,
            axis="y",
            color=COLORS["border"],
            alpha=0.55,
            linewidth=0.7,
        )

        return figure, axis

    def _embed_figure(self, panel, figure):
        canvas = FigureCanvasTkAgg(figure, master=panel)
        canvas.draw()
        canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=10, pady=(0, 10)
        )
        self._chart_canvases.append(canvas)

    def _draw_activity_chart(self, panel):
        try:
            data = backend.get_last_30_days_data()
            labels = [
                datetime.strptime(item[0], "%Y-%m-%d").strftime("%d")
                for item in data
            ]
            values = [item[1] for item in data]

            figure, axis = self._create_figure()

            axis.plot(
                labels,
                values,
                color=COLORS["blue"],
                linewidth=2.2,
                marker="o",
                markersize=3.5,
            )
            axis.fill_between(
                range(len(values)),
                values,
                color=COLORS["blue"],
                alpha=0.12,
            )

            axis.set_ylabel("Solved", color=COLORS["muted"], fontsize=8)
            axis.set_xlabel("Day of month", color=COLORS["muted"], fontsize=8)
            axis.set_xticks(range(0, len(labels), 4))
            axis.set_xticklabels(
                [labels[i] for i in range(0, len(labels), 4)]
            )
            axis.set_ylim(bottom=0)

            self._embed_figure(panel, figure)

        except Exception as error:
            ctk.CTkLabel(
                panel,
                text=f"Chart unavailable: {error}",
                text_color=COLORS["muted"],
            ).pack(padx=15, pady=25)

    def _draw_topic_chart(self, panel):
        try:
            data = backend.stats_by_topic()

            figure, axis = self._create_figure()

            if data:
                labels = [item[0] for item in data]
                values = [item[1] for item in data]

                axis.barh(
                    labels[::-1],
                    values[::-1],
                    color=COLORS["purple"],
                    height=0.58,
                )
                axis.set_xlabel("Solved problems", color=COLORS["muted"], fontsize=8)
                axis.set_xlim(left=0)
            else:
                axis.text(
                    0.5, 0.5, "Solve problems to see topic analytics",
                    ha="center", va="center",
                    color=COLORS["muted"],
                    transform=axis.transAxes,
                    fontsize=9,
                )
                axis.set_xticks([])
                axis.set_yticks([])
                axis.grid(False)

            self._embed_figure(panel, figure)

        except Exception as error:
            ctk.CTkLabel(
                panel,
                text=f"Chart unavailable: {error}",
                text_color=COLORS["muted"],
            ).pack(padx=15, pady=25)

    # ========================================================
    # PROBLEMS PAGE
    # ========================================================

    def show_problems(self):
        self._set_active_nav("Problems")
        self._clear_content()

        page = self._page_container()
        self._page_topbar(page, "PROBLEM MANAGEMENT")

        heading = ctk.CTkFrame(page, fg_color="transparent")
        heading.grid(row=1, column=0, sticky="ew", padx=30, pady=(5, 15))
        heading.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            heading,
            text="Problem library",
            font=ctk.CTkFont(FONT, 26, "bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            heading,
            text="+ Add problem",
            width=140,
            height=37,
            fg_color=COLORS["blue_dark"],
            command=self.open_add_problem,
        ).grid(row=0, column=1, sticky="e")

        filters = ctk.CTkFrame(
            page,
            fg_color=COLORS["surface"],
            corner_radius=12,
        )
        filters.grid(row=2, column=0, sticky="ew", padx=30, pady=5)
        filters.grid_columnconfigure(0, weight=1)

        self.search_var = tk.StringVar()
        self.topic_filter = tk.StringVar(value="All")
        self.difficulty_filter = tk.StringVar(value="All")
        self.status_filter = tk.StringVar(value="All")

        self.search_entry = ctk.CTkEntry(
            filters,
            textvariable=self.search_var,
            placeholder_text="Search problem, topic, pattern or notes...",
            height=36,
            width=280,
        )
        self.search_entry.grid(row=0, column=0, padx=12, pady=12, sticky="ew")

        self.search_entry.bind(
            "<KeyRelease>", lambda _event: self._refresh_problem_table()
        )

        ctk.CTkOptionMenu(
            filters,
            variable=self.topic_filter,
            values=["All"] + self._get_topics(),
            width=130,
            command=lambda _value: self._refresh_problem_table(),
        ).grid(row=0, column=1, padx=5, pady=12)

        ctk.CTkOptionMenu(
            filters,
            variable=self.difficulty_filter,
            values=["All", "Easy", "Medium", "Hard"],
            width=125,
            command=lambda _value: self._refresh_problem_table(),
        ).grid(row=0, column=2, padx=5, pady=12)

        ctk.CTkOptionMenu(
            filters,
            variable=self.status_filter,
            values=["All", "Todo", "Solved", "Revision"],
            width=125,
            command=lambda _value: self._refresh_problem_table(),
        ).grid(row=0, column=3, padx=(5, 12), pady=12)

        self.table_panel = ctk.CTkFrame(
            page,
            fg_color=COLORS["surface"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.table_panel.grid(
            row=3, column=0, sticky="nsew", padx=30, pady=(10, 25)
        )
        self.table_panel.grid_columnconfigure(0, weight=1)

        self._refresh_problem_table()

    def _get_topics(self) -> list[str]:
        try:
            # Keep database access inside the backend layer.
            topics = {
                problem["topic"]
                for problem in backend.get_all_problems()
                if problem.get("topic")
            }
            return sorted(topics, key=str.casefold)
        except Exception:
            return []

    def _refresh_problem_table(self):
        """Rebuild the problem table with one consistent column grid."""
        if not hasattr(self, "table_panel"):
            return

        for widget in self.table_panel.winfo_children():
            widget.destroy()

        try:
            self.problem_rows = backend.filter_by_problems(
                topic=self.topic_filter.get(),
                difficulty=self.difficulty_filter.get(),
                status=self.status_filter.get(),
                search=self.search_var.get(),
            )
        except Exception as error:
            self._show_error("Could not load problems", error)
            return

        # These same weights and uniform group are applied to the header and
        # every body row, so each column starts and ends at the same x-position.
        widths = [4.0, 1.25, 1.1, 1.1, 1.4, 1.55]
        headers = ["PROBLEM", "TOPIC", "DIFFICULTY", "STATUS", "SOLVED ON", "ACTIONS"]

        header = ctk.CTkFrame(
            self.table_panel,
            fg_color=COLORS["surface_2"],
            corner_radius=8,
            height=48,
        )
        header.pack(fill="x", padx=12, pady=(12, 6))
        header.pack_propagate(False)

        for column, weight in enumerate(widths):
            header.grid_columnconfigure(
                column, weight=int(weight * 100), uniform="problem_table"
            )
            ctk.CTkLabel(
                header,
                text=headers[column],
                font=ctk.CTkFont(FONT, 10, "bold"),
                text_color=COLORS["muted"],
                anchor="w" if column == 0 else "center",
            ).grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(16, 10) if column == 0 else 8,
                pady=10,
            )

        if not self.problem_rows:
            ctk.CTkLabel(
                self.table_panel,
                text="No problems found. Add your first DSA problem!",
                font=ctk.CTkFont(FONT, 13),
                text_color=COLORS["muted"],
            ).pack(pady=45)
            return

        for index, problem in enumerate(self.problem_rows):
            self._create_problem_row(problem, widths, index)

        ctk.CTkLabel(
            self.table_panel,
            text=f"{len(self.problem_rows)} problem(s)",
            font=ctk.CTkFont(FONT, 10),
            text_color=COLORS["muted"],
        ).pack(anchor="e", padx=18, pady=(8, 13))

    def _create_problem_row(self, problem, widths, row_index=0):
        row = ctk.CTkFrame(
            self.table_panel,
            fg_color="transparent",
            height=48,
        )
        row.pack(fill="x", padx=12, pady=1)
        row.pack_propagate(False)

        for column, weight in enumerate(widths):
            row.grid_columnconfigure(
                column, weight=int(weight * 100), uniform="problem_table"
            )

        name = problem["problem_name"]
        if problem.get("problem_link"):
            name = "↗  " + name

        ctk.CTkLabel(
            row,
            text=name,
            font=ctk.CTkFont(FONT, 12, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=(16, 10), pady=5)

        ctk.CTkLabel(
            row,
            text=problem.get("topic", "—"),
            font=ctk.CTkFont(FONT, 11),
            text_color=COLORS["muted"],
            anchor="center",
        ).grid(row=0, column=1, sticky="ew", padx=8, pady=5)

        difficulty_colors = {
            "Easy": COLORS["green"],
            "Medium": COLORS["yellow"],
            "Hard": COLORS["red"],
        }
        ctk.CTkLabel(
            row,
            text=problem.get("difficulty", "—"),
            font=ctk.CTkFont(FONT, 11, "bold"),
            text_color=difficulty_colors.get(
                problem.get("difficulty"), COLORS["muted"]
            ),
            anchor="center",
        ).grid(row=0, column=2, sticky="ew", padx=8, pady=5)

        status_colors = {
            "Solved": COLORS["green"],
            "Todo": COLORS["yellow"],
            "Revision": COLORS["purple"],
        }
        ctk.CTkLabel(
            row,
            text=problem.get("status", "—"),
            font=ctk.CTkFont(FONT, 11, "bold"),
            text_color=status_colors.get(
                problem.get("status"), COLORS["muted"]
            ),
            anchor="center",
        ).grid(row=0, column=3, sticky="ew", padx=8, pady=5)

        ctk.CTkLabel(
            row,
            text=problem.get("date_solved") or "—",
            font=ctk.CTkFont(FONT, 10),
            text_color=COLORS["muted"],
            anchor="center",
        ).grid(row=0, column=4, sticky="ew", padx=8, pady=5)

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=5, sticky="nsew", padx=4, pady=4)
        actions.grid_columnconfigure((0, 1), weight=0)
        actions.grid_rowconfigure(0, weight=1)

        button_group = ctk.CTkFrame(actions, fg_color="transparent")
        button_group.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkButton(
            button_group,
            text="Edit",
            width=62,
            height=29,
            corner_radius=7,
            fg_color=COLORS["surface_2"],
            hover_color=COLORS["border"],
            command=lambda p=problem: self.open_edit_problem(p),
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            button_group,
            text="×",
            width=30,
            height=29,
            corner_radius=7,
            fg_color="#4A2431",
            hover_color="#7F1D1D",
            command=lambda p=problem: self.confirm_delete(p),
        ).pack(side="left")

        ctk.CTkFrame(
            self.table_panel,
            height=1,
            fg_color=COLORS["border"],
        ).pack(fill="x", padx=16)

    # ========================================================
    # ADD / EDIT PROBLEM DIALOG
    # ========================================================

    def open_add_problem(self):
        self._open_problem_dialog()

    def open_edit_problem(self, problem):
        self._open_problem_dialog(problem)

    def _open_problem_dialog(self, problem=None):
        is_edit = problem is not None

        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit problem" if is_edit else "Add problem")
        dialog.geometry("520x690")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLORS["background"])
        dialog.transient(self)
        dialog.grab_set()

        container = ctk.CTkScrollableFrame(
            dialog,
            fg_color=COLORS["background"],
        )
        container.pack(fill="both", expand=True, padx=20, pady=18)

        ctk.CTkLabel(
            container,
            text="Edit problem" if is_edit else "Add a new problem",
            font=ctk.CTkFont(FONT, 23, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", pady=(5, 3))

        ctk.CTkLabel(
            container,
            text="Keep your practice history organized.",
            font=ctk.CTkFont(FONT, 11),
            text_color=COLORS["muted"],
        ).pack(anchor="w", pady=(0, 17))

        values = {
            "name": problem.get("problem_name", "") if is_edit else "",
            "link": problem.get("problem_link", "") if is_edit else "",
            "topic": problem.get("topic", "") if is_edit else "",
            "difficulty": problem.get("difficulty", "Easy") if is_edit else "Easy",
            "status": problem.get("status", "Todo") if is_edit else "Todo",
            "pattern": problem.get("pattern", "") if is_edit else "",
            "notes": problem.get("notes", "") if is_edit else "",
        }

        def add_label(text):
            ctk.CTkLabel(
                container,
                text=text,
                font=ctk.CTkFont(FONT, 11, "bold"),
                text_color=COLORS["muted"],
            ).pack(anchor="w", pady=(9, 5))

        def add_entry(label, value, placeholder=""):
            add_label(label)
            entry = ctk.CTkEntry(
                container,
                height=38,
                placeholder_text=placeholder,
            )
            entry.pack(fill="x")
            entry.insert(0, value)
            return entry

        name_entry = add_entry(
            "PROBLEM NAME", values["name"], "e.g. Two Sum"
        )
        link_entry = add_entry(
            "PROBLEM LINK", values["link"], "https://leetcode.com/..."
        )
        topic_entry = add_entry(
            "TOPIC", values["topic"], "e.g. Arrays"
        )

        add_label("DIFFICULTY")
        difficulty_menu = ctk.CTkOptionMenu(
            container,
            values=["Easy", "Medium", "Hard"],
            height=36,
        )
        difficulty_menu.pack(fill="x")
        difficulty_menu.set(values["difficulty"])

        add_label("STATUS")
        status_menu = ctk.CTkOptionMenu(
            container,
            values=["Todo", "Solved", "Revision"],
            height=36,
        )
        status_menu.pack(fill="x")
        status_menu.set(values["status"])

        pattern_entry = add_entry(
            "PATTERN", values["pattern"], "e.g. Two pointers"
        )

        add_label("NOTES")
        notes_box = ctk.CTkTextbox(
            container,
            height=105,
            corner_radius=8,
        )
        notes_box.pack(fill="x")
        notes_box.insert("1.0", values["notes"])

        def save():
            try:
                payload = {
                    "problem_name": name_entry.get(),
                    "problem_link": link_entry.get(),
                    "topic": topic_entry.get(),
                    "difficulty": difficulty_menu.get(),
                    "status": status_menu.get(),
                    "pattern": pattern_entry.get(),
                    "notes": notes_box.get("1.0", "end-1c"),
                }

                if is_edit:
                    updated = backend.update_problem(
                        problem["problem_id"],
                        **payload,
                    )
                    if not updated:
                        raise backend.ProblemNotFoundError(
                            "This problem no longer exists."
                        )
                else:
                    backend.add_problem(**payload)

                dialog.destroy()
                self._after_problem_change()

            except Exception as error:
                self._show_error("Could not save problem", error)

        ctk.CTkButton(
            container,
            text="Save changes" if is_edit else "Add problem",
            height=42,
            fg_color=COLORS["blue_dark"],
            hover_color="#1D4ED8",
            command=save,
        ).pack(fill="x", pady=(20, 10))

        ctk.CTkButton(
            container,
            text="Cancel",
            height=36,
            fg_color=COLORS["surface_2"],
            hover_color=COLORS["border"],
            command=dialog.destroy,
        ).pack(fill="x", pady=(0, 10))

    def confirm_delete(self, problem):
        confirmed = messagebox.askyesno(
            "Delete problem",
            f"Are you sure you want to delete "
            f"'{problem['problem_name']}'?",
        )

        if not confirmed:
            return

        try:
            backend.delete_problem(problem["problem_id"])
            self._after_problem_change()
        except Exception as error:
            self._show_error("Could not delete problem", error)

    def _after_problem_change(self):
        self._refresh_sidebar()

        if self.current_page == "Problems":
            self.show_problems()
        elif self.current_page == "Analytics":
            self.show_analytics()
        elif self.current_page == "Revisions":
            self.show_revisions()
        elif self.current_page == "Goals":
            self.show_goals()
        else:
            self.show_dashboard()

    # ========================================================
    # ANALYTICS PAGE
    # ========================================================

    def show_analytics(self):
        self._set_active_nav("Analytics")
        self._clear_content()

        page = self._page_container()
        self._page_topbar(page, "PERFORMANCE ANALYTICS")

        ctk.CTkLabel(
            page,
            text="Understand your practice.",
            font=ctk.CTkFont(FONT, 26, "bold"),
            text_color=COLORS["text"],
        ).grid(row=1, column=0, sticky="w", padx=30, pady=(5, 15))

        chart_grid = ctk.CTkFrame(page, fg_color="transparent")
        chart_grid.grid(row=2, column=0, sticky="ew", padx=23, pady=5)
        chart_grid.grid_columnconfigure((0, 1), weight=1, uniform="analytics")

        activity = self._panel(
            chart_grid, "Daily solving activity — last 30 days", 0, 0
        )
        topics = self._panel(
            chart_grid, "Topic distribution", 0, 1
        )
        difficulty = self._panel(
            chart_grid, "Difficulty distribution", 1, 0
        )
        weekly = self._panel(
            chart_grid, "Weekly progress — Monday to Sunday", 1, 1
        )

        self._draw_activity_chart(activity)
        self._draw_topic_chart(topics)
        self._draw_difficulty_chart(difficulty)
        self._draw_weekly_chart(weekly)

        performance_panel = self._panel(
            page, "Strong and developing topics", 3, 0
        )
        self._render_topic_performance(performance_panel)

        self._refresh_sidebar()

    def _draw_difficulty_chart(self, panel):
        try:
            data = backend.stats_by_difficulty()
            figure, axis = self._create_figure()

            if data:
                labels = [item[0] for item in data]
                values = [item[1] for item in data]
                colors = [
                    COLORS["green"] if label == "Easy"
                    else COLORS["yellow"] if label == "Medium"
                    else COLORS["red"]
                    for label in labels
                ]

                axis.bar(labels, values, color=colors, width=0.55)
                axis.set_ylabel("Solved", color=COLORS["muted"], fontsize=8)
                axis.set_ylim(bottom=0)
            else:
                axis.text(
                    0.5, 0.5, "No solved problems yet",
                    ha="center", va="center",
                    color=COLORS["muted"],
                    transform=axis.transAxes,
                )
                axis.set_xticks([])
                axis.set_yticks([])
                axis.grid(False)

            self._embed_figure(panel, figure)

        except Exception as error:
            ctk.CTkLabel(
                panel, text=str(error), text_color=COLORS["muted"]
            ).pack(pady=20)

    def _draw_weekly_chart(self, panel):
        try:
            values = backend.get_weekly_progress()
            labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

            figure, axis = self._create_figure()

            axis.bar(
                labels,
                values,
                color=COLORS["cyan"],
                width=0.58,
            )
            axis.set_ylabel("Solved", color=COLORS["muted"], fontsize=8)
            axis.set_ylim(bottom=0)

            self._embed_figure(panel, figure)

        except Exception as error:
            ctk.CTkLabel(
                panel, text=str(error), text_color=COLORS["muted"]
            ).pack(pady=20)

    # ========================================================
    # CONTRIBUTION CALENDAR AND GOAL WIDGETS
    # ========================================================

    def _render_contribution_calendar(self, panel):
        try:
            days = backend.get_contribution_calendar()
        except Exception as error:
            ctk.CTkLabel(
                panel, text=f"Calendar unavailable: {error}",
                text_color=COLORS["muted"],
            ).pack(padx=15, pady=20)
            return

        grid = ctk.CTkFrame(panel, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=(7, 8))

        level_colors = [
            "#263247",
            "#174B3A",
            "#16865A",
            "#34D399",
        ]

        for index, item in enumerate(days):
            row, column = divmod(index, 7)
            cell = ctk.CTkFrame(
                grid,
                fg_color=level_colors[item["level"]],
                corner_radius=5,
                width=43,
                height=43,
            )
            cell.grid(row=row, column=column, padx=3, pady=3, sticky="nsew")
            cell.grid_propagate(False)

            ctk.CTkLabel(
                cell,
                text=f'{item["day"]:02d}',
                font=ctk.CTkFont(FONT, 10, "bold"),
                text_color="#F8FAFC",
            ).pack(pady=(5, 0))

            ctk.CTkLabel(
                cell,
                text=str(item["count"]),
                font=ctk.CTkFont(FONT, 9),
                text_color="#E2E8F0",
            ).pack()

        legend = ctk.CTkFrame(panel, fg_color="transparent")
        legend.pack(anchor="e", padx=15, pady=(0, 12))

        ctk.CTkLabel(
            legend, text="Less",
            font=ctk.CTkFont(FONT, 9),
            text_color=COLORS["muted"],
        ).pack(side="left", padx=(0, 5))

        for color in level_colors:
            swatch = ctk.CTkFrame(
                legend, fg_color=color, width=12, height=12, corner_radius=3
            )
            swatch.pack(side="left", padx=2)

        ctk.CTkLabel(
            legend, text="More",
            font=ctk.CTkFont(FONT, 9),
            text_color=COLORS["muted"],
        ).pack(side="left", padx=(5, 0))

    def _render_goal_summary(self, panel):
        try:
            goals = backend.get_goals()
        except Exception as error:
            ctk.CTkLabel(
                panel, text=f"Goals unavailable: {error}",
                text_color=COLORS["muted"],
            ).pack(padx=15, pady=20)
            return

        for period, label in (("weekly", "Weekly"), ("monthly", "Monthly")):
            goal = goals[period]
            block = ctk.CTkFrame(panel, fg_color="transparent")
            block.pack(fill="x", padx=16, pady=(7, 5))

            target_text = (
                f'{goal["completed"]} / {goal["target"]} solved'
                if goal["target"]
                else f'{goal["completed"]} solved · no target set'
            )

            top = ctk.CTkFrame(block, fg_color="transparent")
            top.pack(fill="x")

            ctk.CTkLabel(
                top, text=f"{label} goal",
                font=ctk.CTkFont(FONT, 12, "bold"),
                text_color=COLORS["text"],
            ).pack(side="left")

            ctk.CTkLabel(
                top, text=target_text,
                font=ctk.CTkFont(FONT, 10),
                text_color=COLORS["muted"],
            ).pack(side="right")

            progress = ctk.CTkProgressBar(
                block,
                height=9,
                progress_color=COLORS["green"] if goal["is_complete"] else COLORS["blue"],
                fg_color=COLORS["surface_2"],
            )
            progress.pack(fill="x", pady=(7, 3))
            progress.set(goal["percentage"] / 100 if goal["target"] else 0)

        ctk.CTkButton(
            panel,
            text="Manage goals →",
            height=32,
            fg_color=COLORS["surface_2"],
            hover_color=COLORS["border"],
            command=self.show_goals,
        ).pack(anchor="e", padx=16, pady=(5, 12))

    def _render_topic_performance(self, panel):
        try:
            performance = backend.get_topic_performance()
        except Exception as error:
            ctk.CTkLabel(
                panel, text=f"Topic analysis unavailable: {error}",
                text_color=COLORS["muted"],
            ).pack(padx=16, pady=20)
            return

        strongest = performance["strongest"]
        least = performance["least_practiced"]

        row = ctk.CTkFrame(panel, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(8, 15))
        row.grid_columnconfigure((0, 1), weight=1, uniform="topic-performance")

        strong_card = ctk.CTkFrame(
            row, fg_color=COLORS["surface_2"], corner_radius=10
        )
        strong_card.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        weak_card = ctk.CTkFrame(
            row, fg_color=COLORS["surface_2"], corner_radius=10
        )
        weak_card.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ctk.CTkLabel(
            strong_card, text="MOST SOLVED",
            font=ctk.CTkFont(FONT, 10, "bold"),
            text_color=COLORS["green"],
        ).pack(anchor="w", padx=13, pady=(12, 4))

        ctk.CTkLabel(
            strong_card,
            text=strongest["topic"] if strongest else "Not enough data",
            font=ctk.CTkFont(FONT, 16, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=13)

        ctk.CTkLabel(
            strong_card,
            text=(
                f'{strongest["solved"]} solved · '
                f'{strongest["completion_rate"]:.0f}% completion'
                if strongest else "Add and solve problems to see this."
            ),
            font=ctk.CTkFont(FONT, 10),
            text_color=COLORS["muted"],
        ).pack(anchor="w", padx=13, pady=(4, 12))

        ctk.CTkLabel(
            weak_card, text="NEEDS MORE PRACTICE",
            font=ctk.CTkFont(FONT, 10, "bold"),
            text_color=COLORS["yellow"],
        ).pack(anchor="w", padx=13, pady=(12, 4))

        ctk.CTkLabel(
            weak_card,
            text=least["topic"] if least else "Not enough data",
            font=ctk.CTkFont(FONT, 16, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=13)

        ctk.CTkLabel(
            weak_card,
            text=(
                f'{least["solved"]} solved · {least["tracked"]} tracked'
                if least else "Add and solve problems to see this."
            ),
            font=ctk.CTkFont(FONT, 10),
            text_color=COLORS["muted"],
        ).pack(anchor="w", padx=13, pady=(4, 12))

    # ========================================================
    # GOAL TRACKER
    # ========================================================

    def show_goals(self):
        self._set_active_nav("Goals")
        self._clear_content()

        page = self._page_container()
        self._page_topbar(page, "GOAL TRACKER")

        ctk.CTkLabel(
            page,
            text="Turn consistency into measurable progress.",
            font=ctk.CTkFont(FONT, 25, "bold"),
            text_color=COLORS["text"],
        ).grid(row=1, column=0, sticky="w", padx=30, pady=(5, 5))

        ctk.CTkLabel(
            page,
            text="Set targets for the number of problems you want to solve.",
            font=ctk.CTkFont(FONT, 12),
            text_color=COLORS["muted"],
        ).grid(row=2, column=0, sticky="w", padx=30, pady=(0, 18))

        try:
            goals = backend.get_goals()
        except Exception as error:
            self._show_error("Could not load goals", error)
            goals = {
                "weekly": {"target": 0, "completed": 0, "percentage": 0,
                           "remaining": 0, "is_complete": False},
                "monthly": {"target": 0, "completed": 0, "percentage": 0,
                            "remaining": 0, "is_complete": False},
            }

        cards = ctk.CTkFrame(page, fg_color="transparent")
        cards.grid(row=3, column=0, sticky="ew", padx=23, pady=5)
        cards.grid_columnconfigure((0, 1), weight=1, uniform="goal-cards")

        self._goal_editor(
            cards, 0, "Weekly target", "weekly", goals["weekly"]
        )
        self._goal_editor(
            cards, 1, "Monthly target", "monthly", goals["monthly"]
        )

        info = ctk.CTkFrame(
            page, fg_color=COLORS["surface"], corner_radius=12
        )
        info.grid(row=4, column=0, sticky="ew", padx=30, pady=15)

        ctk.CTkLabel(
            info,
            text="How goal progress is calculated",
            font=ctk.CTkFont(FONT, 14, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=18, pady=(15, 5))

        ctk.CTkLabel(
            info,
            text=(
                "Only problems marked Solved count toward your goals. "
                "Weekly progress runs Monday–Sunday. Monthly progress "
                "runs from the first to the last day of the current month. "
                "Your targets are saved locally in algotrack.db."
            ),
            font=ctk.CTkFont(FONT, 12),
            text_color=COLORS["muted"],
            wraplength=850,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 16))

        self._refresh_sidebar()

    def _goal_editor(self, parent, column, title, period, goal):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["surface"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=0, column=column, sticky="nsew", padx=7, pady=7)

        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(FONT, 16, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=18, pady=(17, 5))

        progress_text = (
            f'{goal["completed"]} of {goal["target"]} problems solved'
            if goal["target"]
            else f'{goal["completed"]} problems solved · target not set'
        )
        ctk.CTkLabel(
            card, text=progress_text,
            font=ctk.CTkFont(FONT, 11),
            text_color=COLORS["muted"],
        ).pack(anchor="w", padx=18, pady=(0, 8))

        progress = ctk.CTkProgressBar(
            card,
            height=12,
            progress_color=COLORS["green"] if goal["is_complete"] else COLORS["blue"],
            fg_color=COLORS["surface_2"],
        )
        progress.pack(fill="x", padx=18, pady=(0, 5))
        progress.set(goal["percentage"] / 100 if goal["target"] else 0)

        percentage_text = (
            f'{goal["percentage"]}% complete'
            if goal["target"] else "Set a target to begin tracking"
        )
        ctk.CTkLabel(
            card, text=percentage_text,
            font=ctk.CTkFont(FONT, 10, "bold"),
            text_color=COLORS["green"] if goal["is_complete"] else COLORS["blue"],
        ).pack(anchor="w", padx=18, pady=(0, 12))

        entry = ctk.CTkEntry(
            card,
            height=38,
            placeholder_text="Enter number of problems",
        )
        entry.pack(fill="x", padx=18, pady=(0, 10))
        if goal["target"]:
            entry.insert(0, str(goal["target"]))

        def save_goal():
            raw = entry.get().strip()
            try:
                target = int(raw)
                backend.set_goal(period, target)
                messagebox.showinfo(
                    "Goal saved",
                    f"Your {period} target is now {target} solved problems.",
                )
                self.show_goals()
            except ValueError:
                messagebox.showwarning(
                    "Invalid target",
                    "Enter a positive whole number, such as 10 or 25.",
                )
            except Exception as error:
                self._show_error("Could not save goal", error)

        ctk.CTkButton(
            card,
            text="Save target",
            height=38,
            fg_color=COLORS["blue_dark"],
            hover_color="#1D4ED8",
            command=save_goal,
        ).pack(fill="x", padx=18, pady=(0, 17))

    # REVISION PAGE


    def show_revisions(self):
        self._set_active_nav("Revisions")
        self._clear_content()

        page = self._page_container()
        self._page_topbar(page, "SPACED REVISION")

        ctk.CTkLabel(
            page,
            text="Review. Remember. Repeat.",
            font=ctk.CTkFont(FONT, 26, "bold"),
            text_color=COLORS["text"],
        ).grid(row=1, column=0, sticky="w", padx=30, pady=(5, 5))

        ctk.CTkLabel(
            page,
            text="Your revision queue is based on the schedule stored for each problem.",
            font=ctk.CTkFont(FONT, 12),
            text_color=COLORS["muted"],
        ).grid(row=2, column=0, sticky="w", padx=30, pady=(0, 15))

        try:
            due = backend.get_due_revisions()
        except Exception as error:
            self._show_error("Could not load revisions", error)
            due = []

        summary = ctk.CTkFrame(
            page,
            fg_color=COLORS["surface"],
            corner_radius=12,
        )
        summary.grid(row=3, column=0, sticky="ew", padx=30, pady=7)

        ctk.CTkLabel(
            summary,
            text=f"{len(due)} problems due for revision",
            font=ctk.CTkFont(FONT, 16, "bold"),
            text_color=COLORS["purple"],
        ).pack(anchor="w", padx=18, pady=16)

        for row_index, problem in enumerate(due, start=4):
            self._revision_card(page, problem, row_index)

        if not due:
            empty = ctk.CTkFrame(
                page,
                fg_color=COLORS["surface"],
                corner_radius=12,
            )
            empty.grid(row=4, column=0, sticky="ew", padx=30, pady=10)

            ctk.CTkLabel(
                empty,
                text="You're all caught up!",
                font=ctk.CTkFont(FONT, 17, "bold"),
                text_color=COLORS["green"],
            ).pack(pady=(24, 5))

            ctk.CTkLabel(
                empty,
                text="When you schedule a revision, it will appear here when due.",
                font=ctk.CTkFont(FONT, 12),
                text_color=COLORS["muted"],
            ).pack(pady=(0, 24))

        self._refresh_sidebar()

    def _revision_card(self, parent, problem, row_index):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["surface"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(
            row=row_index,
            column=0,
            sticky="ew",
            padx=30,
            pady=6,
        )
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=problem["problem_name"],
            font=ctk.CTkFont(FONT, 14, "bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(13, 2))

        ctk.CTkLabel(
            card,
            text=f"{problem['topic']}  •  {problem['difficulty']}  •  "
                 f"Revision {problem.get('revision_count', 0)}",
            font=ctk.CTkFont(FONT, 11),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 13))

        ctk.CTkButton(
            card,
            text="Mark reviewed",
            width=125,
            height=32,
            fg_color=COLORS["blue_dark"],
            command=lambda p=problem: self._mark_reviewed(p),
        ).grid(row=0, column=1, rowspan=2, padx=16)

    def _mark_reviewed(self, problem):
        try:
            success = backend.record_revision(problem["problem_id"])

            if success:
                messagebox.showinfo(
                    "Revision saved",
                    "Revision recorded. Your next review has been scheduled.",
                )

            self.show_revisions()

        except Exception as error:
            self._show_error("Could not record revision", error)


# APPLICATION ENTRY POINT

if __name__ == "__main__":
    app = AlgoTrackApp()
    app.mainloop()
