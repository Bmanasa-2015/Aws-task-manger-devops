
const taskForm = document.getElementById("task-form");
const taskInput = document.getElementById("task-input");
const taskList = document.getElementById("task-list");
const message = document.getElementById("message");
const totalCount = document.getElementById("total-count");
const completedCount = document.getElementById("completed-count");

let tasks = [];
let nextId = 1;

function renderTasks() {
    taskList.replaceChildren();

    tasks.forEach((task) => {
        const item = document.createElement("li");
        item.className = "task-item";
        if (task.completed) item.classList.add("completed");

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = task.completed;
        checkbox.setAttribute("aria-label", "Mark task completed");

        checkbox.addEventListener("change", () => {
            task.completed = checkbox.checked;
            renderTasks();
        });

        const label = document.createElement("span");
        label.textContent = task.title;

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-button";

        deleteButton.addEventListener("click", () => {
            tasks = tasks.filter((t) => t.id !== task.id);
            renderTasks();
            message.textContent = "Task deleted.";
        });

        item.append(checkbox, label, deleteButton);
        taskList.appendChild(item);
    });

    totalCount.textContent = tasks.length;
    completedCount.textContent =
        tasks.filter((task) => task.completed).length;
}

taskForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const title = taskInput.value.trim();

    if (!title) {
        message.textContent = "Please enter a task.";
        return;
    }

    tasks.push({
        id: nextId++,
        title: title,
        completed: false
    });

    taskInput.value = "";
    message.textContent = "Task added successfully.";
    renderTasks();
});

renderTasks();
