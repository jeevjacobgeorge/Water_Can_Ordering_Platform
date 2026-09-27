"""
Order number generator — creates human-friendly order numbers.
Format: WC-YYYYMMDD-NNNN
"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


async def generate_order_number(db: AsyncSession) -> str:
    """Generate the next sequential order number for today."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"WC-{today}-"

    # Find the highest order number for today
    result = await db.execute(
        select(func.max(Order.order_number)).where(
            Order.order_number.like(f"{prefix}%")
        )
    )
    last_number = result.scalar_one_or_none()

    if last_number:
        # Extract the sequence part and increment
        seq = int(last_number.split("-")[-1]) + 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"
