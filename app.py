# app.py
import os, json, sqlite3
from pathlib import Path
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from dotenv import load_dotenv
from services import read_tinkoff_csv, norm, build_rule_predicates

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "budget.db"
load_dotenv()

SOURCES = ("ЗП", "Аванс", "Декретные")

app = Flask(__name__)

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db(); cur = con.cursor()
    cur.executescript("""
    PRAGMA journal_mode=WAL;

    CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        source TEXT NOT NULL CHECK(source IN ('ЗП','Аванс','Декретные')),
        percent REAL DEFAULT NULL,
        fixed_rub REAL DEFAULT NULL
    );

    CREATE TABLE IF NOT EXISTS incomes(
        id INTEGER PRIMARY KEY,
        dt TEXT NOT NULL,
        source TEXT NOT NULL CHECK(source IN ('ЗП','Аванс','Декретные')),
        amount REAL NOT NULL,
        ym TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY,
        ym TEXT NOT NULL,
        category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
        amount REAL NOT NULL
    );

    /* соответствие мерчант -> категория (обучение) */
    CREATE TABLE IF NOT EXISTS merchant_map(
        merchant_norm TEXT PRIMARY KEY,
        category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE
    );

    /* правила классификации (подстановка категории по ключам/regex) */
    CREATE TABLE IF NOT EXISTS rules(
        id INTEGER PRIMARY KEY,
        pattern TEXT NOT NULL,
        is_regex INTEGER NOT NULL DEFAULT 0,
        category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE
    );
    """)
    con.commit(); con.close()

def ym_prev(ym: str) -> str:
    y, m = map(int, ym.split("-"))
    m -= 1
    if m == 0: y, m = y-1, 12
    return f"{y:04d}-{m:02d}"

def month_data(ym: str):
    con = db(); cur = con.cursor()
    # Incomes current & prev per source
    cur.execute("SELECT source, COALESCE(SUM(amount),0) s FROM incomes WHERE ym=? GROUP BY source",(ym,))
    inc_cur  = {r["source"]: r["s"] for r in cur.fetchall()}
    prev = ym_prev(ym)
    cur.execute("SELECT source, COALESCE(SUM(amount),0) s FROM incomes WHERE ym=? GROUP BY source",(prev,))
    inc_prev = {r["source"]: r["s"] for r in cur.fetchall()}

    # Categories
    cur.execute("SELECT * FROM categories ORDER BY id")
    cats = [dict(r) for r in cur.fetchall()]

    # Expenses (current month) per category
    cur.execute("""
        SELECT c.id, COALESCE(SUM(e.amount),0) s
        FROM categories c
        LEFT JOIN expenses e ON e.category_id=c.id AND e.ym=?
        GROUP BY c.id
    """,(ym,))
    minus_cur_by_cat = {r["id"]: r["s"] for r in cur.fetchall()}

    # Expenses (prev month) per source
    cur.execute("""
        SELECT c.source, COALESCE(SUM(e.amount),0) s
        FROM categories c
        LEFT JOIN expenses e ON e.category_id=c.id AND e.ym=?
        GROUP BY c.source
    """,(prev,))
    minus_prev_by_src = {r["source"]: r["s"] for r in cur.fetchall()}

    # Fixed sum per source
    cur.execute("""
        SELECT source, COALESCE(SUM(fixed_rub),0) s
        FROM categories WHERE fixed_rub IS NOT NULL
        GROUP BY source
    """)
    fixed_by_src = {r["source"]: r["s"] for r in cur.fetchall()}
    con.close()

    # Carryover & Base
    carry = {s: inc_prev.get(s,0) - minus_prev_by_src.get(s,0) for s in SOURCES}
    base  = {s: max(0, inc_cur.get(s,0) + carry.get(s,0) - fixed_by_src.get(s,0)) for s in SOURCES}

    # Table rows
    rows = []
    t_plan = t_minus = 0
    for c in cats:
        src = c["source"]
        if c["fixed_rub"] not in (None, ""):
            plan = float(c["fixed_rub"])
        elif c["percent"] not in (None, ""):
            plan = base[src] * float(c["percent"]) / 100.0
        else:
            plan = 0.0
        spent = minus_cur_by_cat.get(c["id"], 0.0)
        left  = plan - spent
        fact  = (plan / base[src]) if base[src] > 0 and plan else None
        rows.append({
            "id": c["id"], "name": c["name"], "source": src,
            "percent": c["percent"], "fixed_rub": c["fixed_rub"],
            "plan": plan, "spent": spent, "left": left, "fact_pct": fact
        })
        t_plan += plan; t_minus += spent

    summary = {
        "inc_cur": inc_cur, "inc_prev": inc_prev,
        "carry": carry, "base": base,
        "total_plan": t_plan, "total_minus": t_minus,
        "total_left": t_plan - t_minus
    }
    return rows, summary

@app.get("/")
def index():
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    rows, summary = month_data(ym)
    return render_template("index.html", ym=ym, prev=ym_prev(ym),
                           rows=rows, summary=summary, sources=SOURCES)

# --- CRUD для категорий/доходов/минусов
@app.post("/category/add")
def category_add():
    name = request.form["name"].strip()
    source = request.form["source"]
    percent = request.form.get("percent") or None
    fixed = request.form.get("fixed") or None
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO categories(name,source,percent,fixed_rub) VALUES(?,?,?,?)",
                (name, source, percent, fixed))
    con.commit(); con.close()
    ym = request.form.get("m")
    rows, summary = month_data(ym)
    return render_template("_table.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

@app.post("/category/update")
def category_update():
    cid = int(request.form["id"])
    percent = request.form.get("percent")
    fixed = request.form.get("fixed")
    con = db(); cur = con.cursor()
    cur.execute("UPDATE categories SET percent=?, fixed_rub=? WHERE id=?",
                (percent if percent != "" else None,
                 fixed if fixed != "" else None, cid))
    con.commit(); con.close()
    ym = request.form.get("m")
    rows, summary = month_data(ym)
    return render_template("_table.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

@app.post("/income/add")
def income_add():
    dt = request.form["dt"]
    src = request.form["source"]
    amount = float(request.form["amount"] or 0)
    ym = request.form.get("m") or dt[:7]
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO incomes(dt,source,amount,ym) VALUES(?,?,?,?)",(dt,src,amount,ym))
    con.commit(); con.close()
    rows, summary = month_data(ym)
    return render_template("_table.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

@app.post("/minus/add")
def minus_add():
    ym = request.form["ym"]
    cat_id = int(request.form["category_id"])
    amount = float(request.form["amount"] or 0)
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO expenses(ym,category_id,amount) VALUES(?,?,?)",(ym,cat_id,amount))
    con.commit(); con.close()
    rows, summary = month_data(ym)
    return render_template("_table.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

# --- Импорт CSV Тинькофф
@app.get("/import-csv")
def import_csv_form():
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    return render_template("merchants.html", ym=ym, stage="upload", merchants=[], categories=[])

@app.post("/import-csv")
def import_csv_post():
    ym = request.form.get("ym") or date.today().strftime("%Y-%m")
    f = request.files["file"]
    txs = read_tinkoff_csv(f.read())

    con = db(); cur = con.cursor()
    # правила → предикаты
    cur.execute("SELECT * FROM rules ORDER BY id DESC")
    rule_preds = build_rule_predicates(cur.fetchall())

    # загрузим категории и маппинг
    cur.execute("SELECT id, name, source FROM categories ORDER BY id")
    cats = [dict(r) for r in cur.fetchall()]
    by_name = {c["name"].lower(): c for c in cats}
    cur.execute("SELECT merchant_norm, category_id FROM merchant_map")
    mm = {r["merchant_norm"]: r["category_id"] for r in cur.fetchall()}

    # пройдёмся по транзакциям, соберём «неразобранные» и создадим расходы для разобранных
    unknown = {}
    created = 0
    for t in txs:
        if t["ym"] != ym:
            # можно добавить флаг «импортировать и другие месяцы», но пока фильтруем
            continue
        mnorm = t["desc_norm"]

        cat_id = mm.get(mnorm)
        # если нет явной карты → пробуем правила
        if not cat_id:
            for pred, cid in rule_preds:
                if pred(mnorm):
                    cat_id = cid
                    break

        if cat_id:
            # создаём расход
            cur.execute("INSERT INTO expenses(ym,category_id,amount) VALUES(?,?,?)",(ym,cat_id,t["amount"]))
            created += 1
        else:
            unknown[mnorm] = unknown.get(mnorm, 0) + t["amount"]

    con.commit()

    # отдаём список неизвестных мерчантов для обучения
    unknown_list = sorted(unknown.items(), key=lambda x: -x[1])
    con.close()
    return render_template("merchants.html", ym=ym, stage="map", merchants=unknown_list, categories=cats, created=created)

@app.post("/merchants/map")
def merchants_map():
    ym = request.form["ym"]
    con = db(); cur = con.cursor()
    # ожидаем поля вида map-<merchant_norm> = category_id
    items = [(k[4:], int(v)) for k, v in request.form.items() if k.startswith("map-") and v]
    for mnorm, cid in items:
        cur.execute("INSERT OR REPLACE INTO merchant_map(merchant_norm, category_id) VALUES(?,?)",(mnorm, cid))
    con.commit(); con.close()
    return redirect(url_for("import_csv_form", m=ym))

# --- Правила
@app.get("/rules")
def rules_page():
    con = db(); cur = con.cursor()
    cur.execute("SELECT * FROM rules ORDER BY id DESC")
    rules = cur.fetchall()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    cats = cur.fetchall()
    con.close()
    return render_template("rules.html", rules=rules, categories=cats)

@app.post("/rules/add")
def rules_add():
    pattern = request.form["pattern"].strip()
    is_regex = 1 if request.form.get("is_regex") == "on" else 0
    category_id = int(request.form["category_id"])
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO rules(pattern,is_regex,category_id) VALUES(?,?,?)",(pattern, is_regex, category_id))
    con.commit(); con.close()
    return redirect(url_for("rules_page"))

# --- Экспорт / Импорт JSON
@app.get("/export")
def export_json():
    con = db(); cur = con.cursor()
    data = {}
    for t in ("categories","incomes","expenses","merchant_map","rules"):
        cur.execute(f"SELECT * FROM {t}")
        data[t] = [dict(r) for r in cur.fetchall()]
    con.close()
    return app.response_class(json.dumps(data, ensure_ascii=False, indent=2), mimetype="application/json")

@app.post("/import")
def import_json():
    f = request.files["file"]
    data = json.load(f)
    con = db(); cur = con.cursor()
    cur.executescript("DELETE FROM expenses; DELETE FROM incomes; DELETE FROM merchant_map; DELETE FROM rules; DELETE FROM categories;")
    for r in data.get("categories", []):
        cur.execute("INSERT INTO categories(id,name,source,percent,fixed_rub) VALUES(?,?,?,?,?)",
                    (r["id"], r["name"], r["source"], r.get("percent"), r.get("fixed_rub")))
    for r in data.get("incomes", []):
        cur.execute("INSERT INTO incomes(id,dt,source,amount,ym) VALUES(?,?,?,?,?)",
                    (r["id"], r["dt"], r["source"], r["amount"], r["ym"]))
    for r in data.get("expenses", []):
        cur.execute("INSERT INTO expenses(id,ym,category_id,amount) VALUES(?,?,?,?)",
                    (r["id"], r["ym"], r["category_id"], r["amount"]))
    for r in data.get("merchant_map", []):
        cur.execute("INSERT INTO merchant_map(merchant_norm,category_id) VALUES(?,?)",
                    (r["merchant_norm"], r["category_id"]))
    for r in data.get("rules", []):
        cur.execute("INSERT INTO rules(id,pattern,is_regex,category_id) VALUES(?,?,?,?)",
                    (r["id"], r["pattern"], r["is_regex"], r["category_id"]))
    con.commit(); con.close()
    return redirect(url_for("index"))

@app.get("/partials/table")
def partial_table():
    ym = request.args.get("m")
    rows, summary = month_data(ym)
    return render_template("_table.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

@app.get("/api/health")
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        con = db()
        cur = con.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        con.close()
        
        return jsonify({
            "status": "healthy",
            "timestamp": date.today().isoformat(),
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": date.today().isoformat()
        }), 500

# === NEW: JSON API для Excel-грида ===

@app.get("/api/state")
def api_state():
    """Отдаём всё для рендера грида: строки бюджета + summary + источники."""
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    rows, summary = month_data(ym)
    return jsonify({
        "ym": ym, "prev": ym_prev(ym),
        "sources": list(SOURCES),
        "rows": rows,
        "summary": summary,
    })

@app.post("/api/category/add")
def api_category_add():
    data = request.json
    name = (data.get("name") or "").strip()
    source = data.get("source")
    percent = data.get("percent")
    fixed = data.get("fixed_rub")
    if not name or source not in SOURCES:
        return jsonify({"error": "bad input"}), 400
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO categories(name,source,percent,fixed_rub) VALUES(?,?,?,?)",
                (name, source, percent, fixed))
    con.commit(); con.close()
    return api_state()

@app.post("/api/category/update")
def api_category_update():
    data = request.json
    cid = int(data["id"])
    
    # Build update query dynamically based on provided fields
    updates = []
    params = []
    
    if "name" in data:
        updates.append("name=?")
        params.append(data["name"])
    
    if "source" in data:
        updates.append("source=?") 
        params.append(data["source"])
        
    if "percent" in data:
        updates.append("percent=?")
        params.append(data["percent"] if data["percent"] not in ("", None) else None)
        
    if "fixed_rub" in data:
        updates.append("fixed_rub=?")
        params.append(data["fixed_rub"] if data["fixed_rub"] not in ("", None) else None)
    
    if not updates:
        return api_state()  # No changes
        
    params.append(cid)
    
    con = db(); cur = con.cursor()
    cur.execute(f"UPDATE categories SET {', '.join(updates)} WHERE id=?", params)
    con.commit(); con.close()
    return api_state()

@app.post("/api/category/delete")
def api_category_delete():
    cid = int(request.json["id"])
    con = db(); cur = con.cursor()
    # удаляем категорию и связанные минусы
    cur.execute("DELETE FROM expenses WHERE category_id=?", (cid,))
    cur.execute("DELETE FROM categories WHERE id=?", (cid,))
    con.commit(); con.close()
    return api_state()

@app.post("/api/minus")
def api_minus():
    """Быстрое списание: {ym, category_id, amount}"""
    data = request.json
    ym = data.get("ym") or date.today().strftime("%Y-%m")
    cid = int(data["category_id"])
    amount = float(data.get("amount") or 0)
    if amount <= 0:
        return jsonify({"error": "amount must be > 0"}), 400
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO expenses(ym,category_id,amount) VALUES(?,?,?)", (ym, cid, amount))
    con.commit(); con.close()
    return api_state()

@app.post("/api/income/add")
def api_income_add():
    data = request.json
    dt = data["dt"]
    src = data["source"]
    amount = float(data["amount"])
    ym = dt[:7]
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO incomes(dt,source,amount,ym) VALUES(?,?,?,?)",(dt,src,amount,ym))
    con.commit(); con.close()
    return api_state()

@app.get("/grid")
def grid_ui():
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    return render_template("grid.html", ym=ym)

# --- MINI UI ROUTES (упрощённый интерфейс) ---

@app.get("/simple")
def simple_ui():
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    return render_template("simple.html", ym=ym)

@app.get("/partials/table-min")
def partial_table_min():
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

# автосохранение из таблицы (₽/%) — сразу возвращаем обновлённый partial
@app.post("/category/update-min")
def category_update_min():
    cid = int(request.form["id"])
    percent = request.form.get("percent")
    fixed = request.form.get("fixed")
    con = db(); cur = con.cursor()
    cur.execute("UPDATE categories SET percent=?, fixed_rub=? WHERE id=?",
                (percent if percent != "" else None,
                 fixed if fixed != "" else None, cid))
    con.commit(); con.close()
    ym = request.form.get("m")
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

# удаление категории (и её минусов за все месяцы)
@app.post("/category/delete-min")
def category_delete_min():
    ym = request.form["m"]
    cid = int(request.form["id"])
    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM expenses WHERE category_id=?", (cid,))
    cur.execute("DELETE FROM categories WHERE id=?", (cid,))
    con.commit(); con.close()
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

# быстрая добавка дохода (через prompt)
@app.post("/income/add-min")
def income_add_min():
    ym = request.form.get("m")
    dt = request.form["dt"]
    src = request.form["source"]
    amount = float(request.form["amount"] or 0)
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO incomes(dt,source,amount,ym) VALUES(?,?,?,?)",(dt,src,amount,dt[:7]))
    con.commit(); con.close()
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

# добавка категории (через prompt)
@app.post("/category/add-min")
def category_add_min():
    ym = request.form.get("m")
    name = request.form["name"].strip()
    source = request.form["source"]
    percent = request.form.get("percent") or None
    fixed = request.form.get("fixed") or None
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO categories(name,source,percent,fixed_rub) VALUES(?,?,?,?)",
                (name, source, percent, fixed))
    con.commit(); con.close()
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

if __name__ == "__main__":
    init_db()
    app.run(host=os.getenv("HOST","0.0.0.0"), port=int(os.getenv("PORT","8000")), debug=True)