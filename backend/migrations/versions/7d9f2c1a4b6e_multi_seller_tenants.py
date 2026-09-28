"""add multi-seller tenant ownership

Revision ID: 7d9f2c1a4b6e
Revises: 33155ea597b3
"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "7d9f2c1a4b6e"
down_revision: Union[str, Sequence[str], None] = "33155ea597b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'PLATFORM_ADMIN'")

    op.create_table(
        "businesses",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_businesses_is_active", "businesses", ["is_active"], unique=False)

    for table in ("business_settings", "users", "products", "customers", "orders", "customer_can_balances", "can_transactions"):
        op.add_column(table, sa.Column("business_id", sa.UUID(), nullable=True))

    connection = op.get_bind()
    setting_id = connection.execute(
        sa.text("SELECT id FROM business_settings ORDER BY created_at ASC LIMIT 1")
    ).scalar_one_or_none()
    business_id = setting_id or uuid.uuid4()
    if setting_id is None:
        connection.execute(
            sa.text(
                "INSERT INTO businesses (id, name, slug, is_active) "
                "VALUES (:id, :name, :slug, true)"
            ),
            {"id": business_id, "name": "Water Can Seller", "slug": "default"},
        )
        connection.execute(
            sa.text(
                "INSERT INTO business_settings "
                "(id, business_id, business_name, business_phone, currency, default_delivery_charge) "
                "VALUES (:id, :business_id, :name, :phone, 'INR', 0)"
            ),
            {
                "id": uuid.uuid4(),
                "business_id": business_id,
                "name": "Water Can Seller",
                "phone": "9000000000",
            },
        )
    else:
        connection.execute(
            sa.text(
                "INSERT INTO businesses (id, name, slug, is_active) "
                "SELECT :id, business_name, 'default', true FROM business_settings WHERE id = :setting_id"
            ),
            {"id": business_id, "setting_id": setting_id},
        )

    for table in ("business_settings", "users", "products", "customers", "orders", "customer_can_balances", "can_transactions"):
        connection.execute(
            sa.text(f"UPDATE {table} SET business_id = :business_id"),
            {"business_id": business_id},
        )

    op.execute("ALTER TABLE customers DROP CONSTRAINT IF EXISTS customers_phone_key")
    op.execute("ALTER TABLE customer_can_balances DROP CONSTRAINT IF EXISTS customer_can_balances_customer_id_key")

    op.create_foreign_key("fk_business_settings_business", "business_settings", "businesses", ["business_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_users_business", "users", "businesses", ["business_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_products_business", "products", "businesses", ["business_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_customers_business", "customers", "businesses", ["business_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_orders_business", "orders", "businesses", ["business_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_customer_balances_business", "customer_can_balances", "businesses", ["business_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_can_transactions_business", "can_transactions", "businesses", ["business_id"], ["id"], ondelete="RESTRICT")

    for table in ("business_settings", "products", "customers", "orders", "customer_can_balances", "can_transactions"):
        op.alter_column(table, "business_id", nullable=False)

    op.create_index("ix_business_settings_business_id", "business_settings", ["business_id"], unique=False)
    op.create_index("ix_users_business_id", "users", ["business_id"], unique=False)
    op.create_index("ix_products_business_id", "products", ["business_id"], unique=False)
    op.create_index("ix_customers_business_id", "customers", ["business_id"], unique=False)
    op.create_index("ix_orders_business_id", "orders", ["business_id"], unique=False)
    op.create_index("ix_customer_can_balances_business_id", "customer_can_balances", ["business_id"], unique=False)
    op.create_index("ix_can_transactions_business_id", "can_transactions", ["business_id"], unique=False)
    op.create_unique_constraint("uq_business_settings_business_id", "business_settings", ["business_id"])
    op.create_unique_constraint("uq_customers_business_phone", "customers", ["business_id", "phone"])
    op.create_unique_constraint("uq_customer_can_balances_business_customer", "customer_can_balances", ["business_id", "customer_id"])


def downgrade() -> None:
    op.drop_constraint("uq_customer_can_balances_business_customer", "customer_can_balances", type_="unique")
    op.drop_constraint("uq_customers_business_phone", "customers", type_="unique")
    op.drop_constraint("uq_business_settings_business_id", "business_settings", type_="unique")
    for name, table in (
        ("ix_can_transactions_business_id", "can_transactions"),
        ("ix_customer_can_balances_business_id", "customer_can_balances"),
        ("ix_orders_business_id", "orders"),
        ("ix_customers_business_id", "customers"),
        ("ix_products_business_id", "products"),
        ("ix_users_business_id", "users"),
        ("ix_business_settings_business_id", "business_settings"),
    ):
        op.drop_index(name, table_name=table)
    for name, table in (
        ("fk_can_transactions_business", "can_transactions"),
        ("fk_customer_balances_business", "customer_can_balances"),
        ("fk_orders_business", "orders"),
        ("fk_customers_business", "customers"),
        ("fk_products_business", "products"),
        ("fk_users_business", "users"),
        ("fk_business_settings_business", "business_settings"),
    ):
        op.drop_constraint(name, table_name=table, type_="foreignkey")
    for table in ("business_settings", "users", "products", "customers", "orders", "customer_can_balances", "can_transactions"):
        op.drop_column(table, "business_id")
    op.drop_index("ix_businesses_is_active", table_name="businesses")
    op.drop_table("businesses")
