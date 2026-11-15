/**
 * TaskFlow Frontend Application
 * Manages asynchronous task CRUD operations, status toggling, and filtering via Fetch API.
 */

document.addEventListener("DOMContentLoaded", () => {
    // State management
    let currentFilter = "all";
    let tasksCache = [];

    // DOM Elements
    const addTaskForm = document.getElementById("add-task-form");
    const taskTitleInput = document.getElementById("task-title");
    const taskDescInput = document.getElementById("task-desc");
    const taskList = document.getElementById("task-list");
    const emptyState = document.getElementById("empty-state");
    const emptyStateText = document.getElementById("empty-state-text");
    const filterTabs = document.querySelectorAll(".filter-tab");
    const countAll = document.getElementById("count-all");
    const countPending = document.getElementById("count-pending");
    const countCompleted = document.getElementById("count-completed");
    const toast = document.getElementById("toast-message");

    // Edit Modal Elements
    const editModal = document.getElementById("edit-modal");
    const editTaskForm = document.getElementById("edit-task-form");
    const editTaskId = document.getElementById("edit-task-id");
    const editTaskTitle = document.getElementById("edit-task-title");
    const editTaskDesc = document.getElementById("edit-task-desc");
    const closeModalBtn = document.getElementById("close-modal");
    const cancelEditBtn = document.getElementById("cancel-edit-btn");

    /**
     * Display a transient toast notification
     */
    function showToast(message, type = "success") {
        toast.textContent = message;
        toast.className = `toast ${type}`;
        setTimeout(() => {
            toast.className = "toast hidden";
        }, 3500);
    }

    /**
     * Update task counters in the filter bar
     */
    function updateCounters(tasks) {
        const total = tasks.length;
        const pending = tasks.filter(t => t.status === "pending").length;
        const completed = tasks.filter(t => t.status === "completed").length;

        countAll.textContent = total;
        countPending.textContent = pending;
        countCompleted.textContent = completed;
    }

    /**
     * Escape HTML helper to prevent XSS
     */
    function escapeHtml(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Format timestamp to a user-friendly date string
     */
    function formatDate(dateStr) {
        if (!dateStr) return "";
        try {
            const date = new Date(dateStr.replace(" ", "T") + "Z");
            return isNaN(date) ? dateStr : date.toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit"
            });
        } catch {
            return dateStr;
        }
    }

    /**
     * Render the filtered task list to DOM
     */
    function renderTasks() {
        taskList.innerHTML = "";

        const filtered = tasksCache.filter(t => {
            if (currentFilter === "pending") return t.status === "pending";
            if (currentFilter === "completed") return t.status === "completed";
            return true;
        });

        if (filtered.length === 0) {
            emptyState.classList.remove("hidden");
            if (currentFilter === "pending") {
                emptyStateText.textContent = "No pending tasks! Everything is completed.";
            } else if (currentFilter === "completed") {
                emptyStateText.textContent = "No completed tasks yet.";
            } else {
                emptyStateText.textContent = "You're all caught up! Create a new task above.";
            }
        } else {
            emptyState.classList.add("hidden");
            filtered.forEach(task => {
                const isCompleted = task.status === "completed";
                const taskCard = document.createElement("div");
                taskCard.className = `task-item ${isCompleted ? "completed" : ""}`;
                taskCard.id = `task-${task.id}`;

                taskCard.innerHTML = `
                    <div class="task-content-wrapper">
                        <button type="button" class="task-checkbox-btn" title="${isCompleted ? 'Mark as pending' : 'Mark as completed'}" data-id="${task.id}">
                            <span class="check-mark">✓</span>
                        </button>
                        <div class="task-details">
                            <div class="task-header">
                                <span class="task-title">${escapeHtml(task.title)}</span>
                                <span class="status-badge ${task.status}">${task.status}</span>
                            </div>
                            ${task.description ? `<p class="task-desc">${escapeHtml(task.description)}</p>` : ""}
                            <p class="task-meta">Created: ${escapeHtml(formatDate(task.created_at))}</p>
                        </div>
                    </div>
                    <div class="task-actions">
                        <button type="button" class="btn btn-sm btn-edit" data-id="${task.id}" title="Edit task">
                            ✏️ Edit
                        </button>
                        <button type="button" class="btn btn-sm btn-delete" data-id="${task.id}" title="Delete task">
                            🗑️ Delete
                        </button>
                    </div>
                `;

                taskList.appendChild(taskCard);
            });
        }
    }

    /**
     * Fetch all tasks from the API
     */
    async function loadTasks() {
        try {
            const response = await fetch("/api/tasks");
            if (!response.ok) throw new Error("Failed to load tasks");
            const data = await response.json();
            tasksCache = data.tasks || [];
            updateCounters(tasksCache);
            renderTasks();
        } catch (err) {
            showToast(err.message, "error");
        }
    }

    /**
     * Add Task Event Handler
     */
    addTaskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const title = taskTitleInput.value.trim();
        const description = taskDescInput.value.trim();

        if (!title) {
            showToast("Task title is required", "error");
            return;
        }

        try {
            const response = await fetch("/api/tasks", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, description })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to create task");
            }

            tasksCache.unshift(data.task);
            updateCounters(tasksCache);
            renderTasks();
            addTaskForm.reset();
            showToast("Task created successfully!", "success");
        } catch (err) {
            showToast(err.message, "error");
        }
    });

    /**
     * Delegated Click Events for Task List (Toggle, Edit, Delete)
     */
    taskList.addEventListener("click", async (e) => {
        const toggleBtn = e.target.closest(".task-checkbox-btn");
        const editBtn = e.target.closest(".btn-edit");
        const deleteBtn = e.target.closest(".btn-delete");

        // Toggle Status
        if (toggleBtn) {
            const taskId = toggleBtn.dataset.id;
            try {
                const response = await fetch(`/api/tasks/${taskId}/toggle`, {
                    method: "PATCH"
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || "Failed to update status");

                // Update cache
                const idx = tasksCache.findIndex(t => t.id === parseInt(taskId, 10));
                if (idx !== -1) {
                    tasksCache[idx] = data.task;
                    updateCounters(tasksCache);
                    renderTasks();
                }
            } catch (err) {
                showToast(err.message, "error");
            }
        }

        // Open Edit Modal
        if (editBtn) {
            const taskId = parseInt(editBtn.dataset.id, 10);
            const task = tasksCache.find(t => t.id === taskId);
            if (task) {
                editTaskId.value = task.id;
                editTaskTitle.value = task.title;
                editTaskDesc.value = task.description || "";
                editModal.classList.remove("hidden");
                editTaskTitle.focus();
            }
        }

        // Delete Task
        if (deleteBtn) {
            const taskId = deleteBtn.dataset.id;
            if (confirm("Are you sure you want to delete this task?")) {
                try {
                    const response = await fetch(`/api/tasks/${taskId}`, {
                        method: "DELETE"
                    });
                    const data = await response.json();
                    if (!response.ok) throw new Error(data.error || "Failed to delete task");

                    tasksCache = tasksCache.filter(t => t.id !== parseInt(taskId, 10));
                    updateCounters(tasksCache);
                    renderTasks();
                    showToast("Task deleted successfully", "success");
                } catch (err) {
                    showToast(err.message, "error");
                }
            }
        }
    });

    /**
     * Submit Edit Modal
     */
    editTaskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const taskId = editTaskId.value;
        const title = editTaskTitle.value.trim();
        const description = editTaskDesc.value.trim();

        if (!title) {
            showToast("Title cannot be empty", "error");
            return;
        }

        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, description })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Failed to update task");

            const idx = tasksCache.findIndex(t => t.id === parseInt(taskId, 10));
            if (idx !== -1) {
                tasksCache[idx] = data.task;
                updateCounters(tasksCache);
                renderTasks();
            }

            editModal.classList.add("hidden");
            showToast("Task updated successfully", "success");
        } catch (err) {
            showToast(err.message, "error");
        }
    });

    /**
     * Close Modal Handlers
     */
    function closeModal() {
        editModal.classList.add("hidden");
    }

    closeModalBtn.addEventListener("click", closeModal);
    cancelEditBtn.addEventListener("click", closeModal);
    editModal.querySelector(".modal-backdrop").addEventListener("click", closeModal);

    /**
     * Filter Tabs Click Handler
     */
    filterTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            filterTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            currentFilter = tab.dataset.filter;
            renderTasks();
        });
    });

    // Initial load
    loadTasks();
});
