# alembic/versions/0006_add_audit_logs.py
from alembic import op
import sqlalchemy as sa

revision = "0006_add_audit_logs"
down_revision = "6f4ea44f8a6b"  # <- tu 0005 (teachers_identificador_set_not_null)
branch_labels = None
depends_on = None

def upgrade():
    # Crear tabla solo si NO existe (idempotente)
    op.execute("""
    CREATE TABLE IF NOT EXISTS public.audit_logs (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        actor_user_id UUID NOT NULL,
        target_user_id UUID NULL,
        action VARCHAR NOT NULL,
        payload JSONB NULL,
        ip VARCHAR NULL,
        ua VARCHAR NULL,
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)

def downgrade():
    # Borrar solo si existe
    op.execute("DROP TABLE IF EXISTS public.audit_logs;")
