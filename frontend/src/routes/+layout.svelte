<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { pull, push } from '$lib/api';
  import '$lib/styles.css';

  let fatalError: string | null = null;
  let syncInterval: ReturnType<typeof setInterval>;

  if (browser) {
    window.addEventListener('error', (e) => { fatalError = String((e as any).error?.message || e.message); });
    window.addEventListener('unhandledrejection', (e) => { fatalError = String((e as any).reason?.message || (e as any).reason); });
  }

  onMount(() => {
    pull();
    syncInterval = setInterval(() => { push(); pull(); }, 5 * 60 * 1000);
    return () => clearInterval(syncInterval);
  });

  const nav = [
    { href: '/',        label: 'Домой',     icon: 'M10 3l2 4 4 .5-3 3 .7 4.2L10 13l-3.7 1.7.7-4.2-3-3 4-.5 2-4' },
    { href: '/minus',   label: 'Минус',     icon: 'M4 10h12' },
    { href: '/plan',    label: 'План',      icon: 'M3 14h14M3 10h14M3 6h14' },
    { href: '/reports', label: 'Отчёты',    icon: 'M4 14l3-4 3 2 4-6 2 3' },
    { href: '/settings',label: 'Настройки', icon: 'M4 10h12M8 6h8M2 14h8' }
  ];
</script>

<div class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <span class="brand-badge">◆</span> CrystalBudget
    </div>
  </div>
</div>

{#if fatalError}
  <div class="container">
    <div class="card" style="border-color:#7f1d1d">
      <div class="h2">Ошибка приложения</div>
      <div>{fatalError}</div>
    </div>
  </div>
{/if}

<div class="container">
  <slot />
</div>

<nav class="tabbar">
  <div class="tabs">
    {#each nav as n}
      <a class="tab" href={n.href} aria-label={n.label}>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d={n.icon} stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span>{n.label}</span>
      </a>
    {/each}
  </div>
</nav>