let table, state;

function rub(n){ return (Math.round(n||0)).toLocaleString('ru-RU')+' ₽'; }

async function loadGrid(){
  const m = document.getElementById('m').value;
  const s = await fetch(`/api/state?m=${encodeURIComponent(m)}`).then(r=>r.json());
  state = s;

  const cols = [
    {title:"Категория", field:"name", editor:"input", widthGrow:2},
    {title:"Источник", field:"source", editor:"select", editorParams:{values:["ЗП","Аванс","Декретные"]}, width:120},
    {title:"₽ фикс", field:"fixed_rub", editor:"number", hozAlign:"right", width:110},
    {title:"%", field:"percent", editor:"number", hozAlign:"right", width:80},
    {title:"План", field:"plan", hozAlign:"right", width:110, formatter:(c)=>rub(c.getValue())},
    {title:"Потрачено", field:"spent", hozAlign:"right", width:110, formatter:(c)=>rub(c.getValue()),
      cssClass:(c)=> (c.getValue()>(c.getRow().getData().plan||0) ? "text-danger" : "") },
    {title:"Остаток", field:"left", hozAlign:"right", width:110, formatter:(c)=>rub(c.getValue())},
    {title:"", width:60, formatter:(cell)=>`<button class="btn btn-sm btn-outline-danger">×</button>`,
      cellClick: async (e, cell)=>{
        await fetch('/api/category/delete',{method:'POST',headers:{'Content-Type':'application/json'},
          body: JSON.stringify({id: cell.getRow().getData().id})});
        loadGrid();
      }}
  ];

  const data = s.rows.map(r=>({...r}));

  if (!table){
    table = new Tabulator("#grid", {
      data, columns: cols, layout:"fitDataStretch", reactiveData:true,
      index:"id", height:"auto", cellEdited: onEdit
    });
  } else {
    table.replaceData(data);
  }

  document.getElementById('totals').innerHTML =
    `План: <b>${rub(s.summary.total_plan)}</b> · `+
    `Факт: <b>${rub(s.summary.total_minus)}</b> · `+
    `Остаток: <b>${rub(s.summary.total_left)}</b>`;
}

async function onEdit(cell){
  const r = cell.getRow().getData();
  await fetch('/api/category/update', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ id:r.id, percent:r.percent ?? "", fixed_rub:r.fixed_rub ?? "", source:r.source })
  });
  loadGrid();
}

async function addCategoryGrid(){
  const name = prompt("Название категории:","");
  if(!name) return;
  const source = prompt("Источник (ЗП/Аванс/Декретные):","ЗП") || "ЗП";
  await fetch('/api/category/add',{method:'POST',headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name, source})});
  loadGrid();
}

async function addIncomeGrid(){
  const m = document.getElementById('m').value;
  const dt = prompt("Дата (YYYY-MM-DD):", m+"-05"); if(!dt) return;
  const source = prompt("Источник (ЗП/Аванс/Декретные):", "ЗП") || "ЗП";
  const amount = prompt("Сумма, ₽:", ""); if(!amount) return;
  await fetch('/api/income/add',{method:'POST',headers:{'Content-Type':'application/json'},
    body: JSON.stringify({dt, source, amount: parseFloat(amount)})});
  loadGrid();
}

window.addEventListener('DOMContentLoaded', loadGrid);