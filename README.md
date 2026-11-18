# AlgoTrack 🚀
### Your Personal DSA Productivity & Progress Tracking System

**Track. Solve. Analyze. Improve.**

AlgoTrack is a desktop-based Data Structures and Algorithms (DSA) tracking application designed to help developers organize their problem-solving journey, monitor consistency, identify weak topics, and improve their coding skills through data-driven insights.

Instead of simply maintaining a list of solved problems, AlgoTrack provides a centralized workspace to manage problems, track revision progress, visualize performance, and build consistent problem-solving habits.

---

## ✨ Features

### 1. 📊 Interactive Dashboard
- Overall DSA progress at a glance.
- Total problems tracked.
- Solved and pending problem counts.
- Current solving streak.
- Daily solving activity.
- Quick access to add new problems.

### 2. 📝 Problem Management
- Add new DSA problems.
- Edit existing problem details.
- Delete problems.
- Store problem names and links.
- Categorize problems by topic.
- Track difficulty: Easy, Medium, Hard.
- Maintain problem-solving patterns and personal notes.
- Track problem status: Todo, Solved, Revision.
- Search and filter problems by topic, difficulty, status, and keywords.

### 3. 📈 Analytics & Visualization
- Visualize daily problem-solving activity.
- Analyze solved problems by topic.
- Track progress over time.
- Identify areas that need more practice.
- View difficulty-based performance statistics.

### 4. 🔥 Streak Tracker
- Track consecutive days of problem-solving.
- Monitor daily solving activity.
- Encourage consistency through progress tracking.

### 5. 🔄 Revision Management
- Organize problems that require revision.
- Maintain a dedicated revision workspace.
- Keep previously solved problems accessible for practice.

### 6. 🎯 Goal Tracking
- Set and monitor DSA practice goals.
- Track progress toward daily targets.
- Monitor goal completion.

### 7. 📅 Contribution Calendar
- GitHub-style activity visualization.
- Displays problem-solving activity over the last 30 days.
- Highlights active and inactive days.

### 8. 🧠 Smart Insights
- Generate insights from problem-solving activity.
- Identify performance patterns.
- Highlight areas requiring improvement.
- Provide recommendations for the next week's focus.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| CustomTkinter | Modern desktop GUI |
| SQLite | Local database management |
| Matplotlib | Data visualization and charts |
| Tkinter | Native desktop functionality |

---

## 🏗️ Project Architecture

AlgoTrack follows a modular architecture that separates the user interface from database operations.

```text
              USER
                |
                v
       +------------------+
       |   CustomTkinter  |
       |   Frontend       |
       +------------------+
                |
                v
       +------------------+
       |   Backend Logic  |
       |   Python         |
       +------------------+
                |
                v
       +------------------+
       |   SQLite Database|
       |   algotrack.db   |
       +------------------+
                |
                v
       +------------------+
       | Data & Statistics|
       +------------------+
                |
                v
       +------------------+
       |    Matplotlib    |
       | Charts & Insights|
       +------------------+
```

### Architecture Principles
- Separation of concerns.
- Modular code organization.
- Persistent local data storage.
- Reusable backend functions.
- Data-driven dashboard rendering.

---

## 📂 Project Structure

```text
AlgoTrack/
│
├── backend.py
│
├── frontend.py
│
├── requirements.txt
│
├── .gitignore
│
└── algotrack.db
```

**Note:** The SQLite database is initialized automatically by the application. The database file is generated locally when the application runs.

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10 or later recommended.
- Git.
- pip.

### Step 1: Clone the repository

```bash
git clone https://github.com/ananyacodes-dot/AlgoTrack.git
```

### Step 2: Navigate to the project directory

```bash
cd AlgoTrack
```

### Step 3: Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**macOS / Linux**
```bash
source venv/bin/activate
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

Alternatively:

```bash
pip install customtkinter matplotlib
```

### Step 5: Run the application

```bash
python frontend.py
```

The application will initialize its SQLite database and launch the AlgoTrack desktop interface.

*If your frontend file has a different name, use that filename in the command.*

---

## 💾 Data Storage

AlgoTrack uses SQLite for persistent local storage.

Problem records include:

- Problem ID
- Problem name
- Problem link
- Topic
- Difficulty
- Status
- Date solved
- Problem-solving pattern
- Personal notes

The database allows users to retain their problem-solving history between application sessions without requiring an external database server.

---

## 🎯 Project Goals

AlgoTrack was built to explore and implement practical software engineering concepts, including:

- Desktop application development.
- Database design and CRUD operations.
- Backend and frontend separation.
- SQL queries and data aggregation.
- Data visualization.
- Application state management.
- Analytical problem-solving.
- Building maintainable software.

---

## 🚀 Future Improvements

Potential enhancements for future versions:

- Spaced repetition-based revision scheduling.
- LeetCode API integration, where supported.
- Cloud synchronization and user authentication.
- Exportable progress reports.
- More advanced performance analytics.
- Customizable daily and weekly goals.
- Packaging and distribution as a standalone desktop application.

---

## 👩‍💻 Author

**Ananya Barik**

Computer Science Undergraduate | Aspiring Software Engineer

GitHub: [@ananyacodes-dot](https://github.com/ananyacodes-dot)

---

## ⭐ Support

If you find AlgoTrack interesting, consider starring the repository!

**AlgoTrack — Consistency is the algorithm behind progress.**
