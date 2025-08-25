<script lang="ts">
  import { db, type Operation } from '$lib/db';
  import { onMount } from 'svelte';
  
  let operations: Operation[] = [];
  let balance = 0;
  
  onMount(async () => {
    operations = await db.operations.orderBy('date').reverse().limit(20).toArray();
    const ops = await db.operations.toArray();
    balance = ops.reduce((acc, o) => acc + (o.type === 'income' ? 1 : -1) * o.amount_cents, 0) / 100;
  });
</script>

<div class="max-w-screen-sm mx-auto p-4 space-y-4">
  <h1 class="text-2xl font-semibold">Баланс: {balance.toFixed(2)} ₽</h1>
  
  <div class="space-y-2">
    {#each operations as op}
      <div class="flex items-center justify-between border rounded-xl p-3">
        <div class="text-sm">
          <div class="font-medium">{op.type === 'income' ? 'Приход' : 'Расход'} • {new Date(op.date).toLocaleDateString()}</div>
          <div class="text-gray-500">{op.note || 'Без заметки'}</div>
        </div>
        <div class="font-mono">{(op.type === 'income' ? '+' : '-')}{(op.amount_cents / 100).toFixed(2)} ₽</div>
      </div>
    {/each}
  </div>
  
  {#if operations.length === 0}
    <div class="text-center text-gray-500 py-8">
      <p>Операций пока нет</p>
      <a href="/add" class="text-sky-500 underline">Добавить первую операцию</a>
    </div>
  {/if}
</div>