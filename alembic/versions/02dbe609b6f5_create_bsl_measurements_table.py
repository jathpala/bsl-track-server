"""Create BSL measurements table

Revision ID: 02dbe609b6f5
Revises:
Create Date: 2024-09-03 18:04:58.596266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02dbe609b6f5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bsls",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("bsl", sa.DECIMAL(scale=1)),
        sa.Column("date", sa.Date, server_default=sa.func.current_date()),
        sa.Column("time", sa.Time, server_default=sa.func.current_time())
    )


def downgrade() -> None:
    op.drop_table("bsls")
