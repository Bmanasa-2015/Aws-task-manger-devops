

const API_URL = "http://15.252.155.23:5000/api/tasks";
const taskForm = document.getElementById("task-form");
const taskInput = document.getElementById("task-input");
const taskList = document.getElementById("task-list");
const message = document.getElementById("message");
const totalCount = document.getElementById("total-count");
const completedCount = document.getElementById("completed-count");

async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }

    return data;
}

async function loadTasks() {
    const tasks = await apiRequest(API_URL);
    taskList.replaceChildren();

    for (const task of tasks) {
        const item = document.createElement("li");
        item.className = "task-item";

        if (task.completed) {
            item.classList.add("completed");
        }

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = task.completed;
        checkbox.setAttribute("aria-label", "Mark task completed");

        checkbox.addEventListener("change", async () => {
            try {
                await apiRequest(`${API_URL}/${task.id}`, {
                    method: "PUT",
                    body: JSON.stringify({
                        completed: checkbox.checked
                    })
                });

                await loadTasks();
                message.textContent = "Task updated.";
            } catch (error) {
                message.textContent = error.message;
            }
        });

        const title = document.createElement("span");
        title.textContent = task.title;

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-button";

        deleteButton.addEventListener("click", async () => {
            try {
                await apiRequest(`${API_URL}/${task.id}`, {
                    method: "DELETE"
                });

                await loadTasks();
                message.textContent = "Task deleted.";
            } catch (error) {
                message.textContent = error.message;
            }
        });

        item.append(checkbox, title, deleteButton);
        taskList.appendChild(item);
    }

    totalCount.textContent = tasks.length;
    completedCount.textContent =
        tasks.filter(task => task.completed).length;
}

taskForm.addEventListener("submit", async event => {
    event.preventDefault();

    const title = taskInput.value.trim();

    if (!title) {
        message.textContent = "Enter a task first.";
        return;
    }

    try {
        await apiRequest(API_URL, {
            method: "POST",
            body: JSON.stringify({ title })
        });

        taskInput.value = "";
        message.textContent = "Task added successfully.";
        await loadTasks();
    } catch (error) {
        message.textContent = `Error: ${error.message}`;
    }
});

loadTasks().catch(error => {
    message.textContent = `Cannot connect to backend: ${error.message}`;
});
