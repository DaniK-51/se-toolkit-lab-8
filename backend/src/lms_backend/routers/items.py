"""Router for item endpoints — reference implementation."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.db.items import create_item, read_item, read_items, update_item
from lms_backend.models.item import ItemCreate, ItemRecord, ItemUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    """Get all items."""
    try:
        return await read_items(session)
    except OperationalError as exc:
        # Database connection errors should be reported as 500, not 404
        logger.error(
            "database_operation_failed",
            extra={"event": "database_operation_failed", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed",
        ) from exc
    except Exception as exc:
        # Log the actual exception for debugging
        logger.error(
            "items_list_failed",
            extra={"event": "items_list_failed", "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve items",
        ) from exc


@router.get("/{item_id}", response_model=ItemRecord)
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    """Get a specific item by its id."""
    item = await read_item(session, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return item


@router.post("/", response_model=ItemRecord, status_code=201)
async def post_item(body: ItemCreate, session: AsyncSession = Depends(get_session)):
    """Create a new item."""
    try:
        return await create_item(
            session,
            type=body.type,
            parent_id=body.parent_id,
            title=body.title,
            description=body.description,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="parent_id does not reference an existing item",
        )


@router.put("/{item_id}", response_model=ItemRecord)
async def put_item(
    item_id: int, body: ItemUpdate, session: AsyncSession = Depends(get_session)
):
    """Update an existing item."""
    item = await update_item(
        session, item_id=item_id, title=body.title, description=body.description
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return item
