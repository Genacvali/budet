<script lang="ts">
  import { onMount } from 'svelte';
  import { db, type Source } from '$lib/db';
  import { browser } from '$app/environment';

  let list: Source[] = [];
  let name = '';
  let currency = 'RUB';
  let color = '#38bdf8';
  let expected_date = '';

  async function reload() {
    list = (await db.sources.toArray()).filter(s => !s.deleted_at).sort((a,b)=>a.name.localeCompare(b.name));
  }
  onMount(reload);

  function uuid() {
    return (browser && crypto?.randomUUID) ? crypto.randomUUID() : Math.random().toString(36).slice(2);
  }

  async function add() {
    if (!name.trim()) return;
    const now = new Date().toISOString();
    await db.sources.put({
      id: uuid(), user_id: 'local',
      name: name.trim(),
      currency,
      expected_date: expected_date || null,
      icon: null, color,
      created_at: now, updated_at: now, deleted_at: null
    });
    name = ''; expected_date = '';
    await reload();
  }

  async function remove(id: string) {
    const now = new Date().toISOString();
    const src = await db.sources.get(id);
    if (!src) return;
    src.deleted_at = now; src.updated_at = now;
    await db.sources.put(src);
    await reload();
  }
</script>

<section>
  <h1 class="h1">Источники дохода</h1>
  <p class="sub">Добавьте источники (ЗП, Аванс, Подарки...). Они используются в Плане.</p>

  <div class="card">
    <div class="row">
      <div>
        <label class="label" for="source-name">Название</label>
        <input id="source-name" class="input" bind:value={name} placeholder="Зарплата" />
      </div>
      <div>
        <label class="label" for="source-currency">Валюта</label>
        <input id="source-currency" class="input" bind:value={currency} placeholder="RUB" />
      </div>
    </div>

    <div class="row">
      <div>
        <label class="label" for="source-date">Ожидаемая дата (опц.)</label>
        <input id="source-date" class="input" type="date" bind:value={expected_date} />
      </div>
      <div>
        <label class="label" for="source-color">Цвет</label>
        <input id="source-color" class="input" type="color" bind:value={color} />
      </div>
    </div>

    <div style="height:12px"></div>
    <button class="btn" on:click={add}>Добавить источник</button>
  </div>

  <div style="height:12px"></div>
  {#if list.length === 0}
    <div class="card">Пока пусто.</div>
  {:else}
    {#each list as s}
      <div class="card" style="display:flex; align-items:center; justify-content:space-between; gap:12px">
        <div style="display:flex; align-items:center; gap:10px">
          <span style="width:14px; height:14px; background:{s.color || '#64748b'}; border-radius:4px; display:inline-block"></span>
          <div><strong>{s.name}</strong><div class="sub">{s.currency}{#if s.expected_date} · {s.expected_date}{/if}</div></div>
        </div>
        <button class="btn secondary" style="width:auto" on:click={() => remove(s.id)}>Удалить</button>
      </div>
    {/each}
  {/if}
</section>