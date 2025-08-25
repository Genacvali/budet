<script lang="ts">
  import { browser } from '$app/environment';
  let hasToken = false;
  if (browser) { try { hasToken = !!localStorage.getItem('jwt'); } catch {} }
</script>

<section>
  <h1 class="h1">CrystalBudget</h1>
  <p class="sub">Локальный учёт бюджета с синком: офлайн, быстро, просто.</p>

  <div class="card">
    <div class="h2">Быстрый старт</div>
    {#if !hasToken}
      <p class="sub">Зарегистрируйтесь или войдите, чтобы синхронизировать данные между устройствами.</p>
      <div class="row">
        <a class="btn" href="/auth/register">Регистрация</a>
        <a class="btn secondary" href="/auth/login">Войти</a>
      </div>
    {:else}
      <p class="sub">Вы вошли. Начните с добавления операции или настройте план распределения.</p>
      <div class="row">
        <a class="btn" href="/add">Добавить операцию</a>
        <a class="btn secondary" href="/plan">План</a>
      </div>
    {/if}
  </div>
</section>