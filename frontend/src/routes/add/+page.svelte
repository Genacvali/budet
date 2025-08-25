<script lang="ts">
  import { db, type Operation } from '$lib/db';
  import { generateUUID } from '$lib/calc';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  
  let amount = '';
  let type: 'income' | 'expense' = 'expense';
  let category_id = '';
  let source_id: string | null = null;
  let note = '';
  
  let categories: any[] = [];
  let sources: any[] = [];
  
  onMount(async () => {
    await loadData();
  });
  
  async function loadData() {
    categories = await db.categories.where('deleted_at').equals(null).toArray();
    sources = await db.sources.where('deleted_at').equals(null).toArray();
  }
  
  $: filteredCategories = categories.filter(c => c.kind === (type === 'income' ? 'income' : 'expense'));
  
  async function save() {
    if (!amount || !category_id) return;
    
    const now = new Date().toISOString();
    const cents = Math.round(parseFloat(amount.replace(',', '.')) * 100);
    
    const op: Operation = {
      id: generateUUID(),
      user_id: 'local',
      type,
      source_id: type === 'income' ? (source_id || null) : null,
      category_id,
      amount_cents: cents,
      currency: 'RUB',
      rate: 1,
      date: now,
      note: note || null,
      wallet: null,
      created_at: now,
      updated_at: now,
      deleted_at: null
    };
    
    await db.operations.put(op);
    goto('/');
  }
</script>

<div class="max-w-screen-sm mx-auto p-4 space-y-4">
  <div class="flex items-center gap-3">
    <button on:click={() => history.back()} class="text-sky-500">← Назад</button>
    <h1 class="text-xl font-semibold">Добавить операцию</h1>
  </div>
  
  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium mb-2">Тип операции</label>
      <div class="grid grid-cols-2 gap-2">
        <button 
          type="button"
          on:click={() => type = 'expense'}
          class="p-3 rounded-lg border {type === 'expense' ? 'bg-red-50 border-red-200 text-red-700' : 'border-gray-200'}"
        >
          Расход
        </button>
        <button 
          type="button"
          on:click={() => type = 'income'}
          class="p-3 rounded-lg border {type === 'income' ? 'bg-green-50 border-green-200 text-green-700' : 'border-gray-200'}"
        >
          Доход
        </button>
      </div>
    </div>
    
    {#if type === 'income' && sources.length > 0}
      <div>
        <label class="block text-sm font-medium mb-2">Источник дохода</label>
        <select bind:value={source_id} class="w-full border rounded-lg p-3">
          <option value="">Выберите источник...</option>
          {#each sources as s}
            <option value={s.id}>{s.name}</option>
          {/each}
        </select>
      </div>
    {/if}
    
    <div>
      <label class="block text-sm font-medium mb-2">Категория</label>
      <select bind:value={category_id} required class="w-full border rounded-lg p-3">
        <option value="">Выберите категорию...</option>
        {#each filteredCategories as c}
          <option value={c.id}>{c.name}</option>
        {/each}
      </select>
    </div>
    
    <div>
      <label class="block text-sm font-medium mb-2">Сумма (₽)</label>
      <input 
        type="text"
        inputmode="decimal"
        bind:value={amount}
        required
        placeholder="0.00"
        class="w-full border rounded-lg p-3 text-lg font-mono"
      />
    </div>
    
    <div>
      <label class="block text-sm font-medium mb-2">Заметка (необязательно)</label>
      <input 
        type="text"
        bind:value={note}
        placeholder="Описание операции..."
        class="w-full border rounded-lg p-3"
      />
    </div>
    
    <button 
      on:click={save}
      disabled={!amount || !category_id}
      class="w-full bg-sky-500 text-white py-3 rounded-lg font-medium hover:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Сохранить операцию
    </button>
  </div>
</div>