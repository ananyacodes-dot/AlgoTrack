from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "algotrack.db"

VALID_STATUSES = {"Todo", "Solved", "Revision"}
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}
REVISION_INTERVALS = (1, 3, 7, 14, 30)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("AlgoTrack")


class AlgoTrackError(Exception):
    pass


class ValidationError(AlgoTrackError):
    pass


class ProblemNotFoundError(AlgoTrackError):
    pass


class DatabaseError(AlgoTrackError):
    pass


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = None
    try:
        connection = sqlite3.connect(DB_PATH, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        yield connection
        connection.commit()
    except sqlite3.Error as error:
        if connection:
            connection.rollback()
        logger.exception("Database operation failed")
        raise DatabaseError(str(error)) from error
    except Exception:
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()


def initialize_database() -> None:
    try:
        with get_connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")

            connection.execute("""
                CREATE TABLE IF NOT EXISTS problems (
                    problem_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem_name TEXT NOT NULL CHECK(length(trim(problem_name)) > 0),
                    problem_link TEXT NOT NULL DEFAULT '',
                    topic TEXT NOT NULL CHECK(length(trim(topic)) > 0),
                    difficulty TEXT NOT NULL CHECK(difficulty IN ('Easy','Medium','Hard')),
                    status TEXT NOT NULL CHECK(status IN ('Todo','Solved','Revision')),
                    date_solved TEXT,
                    pattern TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    revision_count INTEGER NOT NULL DEFAULT 0,
                    last_reviewed_at TEXT,
                    next_revision_date TEXT
                )
            """)

            existing = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(problems)")
            }
            migrations = {
                "created_at": "TEXT",
                "updated_at": "TEXT",
                "revision_count": "INTEGER NOT NULL DEFAULT 0",
                "last_reviewed_at": "TEXT",
                "next_revision_date": "TEXT",
            }
            for column, definition in migrations.items():
                if column not in existing:
                    connection.execute(
                        f"ALTER TABLE problems ADD COLUMN {column} {definition}"
                    )

            connection.execute("""
                UPDATE problems
                SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
                    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    period TEXT PRIMARY KEY CHECK(period IN ('weekly','monthly')),
                    target INTEGER NOT NULL CHECK(target > 0),
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_problems_status
                ON problems(status)
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_problems_topic
                ON problems(topic)
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_problems_solved
                ON problems(date_solved)
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_problems_revision
                ON problems(next_revision_date)
            """)
    except DatabaseError:
        raise
    except Exception as error:
        logger.exception("Database initialization failed")
        raise DatabaseError(str(error)) from error


def create_table() -> None:
    """Backward-compatible alias for older frontend code."""
    initialize_database()


def _validate_id(problem_id: int) -> int:
    if isinstance(problem_id, bool) or not isinstance(problem_id, int) or problem_id <= 0:
        raise ValidationError("Problem ID must be a positive integer.")
    return problem_id


def _required_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} cannot be empty.")
    return value.strip()


def _optional_text(value: str | None, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be text.")
    return value.strip()


def _validate_link(value: str | None) -> str:
    link = _optional_text(value, "Problem link")
    if not link:
        return ""
    parsed = urlparse(link)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError("Problem link must be a valid HTTP or HTTPS URL.")
    return link


def validate_status(status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValidationError(f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}")


def validate_difficulty(difficulty: str) -> None:
    if difficulty not in VALID_DIFFICULTIES:
        raise ValidationError("Difficulty must be Easy, Medium or Hard.")


def add_problem(
    problem_name: str,
    problem_link: str = "",
    topic: str = "",
    difficulty: str = "Easy",
    status: str = "Todo",
    pattern: str = "",
    notes: str = "",
) -> int:
    problem_name = _required_text(problem_name, "Problem name")
    topic = _required_text(topic, "Topic")
    problem_link = _validate_link(problem_link)
    validate_difficulty(difficulty)
    validate_status(status)
    pattern = _optional_text(pattern, "Pattern")
    notes = _optional_text(notes, "Notes")
    solved_date = str(date.today()) if status == "Solved" else None

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO problems (
                problem_name, problem_link, topic, difficulty, status,
                date_solved, pattern, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            problem_name, problem_link, topic, difficulty, status,
            solved_date, pattern, notes,
        ))
        return int(cursor.lastrowid)


def get_problem_by_id(problem_id: int) -> dict[str, Any] | None:
    problem_id = _validate_id(problem_id)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM problems WHERE problem_id = ?", (problem_id,)
        ).fetchone()
    return dict(row) if row else None


def get_all_problems(
    limit: int | None = None, offset: int = 0
) -> list[dict[str, Any]]:
    if offset < 0 or (limit is not None and limit <= 0):
        raise ValidationError("Invalid pagination values.")
    query = """
        SELECT * FROM problems
        ORDER BY updated_at DESC, problem_id DESC
    """
    params: tuple[Any, ...] = ()
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params = (limit, offset)
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def update_problem(problem_id: int, **changes: Any) -> bool:
    problem_id = _validate_id(problem_id)
    allowed = {
        "problem_name", "problem_link", "topic", "difficulty",
        "status", "pattern", "notes",
    }
    if not changes:
        raise ValidationError("No fields supplied for update.")
    unknown = set(changes) - allowed
    if unknown:
        raise ValidationError(f"Unsupported fields: {', '.join(sorted(unknown))}")

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT * FROM problems WHERE problem_id = ?", (problem_id,)
        ).fetchone()
        if existing is None:
            return False

        values = dict(existing)
        for field, value in changes.items():
            if field == "problem_name":
                value = _required_text(value, "Problem name")
            elif field == "topic":
                value = _required_text(value, "Topic")
            elif field == "problem_link":
                value = _validate_link(value)
            elif field == "difficulty":
                validate_difficulty(value)
            elif field == "status":
                validate_status(value)
            elif field == "pattern":
                value = _optional_text(value, "Pattern")
            elif field == "notes":
                value = _optional_text(value, "Notes")
            values[field] = value

        if values["status"] == "Solved":
            solved_date = (
                existing["date_solved"]
                if existing["status"] == "Solved" and existing["date_solved"]
                else str(date.today())
            )
        else:
            solved_date = None

        connection.execute("""
            UPDATE problems
            SET problem_name=?, problem_link=?, topic=?, difficulty=?,
                status=?, date_solved=?, pattern=?, notes=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE problem_id=?
        """, (
            values["problem_name"], values["problem_link"], values["topic"],
            values["difficulty"], values["status"], solved_date,
            values["pattern"], values["notes"], problem_id,
        ))
    return True


def update_status(problem_id: int, new_status: str) -> bool:
    validate_status(new_status)
    return update_problem(problem_id, status=new_status)


def delete_problem(problem_id: int) -> bool:
    problem_id = _validate_id(problem_id)
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM problems WHERE problem_id = ?", (problem_id,)
        )
    return cursor.rowcount > 0


def filter_by_problems(
    topic: str | None = None,
    difficulty: str | None = None,
    status: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    query = "SELECT * FROM problems WHERE 1=1"
    params: list[Any] = []

    if topic and topic != "All":
        query += " AND topic = ?"
        params.append(topic)
    if difficulty and difficulty != "All":
        validate_difficulty(difficulty)
        query += " AND difficulty = ?"
        params.append(difficulty)
    if status and status != "All":
        validate_status(status)
        query += " AND status = ?"
        params.append(status)
    if search and search.strip():
        query += """
            AND (problem_name LIKE ? OR topic LIKE ?
                 OR pattern LIKE ? OR notes LIKE ?)
        """
        keyword = f"%{search.strip()}%"
        params.extend([keyword] * 4)

    query += " ORDER BY updated_at DESC, problem_id DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def filter_by_topic(topic: str) -> list[dict[str, Any]]:
    return filter_by_problems(topic=topic)


def filter_by_difficulty(difficulty: str) -> list[dict[str, Any]]:
    return filter_by_problems(difficulty=difficulty)


def filter_by_status(status: str) -> list[dict[str, Any]]:
    return filter_by_problems(status=status)


def get_dashboard_stats() -> dict[str, int]:
    with get_connection() as connection:
        row = connection.execute("""
            SELECT COUNT(*) AS total,
                SUM(CASE WHEN status='Solved' THEN 1 ELSE 0 END) AS solved,
                SUM(CASE WHEN status='Todo' THEN 1 ELSE 0 END) AS todo,
                SUM(CASE WHEN status='Revision' THEN 1 ELSE 0 END) AS revision
            FROM problems
        """).fetchone()
    return {
        "total": row["total"] or 0,
        "solved": row["solved"] or 0,
        "todo": row["todo"] or 0,
        "revision": row["revision"] or 0,
    }


def get_todays_count() -> int:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM problems WHERE status='Solved' AND date_solved=?",
            (str(date.today()),),
        ).fetchone()
    return int(row[0])


def get_yesterday_count() -> tuple[str, int]:
    yesterday = date.today() - timedelta(days=1)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM problems WHERE status='Solved' AND date_solved=?",
            (str(yesterday),),
        ).fetchone()
    return str(yesterday), int(row[0])


def stats_by_date() -> list[tuple[str, int]]:
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT date_solved, COUNT(*) AS total
            FROM problems
            WHERE status='Solved' AND date_solved IS NOT NULL
            GROUP BY date_solved ORDER BY date_solved
        """).fetchall()
    return [(row["date_solved"], row["total"]) for row in rows]


def stats_by_topic() -> list[tuple[str, int]]:
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT topic, COUNT(*) AS total
            FROM problems
            WHERE status='Solved'
            GROUP BY topic ORDER BY total DESC, topic ASC
        """).fetchall()
    return [(row["topic"], row["total"]) for row in rows]


def get_topic_performance() -> dict[str, Any]:
    """Compare solved counts with total tracked problems per topic."""
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT topic,
                   COUNT(*) AS tracked,
                   SUM(CASE WHEN status='Solved' THEN 1 ELSE 0 END) AS solved,
                   SUM(CASE WHEN status='Todo' THEN 1 ELSE 0 END) AS todo,
                   SUM(CASE WHEN status='Revision' THEN 1 ELSE 0 END) AS revision
            FROM problems
            GROUP BY topic
            ORDER BY solved DESC, topic ASC
        """).fetchall()

    topics = []
    for row in rows:
        tracked = row["tracked"] or 0
        solved = row["solved"] or 0
        topics.append({
            "topic": row["topic"],
            "tracked": tracked,
            "solved": solved,
            "todo": row["todo"] or 0,
            "revision": row["revision"] or 0,
            "completion_rate": round(solved / tracked * 100, 1) if tracked else 0,
        })

    ranked = sorted(topics, key=lambda item: (item["solved"], item["completion_rate"]))
    return {
        "topics": topics,
        "strongest": max(topics, key=lambda item: item["solved"]) if topics else None,
        "least_practiced": ranked[0] if ranked else None,
    }


def stats_by_difficulty() -> list[tuple[str, int]]:
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT difficulty, COUNT(*) AS total
            FROM problems
            WHERE status='Solved'
            GROUP BY difficulty
            ORDER BY CASE difficulty
                WHEN 'Easy' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Hard' THEN 3 END
        """).fetchall()
    return [(row["difficulty"], row["total"]) for row in rows]


def get_last_30_days_data() -> list[tuple[str, int, int]]:
    today = date.today()
    start = today - timedelta(days=29)
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT date_solved, COUNT(*) AS total
            FROM problems
            WHERE status='Solved' AND date_solved BETWEEN ? AND ?
            GROUP BY date_solved
        """, (str(start), str(today))).fetchall()
    counts = {row["date_solved"]: row["total"] for row in rows}
    return [
        (
            str(day := start + timedelta(days=i)),
            counts.get(str(day), 0),
            day.day,
        )
        for i in range(30)
    ]


def get_contribution_calendar() -> list[dict[str, Any]]:
    result = []
    for day_string, count, day_number in get_last_30_days_data():
        level = 0 if count == 0 else 1 if count <= 2 else 2 if count <= 4 else 3
        result.append({
            "date": day_string,
            "day": day_number,
            "count": count,
            "level": level,
        })
    return result


def get_contribution_calender() -> list[dict[str, Any]]:
    return get_contribution_calendar()


def get_streak() -> int:
    solved_dates = {
        date.fromisoformat(day)
        for day, count in stats_by_date()
        if count > 0
    }
    if not solved_dates:
        return 0
    current = date.today()
    if current not in solved_dates:
        current -= timedelta(days=1)
    streak = 0
    while current in solved_dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


def get_weekly_progress() -> list[int]:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT date_solved, COUNT(*) AS total
            FROM problems
            WHERE status='Solved' AND date_solved BETWEEN ? AND ?
            GROUP BY date_solved
        """, (str(monday), str(monday + timedelta(days=6)))).fetchall()
    counts = {row["date_solved"]: row["total"] for row in rows}
    return [counts.get(str(monday + timedelta(days=i)), 0) for i in range(7)]


def get_weekly_recommendation() -> str:
    topics = dict(stats_by_topic())
    if not topics:
        return "Start solving problems to generate recommendations!"
    least = min(topics, key=topics.get)
    most = max(topics, key=topics.get)
    if least == most:
        return "Keep practising different topics!"
    return (
        f"You have practised {most} the most and {least} the least. "
        f"Consider prioritizing {least} next week."
    )


def get_insights() -> list[str]:
    performance = get_topic_performance()
    topics = performance["topics"]
    if not topics:
        return ["Start solving problems to see performance insights."]

    insights = []
    strongest = performance["strongest"]
    least = performance["least_practiced"]

    if strongest:
        insights.append(
            f"Most solved: {strongest['topic']} ({strongest['solved']} problems)"
        )
    if least:
        insights.append(
            f"Least practised: {least['topic']} ({least['solved']} solved)"
        )

    total = sum(item["solved"] for item in topics)
    if total:
        concentration = max(item["solved"] for item in topics) / total * 100
        if concentration > 40:
            insights.append(
                f"{concentration:.0f}% of your solved problems are concentrated "
                "in one topic. Consider broadening your practice."
            )
    insights.append(f"You have solved {total} problems in total.")
    return insights


def record_revision(problem_id: int) -> bool:
    problem_id = _validate_id(problem_id)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT revision_count FROM problems WHERE problem_id=?",
            (problem_id,),
        ).fetchone()
        if row is None:
            return False

        count = row["revision_count"] + 1
        interval = REVISION_INTERVALS[min(count - 1, len(REVISION_INTERVALS) - 1)]
        next_date = date.today() + timedelta(days=interval)

        connection.execute("""
            UPDATE problems
            SET revision_count=?, last_reviewed_at=?,
                next_revision_date=?, updated_at=CURRENT_TIMESTAMP
            WHERE problem_id=?
        """, (
            count,
            datetime.now().isoformat(timespec="seconds"),
            str(next_date),
            problem_id,
        ))
    return True


def get_due_revisions() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT * FROM problems
            WHERE next_revision_date IS NOT NULL
              AND next_revision_date <= ?
            ORDER BY next_revision_date ASC
        """, (str(date.today()),)).fetchall()
    return [dict(row) for row in rows]


# ============================================================
# WEEKLY AND MONTHLY GOALS
# ============================================================

def set_goal(period: str, target: int) -> bool:
    """Create or replace a weekly/monthly solved-problem target."""
    if period not in {"weekly", "monthly"}:
        raise ValidationError("Goal period must be weekly or monthly.")
    if isinstance(target, bool) or not isinstance(target, int) or target <= 0:
        raise ValidationError("Goal target must be a positive whole number.")

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO goals(period, target, updated_at)
            VALUES(?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(period)
            DO UPDATE SET target=excluded.target,
                          updated_at=CURRENT_TIMESTAMP
        """, (period, target))
    return True


def get_goal_progress(period: str) -> dict[str, Any]:
    """Return target and solved count for the current week or month."""
    if period not in {"weekly", "monthly"}:
        raise ValidationError("Goal period must be weekly or monthly.")

    today = date.today()
    if period == "weekly":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    else:
        start = today.replace(day=1)
        if today.month == 12:
            end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(today.year, today.month + 1, 1) - timedelta(days=1)

    with get_connection() as connection:
        goal = connection.execute(
            "SELECT target FROM goals WHERE period=?", (period,)
        ).fetchone()
        solved = connection.execute("""
            SELECT COUNT(*) FROM problems
            WHERE status='Solved' AND date_solved BETWEEN ? AND ?
        """, (str(start), str(end))).fetchone()[0]

    target = int(goal["target"]) if goal else 0
    completed = int(solved)
    return {
        "period": period,
        "target": target,
        "completed": completed,
        "remaining": max(target - completed, 0) if target else 0,
        "percentage": min(round(completed / target * 100), 100) if target else 0,
        "start_date": str(start),
        "end_date": str(end),
        "is_complete": bool(target and completed >= target),
    }


def get_goals() -> dict[str, dict[str, Any]]:
    return {
        "weekly": get_goal_progress("weekly"),
        "monthly": get_goal_progress("monthly"),
    }


def get_database_info() -> dict[str, Any]:
    with get_connection() as connection:
        total = connection.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        goals = connection.execute("SELECT COUNT(*) FROM goals").fetchone()[0]
    return {
        "database_path": str(DB_PATH),
        "total_problems": int(total),
        "configured_goals": int(goals),
    }


if __name__ == "__main__":
    initialize_database()
    print("AlgoTrack database ready.")
    print(get_database_info())
    print("Dashboard:", get_dashboard_stats())
    print("Goals:", get_goals())

