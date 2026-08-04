const form = document.getElementById('register-form');
const submitBtn = document.getElementById('submit-btn');
const serverMsg = document.getElementById('server-msg');

const fields = {
  name: document.getElementById('name'),
  email: document.getElementById('email'),
  password: document.getElementById('password'),
  confirm: document.getElementById('confirm'),
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function setHint(name, msg, ok = false) {
  const el = document.querySelector(`.hint[data-for="${name}"]`);
  if (!el) return;
  el.textContent = msg || '';
  el.classList.toggle('ok', ok && !!msg);
  fields[name].classList.toggle('invalid', !!msg && !ok);
}

function validateField(name) {
  const v = fields[name].value.trim();
  switch (name) {
    case 'name':
      if (v.length < 2) { setHint(name, 'Минимум 2 символа.'); return false; }
      break;
    case 'email':
      if (!EMAIL_RE.test(v)) { setHint(name, 'Некорректный email.'); return false; }
      break;
    case 'password':
      if (v.length < 6) { setHint(name, 'Минимум 6 символов.'); return false; }
      break;
    case 'confirm':
      if (v !== fields.password.value) { setHint(name, 'Пароли не совпадают.'); return false; }
      break;
  }
  setHint(name, '', true);
  return true;
}

Object.keys(fields).forEach((name) => {
  fields[name].addEventListener('blur', () => validateField(name));
  fields[name].addEventListener('input', () => {
    if (fields[name].classList.contains('invalid')) validateField(name);
  });
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  serverMsg.textContent = '';
  serverMsg.className = 'server-msg';

  const agree = document.getElementById('agree').checked;
  if (!agree) {
    serverMsg.textContent = 'Необходимо принять условия.';
    serverMsg.className = 'server-msg error';
    return;
  }

  let valid = true;
  for (const name of Object.keys(fields)) {
    if (!validateField(name)) valid = false;
  }
  if (!valid) return;

  submitBtn.disabled = true;
  submitBtn.textContent = 'Регистрация…';

  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: fields.name.value,
        email: fields.email.value,
        password: fields.password.value,
        confirm: fields.confirm.value,
      }),
    });
    const data = await res.json();

    if (data.ok) {
      serverMsg.textContent = `Готово! Аккаунт создан: ${data.user.email}`;
      serverMsg.className = 'server-msg success';
      form.reset();
      loadUsers();
    } else {
      serverMsg.textContent = data.errors.join(' ');
      serverMsg.className = 'server-msg error';
    }
  } catch (err) {
    serverMsg.textContent = 'Ошибка сети. Попробуйте ещё раз.';
    serverMsg.className = 'server-msg error';
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Зарегистрироваться';
  }
});

async function loadUsers() {
  const panel = document.getElementById('users-panel');
  const list = document.getElementById('users-list');
  panel.hidden = false;
  list.innerHTML = '<div class="empty">Загрузка…</div>';
  try {
    const res = await fetch('/api/users');
    const data = await res.json();
    if (!data.ok || !data.users.length) {
      list.innerHTML = '<div class="empty">Пока нет зарегистрированных пользователей.</div>';
      return;
    }
    list.innerHTML = data.users.map((u) => {
      const initial = (u.name || '?').charAt(0).toUpperCase();
      const date = new Date(u.createdAt).toLocaleString('ru-RU');
      return `
        <div class="user-row">
          <div class="avatar">${initial}</div>
          <div class="user-info">
            <span class="user-name">${escapeHtml(u.name)}</span>
            <span class="user-email">${escapeHtml(u.email)}</span>
          </div>
          <span class="user-date">${date}</span>
        </div>`;
    }).join('');
  } catch {
    list.innerHTML = '<div class="empty">Не удалось загрузить список.</div>';
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

document.getElementById('refresh-users').addEventListener('click', loadUsers);
loadUsers();
