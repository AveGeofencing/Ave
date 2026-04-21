"""seed COLCOMP departments

Revision ID: 6a49ab1492f7
Revises: 1798175b110d
Create Date: 2026-04-21 16:34:00.822476

"""
from typing import Sequence, Union
from sqlalchemy.sql import table, column

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a49ab1492f7'
down_revision: Union[str, None] = '1798175b110d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    departments_table = table(
        "department",
        column("id", sa.Integer),
        column("name", sa.String),
        column("college_id", sa.Integer),
    )

    op.bulk_insert(departments_table, [
        {"id": 1, "name": "Computer Science", "college_id": 2},
        {"id": 2, "name": "Information Technology", "college_id": 2},
        {"id": 3, "name": "Cybersecurity", "college_id": 2},
        {"id": 4, "name": "Data Science", "college_id": 2},
        {"id": 5, "name": "Software Engineering", "college_id": 2},
    ])

    op.execute("SELECT setval('department_id_seq', (SELECT MAX(id) FROM department));")


def downgrade() -> None:
    op.execute("DELETE FROM department WHERE id IN (1, 2, 3, 4, 5);")
    op.execute("SELECT setval('department_id_seq', 1);")
