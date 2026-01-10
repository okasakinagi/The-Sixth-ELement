const API_BASE = "/api/v1";
const toast = document.getElementById("toast");

const state = {
  token: localStorage.getItem("token") || "",
};

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2200);
}

function setAuthStatus(loggedIn) {
  const statusText = document.getElementById("status-text");
  const statusWrap = document.querySelector(".status");
  if (loggedIn) {
    statusText.textContent = "已登录";
    statusWrap.classList.add("logged-in");
  } else {
    statusText.textContent = "未登录";
    statusWrap.classList.remove("logged-in");
  }
}

async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  if (!headers["Content-Type"] && options.body) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.error || "请求失败";
    throw new Error(message);
  }
  return data;
}

async function handleRegister() {
  const email = document.getElementById("reg-email").value.trim();
  const nickname = document.getElementById("reg-nickname").value.trim();
  const password = document.getElementById("reg-password").value.trim();
  if (!email || !nickname || !password) {
    showToast("请完整填写注册信息");
    return;
  }
  try {
    const data = await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, nickname }),
    });
    state.token = data.access_token;
    localStorage.setItem("token", state.token);
    setAuthStatus(true);
    showToast("注册成功");
    await refreshMe();
    await refreshSurveys();
  } catch (err) {
    showToast(err.message);
  }
}

async function handleLogin() {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value.trim();
  if (!email || !password) {
    showToast("请输入邮箱和密码");
    return;
  }
  try {
    const data = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    state.token = data.access_token;
    localStorage.setItem("token", state.token);
    setAuthStatus(true);
    showToast("登录成功");
    await refreshMe();
    await refreshSurveys();
  } catch (err) {
    showToast(err.message);
  }
}

function handleLogout() {
  state.token = "";
  localStorage.removeItem("token");
  setAuthStatus(false);
  showToast("已退出");
}

async function refreshMe() {
  if (!state.token) {
    return;
  }
  try {
    const data = await apiFetch("/users/me");
    document.getElementById("stat-points").textContent = data.points;
    document.getElementById("stat-activity").textContent = data.activity_points;
    document.getElementById("stat-credit").textContent = data.credit_score;
  } catch (err) {
    showToast(err.message);
  }
}

async function refreshSurveys() {
  try {
    const data = await apiFetch("/surveys");
    const list = document.getElementById("survey-list");
    list.innerHTML = "";
    data.items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "survey-item";
      card.innerHTML = `
        <h4>${item.title}</h4>
        <div>奖励积分：${item.reward_points}</div>
        <div>预计分钟：${item.estimated_minutes || "-"}</div>
        <div>截止时间：${item.deadline || "-"}</div>
        <div class="survey-actions">
          <button data-id="${item.id}" class="btn-fill">提交填写</button>
          <button data-id="${item.id}" class="ghost btn-close">关闭问卷</button>
        </div>
      `;
      list.appendChild(card);
    });
  } catch (err) {
    showToast(err.message);
  }
}

async function refreshFills() {
  if (!state.token) {
    return;
  }
  try {
    const data = await apiFetch("/fills/me");
    const list = document.getElementById("fill-list");
    list.innerHTML = "";
    data.items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "fill-item";
      card.innerHTML = `
        <div>填写记录：${item.id}</div>
        <div>问卷：${item.survey_id}</div>
        <div>状态：${item.status}</div>
        <div>提交时间：${item.created_at}</div>
      `;
      list.appendChild(card);
    });
  } catch (err) {
    showToast(err.message);
  }
}

async function createSurvey() {
  const title = document.getElementById("survey-title").value.trim();
  const link = document.getElementById("survey-link").value.trim();
  const estimated = Number(document.getElementById("survey-minutes").value || 0);
  const reward = Number(document.getElementById("survey-points").value || 0);
  const description = document.getElementById("survey-desc").value.trim();
  if (!title || !link) {
    showToast("标题和链接不能为空");
    return;
  }
  try {
    await apiFetch("/surveys", {
      method: "POST",
      body: JSON.stringify({
        title,
        link,
        estimated_minutes: estimated || null,
        reward_points: reward || 0,
        description,
      }),
    });
    showToast("发布成功");
    await refreshSurveys();
    await refreshMe();
  } catch (err) {
    showToast(err.message);
  }
}

async function submitFill(surveyId) {
  if (!state.token) {
    showToast("请先登录");
    return;
  }
  const duration = prompt("填写用时（秒）", "300");
  if (!duration) {
    return;
  }
  try {
    await apiFetch(`/surveys/${surveyId}/fills`, {
      method: "POST",
      body: JSON.stringify({
        duration_seconds: Number(duration),
      }),
    });
    showToast("提交成功，等待审核");
    await refreshFills();
  } catch (err) {
    showToast(err.message);
  }
}

async function closeSurvey(surveyId) {
  if (!state.token) {
    showToast("请先登录");
    return;
  }
  try {
    await apiFetch(`/surveys/${surveyId}/close`, { method: "POST" });
    showToast("已关闭");
    await refreshSurveys();
  } catch (err) {
    showToast(err.message);
  }
}

document.getElementById("btn-register").addEventListener("click", handleRegister);
document.getElementById("btn-login").addEventListener("click", handleLogin);
document.getElementById("btn-logout").addEventListener("click", handleLogout);
document.getElementById("btn-refresh-me").addEventListener("click", refreshMe);
document.getElementById("btn-refresh-surveys").addEventListener("click", refreshSurveys);
document.getElementById("btn-refresh-fills").addEventListener("click", refreshFills);
document.getElementById("btn-create-survey").addEventListener("click", createSurvey);

document.getElementById("survey-list").addEventListener("click", (event) => {
  const target = event.target;
  if (target.classList.contains("btn-fill")) {
    submitFill(target.dataset.id);
  }
  if (target.classList.contains("btn-close")) {
    closeSurvey(target.dataset.id);
  }
});

setAuthStatus(Boolean(state.token));
refreshSurveys();
refreshMe();
refreshFills();
