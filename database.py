import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta

DB_NAME = "algotrack.db"

VALID_STATUSES = {"Todo", "Solved", "Revision"}
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS problems(
                problem_id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_name TEXT NOT NULL,
                problem_link TEXT,
                topic TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                status TEXT NOT NULL,
                date_solved TEXT,
                pattern TEXT,
                notes TEXT
            )
        """)



def validate_status(status):
    if status not in VALID_STATUSES:
        raise ValueError("Invalid status!")

def validate_difficulty(difficulty):
    if difficulty not in VALID_DIFFICULTIES:
        raise ValueError("Invalid difficulty!")

def validate_problem(problem_name, topic):
    if not problem_name.strip():
        raise ValueError("Problem name cannot be empty!")

    if not topic.strip():
        raise ValueError("Topic cannot be empty!")



def add_problem(problem_name, problem_link, topic,
                difficulty, status, pattern, notes=""):

    validate_problem(problem_name, topic)
    validate_status(status)
    validate_difficulty(difficulty)

    final_date = str(date.today()) if status == "Solved" else None

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO problems(
                problem_name, problem_link, topic,
                difficulty, status, date_solved,
                pattern, notes
            )
            VALUES(?,?,?,?,?,?,?,?)
        """, (
            problem_name.strip(),
            problem_link,
            topic.strip(),
            difficulty,
            status,
            final_date,
            pattern,
            notes
        ))

        return cursor.lastrowid


def get_all_problems():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM problems
            ORDER BY date_solved DESC, problem_id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def update_status(problem_id, new_status):

    validate_status(new_status)

    with get_connection() as conn:

        existing = conn.execute("""
            SELECT status, date_solved
            FROM problems
            WHERE problem_id=?
        """, (problem_id,)).fetchone()

        if existing is None:
            return False

        if new_status == "Solved":
            if existing["status"] == "Solved":
                final_date = existing["date_solved"]
            else:
                final_date = str(date.today())
        else:
            final_date = None

        conn.execute("""
            UPDATE problems
            SET status=?, date_solved=?
            WHERE problem_id=?
        """, (new_status, final_date, problem_id))

        return True


def delete_problem(problem_id):

    with get_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM problems WHERE problem_id=?
        """, (problem_id,))

        return cursor.rowcount > 0


def filter_by_topic(topic):
    return filter_by_problems(topic=topic)

def filter_by_difficulty(difficulty):
    return filter_by_problems(difficulty=difficulty)

def filter_by_status(status):
    return filter_by_problems(status=status)


def filter_by_problems(topic=None, difficulty=None, status=None):

    query = "SELECT * FROM problems WHERE 1=1"
    params = []

    if topic and topic != "All":
        query += " AND topic=?"
        params.append(topic)

    if difficulty and difficulty != "All":
        query += " AND difficulty=?"
        params.append(difficulty)

    if status and status != "All":
        validate_status(status)
        query += " AND status=?"
        params.append(status)

    query += " ORDER BY date_solved DESC, problem_id DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def stats_by_date():

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT date_solved, COUNT(*) AS total
            FROM problems
            WHERE status='Solved'
            AND date_solved IS NOT NULL
            GROUP BY date_solved
            ORDER BY date_solved
        """).fetchall()

        return [(row["date_solved"], row["total"]) for row in rows]


def stats_by_topic():

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT topic, COUNT(*) AS total
            FROM problems
            WHERE status='Solved'
            GROUP BY topic
        """).fetchall()

        return [(row["topic"], row["total"]) for row in rows]


def stats_by_difficulty():

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT difficulty, COUNT(*) AS total
            FROM problems
            WHERE status='Solved'
            GROUP BY difficulty
        """).fetchall()

        return [(row["difficulty"], row["total"]) for row in rows]



def get_last_30_days_data():

    solved = dict(stats_by_date())

    today = date.today()
    start = today - timedelta(days=29)

    full = []

    for i in range(30):
        curr = start + timedelta(days=i)
        date_str = str(curr)

        full.append((
            date_str,
            solved.get(date_str, 0),
            curr.day
        ))

    return full


def get_contribution_calender():

    calendar = []

    for date_str, count, day_num in get_last_30_days_data():

        if count == 0:
            color = "#2d2d2d"
        elif count <= 2:
            color = "#9be9a8"
        elif count <= 4:
            color = "#40c463"
        else:
            color = "#216e39"

        calendar.append({
            "date": date_str,
            "day": day_num,
            "count": count,
            "color": color
        })

    return calendar



def get_dashboard_stats():

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status='Solved' THEN 1 ELSE 0 END) AS solved,
                SUM(CASE WHEN status='Todo' THEN 1 ELSE 0 END) AS todo,
                SUM(CASE WHEN status='Revision' THEN 1 ELSE 0 END) AS revision
            FROM problems
        """).fetchone()

        return {
            "total": rows["total"],
            "solved": rows["solved"] or 0,
            "todo": rows["todo"] or 0,
            "revision": rows["revision"] or 0
        }


def get_yesterday_count():

    yesterday = str(date.today() - timedelta(days=1))

    with get_connection() as conn:
        count = conn.execute("""
            SELECT COUNT(*)
            FROM problems
            WHERE date_solved=? AND status='Solved'
        """, (yesterday,)).fetchone()[0]

    return yesterday, count


def get_todays_count():

    today = str(date.today())

    with get_connection() as conn:
        count = conn.execute("""
            SELECT COUNT(*)
            FROM problems
            WHERE date_solved=? AND status='Solved'
        """, (today,)).fetchone()[0]

    return count

def get_streak():

    dates_data = stats_by_date()

    if not dates_data:
        return 0

    solved_dates = {
        date.fromisoformat(d)
        for d, count in dates_data
        if count > 0
    }

    today = date.today()

    # Allow yesterday's activity to maintain streak
    if today not in solved_dates:
        today -= timedelta(days=1)

    streak = 0

    while today in solved_dates:
        streak += 1
        today -= timedelta(days=1)

    return streak


def get_weekly_progress():

    solved = dict(stats_by_date())

    today = date.today()
    monday = today - timedelta(days=today.weekday())

    week = []

    for i in range(7):
        current = monday + timedelta(days=i)
        week.append(solved.get(str(current), 0))

    return week

def get_weekly_recommendation():

    topics = dict(stats_by_topic())

    if not topics:
        return "Start solving!"

    least_topic = min(topics, key=topics.get)
    most_topic = max(topics, key=topics.get)

    if least_topic == most_topic:
        return "Keep practising different topics!"

    if topics[most_topic] >= topics[least_topic] * 2:
        return (
            f"You practised {most_topic} the most "
            f"and {least_topic} the least. "
            f"Prioritize {least_topic.upper()} next week."
        )

    return f"Good progress! Try more {least_topic} next week."

def get_insights():

    topics = dict(stats_by_topic())

    if not topics:
        return ["Start solving to see insights!"]

    insights = []

    total = sum(topics.values())

    least = min(topics, key=topics.get)
    most = max(topics, key=topics.get)

    insights.append(
        f"Most practiced: {most} ({topics[most]} problems)"
    )

    insights.append(
        f"Least practiced: {least} ({topics[least]} problems)"
    )

    percentage = int(topics[most] / total * 100)

    if percentage > 40:
        insights.append(
            f"{percentage}% of your solved problems "
            f"are from {most}. Try diversifying!"
        )

    return insights


if __name__ == "__main__":

    create_table()

    print("ALGO TRACK BACKEND TEST")

    print("\nDashboard:")
    print(get_dashboard_stats())

    print("\nAll Problems:")
    print(get_all_problems())

    print("\nLast 30 Days:")
    print(get_last_30_days_data())

    print("\nStreak:")
    print(get_streak())

    print("\nWeekly Progress:")
    print(get_weekly_progress())

    print("\nWeekly Recommendation:")
    print(get_weekly_recommendation())

    print("\nInsights:")
    print(get_insights())