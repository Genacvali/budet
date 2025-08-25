<script lang="ts">
  import { register } from '$lib/api';
  import { goto } from '$app/navigation';
  import { isAuthenticated } from '$lib/stores';
  
  let email = '';
  let password = '';
  let confirmPassword = '';
  let error = '';
  let loading = false;
  
  async function handleRegister() {
    if (!email || !password || !confirmPassword) return;
    if (password !== confirmPassword) {
      error = 'Пароли не совпадают';
      return;
    }
    
    loading = true;
    error = '';
    
    try {
      await register(email, password);
      isAuthenticated.set(true);
      goto('/');
    } catch (e) {
      error = e instanceof Error ? e.message : 'Ошибка регистрации';
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center p-4">
  <div class="w-full max-w-md space-y-6">
    <div class="text-center">
      <h1 class="text-2xl font-bold">Регистрация</h1>
      <p class="text-gray-500 mt-2">Создайте новый аккаунт</p>
    </div>
    
    <form on:submit|preventDefault={handleRegister} class="space-y-4">
      <div>
        <label class="block text-sm font-medium mb-1">Email</label>
        <input 
          type="email" 
          bind:value={email}
          required
          class="w-full border rounded-lg px-3 py-2"
          placeholder="your@email.com"
        />
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-1">Пароль (минимум 6 символов)</label>
        <input 
          type="password" 
          bind:value={password}
          required
          minlength="6"
          class="w-full border rounded-lg px-3 py-2"
          placeholder="••••••••"
        />
      </div>
      
      <div>
        <label class="block text-sm font-medium mb-1">Повторите пароль</label>
        <input 
          type="password" 
          bind:value={confirmPassword}
          required
          minlength="6"
          class="w-full border rounded-lg px-3 py-2"
          placeholder="••••••••"
        />
      </div>
      
      {#if error}
        <div class="text-red-500 text-sm">{error}</div>
      {/if}
      
      <button 
        type="submit" 
        disabled={loading}
        class="w-full bg-sky-500 text-white py-2 rounded-lg font-medium hover:bg-sky-600 disabled:opacity-50"
      >
        {loading ? 'Регистрация...' : 'Зарегистрироваться'}
      </button>
    </form>
    
    <div class="text-center">
      <a href="/auth/login" class="text-sky-500 hover:underline">
        Уже есть аккаунт? Войти
      </a>
    </div>
  </div>
</div>