let table, state = null;
let compact = false;

function fmtRub(v){ return (v==null ? "" : `${Math.round(v).toLocaleString('ru-RU')} ₽`); }

async function loadState(){
  const ym = document.getElementById('month').value;
  const res = await fetch(`/api/state?m=${encodeURIComponent(ym)}`);
  state = await res.json();
  document.getElementById('prev').textContent = `Прошлый: ${state.prev}`;

  // init / update table
  renderTable();
  updateTotals();
  fillMinusSelect();
  updateBases();
}

function renderTable(){
  const data = state.rows.map(r => ({
    id: r.id,
    name: r.name,
    source: r.source,
    percent: r.percent,
    fixed_rub: r.fixed_rub,
    plan: r.plan,
    spent: r.spent,
    left: r.left,
    warn: (r.name === 'Ипотека' && (r.fixed_rub||0) < 40000) ? '⚠' : ''
  }));

  const columns = [
    {title:"Категория", field:"name", editor:"input", widthGrow:2},
    {title:"Источник", field:"source", editor:"select", editorParams:{values:["ЗП","Аванс","Декретные"]}, width:120},
    {title:"%", field:"percent", editor:"number", hozAlign:"right", width:80, formatter:(cell)=>cell.getValue() ?? "", editorParams:{step:0.01}},
    {title:"₽ фикс", field:"fixed_rub", editor:"number", hozAlign:"right", width:120, formatter:(cell)=>cell.getValue() ?? "", editorParams:{step:0.01}},
    {title:"План", field:"plan", hozAlign:"right", formatter:(cell)=>fmtRub(cell.getValue()), width:110},
    {title:"Минусы", field:"spent", hozAlign:"right", formatter:(cell)=>fmtRub(cell.getValue()), width:110, cellClick:(e, cell)=>{ if(e.detail === 2) rowMinus(cell.getRow().getData().id); }, formatter:(cell)=>{
        const val = cell.getValue();
        const plan = cell.getRow().getData().plan || 0;
        const color = val > plan ? 'text-danger' : '';
        return `<span class="${color}">${fmtRub(val)}</span>`;
      }},
    {title:"Остаток", field:"left", hozAlign:"right", formatter:(cell)=>fmtRub(cell.getValue()), width:110},
    {title:"", field:"warn", width:40, hozAlign:"center"},
    {title:"", width:110, formatter:function(cell){
        return `<div class="btn-group btn-group-sm">
                  <button class="btn btn-outline-danger" onclick="rowMinus(${cell.getRow().getData().id})">−</button>
                  <button class="btn btn-outline-secondary" onclick="delRow(${cell.getRow().getData().id})">×</button>
                </div>`;
      }
    },
  ];

  const options = {
    index:"id",
    data,
    layout:"fitDataStretch",
    reactiveData:true,
    height: "auto",
    rowHeight: compact ? 28 : 34,
    columns,
    cellEdited: onCellEdited,
    keybindings:{
      "navUp":"up",
      "navDown":"down",
      "navLeft":"left", 
      "navRight":"right",
    },
    rowSelected:function(row){ /* for UX */ },
  };

  const el = document.getElementById('budget-table');
  if (!table) {
    table = new Tabulator(el, options);
    // keyboard shortcut M → minus
    el.addEventListener('keydown', (e)=>{
      if(e.key.toLowerCase()==='m'){
        const row = table.getSelectedRows()[0];
        if(row){ 
          e.preventDefault();
          rowMinus(row.getData().id); 
        }
      }
      // Del → delete row
      if(e.key === 'Delete'){
        const row = table.getSelectedRows()[0];
        if(row){ 
          e.preventDefault();
          delRow(row.getData().id); 
        }
      }
    });
    el.setAttribute('tabindex', '0'); // Make focusable for keyboard events
  } else {
    table.updateOptions(options);
  }
}

function toggleCompact(){
  compact = !compact;
  renderTable();
}

function updateTotals(){
  const s = state.summary;
  document.getElementById('totals').innerHTML =
    `Итого план: <b>${Math.round(s.total_plan).toLocaleString('ru-RU')} ₽</b> · `
  + `Факт: <b>${Math.round(s.total_minus).toLocaleString('ru-RU')} ₽</b> · `
  + `Остаток: <b>${Math.round(s.total_left).toLocaleString('ru-RU')} ₽</b>`;
}

function fillMinusSelect(){
  const sel = document.getElementById('minus-cat');
  sel.innerHTML = "";
  for(const r of state.rows){
    const opt = document.createElement('option');
    opt.value = r.id; opt.textContent = r.name;
    sel.appendChild(opt);
  }
}

function updateBases(){
  const b = state.summary.base || {};
  document.getElementById('bases').textContent =
    `База: ЗП ${Math.round(b['ЗП']||0)} ₽ · Аванс ${Math.round(b['Аванс']||0)} ₽ · Декретные ${Math.round(b['Декретные']||0)} ₽`;
}

async function onCellEdited(cell){
  const r = cell.getRow().getData();
  // При изменении % — очищаем фикс; при изменении ₽ — можем оставить %, сервер всё пересчитает честно.
  if (cell.getField()==="percent") {
    r.fixed_rub = null;
  }
  
  // Also handle name and source changes
  const updateData = { id: r.id };
  const field = cell.getField();
  
  if (field === 'name') {
    updateData.name = r.name;
  } else if (field === 'source') {
    updateData.source = r.source;  
  } else {
    updateData.percent = r.percent;
    updateData.fixed_rub = r.fixed_rub;
  }
  
  await fetch('/api/category/update', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(updateData)
  }).then(r=>r.json()).then(s=>{
    state = s; renderTable(); updateTotals(); fillMinusSelect(); updateBases();
  }).catch(err => {
    console.error('Update failed:', err);
    alert('Ошибка обновления');
  });
}

async function addRow(){
  const name = prompt("Название категории:");
  if(!name) return;
  const source = prompt("Источник (ЗП/Аванс/Декретные):","ЗП");
  if(!["ЗП","Аванс","Декретные"].includes(source||"")) return alert("Неверный источник");
  await fetch('/api/category/add', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ name, source, percent: null, fixed_rub: null })
  }).then(r=>r.json()).then(s=>{
    state = s; renderTable(); updateTotals(); fillMinusSelect(); updateBases();
  }).catch(err => {
    console.error('Add failed:', err);
    alert('Ошибка добавления категории');
  });
}

async function delRow(id){
  if(!confirm("Удалить категорию и её минусы?")) return;
  await fetch('/api/category/delete', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ id })
  }).then(r=>r.json()).then(s=>{
    state = s; renderTable(); updateTotals(); fillMinusSelect(); updateBases();
  }).catch(err => {
    console.error('Delete failed:', err);
    alert('Ошибка удаления');
  });
}

async function rowMinus(id){
  const category = state.rows.find(r => r.id === id);
  const categoryName = category ? category.name : 'категория';
  const amount = parseFloat(prompt(`Сумма списания с "${categoryName}", ₽:`)||"0");
  if(!(amount>0)) return;
  await fetch('/api/minus', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ ym: state.ym, category_id: id, amount })
  }).then(r=>r.json()).then(s=>{
    state = s; renderTable(); updateTotals(); fillMinusSelect(); updateBases();
  }).catch(err => {
    console.error('Minus failed:', err);
    alert('Ошибка списания');
  });
}

async function quickMinus(){
  const cid = parseInt(document.getElementById('minus-cat').value,10);
  const amount = parseFloat(document.getElementById('minus-amount').value||"0");
  if(!(cid>0 && amount>0)) return;
  await fetch('/api/minus', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ ym: state.ym, category_id: cid, amount })
  }).then(r=>r.json()).then(s=>{
    state = s; renderTable(); updateTotals(); updateBases();
    document.getElementById('minus-amount').value = "";
  }).catch(err => {
    console.error('Quick minus failed:', err);
    alert('Ошибка быстрого списания');
  });
}

async function addIncome(){
  const dt = document.getElementById('inc-date').value;
  const source = document.getElementById('inc-source').value;
  const amount = parseFloat(document.getElementById('inc-amount').value||"0");
  if(!dt || !(amount>0)) return;
  await fetch('/api/income/add', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ dt, source, amount })
  }).then(r=>r.json()).then(s=>{
    state = s; updateTotals(); renderTable(); updateBases();
    document.getElementById('inc-amount').value = "";
  }).catch(err => {
    console.error('Income add failed:', err);
    alert('Ошибка добавления дохода');
  });
}

window.addEventListener('DOMContentLoaded', loadState);