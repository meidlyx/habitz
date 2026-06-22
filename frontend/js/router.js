window.addEventListener("beforeunload", function () {
  console.log("СТРАНИЦА ПЕРЕЗАГРУЖАЕТСЯ!");
  console.trace();
});

let greetingShown = false;

if (!localStorage.getItem("token")) {
  window.location.href = "login.html";
}

let currentPage = "main";
let greetingTimer = null;

const pages = document.querySelectorAll(".page");
const navBtns = document.querySelectorAll(".nav-btn");
const tabItems = document.querySelectorAll(".tab-item");

function showPage(pageName) {
  currentPage = pageName;

  pages.forEach((p) => p.classList.remove("active"));
  navBtns.forEach((b) => b.classList.remove("active"));
  tabItems.forEach((t) => t.classList.remove("active"));

  document.getElementById(`page-${pageName}`).classList.add("active");
  document
    .querySelectorAll(`[data-page="${pageName}"]`)
    .forEach((el) => el.classList.add("active"));

  if (pageName === "main") loadMain();
  if (pageName === "tasks") loadTasks();
  if (pageName === "profile") loadProfile();
  if (pageName === "settings") loadSettings();
}

navBtns.forEach((btn) => {
  btn.addEventListener("click", () => showPage(btn.dataset.page));
});

tabItems.forEach((btn) => {
  btn.addEventListener("click", () => showPage(btn.dataset.page));
});

function animateGreeting(name) {
  if (greetingShown) return;
  greetingShown = true;

  const el = document.getElementById("greeting-text");
  const dateEl = document.getElementById("greeting-date");

  const days = [
    "Воскресенье",
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
  ];
  const months = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
  ];
  const now = new Date();
  const dateStr = `${days[now.getDay()]}, ${now.getDate()} ${months[now.getMonth()]}`;

  dateEl.textContent = dateStr;

  const greetText = `Привет, ${name}!`;
  const finalText = `Главная`;

  // Останавливаем предыдущую анимацию
  if (greetingTimer) clearTimeout(greetingTimer);
  el.textContent = "";

  let i = 0;
  let stopped = false;

  function stop() {
    stopped = true;
  }

  function type1() {
    if (stopped || currentPage !== "main") return;
    if (i < greetText.length) {
      el.textContent += greetText[i++];
      greetingTimer = setTimeout(type1, 60);
    } else {
      greetingTimer = setTimeout(erase, 2000);
    }
  }

  function erase() {
    if (stopped || currentPage !== "main") return;
    if (el.textContent.length > 0) {
      el.textContent = el.textContent.slice(0, -1);
      greetingTimer = setTimeout(erase, 30);
    } else {
      greetingTimer = setTimeout(type2, 300);
    }
  }

  let j = 0;
  function type2() {
    if (stopped || currentPage !== "main") return;
    if (j < finalText.length) {
      el.textContent += finalText[j++];
      greetingTimer = setTimeout(type2, 60);
    }
  }

  type1();
}

function renderStreak(streak) {
  const row = document.getElementById("streak-row");
  if (!row) return;
  const days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
  const today = new Date().getDay();
  const todayIndex = today === 0 ? 6 : today - 1;

  row.innerHTML = days
    .map((d, i) => {
      let cls = "streak-day";
      if (i === todayIndex) cls += " today";
      else if (i < todayIndex && streak > todayIndex - i) cls += " done";
      return `<div class="${cls}">${d}</div>`;
    })
    .join("");
}

async function loadMain() {
  const name = localStorage.getItem("name") || "друг";
  animateGreeting(name);

  const profile = await api.getProfile();
  renderStreak(profile.streak);

  await loadHabits();
}

showPage("main");
