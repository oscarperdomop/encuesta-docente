"""zero risk compatibility layer (additive/idempotent)"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0007_zero_risk_compat_layer"
down_revision = "0006_add_audit_logs"
branch_labels = None
depends_on = None


def _table_exists(insp, table: str) -> bool:
    try:
        return insp.has_table(table, schema="public") or insp.has_table(table)
    except Exception:
        names = set(insp.get_table_names()) | set(insp.get_table_names(schema="public"))
        return table in names


def _columns(insp, table: str) -> set[str]:
    for schema in ("public", None):
        try:
            cols = insp.get_columns(table, schema=schema)
            if cols:
                return {c["name"] for c in cols}
        except Exception:
            continue
    return set()


def _add_col_if_missing(table: str, column: sa.Column) -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not _table_exists(insp, table):
        return
    cols = _columns(insp, table)
    if column.name not in cols:
        op.add_column(table, column, schema="public")


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # 1) turnos (tabla usada por runtime; puede faltar en algunas BD)
    if not _table_exists(insp, "turnos"):
        op.create_table(
            "turnos",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'open'")),
            sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            schema="public",
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_turnos_user_id ON public.turnos (user_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_turnos_status ON public.turnos (status)")

    # 2) attempts: compat de columnas de timestamps usadas por backend
    _add_col_if_missing(
        "attempts",
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=True),
    )
    _add_col_if_missing(
        "attempts",
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
    )

    # 3) responses: modelo/runtime usa created_at; migraciones antiguas podían traer creado_en
    _add_col_if_missing(
        "responses",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 4) attempt_limits: algunas instalaciones pudieron quedar sin max_intentos
    _add_col_if_missing(
        "attempt_limits",
        sa.Column("max_intentos", sa.Integer(), nullable=True, server_default=sa.text("2")),
    )
    _add_col_if_missing(
        "attempt_limits",
        sa.Column("extra_otorgados", sa.Integer(), nullable=True, server_default=sa.text("0")),
    )

    # 5) audit_logs: compatibilidad de nomenclatura histórica (user_id/accion vs actor_user_id/action)
    if _table_exists(insp, "audit_logs"):
        _add_col_if_missing("audit_logs", sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        _add_col_if_missing("audit_logs", sa.Column("accion", sa.String(length=100), nullable=True))
        _add_col_if_missing("audit_logs", sa.Column("actor_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        _add_col_if_missing("audit_logs", sa.Column("action", sa.String(length=100), nullable=True))
        _add_col_if_missing("audit_logs", sa.Column("creado_en", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # No-op intencional para evitar operaciones destructivas en rollback automático.
    pass
