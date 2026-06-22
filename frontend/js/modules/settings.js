async function loadSettings() {
  const profile = await api.getProfile();

  const el = document.getElementById("settings-content");

  el.innerHTML = `
    <!-- Изменение профиля -->
    <div class="settings-section">
      <h3 class="settings-title">Изменение профиля</h3>

      <div class="settings-card">
        <p class="settings-label">Изменить аватар</p>
        <div class="settings-row">
          <img src="${profile.avatar_url || "assets/default-avatar.png"}" class="settings-avatar" id="settings-avatar-preview" alt="avatar">
          <input type="file" id="avatar-input" accept="image/*" style="display:none">
          <button class="settings-btn" id="btn-pick-avatar">Выбрать фото</button>
        </div>
      </div>

      <div class="settings-card">
        <p class="settings-label">Изменить имя</p>
        <div class="settings-row">
          <input type="text" class="settings-input" id="settings-name" value="${profile.name}" placeholder="Введите имя...">
          <button class="settings-btn" id="btn-save-name">Ок</button>
        </div>
      </div>
    </div>

    <!-- Тема -->
    <div class="settings-section">
      <h3 class="settings-title">Выбрать тему</h3>
      <div class="settings-card">
        <div class="theme-row">
          <button class="theme-btn ${profile.theme === "light" ? "active" : ""}" data-theme="light">Светлая</button>
          <button class="theme-btn ${profile.theme === "dark" ? "active" : ""}" data-theme="dark">Тёмная</button>
        </div>
      </div>
    </div>

    <!-- Статистика -->
    <div class="settings-section">
      <h3 class="settings-title">Статистика</h3>
      <div class="settings-card">
        <button class="settings-btn-danger" id="btn-reset-stats">Сбросить статистику</button>
      </div>
    </div>

    <!-- Выход -->
    <div class="settings-section">
      <button class="settings-btn-danger" id="btn-logout">Выйти с аккаунта</button>
    </div>
  `;

  // Аватар
  document.getElementById("btn-pick-avatar").addEventListener("click", () => {
    document.getElementById("avatar-input").click();
  });

  document
    .getElementById("avatar-input")
    .addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = async (ev) => {
        const dataUrl = ev.target.result;
        document.getElementById("settings-avatar-preview").src = dataUrl;
        await api.updateProfile({ avatar_url: dataUrl });
        reader.onload = async (ev) => {
          const dataUrl = ev.target.result;
          document.getElementById("settings-avatar-preview").src = dataUrl;
          await api.updateProfile({ avatar_url: dataUrl });
          // Обновляем аватар в профиле если он уже загружен
          const profileAvatar = document.querySelector(".profile-avatar");
          if (profileAvatar) profileAvatar.src = dataUrl;
          localStorage.setItem("avatar", dataUrl);
        };
      };
      reader.readAsDataURL(file);
    });

  // Имя
  document
    .getElementById("btn-save-name")
    .addEventListener("click", async () => {
      const name = document.getElementById("settings-name").value.trim();
      if (!name) return;
      await api.updateProfile({ name });
      localStorage.setItem("name", name);
      alert("Имя обновлено");
    });

  // Тема
  document.querySelectorAll(".theme-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      document
        .querySelectorAll(".theme-btn")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      await api.updateProfile({ theme: btn.dataset.theme });
    });
  });

  // Сброс статистики
  document
    .getElementById("btn-reset-stats")
    .addEventListener("click", async () => {
      if (confirm("Вы уверены? Весь прогресс будет удалён.")) {
        await api.resetStats();
        alert("Статистика сброшена");
        loadProfile();
      }
    });

  // Выход
  document.getElementById("btn-logout").addEventListener("click", () => {
    if (confirm("Выйти из аккаунта?")) {
      localStorage.removeItem("token");
      localStorage.removeItem("name");
      window.location.href = "login.html";
    }
  });
}
