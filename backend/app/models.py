from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime

# ---- Auth ----
class Creds(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class TokenOut(BaseModel):
    token: str

# ---- Entities for sync ----
class Category(BaseModel):
    id: str
    user_id: str
    name: str
    kind: Literal["income","expense"]
    icon: Optional[str] = None
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    active: int = 1
    limit_type: str = "none"
    limit_value: float = 0
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None

class Source(BaseModel):
    id: str
    user_id: str
    name: str
    currency: str = "EUR"
    expected_date: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None

class Rule(BaseModel):
    id: str
    user_id: str
    source_id: str
    category_id: str
    percent: float
    cap_cents: Optional[int] = None
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None

class Operation(BaseModel):
    id: str
    user_id: str
    type: Literal["income","expense"]
    source_id: Optional[str] = None
    category_id: str
    wallet: Optional[str] = None
    amount_cents: int
    currency: str = "EUR"
    rate: float = 1.0
    date: str
    note: Optional[str] = None
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None

# ---- Sync ----
class SyncPush(BaseModel):
    categories: List[Category] = []
    sources:    List[Source]   = []
    rules:      List[Rule]     = []
    operations: List[Operation]= []

class SyncPull(BaseModel):
    categories: List[Category]
    sources:    List[Source]
    rules:      List[Rule]
    operations: List[Operation]
    server_time: str