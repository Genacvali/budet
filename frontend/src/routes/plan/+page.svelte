<script lang="ts">
  import { onMount } from 'svelte';
  import { db, type Category, type Operation } from '$lib/db';

  let categories: Category[] = [];
  let operations: Operation[] = [];
  let planData: Array<{
    category: Category;
    planned: number;
    actual: number;
    remaining: number;
    percentage: number;
    status: 'ok' | 'warning' | 'danger';
  }> = [];

  onMount(async () => {
    categories = await db.categories.where('deleted_at').equals(null).toArray();
    operations = await db.operations.where('deleted_at').equals(null).toArray();
    
    // Группируем операции по категориям за текущий месяц
    const now = new Date();
    const currentMonth = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0');
    
    const monthlyOperations = operations.filter(op => op.date.startsWith(currentMonth));
    
    planData = categories.map(category => {
      const categoryOps = monthlyOperations.filter(op => op.category_id === category.id);
      const actual = categoryOps.reduce((sum, op) => sum + op.amount_cents, 0) / 100;
      const planned = category.limit_value || 0;
      const remaining = planned - actual;
      const percentage = planned > 0 ? Math.min((actual / planned) * 100, 100) : 0;
      
      let status: 'ok' | 'warning' | 'danger' = 'ok';
      if (percentage > 90) status = 'danger';
      else if (percentage > 70) status = 'warning';
      
      return {
        category,
        planned,
        actual,
        remaining,
        percentage,
        status
      };
    }).filter(item => item.planned > 0); // Показываем только категории с планом
  });

  function formatMoney(amount: number): string {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'ok': return 'var(--ok)';
      case 'warning': return 'var(--warning)';
      case 'danger': return 'var(--danger)';
      default: return 'var(--muted)';
    }
  }

  $: totalPlanned = planData.reduce((sum, item) => sum + item.planned, 0);
  $: totalActual = planData.reduce((sum, item) => sum + item.actual, 0);
  $: totalRemaining = totalPlanned - totalActual;
</script>

<style>
  .plan-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 16px;
  }
  .plan-table th {
    text-align: left;
    padding: 12px 8px;
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }
  .plan-table td {
    padding: 12px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
  }
  .category-name {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
  }
  .category-icon {
    width: 20px;
    height: 20px;
    border-radius: 6px;
    display: grid;
    place-items: center;
    font-size: 12px;
  }
  .progress-bar {
    width: 100%;
    height: 6px;
    background: rgba(255,255,255,0.1);
    border-radius: 3px;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease;
  }
  .amount {
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
    font-size: 14px;
  }
  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }
  .summary-card {
    background: var(--card);
    border-radius: var(--radius);
    padding: 16px;
    border: 1px solid rgba(255,255,255,.06);
    text-align: center;
  }
  .summary-value {
    font-size: 24px;
    font-weight: 700;
    margin: 8px 0;
    font-family: 'SF Mono', Monaco, monospace;
  }
  .summary-label {
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
</style>

<section>
  <h1 class="h1">План бюджета</h1>
  <p class="sub">Контроль расходов по категориям за текущий месяц</p>

  <!-- Сводка -->
  <div class="summary-grid">
    <div class="summary-card">
      <div class="summary-label">Запланировано</div>
      <div class="summary-value" style="color: var(--text)">{formatMoney(totalPlanned)}</div>
    </div>
    <div class="summary-card">
      <div class="summary-label">Потрачено</div>
      <div class="summary-value" style="color: var(--warning)">{formatMoney(totalActual)}</div>
    </div>
    <div class="summary-card">
      <div class="summary-label">Остается</div>
      <div class="summary-value" style="color: {totalRemaining >= 0 ? 'var(--ok)' : 'var(--danger)'}">
        {formatMoney(totalRemaining)}
      </div>
    </div>
  </div>

  <!-- Таблица планов -->
  <div class="card">
    <div class="h2">План по категориям</div>
    
    {#if planData.length === 0}
      <p class="sub">
        Нет категорий с установленными лимитами. 
        <a href="/settings">Настройте лимиты</a> для отслеживания бюджета.
      </p>
    {:else}
      <table class="plan-table">
        <thead>
          <tr>
            <th>Категория</th>
            <th>План</th>
            <th>Факт</th>
            <th>Остаток</th>
            <th>Прогресс</th>
          </tr>
        </thead>
        <tbody>
          {#each planData as item}
            <tr>
              <td>
                <div class="category-name">
                  <div 
                    class="category-icon" 
                    style="background-color: {item.category.color}; color: {item.category.color}22"
                  >
                    {item.category.icon || '💰'}
                  </div>
                  {item.category.name}
                </div>
              </td>
              <td>
                <div class="amount">{formatMoney(item.planned)}</div>
              </td>
              <td>
                <div class="amount" style="color: var(--warning)">{formatMoney(item.actual)}</div>
              </td>
              <td>
                <div 
                  class="amount" 
                  style="color: {item.remaining >= 0 ? 'var(--ok)' : 'var(--danger)'}"
                >
                  {formatMoney(item.remaining)}
                </div>
              </td>
              <td style="width: 120px;">
                <div class="progress-bar">
                  <div 
                    class="progress-fill" 
                    style="width: {item.percentage}%; background-color: {getStatusColor(item.status)}"
                  ></div>
                </div>
                <div style="font-size: 11px; color: var(--muted); margin-top: 4px;">
                  {Math.round(item.percentage)}%
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
    
    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.06);">
      <div class="row">
        <a class="btn secondary" href="/add">Добавить операцию</a>
        <a class="btn secondary" href="/settings">Настроить лимиты</a>
      </div>
    </div>
  </div>
</section>