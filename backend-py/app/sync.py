from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime
import uuid
import logging

from .db import get_db
from .auth import get_current_user
from .models import User, Category, Transaction, SyncRequest, SyncResponse

logger = logging.getLogger(__name__)
router = APIRouter()

async def resolve_conflicts_lww(server_item: dict, client_item: dict) -> dict:
    """Last-Writer-Wins conflict resolution"""
    server_updated = datetime.fromisoformat(server_item["updated_at"].replace('Z', '+00:00'))
    client_updated = datetime.fromisoformat(client_item["updated_at"].replace('Z', '+00:00'))
    
    if client_updated > server_updated:
        return client_item
    else:
        return server_item

async def sync_categories(db, user_id: int, client_categories: List[Category]) -> tuple[List[Category], List[dict]]:
    """Sync categories between client and server"""
    conflicts = []
    
    # Get all server categories
    cursor = await db.execute(
        """SELECT id, user_id, name, type, color, icon, sync_id, created_at, updated_at 
           FROM categories WHERE user_id = ?""",
        (user_id,)
    )
    server_categories = {row["sync_id"]: dict(row) for row in await cursor.fetchall()}
    
    # Process client categories
    client_sync_ids = set()
    for client_cat in client_categories:
        client_sync_ids.add(client_cat.sync_id)
        
        if client_cat.sync_id in server_categories:
            # Update existing category (check for conflicts)
            server_cat = server_categories[client_cat.sync_id]
            
            # Check if there's a conflict
            server_updated = datetime.fromisoformat(server_cat["updated_at"].replace('Z', '+00:00'))
            client_updated = client_cat.updated_at
            
            if abs((server_updated - client_updated).total_seconds()) > 1:  # 1 second tolerance
                # Conflict detected
                resolved = await resolve_conflicts_lww(server_cat, client_cat.dict())
                conflicts.append({
                    "type": "category",
                    "sync_id": client_cat.sync_id,
                    "server_version": server_cat,
                    "client_version": client_cat.dict(),
                    "resolved_version": resolved
                })
                
                if resolved == client_cat.dict():
                    # Update server with client version
                    await db.execute(
                        """UPDATE categories 
                           SET name = ?, type = ?, color = ?, icon = ?, updated_at = ?
                           WHERE sync_id = ? AND user_id = ?""",
                        (client_cat.name, client_cat.type.value, client_cat.color,
                         client_cat.icon, client_cat.updated_at.isoformat(),
                         client_cat.sync_id, user_id)
                    )
            else:
                # No conflict, update server
                await db.execute(
                    """UPDATE categories 
                       SET name = ?, type = ?, color = ?, icon = ?, updated_at = ?
                       WHERE sync_id = ? AND user_id = ?""",
                    (client_cat.name, client_cat.type.value, client_cat.color,
                     client_cat.icon, client_cat.updated_at.isoformat(),
                     client_cat.sync_id, user_id)
                )
        else:
            # Create new category
            await db.execute(
                """INSERT INTO categories (user_id, name, type, color, icon, sync_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, client_cat.name, client_cat.type.value, client_cat.color,
                 client_cat.icon, client_cat.sync_id, 
                 client_cat.created_at.isoformat(), client_cat.updated_at.isoformat())
            )
    
    # Get all categories after sync
    cursor = await db.execute(
        """SELECT id, user_id, name, type, color, icon, sync_id, created_at, updated_at 
           FROM categories WHERE user_id = ? ORDER BY name""",
        (user_id,)
    )
    
    final_categories = []
    for row in await cursor.fetchall():
        final_categories.append(Category(**dict(row)))
    
    return final_categories, conflicts

async def sync_transactions(db, user_id: int, client_transactions: List[Transaction]) -> tuple[List[Transaction], List[dict]]:
    """Sync transactions between client and server"""
    conflicts = []
    
    # Get all server transactions
    cursor = await db.execute(
        """SELECT id, user_id, category_id, amount, description, date, sync_id, created_at, updated_at 
           FROM transactions WHERE user_id = ?""",
        (user_id,)
    )
    server_transactions = {row["sync_id"]: dict(row) for row in await cursor.fetchall()}
    
    # Process client transactions
    client_sync_ids = set()
    for client_txn in client_transactions:
        client_sync_ids.add(client_txn.sync_id)
        
        if client_txn.sync_id in server_transactions:
            # Update existing transaction (check for conflicts)
            server_txn = server_transactions[client_txn.sync_id]
            
            # Check if there's a conflict
            server_updated = datetime.fromisoformat(server_txn["updated_at"].replace('Z', '+00:00'))
            client_updated = client_txn.updated_at
            
            if abs((server_updated - client_updated).total_seconds()) > 1:  # 1 second tolerance
                # Conflict detected
                resolved = await resolve_conflicts_lww(server_txn, client_txn.dict())
                conflicts.append({
                    "type": "transaction",
                    "sync_id": client_txn.sync_id,
                    "server_version": server_txn,
                    "client_version": client_txn.dict(),
                    "resolved_version": resolved
                })
                
                if resolved == client_txn.dict():
                    # Update server with client version
                    await db.execute(
                        """UPDATE transactions 
                           SET category_id = ?, amount = ?, description = ?, date = ?, updated_at = ?
                           WHERE sync_id = ? AND user_id = ?""",
                        (client_txn.category_id, float(client_txn.amount), client_txn.description,
                         client_txn.date.isoformat(), client_txn.updated_at.isoformat(),
                         client_txn.sync_id, user_id)
                    )
            else:
                # No conflict, update server
                await db.execute(
                    """UPDATE transactions 
                       SET category_id = ?, amount = ?, description = ?, date = ?, updated_at = ?
                       WHERE sync_id = ? AND user_id = ?""",
                    (client_txn.category_id, float(client_txn.amount), client_txn.description,
                     client_txn.date.isoformat(), client_txn.updated_at.isoformat(),
                     client_txn.sync_id, user_id)
                )
        else:
            # Create new transaction
            # First, verify category exists (map sync_id to actual id)
            cursor = await db.execute(
                "SELECT id FROM categories WHERE sync_id = ? AND user_id = ?",
                (client_txn.category.sync_id if client_txn.category else None, user_id)
            )
            category_row = await cursor.fetchone()
            
            if category_row:
                category_id = category_row["id"]
            else:
                # Category not found, skip this transaction or create default category
                logger.warning(f"Category not found for transaction {client_txn.sync_id}")
                continue
            
            await db.execute(
                """INSERT INTO transactions (user_id, category_id, amount, description, date, sync_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, category_id, float(client_txn.amount), client_txn.description,
                 client_txn.date.isoformat(), client_txn.sync_id,
                 client_txn.created_at.isoformat(), client_txn.updated_at.isoformat())
            )
    
    # Get all transactions after sync with category info
    cursor = await db.execute(
        """SELECT t.id, t.user_id, t.category_id, t.amount, t.description, 
                  t.date, t.sync_id, t.created_at, t.updated_at,
                  c.name as category_name, c.type as category_type, 
                  c.color as category_color, c.icon as category_icon
           FROM transactions t
           LEFT JOIN categories c ON t.category_id = c.id
           WHERE t.user_id = ? 
           ORDER BY t.date DESC""",
        (user_id,)
    )
    
    final_transactions = []
    for row in await cursor.fetchall():
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
        
        final_transactions.append(Transaction(**transaction_data))
    
    return final_transactions, conflicts

@router.post("/", response_model=SyncResponse)
async def sync_data(
    sync_request: SyncRequest,
    current_user: User = Depends(get_current_user)
):
    db = await get_db()
    all_conflicts = []
    
    try:
        # Start transaction
        await db.execute("BEGIN")
        
        # Sync categories first
        final_categories, category_conflicts = await sync_categories(
            db, current_user.id, sync_request.categories
        )
        all_conflicts.extend(category_conflicts)
        
        # Sync transactions
        final_transactions, transaction_conflicts = await sync_transactions(
            db, current_user.id, sync_request.transactions
        )
        all_conflicts.extend(transaction_conflicts)
        
        # Commit transaction
        await db.commit()
        
        logger.info(f"✅ Sync completed for user {current_user.id}: "
                   f"{len(final_categories)} categories, {len(final_transactions)} transactions, "
                   f"{len(all_conflicts)} conflicts")
        
        return SyncResponse(
            categories=final_categories,
            transactions=final_transactions,
            conflicts=all_conflicts,
            last_sync=datetime.utcnow()
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Sync failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )

@router.get("/status")
async def get_sync_status(current_user: User = Depends(get_current_user)):
    db = await get_db()
    
    # Get last sync timestamp (we'll use the latest updated_at from user's data)
    cursor = await db.execute(
        """SELECT MAX(updated_at) as last_sync FROM (
               SELECT updated_at FROM categories WHERE user_id = ?
               UNION ALL
               SELECT updated_at FROM transactions WHERE user_id = ?
           )""",
        (current_user.id, current_user.id)
    )
    row = await cursor.fetchone()
    
    last_sync = None
    if row["last_sync"]:
        last_sync = datetime.fromisoformat(row["last_sync"].replace('Z', '+00:00'))
    
    # Get counts
    cursor = await db.execute(
        """SELECT 
               (SELECT COUNT(*) FROM categories WHERE user_id = ?) as categories_count,
               (SELECT COUNT(*) FROM transactions WHERE user_id = ?) as transactions_count""",
        (current_user.id, current_user.id)
    )
    counts = await cursor.fetchone()
    
    return {
        "last_sync": last_sync.isoformat() if last_sync else None,
        "categories_count": counts["categories_count"],
        "transactions_count": counts["transactions_count"],
        "server_time": datetime.utcnow().isoformat()
    }