<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { pull, push } from '$lib/api';
  import '$lib/styles.css';

  let fatalError: string | null = null;
  let syncInterval: number | undefined;
  let drawer = false;

  if (browser) {
    window.addEventListener('error', (e: ErrorEvent) => { 
      fatalError = String(e.error?.message || e.message); 
    });
    window.addEventListener('unhandledrejection', (e: PromiseRejectionEvent) => { 
      fatalError = String(e.reason?.message || e.reason); 
    });
  }

  onMount(() => {
    // работаем локально: синк включится, если появится токен (но мы его не используем)
    pull();
    syncInterval = setInterval(() => { 
      push(); 
      pull(); 
    }, 5 * 60 * 1000) as unknown as number;
    
    return () => {
      if (syncInterval) {
        clearInterval(syncInterval);
      }
    };
  });

  interface NavLink {
    href: string;
    label: string;
    icon: string;
  }

  const links: NavLink[] = [
    { href: '/',        label: 'Домой',        icon: 'M10 2l6 6v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8l6-6z' },
    { href: '/minus',   label: 'Минус',        icon: 'M4 10h12' },
    { href: '/plan',    label: 'План',         icon: 'M3 14h14M3 10h14M3 6h14' },
    { href: '/sources', label: 'Источники',    icon: 'M4 4h12v12H4z' },
    { href: '/reports', label: 'Отчёты',       icon: 'M4 14l3-4 3 2 4-6 2 3' },
    { href: '/settings',label: 'Настройки',    icon: 'M4 10h12M8 6h8M2 14h8' },
  ];
</script>

<div class="topbar">
  <div class="topbar-inner">
    <button class="btn secondary" style="width:auto; padding:10px 12px" on:click={() => drawer = true} aria-label="Меню">
      ☰
    </button>
    <div class="brand"><span class="brand-badge">◆</span> CrystalBudget</div>
  </div>
</div>

{#if drawer}
  <div class="drawer-backdrop" on:click={() => drawer = false}></div>
  <nav class="drawer" role="menu" aria-label="Главное меню">
    {#each links as n}
      <a class="navlink" href={n.href} on:click={() => drawer=false}>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6">
          <path d={n.icon} stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span>{n.label}</span>
      </a>
    {/each}
    <div class="spacer"></div>
  </nav>
{/if}

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