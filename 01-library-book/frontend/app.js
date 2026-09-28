const state = {
  user: null,
  books: [],
  myBooks: [],
  records: [],
  view: "catalog",
  filter: "all",
  query: "",
  mode: "login",
  editingId: null,
  deleteArmed: false,
};

const SPINES = ["#8f3a32", "#2d6a4f", "#3d4f7c", "#8a6232", "#6b3f55", "#3f5c49"];
const $ = (selector) => document.querySelector(selector);

const token = () => localStorage.getItem("library_token");

function money(value) {
  return `¥${Number(value).toFixed(2)}`;
}

function when(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function spineColor(title) {
  let hash = 0;
  for (const char of title) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return SPINES[hash % SPINES.length];
}

function detailMessage(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join("；");
  return "请求失败";
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.body) headers["Content-Type"] = "application/json";
  if (token()) headers.Authorization = `Bearer ${token()}`;

  const response = await fetch(path, { ...options, headers });
  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (response.status === 401 && token()) {
    localStorage.removeItem("library_token");
    state.user = null;
    showAuth();
  }

  if (!response.ok) {
    const error = new Error(detailMessage(data?.detail));
    error.status = response.status;
    throw error;
  }
  return data;
}

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => {
    node.hidden = true;
  }, 2800);
}

function showAuth() {
  $("#auth").hidden = false;
  $("#auth-error").hidden = true;
}

function hideAuth() {
  $("#auth").hidden = true;
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("is-active", tab.dataset.mode === mode);
  });
  $("#auth-submit").textContent = mode === "login" ? "登录" : "注册并登录";
  $("#auth-form").password.autocomplete = mode === "login" ? "current-password" : "new-password";
}

async function refresh() {
  const [books, myBooks, records] = await Promise.all([
    api("/books"),
    state.user ? api("/users/me/books?limit=100") : Promise.resolve([]),
    state.user ? api("/borrow-records") : Promise.resolve([]),
  ]);
  state.books = books;
  state.myBooks = myBooks;
  state.records = records;
  render();
}

function visibleBooks() {
  const query = state.query.trim().toLowerCase();
  return state.books.filter((book) => {
    const matchesFilter =
      state.filter === "all" ||
      (state.filter === "available" && !book.borrowed) ||
      (state.filter === "borrowed" && book.borrowed);
    const matchesQuery =
      !query ||
      book.title.toLowerCase().includes(query) ||
      book.author.toLowerCase().includes(query);
    return matchesFilter && matchesQuery;
  });
}

function bookCard(book, { returning = false } = {}) {
  const mine = state.myBooks.some((item) => item.id === book.id);
  let action = "";
  if (!book.borrowed) {
    action = `<button type="button" class="solid-button" data-action="borrow" data-id="${book.id}">借阅</button>`;
  } else if (mine || returning) {
    action = `<button type="button" class="solid-button" data-action="return" data-id="${book.id}">归还</button>`;
  } else {
    action = `<button type="button" class="quiet" disabled>已借出</button>`;
  }

  return `
    <article class="card">
      <div class="spine" style="--spine:${spineColor(book.title)}"></div>
      <div class="card-body">
        <span class="pill ${book.borrowed ? "is-out" : ""}">${book.borrowed ? "已借出" : "在架"}</span>
        <h3>${escapeHtml(book.title)}</h3>
        <p class="meta">${escapeHtml(book.author)}</p>
        <p class="price">${money(book.price)}</p>
        <div class="card-actions">
          ${action}
          <button type="button" class="quiet" data-action="edit" data-id="${book.id}">编辑</button>
        </div>
      </div>
    </article>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderStats() {
  const borrowed = state.books.filter((book) => book.borrowed).length;
  $("#stats").innerHTML = [
    ["馆藏", state.books.length],
    ["在架", state.books.length - borrowed],
    ["已借出", borrowed],
  ]
    .map(([label, count]) => `<div class="stat"><span>${label}</span><strong>${count}</strong></div>`)
    .join("");
}

function render() {
  const titles = {
    catalog: ["Catalog", "馆藏"],
    mine: ["On loan", "我的在借"],
    history: ["History", "借阅记录"],
  };
  $("#eyebrow").textContent = titles[state.view][0];
  $("#page-title").textContent = titles[state.view][1];
  $("#user-label").textContent = state.user ? state.user.username : "未登录";
  $("#auth-toggle").textContent = state.user ? "退出" : "登录";
  $("#filters").hidden = state.view !== "catalog";
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("is-active", item.dataset.view === state.view);
  });
  renderStats();

  const view = $("#view");
  if (state.view === "catalog") {
    const books = visibleBooks();
    view.innerHTML = books.length
      ? `<div class="grid">${books.map((book) => bookCard(book)).join("")}</div>`
      : `<div class="empty">架上没有符合条件的书。可以先入库一本。</div>`;
    return;
  }

  if (!state.user) {
    view.innerHTML = `<div class="empty">登录后才能查看这部分。</div>`;
    return;
  }

  if (state.view === "mine") {
    view.innerHTML = state.myBooks.length
      ? `<div class="grid">${state.myBooks.map((book) => bookCard(book, { returning: true })).join("")}</div>`
      : `<div class="empty">你现在没有在借的书。</div>`;
    return;
  }

  const titlesById = new Map(state.books.map((book) => [book.id, book.title]));
  view.innerHTML = state.records.length
    ? `<div class="list">${state.records
        .map((record) => {
          const title = titlesById.get(record.book_id) || `图书 #${record.book_id}`;
          const returned = Boolean(record.return_date);
          return `
            <article class="record">
              <div>
                <h3>${escapeHtml(title)}</h3>
                <p class="meta">借出 ${when(record.borrow_date)}</p>
                <p class="meta">${returned ? `归还 ${when(record.return_date)}` : "尚未归还"}</p>
              </div>
              <span class="pill ${returned ? "" : "is-out"}">${returned ? "已归还" : "借阅中"}</span>
            </article>
          `;
        })
        .join("")}</div>`
    : `<div class="empty">还没有借阅记录。</div>`;
}

async function borrow(bookId, borrowed) {
  if (!state.user) {
    showAuth();
    toast("请先登录");
    return;
  }
  await api(`/books/${bookId}/borrowed`, {
    method: "PATCH",
    body: JSON.stringify({ borrowed }),
  });
  toast(borrowed ? "借阅成功" : "已归还");
  await refresh();
}

function openEdit(bookId) {
  const book = state.books.find((item) => item.id === bookId) || state.myBooks.find((item) => item.id === bookId);
  if (!book) return;
  state.editingId = book.id;
  state.deleteArmed = false;
  const form = $("#edit-form");
  form.title.value = book.title;
  form.author.value = book.author;
  form.price.value = book.price;
  form.price.disabled = book.borrowed;
  $("#save-price").disabled = book.borrowed;
  $("#price-hint").textContent = book.borrowed ? "这本书已借出，不能改价。" : "在架图书可以修改价格。";
  $("#edit-title").textContent = book.title;
  $("#delete-book").textContent = "删除";
  form.querySelector("[data-error]").hidden = true;
  $("#edit-dialog").showModal();
}

function showFormError(form, message) {
  const node = form.querySelector("[data-error]");
  node.textContent = message;
  node.hidden = false;
}

document.querySelectorAll(".nav-item").forEach((item) => {
  item.addEventListener("click", () => {
    state.view = item.dataset.view;
    render();
  });
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    state.filter = chip.dataset.filter;
    document.querySelectorAll(".chip").forEach((item) => item.classList.toggle("is-active", item === chip));
    render();
  });
});

$("#search").addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});

$("#open-create").addEventListener("click", () => {
  $("#create-form").reset();
  $("#create-form [data-error]").hidden = true;
  $("#create-dialog").showModal();
});

document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", () => {
    document.getElementById(button.dataset.close).close();
  });
});

$("#auth-toggle").addEventListener("click", () => {
  if (!state.user) {
    showAuth();
    return;
  }
  localStorage.removeItem("library_token");
  state.user = null;
  state.myBooks = [];
  state.records = [];
  state.view = "catalog";
  render();
  toast("已退出");
});

$("#skip-auth").addEventListener("click", hideAuth);
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => setMode(tab.dataset.mode));
});

$("#auth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    username: form.username.value.trim(),
    password: form.password.value,
  };
  const error = $("#auth-error");
  error.hidden = true;
  try {
    if (state.mode === "register") {
      await api("/users", { method: "POST", body: JSON.stringify(payload) });
    }
    const session = await api("/login", { method: "POST", body: JSON.stringify(payload) });
    localStorage.setItem("library_token", session.token);
    state.user = { id: session.id, username: session.username };
    hideAuth();
    await refresh();
    toast(`欢迎，${state.user.username}`);
  } catch (err) {
    error.textContent = err.message;
    error.hidden = false;
  }
});

$("#create-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    await api("/books", {
      method: "POST",
      body: JSON.stringify({
        title: form.title.value.trim(),
        author: form.author.value.trim(),
        price: Number(form.price.value),
      }),
    });
    $("#create-dialog").close();
    toast("已入库");
    await refresh();
  } catch (err) {
    showFormError(form, err.message);
  }
});

$("#edit-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    await api(`/books/${state.editingId}`, {
      method: "PATCH",
      body: JSON.stringify({
        title: form.title.value.trim(),
        author: form.author.value.trim(),
      }),
    });
    $("#edit-dialog").close();
    toast("资料已更新");
    await refresh();
  } catch (err) {
    showFormError(form, err.message);
  }
});

$("#save-price").addEventListener("click", async () => {
  const form = $("#edit-form");
  try {
    await api(`/books/${state.editingId}/price`, {
      method: "PATCH",
      body: JSON.stringify({ price: Number(form.price.value) }),
    });
    $("#edit-dialog").close();
    toast("价格已更新");
    await refresh();
  } catch (err) {
    showFormError(form, err.message);
  }
});

$("#delete-book").addEventListener("click", async () => {
  if (!state.deleteArmed) {
    state.deleteArmed = true;
    $("#delete-book").textContent = "再点一次删除";
    return;
  }
  try {
    await api(`/books/${state.editingId}`, { method: "DELETE" });
    $("#edit-dialog").close();
    toast("已删除");
    await refresh();
  } catch (err) {
    showFormError($("#edit-form"), err.message);
  }
});

$("#view").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const bookId = Number(button.dataset.id);
  try {
    if (button.dataset.action === "borrow") await borrow(bookId, true);
    if (button.dataset.action === "return") await borrow(bookId, false);
    if (button.dataset.action === "edit") openEdit(bookId);
  } catch (err) {
    toast(err.message);
  }
});

async function boot() {
  if (!token()) {
    showAuth();
    await refresh();
    return;
  }
  try {
    state.user = await api("/users/me");
    hideAuth();
  } catch {
    localStorage.removeItem("library_token");
    state.user = null;
    showAuth();
  }
  await refresh();
}

boot().catch((err) => toast(err.message));
