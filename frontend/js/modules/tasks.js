async function loadTasks() {
  const tasks = await api.getTasks();
  const today = new Date().toISOString().split("T")[0];

  const active = tasks.filter((t) => !t.is_completed);
  const done = tasks.filter((t) => t.is_completed);

  const activeEl = document.getElementById("tasks-list");
  const doneEl = document.getElementById("tasks-done-list");

  activeEl.innerHTML =
    active.length === 0
      ? '<p style="color:var(--text-secondary);text-align:center;padding:20px;">Нет активных задач</p>'
      : active.map((t) => taskCard(t, false, today)).join("");

  doneEl.innerHTML =
    done.length === 0
      ? '<p style="color:var(--text-secondary);text-align:center;padding:20px;">Нет выполненных задач</p>'
      : done.map((t) => taskCard(t, true, today)).join("");

  activeEl.querySelectorAll(".task-checkbox").forEach((cb) => {
    cb.addEventListener("click", async () => {
      const id = cb.dataset.id;
      const res = await api.completeTask(id);
      if (res.success) {
        await api.checkAchievements();
        showXpToast(res.xp_earned, res.leveled_up, res.level);
        loadTasks();
      } else {
        alert(res.error);
      }
    });
  });

  activeEl.querySelectorAll(".task-delete").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api.deleteTask(btn.dataset.id);
      loadTasks();
    });
  });
  doneEl.querySelectorAll(".task-delete").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api.deleteTask(btn.dataset.id);
      loadTasks();
    });
  });
}

function taskCard(task, isDone, today) {
  const isOverdue =
    task.deadline && task.deadline < today && !task.is_completed;
  return `
    <div class="card ${isDone ? "done" : ""} ${isOverdue ? "overdue" : ""}">
      <div class="checkbox ${isDone ? "checked" : ""} ${isOverdue ? "overdue-check" : ""} task-checkbox" data-id="${task.id}"></div>
      <div class="card-info">
        <div class="card-title ${isDone ? "done-text" : ""} ${isOverdue ? "overdue-title" : ""}">${task.title}</div>
        ${task.deadline ? `<div class="card-meta ${isOverdue ? "overdue-text" : ""}">до ${task.deadline}</div>` : ""}
      </div>
      <span class="xp-badge ${isOverdue ? "overdue-badge" : ""}">+${task.xp_reward} XP</span>
      <button class="task-delete" data-id="${task.id}">✕</button>
    </div>
  `;
}

async function addTask() {
  const input = document.getElementById("task-input");
  const title = input.value.trim();
  if (!title) return;
  const res = await api.createTask({ title, difficulty: "easy" });
  if (res.id) {
    input.value = "";
    loadTasks();
  }
}

document.getElementById("btn-add-task").addEventListener("click", addTask);
document.getElementById("task-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") addTask();
});
