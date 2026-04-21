"""seeding college and department tables

Revision ID: 1798175b110d
Revises: f2eb54c34c61
Create Date: 2026-04-21 16:25:53.434673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = '1798175b110d'
down_revision: Union[str, None] = 'f2eb54c34c61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    college_table = table(
        "college",
        column("id", sa.Integer),
        column("name", sa.String),
    )

    op.bulk_insert(college_table, [
        {"id": 1, "name": "COLNAS"},
        {"id": 2, "name": "COLCOMP"},
        {"id": 3, "name": "COLFAST"},
        {"id": 4, "name": "COLENG"},
        {"id": 5, "name": "COLENVS"},
        {"id": 6, "name": "COLMANS"},
    ])

    op.execute("SELECT setval('college_id_seq', (SELECT MAX(id) FROM college));")


def downgrade() -> None:
    op.execute("DELETE FROM college WHERE id IN (1, 2, 3, 4, 5, 6);")
    op.execute("SELECT setval('college_id_seq', 1);")