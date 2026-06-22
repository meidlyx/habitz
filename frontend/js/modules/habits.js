async function loadHabits() {
  const habits = await api.getHabits();

  const active = habits.filter((h) => !h.completed_today);
  const done = habits.filter((h) => h.completed_today);

  const listEl = document.getElementById("habits-list");
  const doneEl = document.getElementById("habits-done-list");
  const doneSectionEl = document.getElementById("done-habits-section");

  listEl.innerHTML =
    active.length === 0
      ? '<p style="color:var(--text-secondary);text-align:center;padding:20px;">Все привычки выполнены!</p>'
      : active.map((h) => habitCard(h, false)).join("");

  doneEl.innerHTML = done.map((h) => habitCard(h, true)).join("");
  doneSectionEl.style.display = done.length === 0 ? "none" : "block";

  listEl.querySelectorAll(".habit-checkbox").forEach((cb) => {
    cb.addEventListener("click", async () => {
      cb.style.pointerEvents = "none";
      const id = cb.dataset.id;
      const res = await api.completeHabit(id);
      if (res.success) {
        await api.checkAchievements();
        showXpToast(res.xp_earned, res.leveled_up, res.level);
        loadHabits();
        const profile = await api.getProfile();
        renderStreak(profile.streak);
      } else {
        alert(res.error);
        cb.style.pointerEvents = "auto";
      }
    });
  });

  listEl.querySelectorAll(".habit-delete").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api.deleteHabit(btn.dataset.id);
      loadHabits();
    });
  });
  listEl.querySelectorAll(".card-info").forEach((info, i) => {
    info.style.cursor = "pointer";
    info.addEventListener("click", () => {
      const allHabits = [...active, ...done];
      const habit = allHabits[i];
      if (!habit) return;

      const diffMap = { easy: "Лёгкая", medium: "Средняя", hard: "Сложная" };
      const dayNames = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];

      let freqText = "Ежедневно";
      if (habit.frequency === "weekly" && habit.days_of_week) {
        try {
          const days = JSON.parse(habit.days_of_week);
          freqText = days.map((d) => dayNames[d]).join(", ");
        } catch {}
      }

      document.getElementById("detail-title").textContent = habit.title;
      document.getElementById("detail-difficulty").textContent =
        diffMap[habit.difficulty] || habit.difficulty;
      document.getElementById("detail-xp").textContent =
        `+${habit.xp_reward} XP`;
      document.getElementById("detail-frequency").textContent = freqText;

      const descRow = document.getElementById("detail-desc-row");
      if (habit.description) {
        document.getElementById("detail-desc").textContent = habit.description;
        descRow.style.display = "flex";
      } else {
        descRow.style.display = "none";
      }

      document.getElementById("modal-habit-detail").classList.remove("hidden");
    });
  });
  doneEl.querySelectorAll(".habit-delete").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api.deleteHabit(btn.dataset.id);
      loadHabits();
    });
  });
}

function habitCard(habit, isDone) {
  const freqText = habit.frequency === "daily" ? "ежедневно" : "по дням";
  return `
    <div class="card ${isDone ? "done" : ""}">
      <div class="checkbox ${isDone ? "checked" : ""} habit-checkbox" data-id="${habit.id}"></div>
      <div class="card-info">
        <div class="card-title ${isDone ? "done-text" : ""}">${habit.title}</div>
        <div class="card-meta">+${habit.xp_reward} XP · ${freqText}</div>
      </div>
      <span class="xp-badge">+${habit.xp_reward} XP</span>
      <button class="task-delete habit-delete" data-id="${habit.id}">✕</button>
    </div>
  `;
}

function showXpToast(xp, leveledUp, level) {
  const toast = document.createElement("div");
  toast.className = "xp-toast";
  const levelNames = [
    "",
    "Новичок",
    "Участник",
    "Активный",
    "Упорный",
    "Целеустремлённый",
    "Опытный",
    "Эксперт",
    "Мастер",
    "Элита",
    "Легенда",
  ];
  toast.innerHTML = leveledUp
    ? `🎉 Новый уровень! ${levelNames[level]}`
    : `+${xp} XP`;
  document.body.appendChild(toast);
  setTimeout(() => toast.classList.add("show"), 100);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}

// Обработчики модалки — только один раз
document.getElementById("btn-add-habit").addEventListener("click", () => {
  document.getElementById("modal-habit").classList.remove("hidden");
});

document.getElementById("modal-habit-close").addEventListener("click", () => {
  document.getElementById("modal-habit").classList.add("hidden");
});

document.getElementById("modal-habit").addEventListener("click", (e) => {
  if (e.target === document.getElementById("modal-habit")) {
    document.getElementById("modal-habit").classList.add("hidden");
  }
});
document.getElementById("modal-detail-close").addEventListener("click", () => {
  document.getElementById("modal-habit-detail").classList.add("hidden");
});
document.getElementById("modal-habit-detail").addEventListener("click", (e) => {
  if (e.target === document.getElementById("modal-habit-detail")) {
    document.getElementById("modal-habit-detail").classList.add("hidden");
  }
});

let selectedDiff = "easy";
document.querySelectorAll(".diff-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document
      .querySelectorAll(".diff-btn")
      .forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    selectedDiff = btn.dataset.diff;
  });
});

document.querySelectorAll(".day-btn").forEach((btn) => {
  btn.addEventListener("click", () => btn.classList.toggle("active"));
});

document
  .getElementById("btn-save-habit")
  .addEventListener("click", async () => {
    const title = document.getElementById("habit-title").value.trim();
    const description = document.getElementById("habit-desc").value.trim();
    if (!title) {
      alert("Введите название привычки");
      return;
    }

    const activeDays = [...document.querySelectorAll(".day-btn.active")].map(
      (b) => parseInt(b.dataset.day),
    );
    const frequency = activeDays.length === 7 ? "daily" : "weekly";

    const res = await api.createHabit({
      title,
      description,
      difficulty: selectedDiff,
      frequency,
      days_of_week: activeDays,
    });

    if (res.id) {
      document.getElementById("modal-habit").classList.add("hidden");
      document.getElementById("habit-title").value = "";
      document.getElementById("habit-desc").value = "";
      loadHabits();
    }
  });
