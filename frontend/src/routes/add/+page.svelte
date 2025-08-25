<script lang="ts">
  import { db, type Operation, type Category, type Source } from '$lib/db';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  
  let amount = '';
  let type: 'income' | 'expense' = 'expense';
  let category_id = '';
  let source_id: string | null = null;
  let note = '';
  let saving = false;
  
  let categories: Category[] = [];
  let sources: Source[] = [];
  
  onMount(async () => {
    await loadData();
  });
  
  async function loadData() {
    categories = (await db.categories.toArray()).filter(c => !c.deleted_at);
    sources = (await db.sources.toArray()).filter(s => !s.deleted_at);
  }
  
  $: filteredCategories = categories.filter(c => c.kind === type);
  
  // Генерация UUID без внешней зависимости
  function generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  
  async function save() {
    if (!amount || !category_id || saving) return;
    
    saving = true;
    try {
      const now = new Date().toISOString();
      const cents = Math.round(parseFloat(amount.replace(',', '.')) * 100);
      
      const op: Operation = {
        id: generateUUID(),
        user_id: 'local',
        type,
        source_id: type === 'income' ? (source_id || null) : null,
        category_id,
        amount_cents: cents,
        currency: 'EUR',
        rate: 1,
        date: now.slice(0, 10), // YYYY-MM-DD
        note: note || null,
        wallet: null,
        created_at: now,
        updated_at: now,
        deleted_at: null
      };
      
      await db.operations.put(op);
      await goto('/');
    } catch (error) {
      console.error('Error saving operation:', error);
      saving = false;
    }
  }

  // Быстрые кнопки сумм
  const quickAmounts = type === 'expense' 
    ? [100, 500, 1000, 2000, 5000]
    : [10000, 20000, 50000, 100000];

  function setQuickAmount(value: number) {
    amount = (value / 100).toString();
  }
</script>

<style>
  .type-button {
    padding: 12px 16px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
    background: var(--card);
    color: var(--text);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-weight: 500;
  }
  
  .type-button.active {
    background: var(--brand);
    color: #001a25;
    border-color: var(--brand);
    transform: translateY(-1px);
  }
  
  .type-button.expense.active {
    background: var(--danger);
    border-color: var(--danger);
  }
  
  .type-button.income.active {
    background: var(--ok);
    border-color: var(--ok);
  }
  
  .quick-amount {
    padding: 8px 12px;
    border-radius: 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: var(--muted);
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: 'SF Mono', Monaco, monospace;
    font-size: 12px;
  }
  
  .quick-amount:hover {
    background: var(--brand);
    color: #001a25;
    border-color: var(--brand);
  }
  
  .amount-input {
    font-size: 24px !important;
    font-weight: 600;
    text-align: center;
    font-family: 'SF Mono', Monaco, monospace;
  }
</style>

<section>
  <h1 class="h1">Добавить операцию</h1>
  <p class="sub">Быстрое добавление дохода или расхода</p>

  <div class="card">
    <!-- Тип операции -->
    <div style="margin-bottom: 24px;">
      <div class="label">Тип операции</div>
      <div class="row">
        <button 
          type="button"
          class="type-button expense {type === 'expense' ? 'active' : ''}"
          on:click={() => type = 'expense'}
        >
          📉 Расход
        </button>
        <button 
          type="button"
          class="type-button income {type === 'income' ? 'active' : ''}"
          on:click={() => type = 'income'}
        >
          📈 Доход
        </button>
      </div>
    </div>

    <!-- Источник дохода -->
    {#if type === 'income' && sources.length > 0}
      <div style="margin-bottom: 20px;">
        <label class="label" for="source-select">Источник дохода</label>
        <select id="source-select" bind:value={source_id} class="input select">
          <option value={null}>Выберите источник...</option>
          {#each sources as source}
            <option value={source.id}>{source.name}</option>
          {/each}
        </select>
      </div>
    {/if}

    <!-- Категория -->
    <div style="margin-bottom: 20px;">
      <label class="label" for="category-select">Категория</label>
      <select id="category-select" bind:value={category_id} required class="input select">
        <option value="">Выберите категорию...</option>
        {#each filteredCategories as category}
          <option value={category.id}>
            {category.icon || '💰'} {category.name}
          </option>
        {/each}
      </select>
    </div>

    <!-- Сумма -->
    <div style="margin-bottom: 20px;">
      <label class="label" for="amount-input">Сумма (₽)</label>
      <input 
        id="amount-input"
        type="text"
        inputmode="decimal"
        bind:value={amount}
        required
        placeholder="0"
        class="input amount-input"
      />
      
      <!-- Быстрые кнопки сумм -->
      <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px;">
        {#each quickAmounts as quickAmount}
          <button 
            type="button"
            class="quick-amount"
            on:click={() => setQuickAmount(quickAmount)}
          >
            {(quickAmount / 100).toLocaleString('ru-RU')} ₽
          </button>
        {/each}
      </div>
    </div>

    <!-- Заметка -->
    <div style="margin-bottom: 24px;">
      <label class="label" for="note-input">Заметка (необязательно)</label>
      <input 
        id="note-input"
        type="text"
        bind:value={note}
        placeholder="Описание операции..."
        class="input"
      />
    </div>

    <!-- Кнопки действий -->
    <div class="row">
      <button 
        class="btn secondary"
        on:click={() => history.back()}
      >
        Отмена
      </button>
      <button 
        class="btn"
        on:click={save}
        disabled={!amount || !category_id || saving}
      >
        {saving ? '💾 Сохранение...' : '✅ Сохранить'}
      </button>
    </div>
  </div>

  <!-- Подсказка для новых пользователей -->
  {#if filteredCategories.length === 0}
    <div class="card" style="border-color: var(--warning); background: rgba(245,158,11,0.05);">
      <div class="h2" style="color: var(--warning);">
        📝 Настройте категории
      </div>
      <p style="color: var(--muted);">
        Для добавления операций нужно сначала создать категории {type === 'income' ? 'доходов' : 'расходов'}.
      </p>
      <div style="margin-top: 16px;">
        <a class="btn secondary" href="/settings">Перейти к настройкам</a>
      </div>
    </div>
  {/if}
</section>