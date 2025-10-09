"""add creado_en y actualizado_en en attempts"""
from alembic import op
import sqlalchemy as sa

# revisa tu head/prev
revision = "0004_add_attempt_timestamps"
down_revision = "0003_attempt_limits"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "attempts",
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "attempts",
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

def downgrade():
    op.drop_column("attempts", "actualizado_en")
    op.drop_column("attempts", "creado_en")
