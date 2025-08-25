<script lang="ts">
  import { onMount } from 'svelte';
  import { db, type Category } from '$lib/db';
  import { push } from '$lib/api';
  import { browser } from '$app/environment';

  let categories: Category[] = [];
  let amount = '';
  let category_id = '';
  let note = '';
  let saved = false;
  let error = '';

  onMount(async () => {
    // берём только активные РАСХОДные категории
    categories = (await db.categories.toArray()).filter(c => c.kind === 'expense' && !c.deleted_at);
    if (categories.length && !category_id) category_id = categories[0].id;
  });

  function cents(v: string): number {
    const num = Number(v.replace(',', '.'));
    if (!isFinite(num)) return 0;
    return Math.round(num * 100);
  }

  async function saveExpense() {
    error = '';
    saved = false;
    const amt = cents(amount);
    if (!amt || !category_id) { error = 'Заполните сумму и категорию'; return; }

    const now = new Date();
    const iso = now.toISOString();
    const id = (browser && crypto?.randomUUID) ? crypto.randomUUID() : Math.random().toString(36).slice(2);

    // Записываем как тип 'expense' с положительной суммой в центах
    await db.operations.put({
      id,
      user_id: 'local',         // на пуше сервер подменит на реального юзера
      type: 'expense',
      source_id: null,
      category_id,
      wallet: null,
      amount_cents: amt,
      currency: 'EUR',
      rate: 1.0,
      date: iso.slice(0,10),
      note: note || null,
      created_at: iso,
      updated_at: iso,
      deleted_at: null
    });

    // Синкнем без ожидания
    push();

    amount = '';
    note = '';
    saved = true;
    setTimeout(()=> saved = false, 1500);
  }
</script>

<section>
  <h1 class="h1">Минус</h1>
  <p class="sub">Быстрое списание расходов: сумма + категория — и готово.</p>

  <div class="card">
    {#if error}<div style="color:#ef4444; margin-bottom:10px">{error}</div>{/if}
    <div class="row">
      <div>
        <label class="label" for="minus-amount">Сумма</label>
        <input id="minus-amount" class="input" inputmode="decimal" placeholder="0.00" bind:value={amount} />
      </div>
      <div>
        <label class="label" for="minus-category">Категория</label>
        <select id="minus-category" class="select" bind:value={category_id}>
          {#each categories as c}
            <option value={c.id}>{c.name}</option>
          {/each}
        </select>
      </div>
    </div>

    <div style="height:8px"></div>
    <label class="label" for="minus-note">Заметка (опционально)</label>
    <input id="minus-note" class="input" placeholder="например: кофе" bind:value={note} />

    <div style="height:12px"></div>
    <button class="btn" on:click|preventDefault={saveExpense}>Списать</button>
    {#if saved}<span style="margin-left:8px; color:#22c55e">Сохранено</span>{/if}
  </div>
</section>