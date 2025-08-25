import os, time, jwt
JWT_SECRET = os.getenv("JWT_SECRET", "DEV_ONLY_CHANGE_ME")
ALGO = "HS256"

def make_token(uid: str, email: str, ttl_sec: int = 30*24*3600):
    now = int(time.time())
    payload = {"uid": uid, "eml": email, "iat": now, "exp": now + ttl_sec}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGO)

def parse_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGO])