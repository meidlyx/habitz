const API = "/api";

function getToken() {
  return localStorage.getItem("token");
}

async function request(method, path, body = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
  };

  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${API}${path}`, options);

  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/login.html";
    return;
  }

  return res.json();
}

const api = {
  // Профиль
  getProfile: () => request("GET", "/profile"),
  updateProfile: (data) => request("PUT", "/profile", data),
  getStats: () => request("GET", "/profile/stats"),
  getActivity: () => request("GET", "/profile/activity"),
  useFreeze: () => request("POST", "/profile/use-freeze"),
  useBoost: () => request("POST", "/profile/use-boost"),
  resetStats: () => request("POST", "/profile/reset-stats"),

  // Привычки
  getHabits: () => request("GET", "/habits"),
  createHabit: (data) => request("POST", "/habits", data),
  deleteHabit: (id) => request("DELETE", `/habits/${id}`),
  completeHabit: (id) => request("POST", `/habits/${id}/complete`),

  // Задачи
  getTasks: () => request("GET", "/tasks"),
  createTask: (data) => request("POST", "/tasks", data),
  deleteTask: (id) => request("DELETE", `/tasks/${id}`),
  completeTask: (id) => request("POST", `/tasks/${id}/complete`),

  // Достижения
  getAchievements: () => request("GET", "/achievements"),
  checkAchievements: () => request("POST", "/achievements/check"),
};
