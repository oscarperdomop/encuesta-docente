# alembic/versions/6f4ea44f8a6b_teachers_identificador_set_not_null.py
from alembic import op
import sqlalchemy as sa

revision = "6f4ea44f8a6b"                    # SOLO el hash/ID, sin texto extra
down_revision = "0004_add_attempt_timestamps" # el ID exacto del anterior
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TABLE public.teachers ALTER COLUMN identificador SET NOT NULL")

def downgrade():
    op.execute("ALTER TABLE public.teachers ALTER COLUMN identificador DROP NOT NULL")
