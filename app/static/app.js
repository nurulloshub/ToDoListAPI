// ============================================================
// State
// ============================================================
const state = {
  accessToken: localStorage.getItem('access_token') || null,
  refreshToken: localStorage.getItem('refresh_token') || null,
  userName: localStorage.getItem('user_name') || null,
  page: 1,
  limit: 10,
  filter: 'all',           // all | active | completed
  search: '',
  sort: 'created_at:desc',
  total: 0,
  items: [],
};

// ============================================================
// Token persistence & refresh
// ============================================================
function saveTokens(data, name = null) {
  state.accessToken = data.access_token;
  state.refreshToken = data.refresh_token;
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  if (name) {
    state.userName = name;
    localStorage.setItem('user_name', name);
  }
}

function clearTokens() {
  state.accessToken = state.refreshToken = state.userName = null;
  ['access_token', 'refresh_token', 'user_name'].forEach(k => localStorage.removeItem(k));
}

async function tryRefresh() {
  if (!state.refreshToken) return false;
  try {
    const res = await fetch('/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: state.refreshToken }),
    });
    if (!res.ok) return false;
    saveTokens(await res.json());
    return true;
  } catch {
    return false;
  }
}

// Authenticated fetch with transparent refresh + retry-once on 401
async function apiFetch(path, options = {}, retry = true) {
  const headers = { ...(options.headers || {}) };
  if (state.accessToken) headers['Authorization'] = `Bearer ${state.accessToken}`;

  const res = await fetch(path, { ...options, headers });

  if (res.status === 401 && retry && state.refreshToken) {
    if (await tryRefresh()) return apiFetch(path, options, false);
    clearTokens();
    showView('auth');
  }
  return res;
}

// ============================================================
// UI helpers
// ============================================================
function showView(name) {
  document.getElementById('auth-view').classList.toggle('hidden', name !== 'auth');
  document.getElementById('todos-view').classList.toggle('hidden', name !== 'todos');
}

let toastTimer;
function showToast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add('hidden'), 2500);
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str ?? '';
  return d.innerHTML;
}

function escapeAttr(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

// ============================================================
// Auth forms
// ============================================================
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const target = tab.dataset.tab;
    document.getElementById('login-form').classList.toggle('hidden', target !== 'login');
    document.getElementById('register-form').classList.toggle('hidden', target !== 'register');
    document.getElementById('auth-error').classList.add('hidden');
  });
});

function showAuthError(msg) {
  const el = document.getElementById('auth-error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

document.getElementById('login-form').addEventListener('submit', async e => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const res = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: fd.get('email'), password: fd.get('password') }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    saveTokens(data);
    enterApp();
  } catch (err) {
    showAuthError(err.message);
  }
});

document.getElementById('register-form').addEventListener('submit', async e => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const res = await fetch('/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: fd.get('name'),
        email: fd.get('email'),
        password: fd.get('password'),
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Registration failed');
    saveTokens(data, fd.get('name'));
    enterApp();
  } catch (err) {
    showAuthError(err.message);
  }
});

document.getElementById('logout-btn').addEventListener('click', () => {
  clearTokens();
  showView('auth');
  document.getElementById('login-form').reset();
  document.getElementById('register-form').reset();
});

// ============================================================
// Todos: load & render
// ============================================================
function buildQuery() {
  const p = new URLSearchParams();
  p.set('page', state.page);
  p.set('limit', state.limit);
  if (state.filter === 'active') p.set('completed', 'false');
  if (state.filter === 'completed') p.set('completed', 'true');
  if (state.search) p.set('search', state.search);
  const [sortBy, order] = state.sort.split(':');
  p.set('sort_by', sortBy);
  p.set('order', order);
  return p.toString();
}

async function loadTodos() {
  try {
    const res = await apiFetch(`/todos?${buildQuery()}`);
    if (!res.ok) throw new Error('Failed to load todos');
    const data = await res.json();
    state.items = data.data;
    state.total = data.total;
    renderTodos();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderTodos() {
  const list = document.getElementById('todos-list');
  const empty = document.getElementById('empty-state');
  const pagination = document.getElementById('pagination');

  if (state.items.length === 0) {
    list.innerHTML = '';
    empty.classList.remove('hidden');
    pagination.classList.add('hidden');
    return;
  }

  empty.classList.add('hidden');
  list.innerHTML = state.items.map(todo => `
    <div class="todo-card${todo.completed ? ' completed' : ''}" data-id="${todo.id}">
      <label class="todo-checkbox">
        <input type="checkbox" ${todo.completed ? 'checked' : ''} data-action="toggle">
        <span class="checkmark"></span>
      </label>
      <div class="todo-content">
        <div class="todo-title">${escapeHtml(todo.title)}</div>
        ${todo.description ? `<div class="todo-desc">${escapeHtml(todo.description)}</div>` : ''}
      </div>
      <div class="todo-actions">
        <button class="icon-btn" data-action="edit" title="Edit">✏️</button>
        <button class="icon-btn" data-action="delete" title="Delete">🗑️</button>
      </div>
    </div>
  `).join('');

  const totalPages = Math.max(1, Math.ceil(state.total / state.limit));
  if (totalPages > 1) {
    pagination.classList.remove('hidden');
    document.getElementById('page-info').textContent = `Page ${state.page} of ${totalPages}`;
    document.getElementById('prev-btn').disabled = state.page <= 1;
    document.getElementById('next-btn').disabled = state.page >= totalPages;
  } else {
    pagination.classList.add('hidden');
  }
}

// ============================================================
// Todos: create
// ============================================================
document.getElementById('create-form').addEventListener('submit', async e => {
  e.preventDefault();
  const form = e.target;
  const fd = new FormData(form);
  const title = fd.get('title').trim();
  if (!title) return;

  const res = await apiFetch('/todos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title,
      description: fd.get('description').trim() || null,
    }),
  });
  if (res.ok) {
    form.reset();
    state.page = 1;
    loadTodos();
  } else {
    showToast('Create failed', 'error');
  }
});

// ============================================================
// Todos: edit / delete / toggle (event delegation)
// ============================================================
document.getElementById('todos-list').addEventListener('click', async e => {
  const card = e.target.closest('.todo-card');
  if (!card) return;
  const id = card.dataset.id;
  const action = e.target.dataset.action;

  if (action === 'delete') {
    if (!confirm('Delete this todo?')) return;
    const res = await apiFetch(`/todos/${id}`, { method: 'DELETE' });
    if (res.ok || res.status === 204) {
      showToast('Deleted', 'success');
      if (state.items.length === 1 && state.page > 1) state.page--;
      loadTodos();
    } else {
      showToast('Delete failed', 'error');
    }
  } else if (action === 'edit') {
    enterEditMode(card);
  } else if (action === 'save') {
    const title = card.querySelector('.edit-title').value.trim();
    const description = card.querySelector('.edit-desc').value.trim() || null;
    if (!title) return;
    const res = await apiFetch(`/todos/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description }),
    });
    if (res.ok) { showToast('Updated', 'success'); loadTodos(); }
    else showToast('Update failed', 'error');
  } else if (action === 'cancel') {
    loadTodos();
  }
});

document.getElementById('todos-list').addEventListener('change', async e => {
  if (e.target.dataset.action !== 'toggle') return;
  const card = e.target.closest('.todo-card');
  const id = card.dataset.id;
  const completed = e.target.checked;

  const res = await apiFetch(`/todos/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed }),
  });
  if (res.ok) loadTodos();
  else { e.target.checked = !completed; showToast('Update failed', 'error'); }
});

function enterEditMode(card) {
  const id = card.dataset.id;
  const todo = state.items.find(t => String(t.id) === String(id));
  if (!todo) return;

  card.classList.add('editing');
  card.innerHTML = `
    <div class="edit-form">
      <input type="text" class="edit-title" value="${escapeAttr(todo.title)}" maxlength="200">
      <input type="text" class="edit-desc" value="${escapeAttr(todo.description || '')}" maxlength="2000" placeholder="Description">
      <div class="edit-actions">
        <button class="btn-cancel" data-action="cancel">Cancel</button>
        <button class="btn-save" data-action="save">Save</button>
      </div>
    </div>
  `;
  const first = card.querySelector('.edit-title');
  first.focus();
  first.select();
  card.addEventListener('keydown', ev => {
    if (ev.key === 'Escape') loadTodos();
    if (ev.key === 'Enter' && ev.target.tagName === 'INPUT') {
      card.querySelector('[data-action="save"]').click();
    }
  }, { once: false });
}

// ============================================================
// Filter / search / sort / pagination
// ============================================================
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.filter = btn.dataset.filter;
    state.page = 1;
    loadTodos();
  });
});

let searchTimer;
document.getElementById('search-input').addEventListener('input', e => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.search = e.target.value.trim();
    state.page = 1;
    loadTodos();
  }, 300);
});

document.getElementById('sort-select').addEventListener('change', e => {
  state.sort = e.target.value;
  state.page = 1;
  loadTodos();
});

document.getElementById('prev-btn').addEventListener('click', () => {
  if (state.page > 1) { state.page--; loadTodos(); }
});
document.getElementById('next-btn').addEventListener('click', () => {
  state.page++;
  loadTodos();
});

// ============================================================
// Entry point
// ============================================================
function enterApp() {
  showView('todos');
  document.getElementById('user-name').textContent = state.userName || 'User';
  loadTodos();
}

if (state.accessToken) enterApp();
else showView('auth');