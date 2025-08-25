from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date
import uuid
import logging

from .db import get_db
from .auth import get_current_user
from .models import User, Transaction, TransactionCreate, TransactionUpdate, StatsResponse

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_user_transaction(db, user_id: int, transaction_id: int):
    cursor = await db.execute(
        """SELECT t.id, t.user_id, t.category_id, t.amount, t.description, 
                  t.date, t.sync_id, t.created_at, t.updated_at,
                  c.name as category_name, c.type as category_type, 
                  c.color as category_color, c.icon as category_icon
           FROM transactions t
           LEFT JOIN categories c ON t.category_id = c.id
           WHERE t.id = ? AND t.user_id = ?""",
        (transaction_id, user_id)
    )
    row = await cursor.fetchone()
    if row:
        return dict(row)
    return None

@router.get("/", response_model=List[Transaction])
async def get_transactions(
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    category_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    db = await get_db()
    
    # Build query with filters
    where_conditions = ["t.user_id = ?"]
    params = [current_user.id]
    
    if category_id:
        where_conditions.append("t.category_id = ?")
        params.append(category_id)
    
    if start_date:
        where_conditions.append("DATE(t.date) >= ?")
        params.append(start_date.isoformat())
    
    if end_date:
        where_conditions.append("DATE(t.date) <= ?")
        params.append(end_date.isoformat())
    
    params.extend([limit, offset])
    
    query = f"""
        SELECT t.id, t.user_id, t.category_id, t.amount, t.description, 
               t.date, t.sync_id, t.created_at, t.updated_at,
               c.name as category_name, c.type as category_type, 
               c.color as category_color, c.icon as category_icon
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE {' AND '.join(where_conditions)}
        ORDER BY t.date DESC, t.created_at DESC
        LIMIT ? OFFSET ?
    """
    
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    
    transactions = []
    for row in rows:
        transaction_data = {
            "id": row["id"],
            "user_id": row["user_id"],
            "category_id": row["category_id"],
            "amount": float(row["amount"]),
            "description": row["description"],
            "date": datetime.fromisoformat(row["date"].replace('Z', '+00:00')),
            "sync_id": row["sync_id"],
            "created_at": datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
            "updated_at": datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00'))
        }
        
        if row["category_name"]:
            transaction_data["category"] = {
                "id": row["category_id"],
                "name": row["category_name"],
                "type": row["category_type"],
                "color": row["category_color"],
                "icon": row["category_icon"]
            }
        
        transactions.append(Transaction(**transaction_data))
    
    return transactions

@router.post("/", response_model=Transaction)
async def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    db = await get_db()
    
    # Verify category exists and belongs to user
    cursor = await db.execute(
        "SELECT id FROM categories WHERE id = ? AND user_id = ?",
        (transaction.category_id, current_user.id)
    )
    if not await cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or doesn't belong to user"
        )
    
    sync_id = str(uuid.uuid4())
    
    cursor = await db.execute(
        """INSERT INTO transactions (user_id, category_id, amount, description, date, sync_id)
           VALUES (?, ?, ?, ?, ?, ?) 
           RETURNING id, created_at, updated_at""",
        (current_user.id, transaction.category_id, float(transaction.amount), 
         transaction.description, transaction.date.isoformat(), sync_id)
    )
    row = await cursor.fetchone()
    await db.commit()
    
    return Transaction(
        id=row["id"],
        user_id=current_user.id,
        category_id=transaction.category_id,
        amount=transaction.amount,
        description=transaction.description,
        date=transaction.date,
        sync_id=sync_id,
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user)
):
    db = await get_db()
    
    transaction = await get_user_transaction(db, current_user.id, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    transaction_data = {
        "id": transaction["id"],
        "user_id": transaction["user_id"],
        "category_id": transaction["category_id"],
        "amount": float(transaction["amount"]),
        "description": transaction["description"],
        "date": datetime.fromisoformat(transaction["date"].replace('Z', '+00:00')),
        "sync_id": transaction["sync_id"],
        "created_at": datetime.fromisoformat(transaction["created_at"].replace('Z', '+00:00')),
        "updated_at": datetime.fromisoformat(transaction["updated_at"].replace('Z', '+00:00'))
    }
    
    if transaction["category_name"]:
        transaction_data["category"] = {
            "id": transaction["category_id"],
            "name": transaction["category_name"],
            "type": transaction["category_type"],
            "color": transaction["category_color"],
            "icon": transaction["category_icon"]
        }
    
    return Transaction(**transaction_data)

@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_user)
):
    db = await get_db()
    
    # Check if transaction exists
    existing_transaction = await get_user_transaction(db, current_user.id, transaction_id)
    if not existing_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Verify category if provided
    if transaction_update.category_id:
        cursor = await db.execute(
            "SELECT id FROM categories WHERE id = ? AND user_id = ?",
            (transaction_update.category_id, current_user.id)
        )
        if not await cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or doesn't belong to user"
            )
    
    # Build update query
    update_fields = []
    update_values = []
    
    if transaction_update.amount is not None:
        update_fields.append("amount = ?")
        update_values.append(float(transaction_update.amount))
    
    if transaction_update.description is not None:
        update_fields.append("description = ?")
        update_values.append(transaction_update.description)
    
    if transaction_update.date is not None:
        update_fields.append("date = ?")
        update_values.append(transaction_update.date.isoformat())
    
    if transaction_update.category_id is not None:
        update_fields.append("category_id = ?")
        update_values.append(transaction_update.category_id)
    
    if not update_fields:
        # No fields to update, return existing transaction
        return await get_transaction(transaction_id, current_user)
    
    update_values.extend([transaction_id, current_user.id])
    
    query = f"""UPDATE transactions 
               SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?"""
    
    await db.execute(query, update_values)
    await db.commit()
    
    return await get_transaction(transaction_id, current_user)

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user)
):
    db = await get_db()
    
    # Check if transaction exists
    transaction = await get_user_transaction(db, current_user.id, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Delete transaction
    await db.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, current_user.id)
    )
    await db.commit()
    
    return {"message": "Transaction deleted successfully"}

@router.get("/stats/summary", response_model=StatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    db = await get_db()
    
    # Set default date range (current month if not specified)
    if not start_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
    
    if not end_date:
        end_date = date.today()
    
    # Get income and expense totals
    cursor = await db.execute(
        """SELECT 
               c.type,
               SUM(t.amount) as total
           FROM transactions t
           JOIN categories c ON t.category_id = c.id
           WHERE t.user_id = ? 
             AND DATE(t.date) >= ? 
             AND DATE(t.date) <= ?
           GROUP BY c.type""",
        (current_user.id, start_date.isoformat(), end_date.isoformat())
    )
    
    totals = {"income": 0, "expense": 0}
    for row in await cursor.fetchall():
        totals[row["type"]] = float(row["total"])
    
    # Get category stats
    cursor = await db.execute(
        """SELECT 
               c.id, c.name, c.type, c.color,
               SUM(t.amount) as total,
               COUNT(t.id) as count
           FROM categories c
           LEFT JOIN transactions t ON c.id = t.category_id 
               AND DATE(t.date) >= ? AND DATE(t.date) <= ?
           WHERE c.user_id = ?
           GROUP BY c.id, c.name, c.type, c.color
           ORDER BY total DESC""",
        (start_date.isoformat(), end_date.isoformat(), current_user.id)
    )
    
    categories_stats = []
    for row in await cursor.fetchall():
        categories_stats.append({
            "category_id": row["id"],
            "category_name": row["name"],
            "category_type": row["type"],
            "category_color": row["color"],
            "total": float(row["total"]) if row["total"] else 0,
            "count": row["count"]
        })
    
    return StatsResponse(
        total_income=totals["income"],
        total_expense=totals["expense"],
        balance=totals["income"] - totals["expense"],
        categories_stats=categories_stats,
        monthly_stats=[],  # TODO: Implement monthly breakdown
        period_start=datetime.combine(start_date, datetime.min.time()),
        period_end=datetime.combine(end_date, datetime.max.time())
    )