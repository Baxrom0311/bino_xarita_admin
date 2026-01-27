"""fix rooms id identity

Revision ID: b1d4f3a9c2e0
Revises: 8b1f2a3c4d5e
Create Date: 2026-01-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b1d4f3a9c2e0'
down_revision: Union[str, Sequence[str], None] = '8b1f2a3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DO $$
        BEGIN
            -- Ensure ID is integer (casts existing values if any)
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'rooms'
                  AND column_name = 'id'
                  AND data_type IN ('character varying', 'text')
            ) THEN
                ALTER TABLE rooms
                ALTER COLUMN id TYPE INTEGER
                USING id::integer;
            END IF;

            -- Ensure default identity/sequence exists
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'rooms'
                  AND column_name = 'id'
                  AND is_identity = 'YES'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = 'rooms_id_seq'
                ) THEN
                    CREATE SEQUENCE rooms_id_seq OWNED BY rooms.id;
                END IF;

                ALTER TABLE rooms
                ALTER COLUMN id SET DEFAULT nextval('rooms_id_seq');

                PERFORM setval(
                    'rooms_id_seq',
                    COALESCE((SELECT MAX(id) FROM rooms), 1),
                    true
                );
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_class WHERE relname = 'rooms_id_seq'
            ) THEN
                ALTER TABLE rooms ALTER COLUMN id DROP DEFAULT;
                DROP SEQUENCE rooms_id_seq;
            END IF;
        END
        $$;
        """
    )
