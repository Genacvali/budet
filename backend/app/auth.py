from fastapi import APIRouter, HTTPException, Depends
from pydantic import EmailStr
from .models import Creds, TokenOut
from .jwt_utils import make_token
from .db import get_db
import bcrypt, time, uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
async def register(c: Creds, db = Depends(get_db)):
    if len(c.password) < 6:
        raise HTTPException(400, "password too short")
    email = c.email.lower()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    uid = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(c.password.encode(), bcrypt.gensalt()).decode()
    try:
        await db.execute(
            "INSERT INTO users(id,email,password_hash,created_at,updated_at) VALUES(?,?,?,?,?)",
            (uid, email, pw_hash, now, now)
        )
        await db.commit()
    except Exception:
        raise HTTPException(409, "email exists")
    return {"token": make_token(uid, email)}

@router.post("/login", response_model=TokenOut)
async def login(c: Creds, db = Depends(get_db)):
    email = c.email.lower()
    row = await (await db.execute("SELECT id,password_hash FROM users WHERE email=?", (email,))).fetchone()
    if not row:
        raise HTTPException(401, "invalid credentials")
    if not bcrypt.checkpw(c.password.encode(), row["password_hash"].encode()):
        raise HTTPException(401, "invalid credentials")
    return {"token": make_token(row["id"], email)}

@router.get("/me")
async def me(db = Depends(get_db), authorization: str = Depends(lambda authorization: authorization)):
    # Используем простую проверку через deps в main (глобальный middleware)
    return {"ok": True}