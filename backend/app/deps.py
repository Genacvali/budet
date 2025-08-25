from fastapi import Header, HTTPException
from .jwt_utils import parse_token

def get_claims(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return parse_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")