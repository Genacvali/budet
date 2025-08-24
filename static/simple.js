// Простой слой над твоими API/partial, без HTMX для действий — только для первоначального рендера
async function refreshState(){
  const m = document.getElementById('m').value;
  const res = await fetch(`/api/state?m=${encodeURIComponent(m)}`);
  const s = await res.json();

  // prev
  const prev = document.getElementById('prev');
  prev.textContent = `Прошлый: ${s.prev}`;

  // sources KPIs
  const wrap = document.getElementById('sources');
  wrap.innerHTML = '';
  const order = ['ЗП','Аванс','Декретные'];
  for (const src of order){
    const base = Math.round((s.summary.base || {})[src] || 0).toLocaleString('ru-RU');
    const inc  = Math.round((s.summary.inc_cur || {})[src] || 0).toLocaleString('ru-RU');
    const car  = Math.round((s.summary.carry  || {})[src] || 0).toLocaleString('ru-RU');
    const col = document.createElement('div');
    col.className = 'col-12 col-md-4';
    col.innerHTML = `
      <div class="card card-kpi"><div class="card-body">
        <div class="d-flex justify-content-between">
          <div class="fw-semibold">${src}</div>
          <span class="badge text-bg-secondary">база: ${base} ₽</span>
        </div>
        <div class="small mt-2">Доход: ${inc} ₽ · Перенос: ${car} ₽</div>
      </div></div>`;
    wrap.appendChild(col);
  }

  // заполнить селект категорий в модалке «минус»
  const minusSel = document.getElementById('minus-cat');
  minusSel.innerHTML = '';
  (s.rows || []).forEach(r=>{
    const o = document.createElement('option');
    o.value = r.id; o.textContent = r.name;
    minusSel.appendChild(o);
  });
}

async function simpleAddIncome(){
  const dt = document.getElementById('inc-date').value;
  const source = document.getElementById('inc-source').value;
  const amount = parseFloat(document.getElementById('inc-amount').value || '0');
  if(!dt || !(amount>0)) return;
  
  try {
    await fetch('/api/income/add',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ dt, source, amount })
    });
    document.getElementById('inc-amount').value = '';
    await refreshTableAndState();
    bootstrap.Modal.getInstance(document.getElementById('incomeModal')).hide();
  } catch(err) {
    alert('Ошибка добавления дохода');
  }
}

async function simpleMinus(){
  const ym = document.getElementById('m').value;
  const category_id = parseInt(document.getElementById('minus-cat').value,10);
  const amount = parseFloat(document.getElementById('minus-amount').value || '0');
  if(!(category_id>0 && amount>0)) return;
  
  try {
    await fetch('/api/minus',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ ym, category_id, amount })
    });
    document.getElementById('minus-amount').value = '';
    await refreshTableAndState();
    bootstrap.Modal.getInstance(document.getElementById('minusModal')).hide();
  } catch(err) {
    alert('Ошибка списания');
  }
}

async function simpleAddCategory(){
  const name = document.getElementById('cat-name').value.trim();
  const source = document.getElementById('cat-source').value;
  const percent = document.getElementById('cat-percent').value || null;
  const fixed_rub = document.getElementById('cat-fixed').value || null;
  if(!name) return;
  
  try {
    await fetch('/api/category/add',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ name, source, percent, fixed_rub })
    });
    document.getElementById('cat-name').value = '';
    document.getElementById('cat-percent').value = '';
    document.getElementById('cat-fixed').value = '';
    await refreshTableAndState();
    bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
  } catch(err) {
    alert('Ошибка добавления категории');
  }
}

async function refreshTableAndState(){
  const m = document.getElementById('m').value;
  // обновим partial таблицы (HTMX-элемент)
  const wr = document.getElementById('table-wrap');
  wr.setAttribute('hx-get', `/partials/table?m=${encodeURIComponent(m)}&compact=1`);
  htmx.process(wr);
  htmx.trigger(wr, 'load');
  await refreshState();
}

// Theme toggle functionality
function initThemeToggle() {
  const themeToggle = document.getElementById('themeToggle');
  const html = document.documentElement;
  
  // Get saved theme or default to dark
  const savedTheme = localStorage.getItem('theme') || 'dark';
  html.setAttribute('data-bs-theme', savedTheme);
  updateThemeButton(savedTheme);
  
  themeToggle?.addEventListener('click', () => {
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeButton(newTheme);
  });
}

function updateThemeButton(theme) {
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.textContent = theme === 'dark' ? '☀️ Светло' : '🌙 Темно';
  }
}

window.addEventListener('DOMContentLoaded', () => {
  refreshState();
  initThemeToggle();
});