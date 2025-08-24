import os, sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, jsonify

APP_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(APP_DIR, "budget.db")
SOURCES = ("ЗП", "Аванс", "Декретные")

app = Flask(__name__)

# ── DB ────────────────────────────────────────────────────────────────────────
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db(); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS incomes(
        id INTEGER PRIMARY KEY, dt TEXT NOT NULL, source TEXT NOT NULL,
        amount REAL NOT NULL, ym TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, source TEXT NOT NULL,
        percent REAL, fixed_rub REAL, UNIQUE(name, source))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY, ym TEXT NOT NULL, category_id INTEGER NOT NULL,
        amount REAL NOT NULL, FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE)""")
    con.commit(); con.close()
init_db()

# ── Helpers ──────────────────────────────────────────────────────────────────
def ym_prev(ym: str) -> str:
    y, m = map(int, ym.split("-"))
    if m == 1: return f"{y-1}-12"
    return f"{y:04d}-{m-1:02d}"

def month_income_by_source(con, ym):
    cur = con.cursor()
    cur.execute("SELECT source, SUM(amount) s FROM incomes WHERE ym=? GROUP BY source",(ym,))
    out = {r["source"]: r["s"] or 0.0 for r in cur.fetchall()}
    for s in SOURCES: out.setdefault(s, 0.0)
    return out

def month_expenses_by_category(con, ym):
    cur = con.cursor()
    cur.execute("SELECT category_id, SUM(amount) s FROM expenses WHERE ym=? GROUP BY category_id",(ym,))
    return {r["category_id"]: r["s"] or 0.0 for r in cur.fetchall()}

def categories_all(con):
    cur = con.cursor()
    cur.execute("SELECT id,name,source,percent,fixed_rub FROM categories ORDER BY name COLLATE NOCASE")
    return cur.fetchall()

def month_data(ym: str):
    """rows: [{id,name,source,percent,fixed_rub,plan,spent,left,fact_pct}], summary: {...}"""
    con = db()
    prev = ym_prev(ym)
    inc_prev = month_income_by_source(con, prev)
    inc_cur  = month_income_by_source(con, ym)

    # прошлые траты по источникам
    cur = con.cursor()
    cur.execute("""
        SELECT c.source s, SUM(e.amount) x
        FROM expenses e JOIN categories c ON c.id=e.category_id
        WHERE e.ym=? GROUP BY c.source
    """,(prev,))
    spent_prev_by_src = {r["s"]: r["x"] or 0.0 for r in cur.fetchall()}
    for s in SOURCES: spent_prev_by_src.setdefault(s, 0.0)

    # перенос и база (не редактируется руками)
    carry = {s: inc_prev.get(s,0.0) - spent_prev_by_src.get(s,0.0) for s in SOURCES}
    base  = {s: max(0.0, inc_cur.get(s,0.0) + carry.get(s,0.0)) for s in SOURCES}

    cats = categories_all(con)
    spent_by_cat = month_expenses_by_category(con, ym)

    rows = []; total_plan = total_minus = 0.0
    for c in cats:
        cid, name, source, percent, fixed = c["id"], c["name"], c["source"], c["percent"], c["fixed_rub"]
        b = base.get(source, 0.0)
        plan = 0.0
        if fixed not in (None, "") and float(fixed) > 0: plan = float(fixed)
        elif percent not in (None, ""): plan = b * float(percent) / 100.0
        spent = float(spent_by_cat.get(cid, 0.0))
        left = plan - spent
        rows.append(dict(
            id=cid, name=name, source=source,
            percent=None if percent in ("", None) else float(percent),
            fixed_rub=None if fixed in ("", None) else float(fixed),
            plan=round(plan,2), spent=round(spent,2), left=round(left,2),
            fact_pct=(spent/plan) if plan>0 else None
        ))
        total_plan += plan; total_minus += spent

    summary = dict(
        total_plan=round(total_plan,2),
        total_minus=round(total_minus,2),
        total_left=round(total_plan-total_minus,2),
        base=base, inc_cur=inc_cur, carry=carry
    )
    con.close()
    return rows, summary

# ── Minimal UI routes ────────────────────────────────────────────────────────
@app.get("/")
def root(): return redirect(url_for("simple_ui"))

@app.get("/simple")
def simple_ui():
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    return render_template("simple.html", ym=ym)

@app.get("/partials/table-min")
def partial_table_min():
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

@app.post("/category/update-min")
def category_update_min():
    cid = int(request.form["id"])
    percent = request.form.get("percent")
    fixed   = request.form.get("fixed")
    source  = request.form.get("source")  # NEW

    percent = None if percent in (None, "") else percent
    fixed   = None if fixed   in (None, "") else fixed

    con = db(); cur = con.cursor()
    if source in SOURCES:
        cur.execute("UPDATE categories SET percent=?, fixed_rub=?, source=? WHERE id=?",
                    (percent, fixed, source, cid))
    else:
        cur.execute("UPDATE categories SET percent=?, fixed_rub=? WHERE id=?",
                    (percent, fixed, cid))
    con.commit(); con.close()

    ym = request.form.get("m") or date.today().strftime("%Y-%m")
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

@app.post("/category/delete-min")
def category_delete_min():
    ym = request.form["m"]; cid = int(request.form["id"])
    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM expenses WHERE category_id=?", (cid,))
    cur.execute("DELETE FROM categories WHERE id=?", (cid,))
    con.commit(); con.close()
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

@app.post("/income/add-min")
def income_add_min():
    ym = request.form.get("m") or date.today().strftime("%Y-%m")
    dt = request.form["dt"]; src = request.form["source"]; amount = float(request.form["amount"] or 0)
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO incomes(dt,source,amount,ym) VALUES(?,?,?,?)",(dt,src,amount,dt[:7]))
    con.commit(); con.close()
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

@app.post("/category/add-min")
def category_add_min():
    ym = request.form["m"]; name = request.form["name"].strip()
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO categories(name,source) VALUES(?,?)",(name,"ЗП"))
    con.commit(); con.close()
    rows, summary = month_data(ym)
    return render_template("_table_min.html", ym=ym, rows=rows, summary=summary, sources=SOURCES)

# ── Optional JSON (если пригодится) ─────────────────────────────────────────
@app.get("/api/state")
def api_state():
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    rows, summary = month_data(ym)
    return jsonify(dict(ym=ym, prev=ym_prev(ym), rows=rows, summary=summary))

@app.post("/api/minus")
def api_minus():
    ym = request.json.get("ym") or date.today().strftime("%Y-%m")
    cid = int(request.json["category_id"]); amount = float(request.json["amount"])
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO expenses(ym,category_id,amount) VALUES(?,?,?)",(ym,cid,amount))
    con.commit(); con.close()
    rows, summary = month_data(ym)
    return jsonify(dict(ok=True, ym=ym, rows=rows, summary=summary))

# ---------- GRID ----------
@app.get("/grid")
def grid_ui():
    ym = request.args.get("m") or date.today().strftime("%Y-%m")
    return render_template("grid.html", ym=ym)

@app.post("/api/category/add")
def api_category_add():
    name = (request.json.get("name") or "").strip()
    source = request.json.get("source") or "ЗП"
    if not name or source not in SOURCES:
        return jsonify({"error":"bad input"}), 400
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO categories(name,source) VALUES(?,?)",(name, source))
    con.commit(); con.close()
    return jsonify({"ok": True})

@app.post("/api/category/update")
def api_category_update():
    cid     = int(request.json["id"])
    percent = request.json.get("percent")
    fixed   = request.json.get("fixed_rub")
    source  = request.json.get("source")
    con = db(); cur = con.cursor()
    cur.execute("""UPDATE categories SET
                      percent=?,
                      fixed_rub=?,
                      source=COALESCE(?, source)
                   WHERE id=?""",
                (percent if percent!="" else None,
                 fixed   if fixed!=""   else None,
                 source if source in SOURCES else None,
                 cid))
    con.commit(); con.close()
    return jsonify({"ok": True})

@app.post("/api/category/delete")
def api_category_delete():
    cid = int(request.json["id"])
    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM expenses WHERE category_id=?", (cid,))
    cur.execute("DELETE FROM categories WHERE id=?", (cid,))
    con.commit(); con.close()
    return jsonify({"ok": True})

@app.post("/api/income/add")
def api_income_add():
    dt = request.json["dt"]; source = request.json["source"]; amount = float(request.json["amount"])
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO incomes(dt,source,amount,ym) VALUES(?,?,?,?)",(dt,source,amount,dt[:7]))
    con.commit(); con.close()
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)