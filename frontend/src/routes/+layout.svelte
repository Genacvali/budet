<script lang="ts">
  import { onMount } from 'svelte';
  import { pull, push } from '$lib/api';
  import { isAuthenticated, syncInProgress } from '$lib/stores';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import '../app.postcss';

  let showNav = true;
  
  onMount(async () => {
    if ($isAuthenticated) {
      await pull();
    }
  });

  // Периодический синк каждые 5 минут
  let syncInterval: ReturnType<typeof setInterval>;
  onMount(() => {
    if ($isAuthenticated) {
      syncInterval = setInterval(async () => {
        if (!$syncInProgress) {
          syncInProgress.set(true);
          try {
            await push();
            await pull();
          } catch (e) {
            console.error('Sync failed:', e);
          }
          syncInProgress.set(false);
        }
      }, 5 * 60 * 1000);
    }
    
    return () => {
      if (syncInterval) clearInterval(syncInterval);
    };
  });

  const doSync = async () => {
    if ($syncInProgress) return;
    syncInProgress.set(true);
    try {
      await push(); 
      await pull(); 
    } catch (e) {
      console.error('Manual sync failed:', e);
    }
    syncInProgress.set(false);
  };

  $: showNav = $isAuthenticated && !$page.url.pathname.includes('auth');
</script>

<div class="min-h-screen {showNav ? 'pb-20' : ''}">
  <slot />
</div>

{#if showNav}
<nav class="fixed bottom-0 inset-x-0 border-t bg-white/80 dark:bg-gray-900/80 backdrop-blur">
  <div class="max-w-screen-sm mx-auto grid grid-cols-5 text-center text-xs">
    <a href="/" class="p-3 flex flex-col items-center gap-1" class:text-sky-500={$page.url.pathname === '/'}>
      <div>🏠</div>
      <div>Домой</div>
    </a>
    <a href="/add" class="p-3 flex flex-col items-center gap-1" class:text-sky-500={$page.url.pathname === '/add'}>
      <div>➕</div>
      <div>Добавить</div>
    </a>
    <a href="/plan" class="p-3 flex flex-col items-center gap-1" class:text-sky-500={$page.url.pathname === '/plan'}>
      <div>📊</div>
      <div>План</div>
    </a>
    <a href="/reports" class="p-3 flex flex-col items-center gap-1" class:text-sky-500={$page.url.pathname === '/reports'}>
      <div>📈</div>
      <div>Отчёты</div>
    </a>
    <button on:click={doSync} class="p-3 flex flex-col items-center gap-1" disabled={$syncInProgress}>
      <div>{$syncInProgress ? '⏳' : '🔄'}</div>
      <div>Синк</div>
    </button>
  </div>
</nav>
{/if}