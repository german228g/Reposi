import express from 'express';
import bcrypt from 'bcryptjs';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(join(__dirname, 'public')));

const DATA_DIR = join(__dirname, 'data');
const USERS_FILE = join(DATA_DIR, 'users.json');

function loadUsers() {
  if (!existsSync(USERS_FILE)) return [];
  try {
    return JSON.parse(readFileSync(USERS_FILE, 'utf8'));
  } catch {
    return [];
  }
}

function saveUsers(users) {
  if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true });
  writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

app.post('/api/register', async (req, res) => {
  const { name, email, password, confirm } = req.body || {};

  const errors = [];
  if (!name || name.trim().length < 2) errors.push('Имя должно содержать минимум 2 символа.');
  if (!email || !EMAIL_RE.test(email)) errors.push('Некорректный email.');
  if (!password || password.length < 6) errors.push('Пароль должен быть не короче 6 символов.');
  if (password !== confirm) errors.push('Пароли не совпадают.');

  if (errors.length) return res.status(400).json({ ok: false, errors });

  const users = loadUsers();
  const exists = users.some((u) => u.email.toLowerCase() === email.toLowerCase());
  if (exists) return res.status(409).json({ ok: false, errors: ['Пользователь с таким email уже зарегистрирован.'] });

  const hash = await bcrypt.hash(password, 10);
  const user = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
    name: name.trim(),
    email: email.trim().toLowerCase(),
    passwordHash: hash,
    createdAt: new Date().toISOString(),
  };
  users.push(user);
  saveUsers(users);

  return res.json({ ok: true, user: { id: user.id, name: user.name, email: user.email, createdAt: user.createdAt } });
});

app.get('/api/users', (req, res) => {
  const users = loadUsers().map(({ passwordHash, ...u }) => u);
  res.json({ ok: true, count: users.length, users });
});

app.get('/api/health', (req, res) => res.json({ ok: true, uptime: process.uptime() }));

app.listen(PORT, () => {
  console.log(`Сайт регистрации запущен: http://localhost:${PORT}`);
});
