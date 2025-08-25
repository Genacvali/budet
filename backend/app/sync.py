from fastapi import APIRouter, Depends, HTTPException, Request
from .db import get_db
from .models import SyncPush
import time

router = APIRouter(prefix="/api/sync", tags=["sync"])

TABLES = {
    "categories": ["id","user_id","name","kind","icon","color","active","limit_type","limit_value","created_at","updated_at","deleted_at"],
    "sources":    ["id","user_id","name","currency","expected_date","icon","color","created_at","updated_at","deleted_at"],
    "rules":      ["id","user_id","source_id","category_id","percent","cap_cents","created_at","updated_at","deleted_at"],
    "operations": ["id","user_id","type","source_id","category_id","wallet","amount_cents","currency","rate","date","note","created_at","updated_at","deleted_at"],
}

@router.get("/pull")
async def pull(since: str | None = None, request: Request = None, db = Depends(get_db)):
    claims = request.state.claims
    uid = claims["uid"]
    since = since or "1970-01-01T00:00:00Z"
    payload = {}
    for t, cols in TABLES.items():
        rows = await (await db.execute(
            f"SELECT {', '.join(cols)} FROM {t} WHERE user_id=? AND updated_at>?",
            (uid, since)
        )).fetchall()
        payload[t] = [dict(r) for r in rows]
    payload["server_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return payload

@router.post("/push")
async def push(body: SyncPush, request: Request, db = Depends(get_db)):
    claims = request.state.claims
    uid = claims["uid"]
    for t, cols in TABLES.items():
        rows = getattr(body, t)
        if not rows: continue
        qs_cols = ",".join(cols)
        placeholders = ",".join(["?"]*len(cols))
        setters = ",".join([f"{c}=excluded.{c}" for c in cols if c!="id"])
        for row in rows:
            row.user_id = uid
            values = [getattr(row, c) for c in cols]
            await db.execute(
                f"INSERT INTO {t}({qs_cols}) VALUES({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {setters}",
                values
            )
    await db.commit()
    return {"ok": True}