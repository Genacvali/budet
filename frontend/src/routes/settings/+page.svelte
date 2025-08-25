<script lang="ts">
  import { onMount } from 'svelte';
  import { db } from '$lib/db';
  import { browser } from '$app/environment';

  let rollover = false;
  let saved = false;

  onMount(async () => {
    const v = await db.meta.get('rollover_enabled');
    rollover = v?.value === '1';
  });

  async function toggleRollover() {
    rollover = !rollover;
    await db.meta.put({ key: 'rollover_enabled', value: rollover ? '1' : '0' });
    saved = true; setTimeout(()=> saved=false, 1200);
  }

  // Временная ручная кнопка «перенести сейчас» (нулевой MVP):
  // просто помечаем месяц применённым — логика перерасчёта бюджета будет
  // добавлена вместе с модулем "План". Здесь только фиксация месяца.
  async function applyRolloverNow() {
    const ym = new Date().toISOString().slice(0,7); // YYYY-MM
    await db.meta.put({ key: 'last_rollover_month', value: ym });
    saved = true; setTimeout(()=> saved=false, 1200);
  }
</script>

<section>
  <h1 class="h1">Настройки</h1>
  <p class="sub">Общие параметры приложения.</p>

  <div class="card">
    <div class="h2">Перенос остатка на следующий месяц</div>
    <p class="sub">Включите, чтобы остатки бюджета автоматически переносились. (Логика будет применяться на экране «План».)</p>

    <label style="display:flex; align-items:center; gap:10px">
      <input type="checkbox" checked={rollover} on:change={toggleRollover} />
      Включить перенос остатка
    </label>

    <div style="height:10px"></div>
    <button class="btn secondary" on:click={applyRolloverNow}>Отметить перенос сейчас</button>
    {#if saved}<span style="margin-left:8px; color:#22c55e">Сохранено</span>{/if}
  </div>
</section>