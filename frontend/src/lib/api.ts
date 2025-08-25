import { db } from './db';
import { browser } from '$app/environment';

const API = import.meta.env.VITE_API_BASE || ''; // напр. "" если проксируем Caddy
let token: string | null = browser ? localStorage.getItem('jwt') : null;

export function setToken(t: string) { 
  token = t; 
  if (browser) localStorage.setItem('jwt', t); 
}

export function clearToken() {
  token = null;
  if (browser) localStorage.removeItem('jwt');
}

const authHeaders = (): Record<string, string> =>
  token ? { Authorization: 'Bearer ' + token } : {};

export async function register(email: string, password: string) {
  const res = await fetch(`${API}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  setToken(data.token);
  return data;
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  setToken(data.token);
  return data;
}

export async function pull() {
  if (!token) return;
  const since = (await db.meta.get('last_pull'))?.value || '1970-01-01T00:00:00Z';
  const res = await fetch(`${API}/api/sync/pull?since=${encodeURIComponent(since)}`, { headers: authHeaders() });
  if (!res.ok) return;
  const data = await res.json();
  await db.transaction('rw', [db.categories, db.sources, db.rules, db.operations, db.meta], async () => {
    for (const t of ['categories','sources','rules','operations'] as const) {
      const rows = data[t] as any[];
      for (const row of rows) await (db as any)[t].put(row);
    }
    await db.meta.put({key:'last_pull', value: data.server_time});
  });
}

export async function push() {
  if (!token) return;
  // В простом варианте — шлём всё, оптимизация: dirty-таблица или compare updated_at
  const payload = {
    categories: await db.categories.toArray(),
    sources:    await db.sources.toArray(),
    rules:      await db.rules.toArray(),
    operations: await db.operations.toArray(),
  };
  await fetch(`${API}/api/sync/push`, {
    method: 'POST',
    headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders()),
    body: JSON.stringify(payload)
  }); // SW фоново отправит, если оффлайн
}