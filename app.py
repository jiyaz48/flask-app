from contextlib import closing
import os
import sqlite3
from flask import Flask, jsonify, render_template, request

# Initialize the Flask application
app = Flask(__name__)

# Default database path configuration
DEFAULT_DB_PATH = os.path.join(app.root_path, "data", "tasks.db")


def get_db_path():
    """
    Retrieves the active database file path.
    Precedence:
    1. app.config["DB_PATH"] (e.g., set by tests)
    2. os.environ.get("DB_PATH") (e.g., set in Docker or host)
    3. DEFAULT_DB_PATH (local data/tasks.db)
    """
    return app.config.get("DB_PATH") or os.environ.get("DB_PATH", DEFAULT_DB_PATH)


def get_db_connection():
    """
    Creates and returns a SQLite database connection with row factory enabled.
    Ensures the parent directory exists before establishing connection.
    """
    db_path = get_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes the database schema if it doesn't already exist.
    Called automatically on application startup.
    """
    with closing(get_db_connection()) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


# Automatically initialize the database on application load
with app.app_context():
    init_db()


# -------------------------------------------------------------------------
# Web Routes
# -------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    """
    Root endpoint:
    Renders the modern, responsive TaskFlow dashboard.
    Preserves the welcome banner for CI/CD test assertions.
    """
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint:
    Used by orchestrators (Docker Compose, Kubernetes, Load Balancers)
    to verify that the application is alive and healthy.
    Kept exactly unchanged.
    """
    return jsonify(
        status="healthy",
        message="Application is running smoothly"
    ), 200


# -------------------------------------------------------------------------
# TaskFlow REST API Endpoints
# -------------------------------------------------------------------------

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    """
    Retrieves tasks with optional filtering:
    - ?filter=all (default)
    - ?filter=pending
    - ?filter=completed
    """
    status_filter = request.args.get("filter", "all").lower().strip()

    with closing(get_db_connection()) as conn:
        if status_filter == "pending":
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY id DESC",
                ("pending",)
            ).fetchall()
        elif status_filter == "completed":
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY id DESC",
                ("completed",)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY id DESC"
            ).fetchall()

        tasks = [dict(row) for row in rows]

    return jsonify(tasks=tasks), 200


@app.route("/api/tasks", methods=["POST"])
def create_task():
    """
    Creates a new task.
    Validates input: title is required and cannot be empty or whitespace only.
    """
    data = request.get_json(silent=True) or request.form.to_dict()

    if not data or not isinstance(data, dict):
        return jsonify(error="Invalid request payload. JSON object expected."), 400

    title = data.get("title", "")
    if not isinstance(title, str) or not title.strip():
        return jsonify(error="Task title is required and cannot be empty."), 400

    title = title.strip()
    if len(title) > 200:
        return jsonify(error="Task title cannot exceed 200 characters."), 400

    description = data.get("description", "")
    if description is None:
        description = ""
    elif not isinstance(description, str):
        description = str(description)
    description = description.strip()

    with closing(get_db_connection()) as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, description, status) VALUES (?, ?, 'pending')",
            (title, description)
        )
        task_id = cursor.lastrowid
        conn.commit()

        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()
        task = dict(row)

    return jsonify(task=task), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    """
    Updates an existing task's title, description, or status.
    """
    data = request.get_json(silent=True) or request.form.to_dict()

    if not data or not isinstance(data, dict):
        return jsonify(error="Invalid request payload. JSON object expected."), 400

    with closing(get_db_connection()) as conn:
        existing = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if not existing:
            return jsonify(error=f"Task with id {task_id} not found."), 404

        title = data.get("title")
        if title is not None:
            if not isinstance(title, str) or not title.strip():
                return jsonify(error="Task title cannot be empty."), 400
            title = title.strip()
            if len(title) > 200:
                return jsonify(error="Task title cannot exceed 200 characters."), 400
        else:
            title = existing["title"]

        description = data.get("description")
        if description is not None:
            description = str(description).strip()
        else:
            description = existing["description"]

        status = data.get("status")
        if status is not None:
            if status not in ("pending", "completed"):
                return jsonify(error="Status must be either 'pending' or 'completed'."), 400
        else:
            status = existing["status"]

        conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, description, status, task_id)
        )
        conn.commit()

        updated = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()
        task = dict(updated)

    return jsonify(task=task), 200


@app.route("/api/tasks/<int:task_id>/toggle", methods=["PATCH"])
def toggle_task(task_id):
    """
    Toggles the status of a task between 'pending' and 'completed'.
    """
    with closing(get_db_connection()) as conn:
        existing = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if not existing:
            return jsonify(error=f"Task with id {task_id} not found."), 404

        new_status = "completed" if existing["status"] == "pending" else "pending"

        conn.execute(
            """
            UPDATE tasks
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_status, task_id)
        )
        conn.commit()

        updated = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()
        task = dict(updated)

    return jsonify(task=task), 200


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """
    Deletes a task by ID.
    """
    with closing(get_db_connection()) as conn:
        existing = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if not existing:
            return jsonify(error=f"Task with id {task_id} not found."), 404

        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

    return jsonify(message="Task deleted successfully"), 200


if __name__ == "__main__":
    # Binding to host '0.0.0.0' allows external connections,
    # which is essential when running inside a Docker container.
    app.run(host="0.0.0.0", port=5000, debug=False)
