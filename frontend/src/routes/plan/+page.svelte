<script lang="ts">
  import { db } from '$lib/db';
  import { onMount } from 'svelte';
  
  let categories: any[] = [];
  let operations: any[] = [];
  let facts: Record<string, number> = {};
  
  onMount(async () => {
    categories = await db.categories.where('kind').equals('expense').and(c => !c.deleted_at).toArray();
    operations = await db.operations.where('type').equals('expense').and(o => !o.deleted_at).toArray();
    
    // Подсчет фактических трат по категориям
    facts = {};
    for (const op of operations) {
      facts[op.category_id] = (facts[op.category_id] || 0) + op.amount_cents;
    }
  });
  
  function getUsageColor(used: number, plan: number) {
    if (plan <= 0) return 'text-gray-400';
    const pct = used / plan;
    if (pct < 0.8) return 'text-green-600';
    if (pct < 1.0) return 'text-yellow-600';
    return 'text-red-600';
  }
</script>

<div class="max-w-screen-sm mx-auto p-4 space-y-4">
  <h1 class="text-xl font-semibold">План месяца</h1>
  
  <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
    <p class="text-blue-700 text-sm">
      💡 Планы будут автоматически рассчитываться на основе правил распределения доходов
    </p>
  </div>
  
  <div class="space-y-3">
    {#each categories as category}
      {@const spent = facts[category.id] || 0}
      {@const plan = 0} <!-- TODO: рассчитать план из правил -->
      
      <div class="border rounded-lg p-4">
        <div class="flex justify-between items-start mb-2">
          <div>
            <h3 class="font-medium">{category.name}</h3>
            <div class="text-sm text-gray-500">
              План: {(plan / 100).toFixed(2)} ₽
            </div>
          </div>
          <div class="text-right">
            <div class="font-mono {getUsageColor(spent, plan)}">
              {(spent / 100).toFixed(2)} ₽
            </div>
            <div class="text-xs text-gray-500">
              потрачено
            </div>
          </div>
        </div>
        
        {#if plan > 0}
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div 
              class="h-2 rounded-full {spent/plan < 0.8 ? 'bg-green-500' : spent/plan < 1.0 ? 'bg-yellow-500' : 'bg-red-500'}"
              style="width: {Math.min((spent/plan) * 100, 100)}%"
            ></div>
          </div>
          <div class="text-xs text-gray-500 mt-1">
            Остаток: {((plan - spent) / 100).toFixed(2)} ₽
          </div>
        {:else}
          <div class="text-xs text-gray-400">
            План не задан
          </div>
        {/if}
      </div>
    {/each}
  </div>
  
  {#if categories.length === 0}
    <div class="text-center text-gray-500 py-8">
      <p>Категории расходов не найдены</p>
      <a href="/settings" class="text-sky-500 underline">Добавить категории</a>
    </div>
  {/if}
</div>