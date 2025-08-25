<script lang="ts">
  import { browser } from '$app/environment';
  let hasToken = false;
  if (browser) { try { hasToken = !!localStorage.getItem('jwt'); } catch {} }
</script>

<section style="font-family:system-ui; padding:16px; max-width:720px; margin:auto">
  <h1>Budget PWA</h1>
  <p>Локальный учёт бюджета с синком.</p>

  {#if !hasToken}
    <p><a href="/auth/register">Регистрация</a> · <a href="/auth/login">Войти</a></p>
  {:else}
    <p><a href="/add">Добавить операцию</a> · <a href="/plan">План</a> · <a href="/reports">Отчёты</a></p>
  {/if}
</section>