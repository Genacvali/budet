<script lang="ts">
  import { onMount } from 'svelte';
  import { db, type Category, type Source, type Rule } from '$lib/db';
  import { browser } from '$app/environment';

  let categories: Category[] = [];
  let sources: Source[] = [];
  let rules: Rule[] = [];

  // Сумма, которую ожидаем по каждому источнику в этом месяце (симулятор)
  // Храним в meta: sim_amount_<source_id> = строка рублей (например "50000.00")
  let sim: Record<string,string> = {};

  function centsFromStr(v: string): number {
    const n = Number(String(v || '').replace(',', '.'));
    return Number.isFinite(n) ? Math.round(n * 100) : 0;
  }
  function rub(cents: number): string {
    return (cents/100).toFixed(2);
  }
  function nowIso(){ return new Date().toISOString(); }
  function uuid(){ return (browser && crypto?.randomUUID) ? crypto.randomUUID() : Math.random().toString(36).slice(2); }

  async function loadAll() {
    categories = (await db.categories.toArray()).filter(c => c.kind==='expense' && !c.deleted_at)
      .sort((a,b)=>a.name.localeCompare(b.name));
    sources = (await db.sources.toArray()).filter(s => !s.deleted_at)
      .sort((a,b)=>a.name.localeCompare(b.name));
    rules = (await db.rules.toArray()).filter(r => !r.deleted_at);

    // загрузим симулятор
    for (const s of sources) {
      const k = 'sim_amount_' + s.id;
      sim[s.id] = (await db.meta.get(k))?.value || '';
    }
  }

  onMount(loadAll);

  // Получить/создать правило для пары (category, source)
  function getRule(catId: string, srcId: string): Rule {
    let r = rules.find(r => r.category_id===catId && r.source_id===srcId && !r.deleted_at);
    if (!r) {
      const t = nowIso();
      r = { id: uuid(), user_id:'local', source_id:srcId, category_id:catId, percent:0, fixed_cents:null, cap_cents:null, created_at:t, updated_at:t, deleted_at:null };
      rules.push(r);
      // не записываем в БД до первого ввода, чтобы не плодить пустые строки
    }
    return r;
  }

  async function saveRule(r: Rule) {
    r.updated_at = nowIso();
    await db.rules.put(r);
  }

  async function onPercentChange(catId: string, srcId: string, v: string) {
    let r = getRule(catId, srcId);
    const num = Number(v.replace(',', '.')); r.percent = Number.isFinite(num) ? num : 0;
    await saveRule(r);
  }
  async function onFixedChange(catId: string, srcId: string, v: string) {
    let r = getRule(catId, srcId);
    const c = centsFromStr(v); r.fixed_cents = c || null;
    await saveRule(r);
  }
  async function onSimChange(srcId: string, v: string) {
    sim[srcId] = v;
    await db.meta.put({ key: 'sim_amount_'+srcId, value: v });
  }

  // Подсчёт «Минусы ₽» по категории за текущий месяц
  let monthKey = new Date().toISOString().slice(0,7); // YYYY-MM
  let spentByCat: Record<string, number> = {};

  async function calcSpent() {
    spentByCat = {};
    const ops = await db.operations.toArray();
    for (const op of ops) {
      if (op.deleted_at) continue;
      if (op.type !== 'expense') continue;
      if (!op.date?.startsWith(monthKey)) continue;
      spentByCat[op.category_id] = (spentByCat[op.category_id] || 0) + (op.amount_cents || 0);
    }
  }
  onMount(calcSpent);

  function planFor(catId: string, srcId: string): number {
    const r = rules.find(r => r.category_id===catId && r.source_id===srcId && !r.deleted_at);
    const income = centsFromStr(sim[srcId] || '0'); // сумма для источника
    if (!r) return 0;
    const byPercent = Math.round(income * (r.percent || 0) / 100);
    const byFixed = r.fixed_cents || 0;
    let total = byPercent + byFixed;
    if (r.cap_cents != null) total = Math.min(total, r.cap_cents);
    return total;
  }

  function remainder(catId: string): number {
    const planned = sources.reduce((sum,s)=> sum + planFor(catId, s.id), 0);
    const spent = spentByCat[catId] || 0;
    return planned - spent;
  }
</script>

<section>
  <h1 class="h1">План месяца</h1>
  <p class="sub">Задайте проценты или фикс для каждой пары «Категория × Источник». Вверху введите суммы ожидаемых доходов.</p>

  <!-- Симулятор доходов -->
  <div class="card">
    <div class="h2">Ожидаемые суммы по источникам</div>
    <div class="row">
      {#each sources as s}
        <div>
          <label class="label" for="sim-{s.id}">{s.name} ({s.currency || 'RUB'})</label>
          <input id="sim-{s.id}" class="input" inputmode="decimal" placeholder="0.00" bind:value={sim[s.id]}
                 on:change={(e)=> onSimChange(s.id, (e.target as HTMLInputElement).value)} />
        </div>
      {/each}
    </div>
  </div>

  <div style="height:12px"></div>

  <!-- Таблица плана -->
  <div class="card" style="overflow:auto">
    <table style="width:100%; border-collapse:collapse; min-width:780px">
      <thead style="text-align:left; color:var(--muted); font-size:12px">
        <tr>
          <th style="padding:8px">Категория</th>
          <th style="padding:8px">Источник</th>
          <th style="padding:8px; width:110px">Ввод %</th>
          <th style="padding:8px; width:140px">Ввод ₽</th>
          <th style="padding:8px; width:120px">План ₽</th>
          <th style="padding:8px; width:120px">Минусы ₽</th>
          <th style="padding:8px; width:120px">Остаток ₽</th>
        </tr>
      </thead>
      <tbody>
        {#each categories as c}
          {#each sources as s}
          <tr style="border-top:1px solid rgba(255,255,255,.06)">
            <td style="padding:8px">{c.name}</td>
            <td style="padding:8px">{s.name}</td>
            <td style="padding:8px">
              {#key c.id + ':' + s.id}
                <input class="input" style="padding:10px; font-size:16px" inputmode="decimal"
                  value={(rules.find(r=>r.category_id===c.id && r.source_id===s.id)?.percent ?? 0).toString()}
                  on:change={(e)=> onPercentChange(c.id, s.id, (e.target as HTMLInputElement).value)} />
              {/key}
            </td>
            <td style="padding:8px">
              {#key 'f'+c.id + ':' + s.id}
                <input class="input" style="padding:10px; font-size:16px" inputmode="decimal"
                  value={(() => {
                    const r = rules.find(r=>r.category_id===c.id && r.source_id===s.id);
                    return r?.fixed_cents ? (r.fixed_cents/100).toFixed(2) : '';
                  })()}
                  placeholder="0.00"
                  on:change={(e)=> onFixedChange(c.id, s.id, (e.target as HTMLInputElement).value)} />
              {/key}
            </td>
            <td style="padding:8px; font-variant-numeric: tabular-nums">{rub(planFor(c.id, s.id))}</td>
            {#if s === sources[0]}
              <!-- объединяем ячейки «Минусы» и «Остаток» по категории -->
              <td style="padding:8px; font-variant-numeric: tabular-nums" rowspan={sources.length}>
                {rub(spentByCat[c.id] || 0)}
              </td>
              <td style="padding:8px; font-variant-numeric: tabular-nums" rowspan={sources.length}>
                {rub(remainder(c.id))}
              </td>
            {/if}
          </tr>
          {/each}
        {/each}
      </tbody>
    </table>
  </div>
</section>