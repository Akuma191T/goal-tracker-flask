import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DATA_FILE = "data/goals.json"

def load_goals():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_goals(goals):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(goals, file, ensure_ascii=False, indent=4)


def get_next_id(goals):
    if not goals:
        return 1
    return max(goal["id"] for goal in goals) + 1


def get_status(goal):
    if goal["progress"] >= 100:
        return "Completed"

    if goal["deadline"]:
        deadline_date = datetime.strptime(goal["deadline"], "%Y-%m-%d").date()
        if deadline_date < datetime.now().date():
            return "Overdue"

    return "Active"


def validate_goal_form(title, deadline, progress, reminder):
    errors = []

    if not title.strip():
        errors.append("Название цели не может быть пустым.")

    if not reminder.strip():
        errors.append("Поле напоминания не может быть пустым.")

    try:
        progress_value = int(progress)
        if progress_value < 0 or progress_value > 100:
            errors.append("Прогресс должен быть в диапазоне от 0 до 100.")
    except ValueError:
        errors.append("Прогресс должен быть числом.")

    try:
        datetime.strptime(deadline, "%Y-%m-%d")
    except ValueError:
        errors.append("Некорректный формат даты дедлайна.")

    return errors


@app.route("/")
def index():
    goals = load_goals()

    status_filter = request.args.get("status", "All")

    for goal in goals:
        goal["status"] = get_status(goal)

    if status_filter != "All":
        goals = [goal for goal in goals if goal["status"] == status_filter]

    total_goals = len(load_goals())
    completed_goals = len([g for g in load_goals() if get_status(g) == "Completed"])
    overdue_goals = len([g for g in load_goals() if get_status(g) == "Overdue"])
    active_goals = len([g for g in load_goals() if get_status(g) == "Active"])

    average_progress = 0
    all_goals = load_goals()
    if all_goals:
        average_progress = sum(g["progress"] for g in all_goals) / len(all_goals)

    chart_labels = [goal["title"] for goal in all_goals]
    chart_values = [goal["progress"] for goal in all_goals]

    return render_template(
        "index.html",
        goals=goals,
        total_goals=total_goals,
        completed_goals=completed_goals,
        overdue_goals=overdue_goals,
        active_goals=active_goals,
        average_progress=round(average_progress, 1),
        status_filter=status_filter,
        chart_labels=chart_labels,
        chart_values=chart_values,
        errors=[]
    )


@app.route("/add", methods=["POST"])
def add_goal():
    goals = load_goals()

    title = request.form["title"]
    deadline = request.form["deadline"]
    progress = request.form["progress"]
    reminder = request.form["reminder"]

    errors = validate_goal_form(title, deadline, progress, reminder)

    if errors:
        for goal in goals:
            goal["status"] = get_status(goal)

        chart_labels = [goal["title"] for goal in goals]
        chart_values = [goal["progress"] for goal in goals]

        total_goals = len(goals)
        completed_goals = len([g for g in goals if g["status"] == "Completed"])
        overdue_goals = len([g for g in goals if g["status"] == "Overdue"])
        active_goals = len([g for g in goals if g["status"] == "Active"])
        average_progress = 0

        if goals:
            average_progress = sum(g["progress"] for g in goals) / len(goals)

        return render_template(
            "index.html",
            goals=goals,
            total_goals=total_goals,
            completed_goals=completed_goals,
            overdue_goals=overdue_goals,
            active_goals=active_goals,
            average_progress=round(average_progress, 1),
            status_filter="All",
            chart_labels=chart_labels,
            chart_values=chart_values,
            errors=errors
        )

    new_goal = {
        "id": get_next_id(goals),
        "title": title.strip(),
        "deadline": deadline,
        "progress": int(progress),
        "reminder": reminder.strip()
    }

    goals.append(new_goal)
    save_goals(goals)

    return redirect(url_for("index"))


@app.route("/edit/<int:goal_id>", methods=["GET", "POST"])
def edit_goal(goal_id):
    goals = load_goals()
    goal = next((g for g in goals if g["id"] == goal_id), None)

    if goal is None:
        return "Goal not found", 404

    errors = []

    if request.method == "POST":
        title = request.form["title"]
        deadline = request.form["deadline"]
        progress = request.form["progress"]
        reminder = request.form["reminder"]

        errors = validate_goal_form(title, deadline, progress, reminder)

        if not errors:
            goal["title"] = title.strip()
            goal["deadline"] = deadline
            goal["progress"] = int(progress)
            goal["reminder"] = reminder.strip()

            save_goals(goals)
            return redirect(url_for("index"))

    return render_template("edit.html", goal=goal, errors=errors)


@app.route("/delete/<int:goal_id>")
def delete_goal(goal_id):
    goals = load_goals()
    goals = [g for g in goals if g["id"] != goal_id]
    save_goals(goals)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)