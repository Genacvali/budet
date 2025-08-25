from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: CategoryType
    # Pydantic v2 → pattern вместо regex
    color: str = Field(..., pattern=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = Field(None, max_length=50)

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    # Тоже меняем на pattern
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    icon: Optional[str] = Field(None, max_length=50)

class Category(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    sync_id: str
    
    class Config:
        from_attributes = True

class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: str = Field(..., min_length=1, max_length=500)
    date: datetime
    category_id: int

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    date: Optional[datetime] = None
    category_id: Optional[int] = None

class Transaction(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    sync_id: str
    category: Optional[Category] = None
    
    class Config:
        from_attributes = True

class SyncData(BaseModel):
    categories: List[Category] = []
    transactions: List[Transaction] = []
    last_sync: Optional[datetime] = None

class SyncRequest(BaseModel):
    last_sync: Optional[datetime] = None
    categories: List[Category] = []
    transactions: List[Transaction] = []

class SyncResponse(BaseModel):
    categories: List[Category]
    transactions: List[Transaction]
    conflicts: List[dict] = []
    last_sync: datetime

class StatsResponse(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    categories_stats: List[dict]
    monthly_stats: List[dict]
    period_start: datetime
    period_end: datetime
