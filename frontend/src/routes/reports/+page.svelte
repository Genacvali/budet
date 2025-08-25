<script lang="ts">
  import { onMount } from 'svelte';
  import { db, type Operation, type Category } from '$lib/db';

  let operations: Operation[] = [];
  let categories: Category[] = [];
  let period: 'week' | 'month' | 'year' = 'month';
  let loading = true;

  // Аналитические данные
  let totalIncome = 0;
  let totalExpense = 0;
  let balance = 0;
  let categoryStats: Array<{
    category: Category;
    amount: number;
    percentage: number;
    count: number;
  }> = [];
  
  let recentOperations: Operation[] = [];
  let dailyStats: Array<{ date: string; income: number; expense: number; }> = [];

  onMount(async () => {
    await loadData();
  });

  async function loadData() {
    loading = true;
    
    categories = (await db.categories.toArray()).filter(c => !c.deleted_at);
    operations = (await db.operations.toArray()).filter(o => !o.deleted_at);
    
    calculateStats();
    loading = false;
  }

  function calculateStats() {
    const now = new Date();
    let startDate: Date;
    
    // Определяем период для анализа
    switch (period) {
      case 'week':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'month':
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'year':
        startDate = new Date(now.getFullYear(), 0, 1);
        break;
    }

    const periodOps = operations.filter(op => new Date(op.date) >= startDate);
    
    // Общие суммы
    totalIncome = periodOps
      .filter(op => op.type === 'income')
      .reduce((sum, op) => sum + op.amount_cents, 0) / 100;
      
    totalExpense = periodOps
      .filter(op => op.type === 'expense')
      .reduce((sum, op) => sum + op.amount_cents, 0) / 100;
      
    balance = totalIncome - totalExpense;

    // Статистика по категориям (только расходы)
    const expenseOps = periodOps.filter(op => op.type === 'expense');
    const categoryTotals = new Map<string, { amount: number; count: number }>();
    
    expenseOps.forEach(op => {
      const current = categoryTotals.get(op.category_id) || { amount: 0, count: 0 };
      categoryTotals.set(op.category_id, {
        amount: current.amount + op.amount_cents,
        count: current.count + 1
      });
    });

    categoryStats = Array.from(categoryTotals.entries())
      .map(([categoryId, data]) => {
        const category = categories.find(c => c.id === categoryId);
        if (!category) return null;
        
        const amount = data.amount / 100;
        const percentage = totalExpense > 0 ? (amount / totalExpense) * 100 : 0;
        
        return {
          category,
          amount,
          percentage,
          count: data.count
        };
      })
      .filter(item => item !== null)
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 10); // Топ-10 категорий

    // Недавние операции
    recentOperations = operations
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5);

    // Дневная статистика за последние 7 дней
    dailyStats = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      const dateStr = date.toISOString().slice(0, 10);
      
      const dayOps = operations.filter(op => op.date === dateStr);
      const dayIncome = dayOps.filter(op => op.type === 'income').reduce((sum, op) => sum + op.amount_cents, 0) / 100;
      const dayExpense = dayOps.filter(op => op.type === 'expense').reduce((sum, op) => sum + op.amount_cents, 0) / 100;
      
      dailyStats.push({ date: dateStr, income: dayIncome, expense: dayExpense });
    }
  }

  $: {
    if (!loading) calculateStats();
  }

  function formatMoney(amount: number): string {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('ru-RU', { 
      day: 'numeric', 
      month: 'short' 
    });
  }

  function getCategoryById(id: string): Category | undefined {
    return categories.find(c => c.id === id);
  }
</script>

<style>
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }
  
  .stat-card {
    background: var(--card);
    border-radius: var(--radius);
    padding: 16px;
    border: 1px solid rgba(255,255,255,.06);
    text-align: center;
  }
  
  .stat-value {
    font-size: 24px;
    font-weight: 700;
    margin: 8px 0;
    font-family: 'SF Mono', Monaco, monospace;
  }
  
  .stat-label {
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .period-selector {
    display: flex;
    gap: 4px;
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 4px;
    margin-bottom: 24px;
  }
  
  .period-btn {
    padding: 8px 12px;
    border-radius: 6px;
    background: transparent;
    border: none;
    color: var(--muted);
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.2s ease;
  }
  
  .period-btn.active {
    background: var(--brand);
    color: #001a25;
  }

  .category-bar {
    width: 100%;
    height: 8px;
    background: rgba(255,255,255,0.1);
    border-radius: 4px;
    overflow: hidden;
    margin-top: 8px;
  }
  
  .category-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
  }

  .chart {
    display: flex;
    align-items: end;
    gap: 8px;
    height: 120px;
    padding: 16px 0;
    border-top: 1px solid rgba(255,255,255,0.06);
  }
  
  .chart-bar {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }
  
  .chart-income, .chart-expense {
    width: 100%;
    border-radius: 2px 2px 0 0;
    min-height: 2px;
    transition: height 0.5s ease;
  }
  
  .chart-income {
    background: var(--ok);
  }
  
  .chart-expense {
    background: var(--danger);
    margin-top: 2px;
  }
  
  .chart-date {
    font-size: 10px;
    color: var(--muted);
    margin-top: 4px;
  }

  .recent-list {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  
  .recent-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.03);
  }
  
  .recent-item:last-child {
    border-bottom: none;
  }
  
  .recent-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: grid;
    place-items: center;
    font-size: 14px;
  }
  
  .recent-info {
    flex: 1;
  }
  
  .recent-amount {
    font-family: 'SF Mono', Monaco, monospace;
    font-weight: 600;
  }
</style>

<section>
  <h1 class="h1">Отчёты</h1>
  <p class="sub">Аналитика доходов и расходов</p>

  <!-- Переключатель периода -->
  <div class="period-selector">
    <button 
      class="period-btn {period === 'week' ? 'active' : ''}"
      on:click={() => period = 'week'}
    >
      Неделя
    </button>
    <button 
      class="period-btn {period === 'month' ? 'active' : ''}"
      on:click={() => period = 'month'}
    >
      Месяц
    </button>
    <button 
      class="period-btn {period === 'year' ? 'active' : ''}"
      on:click={() => period = 'year'}
    >
      Год
    </button>
  </div>

  {#if loading}
    <div class="card">
      <div style="text-align: center; padding: 32px; color: var(--muted);">
        📊 Загружаем данные...
      </div>
    </div>
  {:else}
    <!-- Общая статистика -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Доходы</div>
        <div class="stat-value" style="color: var(--ok)">{formatMoney(totalIncome)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Расходы</div>
        <div class="stat-value" style="color: var(--danger)">{formatMoney(totalExpense)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Баланс</div>
        <div class="stat-value" style="color: {balance >= 0 ? 'var(--ok)' : 'var(--danger)'}">
          {formatMoney(balance)}
        </div>
      </div>
    </div>

    <!-- График по дням -->
    <div class="card">
      <div class="h2">Динамика за неделю</div>
      <div class="chart">
        {#each dailyStats as day}
          {@const maxAmount = Math.max(...dailyStats.map(d => Math.max(d.income, d.expense)), 1)}
          <div class="chart-bar">
            <div 
              class="chart-income" 
              style="height: {(day.income / maxAmount) * 80}px"
              title="Доходы: {formatMoney(day.income)}"
            ></div>
            <div 
              class="chart-expense" 
              style="height: {(day.expense / maxAmount) * 80}px"
              title="Расходы: {formatMoney(day.expense)}"
            ></div>
            <div class="chart-date">{formatDate(day.date)}</div>
          </div>
        {/each}
      </div>
      <div style="display: flex; gap: 16px; justify-content: center; margin-top: 12px; font-size: 11px;">
        <div style="display: flex; align-items: center; gap: 4px;">
          <div style="width: 12px; height: 4px; background: var(--ok); border-radius: 2px;"></div>
          Доходы
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
          <div style="width: 12px; height: 4px; background: var(--danger); border-radius: 2px;"></div>
          Расходы
        </div>
      </div>
    </div>

    <!-- Топ категорий расходов -->
    {#if categoryStats.length > 0}
      <div class="card">
        <div class="h2">Топ категорий расходов</div>
        {#each categoryStats as item}
          <div style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 8px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <div 
                  style="width: 16px; height: 16px; border-radius: 4px; background: {item.category.color}; display: grid; place-items: center; font-size: 10px;"
                >
                  {item.category.icon || '💰'}
                </div>
                <span style="font-weight: 500;">{item.category.name}</span>
                <span style="color: var(--muted); font-size: 12px;">({item.count} операций)</span>
              </div>
              <div style="font-family: 'SF Mono', Monaco, monospace; font-weight: 600;">
                {formatMoney(item.amount)}
              </div>
            </div>
            <div class="category-bar">
              <div 
                class="category-fill" 
                style="width: {item.percentage}%; background: {item.category.color};"
              ></div>
            </div>
            <div style="text-align: right; font-size: 11px; color: var(--muted); margin-top: 4px;">
              {item.percentage.toFixed(1)}% от общих расходов
            </div>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Последние операции -->
    {#if recentOperations.length > 0}
      <div class="card">
        <div class="h2">Последние операции</div>
        <ul class="recent-list">
          {#each recentOperations as op}
            {@const category = getCategoryById(op.category_id)}
            <li class="recent-item">
              <div 
                class="recent-icon"
                style="background: {category?.color || 'var(--muted)'}22; color: {category?.color || 'var(--muted)'}"
              >
                {category?.icon || '💰'}
              </div>
              <div class="recent-info">
                <div style="font-weight: 500;">{category?.name || 'Без категории'}</div>
                <div style="font-size: 12px; color: var(--muted);">
                  {formatDate(op.date)} • {op.note || 'Без описания'}
                </div>
              </div>
              <div 
                class="recent-amount"
                style="color: {op.type === 'income' ? 'var(--ok)' : 'var(--danger)'}"
              >
                {op.type === 'income' ? '+' : '-'}{formatMoney(op.amount_cents / 100)}
              </div>
            </li>
          {/each}
        </ul>
      </div>
    {/if}

    {#if operations.length === 0}
      <div class="card" style="text-align: center; padding: 48px 16px;">
        <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
        <div class="h2">Нет данных для отчёта</div>
        <p style="color: var(--muted); margin: 12px 0 24px 0;">
          Добавьте несколько операций, чтобы увидеть аналитику
        </p>
        <a class="btn" href="/add">Добавить операцию</a>
      </div>
    {/if}
  {/if}
</section>