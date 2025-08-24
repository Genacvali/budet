# services.py
import csv, io, re, unicodedata
from datetime import datetime

# --- утилиты нормализации
def norm(s: str) -> str:
    if s is None: return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.strip().lower()
    # убираем лишние пробелы и общие мусорные хвосты
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\b(ru|www)\b", "", s)
    return s.strip()

def parse_amount(v: str) -> float:
    # подстраиваемся под "1 234,56" и "-1 234.56"
    v = (v or "").replace("\u00A0"," ").replace(" "," ")
    v = v.replace(" ", "").replace(",", ".")
    try:
        return float(v)
    except:
        return 0.0

def parse_date_any(s: str):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except: pass
    # иногда csv тащит полный «2025-08-05 12:34:56»
    try:
        return datetime.fromisoformat(s)
    except:
        return None

# --- правила (ключевые слова / regex)
def build_rule_predicates(rows):
    """
    rows: [{'pattern': 'taxi|yandex', 'is_regex':1, 'category_id': 3}, ...]
    Возвращает список функций-предикатов.
    """
    preds = []
    for r in rows:
        pat = r["pattern"].strip()
        if not pat: 
            continue
        if r["is_regex"]:
            rx = re.compile(pat, re.I)
            preds.append((lambda desc, rx=rx: bool(rx.search(desc)), r["category_id"]))
        else:
            keys = [k for k in re.split(r"[;,|]", pat) if k.strip()]
            keys = [norm(k) for k in keys]
            preds.append((lambda desc, keys=keys: any(k in desc for k in keys), r["category_id"]))
    return preds

# --- парсер CSV Тинькофф
def read_tinkoff_csv(file_bytes: bytes):
    """
    Возвращает список транзакций:
    dict(dt: date, ym: 'YYYY-MM', amount: float (отрицательные = расход), 
         description: str, mcc: str)
    Поддерживает «Сумма операции», «Сумма», «Описание», «Категория», «MCC», «Дата операции».
    """
    text = file_bytes.decode("utf-8", errors="ignore")
    # Тинькофф CSV может быть ; или ,
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(text.splitlines()[0])
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    out = []
    for row in reader:
        # поля называются по-разному в разных выгрузках
        desc = row.get("Описание") or row.get("Описание операции") or row.get("Операция") or ""
        mcc  = row.get("MCC") or row.get("mcc") or ""
        amt  = row.get("Сумма операции") or row.get("Сумма") or row.get("Amount") or ""
        cur  = row.get("Валюта операции") or row.get("Валюта") or "RUB"
        dt_s = row.get("Дата операции") or row.get("Дата") or row.get("Дата платежа") or row.get("Date") or ""
        dt   = parse_date_any(dt_s)
        if not dt: 
            continue
        amount = parse_amount(amt)
        # фильтруем только расходы в рублях
        if amount >= 0 or ("RUB" not in (cur or "RUB")):
            continue
        desc_n = norm(desc)
        out.append({
            "dt": dt.date(),
            "ym": dt.strftime("%Y-%m"),
            "amount": abs(amount),      # делаем положительным числом расход
            "description": desc,
            "desc_norm": desc_n,
            "mcc": (mcc or "").strip()
        })
    return out