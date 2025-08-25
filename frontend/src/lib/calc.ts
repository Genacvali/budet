import type { Source, Rule, Operation, Category } from './db';

export function simulatePlan(amountBySource: Record<string, number>, rules: Rule[], caps: Record<string, number> = {}) {
  // Возвращает распределение по категориям с учетом процентов и cap, остаток -> "reserve" (id 'reserve' например)
  const out: Record<string, number> = {};
  for (const [sourceId, amount] of Object.entries(amountBySource)) {
    let remaining = amount;
    const rs = rules.filter(r => r.source_id === sourceId && !r.deleted_at);
    // сначала применяем проценты и капы
    for (const r of rs) {
      const share = Math.floor((amount * (r.percent/100)));
      const cap = r.cap_cents ?? Infinity;
      const val = Math.min(share, cap);
      out[r.category_id] = (out[r.category_id] || 0) + val;
      remaining -= val;
    }
    // остаток — в категорию "reserve" (или любую выбранную пользователем)
    out['reserve'] = (out['reserve'] || 0) + Math.max(0, remaining);
  }
  return out;
}

export function factByCategory(ops: Operation[]) {
  const res: Record<string, number> = {};
  for (const o of ops.filter(o=>!o.deleted_at)) {
    const sign = o.type === 'expense' ? -1 : 1;
    res[o.category_id] = (res[o.category_id] || 0) + sign * o.amount_cents;
  }
  return res;
}

export function colorByUsage(used: number, plan: number) {
  if (plan <= 0) return 'text-gray-400';
  const pct = used/plan;
  if (pct < 0.8) return 'text-gray-400';
  if (pct < 1.0) return 'text-yellow-500';
  return 'text-red-500';
}

export function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}