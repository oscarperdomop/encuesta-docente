# alembic/versions/0003_attempt_limits.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "0003_attempt_limits"
down_revision = "0002_schema_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    if "attempt_limits" not in insp.get_table_names():
        op.create_table(
            "attempt_limits",
            sa.Column("survey_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id",   sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("extra_otorgados", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("creado_en",      sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("survey_id", "user_id"),
            sa.UniqueConstraint("survey_id", "user_id", name="uq_attempt_limits_survey_user"),
            sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"]),
            sa.ForeignKeyConstraint(["user_id"],   ["users.id"]),
        )
    # Si ya existe, no hacemos nada; Alembic igualmente marcará la revisión como aplicada.


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "attempt_limits" in insp.get_table_names():
        op.drop_table("attempt_limits")
