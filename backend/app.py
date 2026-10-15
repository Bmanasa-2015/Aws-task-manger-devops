
import os

import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Used by local development and CI tests when DB_HOST is not set.
tasks = []
next_id = 1


def use_database():
    return bool(os.getenv("DB_HOST"))


def get_db_connection():
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connection_timeout=5,
    )


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "AWS Task Manager API is running",
        "status": "success",
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    if not use_database():
        return jsonify(tasks), 200

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, title, completed FROM tasks ORDER BY id"
        )
        rows = cursor.fetchall()
        result = [
            {
                "id": row["id"],
                "title": row["title"],
                "completed": bool(row["completed"]),
            }
            for row in rows
        ]
        return jsonify(result), 200
    except mysql.connector.Error:
        app.logger.exception("Failed to retrieve tasks from RDS")
        return jsonify({"error": "Database operation failed"}), 503
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


@app.route("/api/tasks", methods=["POST"])
def create_task():
    global next_id

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required"}), 400

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Task title is required"}), 400

    title = title.strip()
    if len(title) > 200:
        return jsonify({
            "error": "Task title must be 200 characters or fewer"
        }), 400

    if use_database():
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (title, completed) VALUES (%s, %s)",
                (title, False),
            )
            task = {
                "id": cursor.lastrowid,
                "title": title,
                "completed": False,
            }
            conn.commit()
            return jsonify(task), 201
        except mysql.connector.Error:
            if conn is not None and conn.is_connected():
                conn.rollback()
            app.logger.exception("Failed to create task in RDS")
            return jsonify({"error": "Database operation failed"}), 503
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None and conn.is_connected():
                conn.close()

    task = {"id": next_id, "title": title, "completed": False}
    next_id += 1
    tasks.append(task)
    return jsonify(task), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required"}), 400

    title = None
    if "title" in data:
        value = data["title"]
        if not isinstance(value, str) or not value.strip():
            return jsonify({"error": "Task title cannot be empty"}), 400
        title = value.strip()
        if len(title) > 200:
            return jsonify({"error": "Task title is too long"}), 400

    if "completed" in data and not isinstance(data["completed"], bool):
        return jsonify({"error": "completed must be true or false"}), 400

    if use_database():
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, title, completed FROM tasks WHERE id = %s",
                (task_id,),
            )
            current = cursor.fetchone()

            if current is None:
                return jsonify({"error": "Task not found"}), 404

            new_title = title if title is not None else current["title"]
            new_completed = (
                data["completed"]
                if "completed" in data
                else bool(current["completed"])
            )

            cursor.execute(
                "UPDATE tasks SET title = %s, completed = %s WHERE id = %s",
                (new_title, new_completed, task_id),
            )
            conn.commit()
            return jsonify({
                "id": task_id,
                "title": new_title,
                "completed": new_completed,
            }), 200
        except mysql.connector.Error:
            if conn is not None and conn.is_connected():
                conn.rollback()
            app.logger.exception("Failed to update task in RDS")
            return jsonify({"error": "Database operation failed"}), 503
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None and conn.is_connected():
                conn.close()

    for task in tasks:
        if task["id"] == task_id:
            if title is not None:
                task["title"] = title
            if "completed" in data:
                task["completed"] = data["completed"]
            return jsonify(task), 200

    return jsonify({"error": "Task not found"}), 404


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    if use_database():
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, title, completed FROM tasks WHERE id = %s",
                (task_id,),
            )
            row = cursor.fetchone()

            if row is None:
                return jsonify({"error": "Task not found"}), 404

            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            conn.commit()
            deleted_task = {
                "id": row["id"],
                "title": row["title"],
                "completed": bool(row["completed"]),
            }
            return jsonify({
                "message": "Task deleted successfully",
                "task": deleted_task,
            }), 200
        except mysql.connector.Error:
            if conn is not None and conn.is_connected():
                conn.rollback()
            app.logger.exception("Failed to delete task from RDS")
            return jsonify({"error": "Database operation failed"}), 503
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None and conn.is_connected():
                conn.close()

    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            deleted_task = tasks.pop(index)
            return jsonify({
                "message": "Task deleted successfully",
                "task": deleted_task,
            }), 200

    return jsonify({"error": "Task not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
