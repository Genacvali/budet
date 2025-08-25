import { db } from './db';
import { browser } from '$app/environment';

const rawBase = (import.meta as any).env?.VITE_API_BASE as string | undefined;
const API = (rawBase ? rawBase.replace(/\/+$/, '') : '');

let token: string | null = null;
if (browser) {
  try { token = localStorage.getItem('jwt'); } catch { token = null; }
}

export const setToken = (t: string | null) => {
  token = t;
  if (browser) {
    try { t ? localStorage.setItem('jwt', t) : localStorage.removeItem('jwt'); } catch {}
  }
};
export const clearToken = () => setToken(null);

const authHeaders = (): Record<string,string> => token ? { Authorization: `Bearer ${token}` } : {};

export async function register(email: string, password: string) {
  const res = await fetch(`${API}/api/auth/register`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) throw new Error(await safeText(res));
  const data = await res.json();
  setToken(data.token ?? null);
  return data;
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API}/api/auth/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) throw new Error(await safeText(res));
  const data = await res.json();
  setToken(data.token ?? null);
  return data;
}

export async function pull() {
  if (!token) return;
  try {
    const since = (await db.meta.get('last_pull'))?.value || '1970-01-01T00:00:00Z';
    const res = await fetch(`${API}/api/sync/pull?since=${encodeURIComponent(since)}`, { headers: authHeaders() });
    if (res.status === 401 || res.status === 403) return;
    if (!res.ok) return;
    const data = await res.json();
    await db.transaction('rw', [db.categories, db.sources, db.rules, db.operations, db.meta], async () => {
      for (const t of ['categories','sources','rules','operations'] as const) {
        const rows = (data as any)[t] as any[] | undefined;
        if (!rows?.length) continue;
        for (const row of rows) await (db as any)[t].put(row);
      }
      await db.meta.put({ key:'last_pull', value: data.server_time });
    });
  } catch {}
}

export async function push() {
  if (!token) return;
  try {
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
    });
  } catch {}
}

async function safeText(res: Response) {
  try { return await res.text(); } catch { return `${res.status} ${res.statusText}`; }
}