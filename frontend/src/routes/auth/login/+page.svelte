<script lang="ts">
  import { login } from '$lib/api';
  import { goto } from '$app/navigation';
  let email = ''; let password = ''; let error = '';

  async function onSubmit() {
    error = '';
    try { await login(email, password); await goto('/'); }
    catch (e) { error = String(e); }
  }
</script>

<section style="font-family:system-ui; padding:16px; max-width:480px; margin:auto">
  <h2>Вход</h2>
  {#if error}<div style="color:#b91c1c">{error}</div>{/if}
  <label for="login-email">Email<br/><input id="login-email" bind:value={email} type="email" required /></label><br/><br/>
  <label for="login-password">Пароль<br/><input id="login-password" bind:value={password} type="password" minlength="6" required /></label><br/><br/>
  <button on:click|preventDefault={onSubmit}>Войти</button>
</section>