from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
import logging

from .db import get_db
from .auth import get_current_user
from .models import User, Category, CategoryCreate, CategoryUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_user_category(db, user_id: int, category_id: int):
    cursor = await db.execute(
        """SELECT id, user_id, name, type, color, icon, sync_id, created_at, updated_at 
           FROM categories WHERE id = ? AND user_id = ?""",
        (category_id, user_id)
    )
    row = await cursor.fetchone()
    if row:
        return dict(row)
    return None

@router.get("/", response_model=List[Category])
async def get_categories(current_user: User = Depends(get_current_user)):
    db = await get_db()
    
    cursor = await db.execute(
        """SELECT id, user_id, name, type, color, icon, sync_id, created_at, updated_at 
           FROM categories WHERE user_id = ? ORDER BY name""",
        (current_user.id,)
    )
    rows = await cursor.fetchall()
    
    categories = []
    for row in rows:
        categories.append(Category(**dict(row)))
    
    return categories

@router.post("/", response_model=Category)
async def create_category(
    category: CategoryCreate,
    current_user: User = Depends(get_current_user)
):
    db = await get_db()
    
    # Check if category with same name already exists
    cursor = await db.execute(
        "SELECT id FROM categories WHERE user_id = ? AND name = ?",
        (current_user.id, category.name)
    )
    if await cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    sync_id = str(uuid.uuid4())
    
    cursor = await db.execute(
        """INSERT INTO categories (user_id, name, type, color, icon, sync_id)
           VALUES (?, ?, ?, ?, ?, ?) RETURNING id, created_at, updated_at""",
        (current_user.id, category.name, category.type.value, 
         category.color, category.icon, sync_id)
    )
    row = await cursor.fetchone()
    await db.commit()
    
    return Category(
        id=row["id"],
        user_id=current_user.id,
        name=category.name,
        type=category.type,
        color=category.color,
        icon=category.icon,
        sync_id=sync_id,
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user)
):
    db = await get_db()
    
    category = await get_user_category(db, current_user.id, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return Category(**category)

@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_user)
):
    db = await get_db()
    
    # Check if category exists
    existing_category = await get_user_category(db, current_user.id, category_id)
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if new name conflicts with existing category
    if category_update.name:
        cursor = await db.execute(
            "SELECT id FROM categories WHERE user_id = ? AND name = ? AND id != ?",
            (current_user.id, category_update.name, category_id)
        )
        if await cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )
    
    # Build update query
    update_fields = []
    update_values = []
    
    if category_update.name is not None:
        update_fields.append("name = ?")
        update_values.append(category_update.name)
    
    if category_update.color is not None:
        update_fields.append("color = ?")
        update_values.append(category_update.color)
    
    if category_update.icon is not None:
        update_fields.append("icon = ?")
        update_values.append(category_update.icon)
    
    if not update_fields:
        # No fields to update
        return Category(**existing_category)
    
    update_values.append(category_id)
    update_values.append(current_user.id)
    
    query = f"""UPDATE categories 
               SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?
               RETURNING id, user_id, name, type, color, icon, sync_id, created_at, updated_at"""
    
    cursor = await db.execute(query, update_values)
    row = await cursor.fetchone()
    await db.commit()
    
    return Category(**dict(row))

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user)
):
    db = await get_db()
    
    # Check if category exists
    category = await get_user_category(db, current_user.id, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category has transactions
    cursor = await db.execute(
        "SELECT COUNT(*) as count FROM transactions WHERE category_id = ?",
        (category_id,)
    )
    row = await cursor.fetchone()
    if row["count"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with existing transactions"
        )
    
    # Delete category
    await db.execute(
        "DELETE FROM categories WHERE id = ? AND user_id = ?",
        (category_id, current_user.id)
    )
    await db.commit()
    
    return {"message": "Category deleted successfully"}