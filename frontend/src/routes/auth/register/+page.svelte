<script lang="ts">
  import { register } from '$lib/api';
  import { goto } from '$app/navigation';
  let email = ''; let password = ''; let error = '';

  async function onSubmit() {
    error = '';
    try { await register(email, password); await goto('/'); }
    catch (e) { error = String(e); }
  }
</script>

<section style="font-family:system-ui; padding:16px; max-width:480px; margin:auto">
  <h2>Регистрация</h2>
  {#if error}<div style="color:#b91c1c">{error}</div>{/if}
  <label for="register-email">Email<br/><input id="register-email" bind:value={email} type="email" required /></label><br/><br/>
  <label for="register-password">Пароль<br/><input id="register-password" bind:value={password} type="password" minlength="6" required /></label><br/><br/>
  <button on:click|preventDefault={onSubmit}>Создать</button>
</section>