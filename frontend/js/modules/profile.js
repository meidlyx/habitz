async function loadProfile() {
  const profile = await api.getProfile();
  const stats = await api.getStats();
  const achievements = await api.getAchievements();

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
  const levelColors = [
    "",
    "#9ca3af",
    "#4ade80",
    "#38bdf8",
    "#60a5fa",
    "#a78bfa",
    "#f472b6",
    "#fb923c",
    "#f87171",
    "#fbbf24",
    "#f0c040",
  ];
  const levelGradients = [
    "",
    "#1f2937, #000000",
    "#052e16, #000000",
    "#0c2340, #000000",
    "#1e2d6b, #000000",
    "#2e1065, #000000",
    "#4a0d2a, #000000",
    "#3d1a05, #000000",
    "#3d0a0a, #000000",
    "#3d1f05, #000000",
    "#1e0f40, #000000",
  ];

  const el = document.getElementById("profile-content");

  el.innerHTML = `
    <!-- Аватар и имя -->
    <div class="profile-avatar-block">
      <div class="profile-avatar-wrap">
        <img src="${profile.avatar_url || localStorage.getItem("avatar") || "assets/default-avatar.png"}" class="profile-avatar" alt="avatar">
      </div>
      <div class="profile-name-block">
        <h2 class="profile-name">${profile.name}${profile.level === 10 ? ' <span class="legend-badge">★</span>' : ""}</h2>
      </div>
    </div>

    <!-- Уровень -->
    <div class="level-card" style="background: linear-gradient(135deg, ${levelGradients[profile.level]});">
      <div class="level-card-top">
        <span class="level-name" style="color:${levelColors[profile.level]}">${levelNames[profile.level]}</span>
        <button class="all-levels-btn" id="btn-all-levels">Все уровни</button>
      </div>
      <div class="level-xp-text">${profile.xp} / ${profile.next_level_xp || "—"} XP</div>
      <div class="level-bar-track">
        <div class="level-bar-fill" style="width:${profile.next_level_xp ? Math.min(((profile.xp - profile.current_level_xp) / (profile.next_level_xp - profile.current_level_xp)) * 100, 100) : 100}%; background:${levelColors[profile.level]};"></div>
      </div>
    </div>

    <!-- Инвентарь -->
    <h3 class="section-title">Инвентарь</h3>
    <div class="inventory-row">
      <div class="inventory-card freeze-card">
        <div class="inventory-info">
          <span class="inventory-count">${stats.freeze_count}</span>
          <span class="inventory-label">Заморозка</span>
        </div>
        <button class="inventory-btn freeze-btn" id="btn-use-freeze">Использовать</button>
      </div>
      <div class="inventory-card boost-card">
        <div class="inventory-info">
          <span class="inventory-count boost-count" id="boost-count">${profile.boost_count ?? 0}</span>
          <span class="inventory-label">Кото-бонус</span>
        </div>
        <button class="inventory-btn boost-btn" id="btn-use-boost">Использовать</button>
      </div>
    </div>

    <!-- Статистика -->
    <h3 class="section-title">Статистика</h3>
    <div class="stats-grid">
      <div class="stat-card xp-stat">
        <span class="stat-val">${stats.xp}</span>
        <span class="stat-label">Всего XP</span>
      </div>
      <div class="stat-card streak-stat">
        <span class="stat-val">${stats.streak}</span>
        <span class="stat-label">Серия</span>
      </div>
      <div class="stat-card tasks-stat">
        <span class="stat-val">${stats.tasks_completed}</span>
        <span class="stat-label">Вып. задач</span>
      </div>
      <div class="stat-card ach-stat">
        <span class="stat-val">${stats.achievements}</span>
        <span class="stat-label">Достижений</span>
      </div>
    </div>

    <!-- График активности -->
    <h3 class="section-title">График активности</h3>
    <div class="activity-grid" id="activity-grid"></div>

    <!-- Достижения -->
    <h3 class="section-title">Достижения</h3>
    <div class="ach-filters">
      <button class="ach-filter active" data-cat="all">Все</button>
      <button class="ach-filter" data-cat="Привычки">Привычки</button>
      <button class="ach-filter" data-cat="Задачи">Задачи</button>
      <button class="ach-filter" data-cat="Серия">Серия</button>
      <button class="ach-filter" data-cat="Опыт">Опыт</button>
    </div>
    <div class="ach-list" id="ach-list"></div>
  `;

  // График активности
  const activity = await api.getActivity();
  renderActivity(activity);

  // Достижения
  renderAchievements(achievements, "all");

  // Фильтры достижений
  document.querySelectorAll(".ach-filter").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".ach-filter")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      renderAchievements(achievements, btn.dataset.cat);
    });
  });

  // Использовать заморозку
  document
    .getElementById("btn-use-freeze")
    .addEventListener("click", async () => {
      if (stats.freeze_count <= 0) {
        alert("Нет заморозок");
        return;
      }
      if (confirm("Использовать заморозку серии?")) {
        await api.useFreeze();
        loadProfile();
      }
    });

  // Использовать кото-бонус
  document
    .getElementById("btn-use-boost")
    .addEventListener("click", async () => {
      if (
        confirm(
          "Активировать Кото-бонус? Лимит XP увеличится до 500 на случайное время (1-7 дней).",
        )
      ) {
        const res = await api.useBoost();
        if (res.success) {
          alert(`Кото-бонус активирован до ${res.boost_expires_at}!`);
          loadProfile();
        } else {
          alert(res.error);
        }
      }
    });

  // Все уровни
  document.getElementById("btn-all-levels").addEventListener("click", () => {
    showAllLevels(profile.level, profile.xp);
  });
}

function renderActivity(activity) {
  const grid = document.getElementById("activity-grid");
  const today = new Date();
  let html = "";

  for (let i = 89; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(today.getDate() - i);
    const dateStr = date.toISOString().split("T")[0];
    const count = activity[dateStr] || 0;

    let cls = "activity-cell";
    if (count === 0) cls += " empty";
    else if (count <= 2) cls += " low";
    else cls += " high";

    html += `<div class="${cls}" data-date="${dateStr}" data-count="${count}"></div>`;
  }
  grid.innerHTML = html;

  // Тултип при наведении
  const tooltip = document.createElement("div");
  tooltip.className = "activity-tooltip hidden";
  document.body.appendChild(tooltip);

  grid.querySelectorAll(".activity-cell").forEach((cell) => {
    cell.addEventListener("mouseenter", (e) => {
      const date = cell.dataset.date;
      const count = cell.dataset.count;
      const [year, month, day] = date.split("-");
      const months = [
        "янв",
        "фев",
        "мар",
        "апр",
        "май",
        "июн",
        "июл",
        "авг",
        "сен",
        "окт",
        "ноя",
        "дек",
      ];
      tooltip.innerHTML = `
      <div class="tooltip-date">${parseInt(day)} ${months[parseInt(month) - 1]} ${year}</div>
      <div class="tooltip-count">${count > 0 ? `${count} выполнений` : "Нет активности"}</div>
    `;
      tooltip.classList.remove("hidden");
      const rect = cell.getBoundingClientRect();
      tooltip.style.left = `${rect.left + rect.width / 2}px`;
      tooltip.style.top = `${rect.top - 8}px`;
      tooltip.style.transform = "translate(-50%, -100%)";
    });

    cell.addEventListener("mouseleave", () => {
      tooltip.classList.add("hidden");
    });
  });
}

function renderAchievements(achievements, category) {
  const list = document.getElementById("ach-list");
  const filtered =
    category === "all"
      ? achievements
      : achievements.filter((a) => a.category === category);

  list.innerHTML = filtered
    .map(
      (a) => `
    <div class="ach-item ${a.unlocked ? "unlocked" : "locked"}">
      <div class="ach-icon">${a.unlocked ? "🏆" : "🔒"}</div>
      <div class="ach-info">
        <div class="ach-title">${a.title}</div>
        <div class="ach-desc">${a.description}</div>
        <div class="ach-bar-track">
          <div class="ach-bar-fill" style="width:${Math.min((a.progress / a.goal) * 100, 100)}%"></div>
        </div>
      </div>
      <div class="ach-progress">${a.progress}/${a.goal}</div>
    </div>
  `,
    )
    .join("");
}

function showAllLevels(currentLevel, currentXp) {
  const levelNames = [
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
  const levelXp = [0, 200, 500, 1000, 2000, 3500, 5500, 8000, 11000, 15000];
  const levelColors = [
    "#9ca3af",
    "#4ade80",
    "#38bdf8",
    "#60a5fa",
    "#a78bfa",
    "#f472b6",
    "#fb923c",
    "#f87171",
    "#fbbf24",
    "#f0c040",
  ];
  const levelGradients = [
    "#1f2937",
    "#052e16",
    "#0c2340",
    "#1e2d6b",
    "#2e1065",
    "#4a0d2a",
    "#3d1a05",
    "#3d0a0a",
    "#3d1f05",
    "#1e0f40",
  ];
  const levelPerks = [
    "Базовый доступ, график активности, 1 заморозка в неделю",
    "+2 заморозки серии",
    "Лимит 500 XP/день на 3 дня + +3 заморозки",
    "+3 заморозки серии",
    "Лимит 500 XP/день на 5 дней + +3 заморозки",
    "+4 заморозки серии",
    "Лимит 500 XP/день на 7 дней + +5 заморозок",
    "+5 заморозок + еженедельная заморозка становится 2",
    "Лимит 500 XP/день на 7 дней + +5 заморозок",
    "Золотой значок + уникальная рамка + особый цвет имени",
  ];

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal levels-modal">
      <div class="modal-header">
        <h3>Все уровни</h3>
        <button class="modal-close" id="close-levels">✕</button>
      </div>
      <div class="modal-body">
        ${levelNames
          .map((name, i) => {
            const lvl = i + 1;
            const isDone = lvl < currentLevel;
            const isCurrent = lvl === currentLevel;
            return `
              <div class="level-item ${isCurrent ? "current" : ""} ${isDone ? "done-level" : ""}"
                style="background: linear-gradient(135deg, ${levelGradients[i]}, #000); border-color: ${isCurrent ? levelColors[i] : "var(--border)"}">
                <div class="level-item-top">
                  <span class="level-item-name" style="color:${levelColors[i]}">${name}</span>
                  <span class="level-item-xp">${isDone ? "✓" : isCurrent ? `${currentXp}/${levelXp[i + 1] || "—"} XP` : `от ${levelXp[i]} XP`}</span>
                </div>
                <div class="level-item-perk">${levelPerks[i]}</div>
              </div>
            `;
          })
          .join("")}
      </div>
    </div>
  `;

  document.body.appendChild(overlay);
  document
    .getElementById("close-levels")
    .addEventListener("click", () => overlay.remove());
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.remove();
  });
}
