"""
Seed data for development — creates initial owner, staff, customer, product, 
business settings, and sample orders.

Run: python -m app.db.seed
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import async_session_factory, engine, Base
from app.models import (
    User,
    UserRole,
    Customer,
    CustomerAddress,
    AddressLabel,
    Product,
    Order,
    OrderStatus,
    PaymentStatus,
    DeliverySlot,
    OrderAssignment,
    OrderCanSummary,
    CustomerCanBalance,
    CanTransaction,
    CanTransactionType,
    Payment,
    PaymentProvider,
    PaymentRecordStatus,
    BusinessSettings,
)

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    """Simple password hash using passlib."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


async def seed():
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    logger.info("Seeding database for %s environment...", settings.ENVIRONMENT)

    async with async_session_factory() as session:
        # Check if already seeded
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            logger.info("Database already seeded — skipping.")
            return

        now = datetime.now(timezone.utc)

        # ── Owner ──────────────────────────────────────────
        owner = User(
            id=uuid.uuid4(),
            name="Demo Owner",
            phone="9000000001",
            email="owner@watercan.dev",
            password_hash=_hash_password(settings.SEED_OWNER_PASSWORD),
            role=UserRole.OWNER,
            is_active=True,
        )
        session.add(owner)

        # ── Staff ──────────────────────────────────────────
        staff_akhil = User(
            id=uuid.uuid4(),
            name="Akhil",
            phone="9000000002",
            email="akhil@watercan.dev",
            password_hash=_hash_password(settings.SEED_STAFF_PASSWORD),
            role=UserRole.STAFF,
            is_active=True,
        )
        staff_rahul = User(
            id=uuid.uuid4(),
            name="Rahul",
            phone="9000000003",
            email="rahul@watercan.dev",
            password_hash=_hash_password(settings.SEED_STAFF_PASSWORD),
            role=UserRole.STAFF,
            is_active=True,
        )
        session.add_all([staff_akhil, staff_rahul])

        # ── Product ────────────────────────────────────────
        product = Product(
            id=uuid.uuid4(),
            name="20L Water Can",
            description="Premium purified 20-litre water can",
            price_per_unit=50.00,
            unit_name="can",
            is_active=True,
        )
        session.add(product)

        # ── Business Settings ──────────────────────────────
        biz_settings = BusinessSettings(
            id=uuid.uuid4(),
            business_name="AquaPure Water Supply",
            business_phone="9000000001",
            business_address="Pattom, Trivandrum, Kerala",
            business_whatsapp="9000000001",
            currency="INR",
            default_delivery_charge=0.00,
        )
        session.add(biz_settings)

        # ── Customer 1: John George (existing customer) ───
        customer_john = Customer(
            id=uuid.uuid4(),
            name="John George",
            phone="9876543210",
            email="john@example.com",
            is_active=True,
        )
        session.add(customer_john)

        address_john = CustomerAddress(
            id=uuid.uuid4(),
            customer_id=customer_john.id,
            label=AddressLabel.HOME,
            address_line_1="Pallimukku",
            address_line_2="Near SBI Bank",
            city="Trivandrum",
            district="Thiruvananthapuram",
            state="Kerala",
            pincode="695004",
            latitude=8.5241,
            longitude=76.9366,
            is_default=True,
        )
        session.add(address_john)

        # ── Customer 2: Arun (newer customer) ─────────────
        customer_arun = Customer(
            id=uuid.uuid4(),
            name="Arun Kumar",
            phone="9999999999",
            is_active=True,
        )
        session.add(customer_arun)

        address_arun = CustomerAddress(
            id=uuid.uuid4(),
            customer_id=customer_arun.id,
            label=AddressLabel.HOME,
            address_line_1="Kazhakkoottam",
            city="Trivandrum",
            district="Thiruvananthapuram",
            state="Kerala",
            pincode="695582",
            is_default=True,
        )
        session.add(address_arun)

        await session.flush()

        # ── Can Balances ───────────────────────────────────
        john_balance = CustomerCanBalance(
            id=uuid.uuid4(),
            customer_id=customer_john.id,
            current_balance=4,
        )
        arun_balance = CustomerCanBalance(
            id=uuid.uuid4(),
            customer_id=customer_arun.id,
            current_balance=0,
        )
        session.add_all([john_balance, arun_balance])

        # ── Sample Orders ─────────────────────────────────
        today = now.strftime("%Y%m%d")

        # Order 1 — Delivered (John)
        order1 = Order(
            id=uuid.uuid4(),
            order_number=f"WC-{today}-0001",
            customer_id=customer_john.id,
            address_id=address_john.id,
            product_id=product.id,
            quantity=5,
            price_per_unit=50.00,
            subtotal=250.00,
            delivery_charge=0.00,
            discount=0.00,
            total_amount=250.00,
            payment_status=PaymentStatus.PAID,
            order_status=OrderStatus.DELIVERED,
            delivery_slot=DeliverySlot.MORNING,
        )
        session.add(order1)

        # Order 2 — Paid, assigned to Akhil (John)
        order2 = Order(
            id=uuid.uuid4(),
            order_number=f"WC-{today}-0002",
            customer_id=customer_john.id,
            address_id=address_john.id,
            product_id=product.id,
            quantity=3,
            price_per_unit=50.00,
            subtotal=150.00,
            delivery_charge=0.00,
            discount=0.00,
            total_amount=150.00,
            payment_status=PaymentStatus.PAID,
            order_status=OrderStatus.ASSIGNED,
            delivery_slot=DeliverySlot.AFTERNOON,
        )
        session.add(order2)

        # Order 3 — Paid, unassigned (Arun)
        order3 = Order(
            id=uuid.uuid4(),
            order_number=f"WC-{today}-0003",
            customer_id=customer_arun.id,
            address_id=address_arun.id,
            product_id=product.id,
            quantity=2,
            price_per_unit=50.00,
            subtotal=100.00,
            delivery_charge=0.00,
            discount=0.00,
            total_amount=100.00,
            payment_status=PaymentStatus.PAID,
            order_status=OrderStatus.CONFIRMED,
            delivery_slot=DeliverySlot.MORNING,
        )
        session.add(order3)

        # Order 4 — Out for delivery (John)
        order4 = Order(
            id=uuid.uuid4(),
            order_number=f"WC-{today}-0004",
            customer_id=customer_john.id,
            address_id=address_john.id,
            product_id=product.id,
            quantity=5,
            price_per_unit=50.00,
            subtotal=250.00,
            delivery_charge=0.00,
            discount=0.00,
            total_amount=250.00,
            payment_status=PaymentStatus.PAID,
            order_status=OrderStatus.OUT_FOR_DELIVERY,
            delivery_slot=DeliverySlot.EVENING,
        )
        session.add(order4)

        # Order 5 — Pending payment (Arun)
        order5 = Order(
            id=uuid.uuid4(),
            order_number=f"WC-{today}-0005",
            customer_id=customer_arun.id,
            address_id=address_arun.id,
            product_id=product.id,
            quantity=10,
            price_per_unit=50.00,
            subtotal=500.00,
            delivery_charge=0.00,
            discount=0.00,
            total_amount=500.00,
            payment_status=PaymentStatus.PENDING,
            order_status=OrderStatus.PENDING_PAYMENT,
        )
        session.add(order5)

        await session.flush()

        # ── Order Assignments ─────────────────────────────
        assignment2 = OrderAssignment(
            id=uuid.uuid4(),
            order_id=order2.id,
            staff_id=staff_akhil.id,
            assigned_by=owner.id,
            assigned_at=now,
        )
        assignment4 = OrderAssignment(
            id=uuid.uuid4(),
            order_id=order4.id,
            staff_id=staff_rahul.id,
            assigned_by=owner.id,
            assigned_at=now,
        )
        session.add_all([assignment2, assignment4])

        # ── Order Can Summary (for delivered order) ───────
        can_summary1 = OrderCanSummary(
            id=uuid.uuid4(),
            order_id=order1.id,
            cans_delivered=5,
            empty_cans_returned=3,
            notes="3 empty cans collected",
        )
        session.add(can_summary1)

        # ── Can Transactions (for delivered order) ────────
        tx_delivered = CanTransaction(
            id=uuid.uuid4(),
            customer_id=customer_john.id,
            order_id=order1.id,
            transaction_type=CanTransactionType.DELIVERED,
            quantity=5,
            balance_before=2,
            balance_after=7,
            notes="Order WC-{}-0001 delivered".format(today),
            created_by=owner.id,
        )
        tx_returned = CanTransaction(
            id=uuid.uuid4(),
            customer_id=customer_john.id,
            order_id=order1.id,
            transaction_type=CanTransactionType.RETURNED,
            quantity=3,
            balance_before=7,
            balance_after=4,
            notes="3 empty cans returned",
            created_by=owner.id,
        )
        session.add_all([tx_delivered, tx_returned])

        # ── Payment records ───────────────────────────────
        for order in [order1, order2, order3, order4]:
            payment = Payment(
                id=uuid.uuid4(),
                order_id=order.id,
                provider=PaymentProvider.RAZORPAY,
                provider_order_id=f"order_test_{order.order_number}",
                provider_payment_id=f"pay_test_{order.order_number}",
                amount=order.total_amount,
                currency="INR",
                status=PaymentRecordStatus.CAPTURED,
            )
            session.add(payment)

        await session.commit()
        logger.info("✅ Seed data created successfully!")
        logger.info("  Owner: owner@watercan.dev / configured seed password")
        logger.info("  Staff: akhil@watercan.dev / configured seed password")
        logger.info("  Staff: rahul@watercan.dev / configured seed password")
        logger.info("  Customer: John George (9876543210)")
        logger.info("  Customer: Arun Kumar (9999999999)")
        logger.info("  Product: 20L Water Can @ ₹50")
        logger.info("  Orders: 5 sample orders in various states")


if __name__ == "__main__":
    asyncio.run(seed())
