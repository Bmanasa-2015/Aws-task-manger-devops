
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Temporary storage for local testing.
# We will connect this API to MySQL/RDS later.
tasks = []
next_id = 1


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "AWS Task Manager API is running",
        "status": "success"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    return jsonify(tasks), 200


@app.route("/api/tasks", methods=["POST"])
def create_task():
    global next_id

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required"}), 400

    title = data.get("title")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Task title is required"}), 400

    if len(title.strip()) > 200:
        return jsonify({"error": "Task title must be 200 characters or fewer"}), 400

    task = {
        "id": next_id,
        "title": title.strip(),
        "completed": False
    }

    next_id += 1
    tasks.append(task)

    return jsonify(task), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON request body is required"}), 400

    for task in tasks:
        if task["id"] == task_id:
            if "title" in data:
                title = data["title"]

                if not isinstance(title, str) or not title.strip():
                    return jsonify({"error": "Task title cannot be empty"}), 400

                if len(title.strip()) > 200:
                    return jsonify({"error": "Task title is too long"}), 400

                task["title"] = title.strip()

            if "completed" in data:
                if not isinstance(data["completed"], bool):
                    return jsonify({"error": "completed must be true or false"}), 400

                task["completed"] = data["completed"]

            return jsonify(task), 200

    return jsonify({"error": "Task not found"}), 404


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            deleted_task = tasks.pop(index)
            return jsonify({
                "message": "Task deleted successfully",
                "task": deleted_task
            }), 200

    return jsonify({"error": "Task not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
