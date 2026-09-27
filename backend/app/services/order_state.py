"""
Order state machine — validates and enforces order status transitions.
"""

import logging

from app.models.order import OrderStatus, VALID_STATUS_TRANSITIONS

logger = logging.getLogger(__name__)


class InvalidStatusTransition(Exception):
    """Raised when an invalid order status transition is attempted."""

    def __init__(self, current: OrderStatus, target: OrderStatus):
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition from {current.value} to {target.value}"
        )


def validate_transition(current: OrderStatus, target: OrderStatus) -> None:
    """
    Validate that the transition from current to target status is allowed.
    Raises InvalidStatusTransition if not.
    """
    allowed = VALID_STATUS_TRANSITIONS.get(current, [])
    if target not in allowed:
        logger.warning(
            "Invalid order status transition: %s → %s",
            current.value,
            target.value,
        )
        raise InvalidStatusTransition(current, target)


def can_cancel(current: OrderStatus) -> bool:
    """Check if an order in the current status can be cancelled."""
    return OrderStatus.CANCELLED in VALID_STATUS_TRANSITIONS.get(current, [])
