from alembic import op
import sqlalchemy as sa

revision = '0001_init_core'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS citext;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.create_table(
        'users',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.dialects.postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column('nombre', sa.String(200), nullable=True),
        sa.Column('estado', sa.String(20), nullable=False, server_default='activo'),
        sa.Column('creado_en', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )

    op.create_table(
        'roles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nombre', sa.String(50), nullable=False, unique=True),
    )

    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    )

def downgrade():
    op.drop_table('user_roles')
    op.drop_table('roles')
    op.drop_table('users')
    op.execute("DROP EXTENSION IF EXISTS pgcrypto;")
    op.execute("DROP EXTENSION IF EXISTS citext;")
