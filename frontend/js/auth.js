const API = "/api";

// Переключение вкладок
document.getElementById("tab-login").addEventListener("click", () => {
  document.getElementById("tab-login").classList.add("active");
  document.getElementById("tab-register").classList.remove("active");
  document.getElementById("form-login").classList.remove("hidden");
  document.getElementById("form-register").classList.add("hidden");
});

document.getElementById("tab-register").addEventListener("click", () => {
  document.getElementById("tab-register").classList.add("active");
  document.getElementById("tab-login").classList.remove("active");
  document.getElementById("form-register").classList.remove("hidden");
  document.getElementById("form-login").classList.add("hidden");
});

// Вход
document.getElementById("btn-login").addEventListener("click", async () => {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value.trim();
  const errorEl = document.getElementById("login-error");

  if (!email || !password) {
    errorEl.textContent = "Заполните все поля";
    return;
  }

  try {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (!res.ok) {
      errorEl.textContent = data.error;
      return;
    }

    localStorage.setItem("token", data.token);
    localStorage.setItem("name", data.name);
    window.location.href = "/app.html";
  } catch (err) {
    errorEl.textContent = "Ошибка соединения с сервером";
  }
});

// Регистрация
document.getElementById("btn-register").addEventListener("click", async () => {
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value.trim();
  const errorEl = document.getElementById("reg-error");

  if (!name || !email || !password) {
    errorEl.textContent = "Заполните все поля";
    return;
  }

  try {
    const res = await fetch(`${API}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });

    const data = await res.json();

    if (!res.ok) {
      errorEl.textContent = data.error;
      return;
    }

    localStorage.setItem("token", data.token);
    localStorage.setItem("name", data.name);
    window.location.href = "/app.html";
  } catch (err) {
    errorEl.textContent = "Ошибка соединения с сервером";
  }
});

// Если уже залогинен — сразу в приложение
if (localStorage.getItem("token")) {
  window.location.href = "/app.html";
}
