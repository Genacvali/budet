<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { pull, push } from '$lib/api';

  let fatalError: string | null = null;
  let syncInterval: ReturnType<typeof setInterval>;

  if (browser) {
    window.addEventListener('error', (e) => { fatalError = String((e as any).error?.message || e.message); });
    window.addEventListener('unhandledrejection', (e) => { fatalError = String((e as any).reason?.message || (e as any).reason); });
  }

  onMount(() => {
    // первая синхронизация
    pull();
    // периодический синк
    syncInterval = setInterval(() => { push(); pull(); }, 5 * 60 * 1000);
    return () => clearInterval(syncInterval);
  });
</script>

{#if fatalError}
  <div style="padding:12px; background:#fee2e2; color:#7f1d1d; font-family:system-ui">
    <strong>Ошибка приложения:</strong> {fatalError}
  </div>
{/if}

<slot />