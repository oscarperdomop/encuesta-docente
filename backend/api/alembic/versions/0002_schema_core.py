from alembic import op
import sqlalchemy as sa

revision = '0002_schema_core'
down_revision = '0001_init_core'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'teachers',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('identificador', sa.String(50), nullable=False, unique=True),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('programa', sa.String(200), nullable=True),
        sa.Column('estado', sa.String(20), nullable=False, server_default='activo'),
    )

    op.create_table(
        'periods',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('nombre', sa.String(50), nullable=False, unique=True),
        sa.Column('anyo', sa.Integer, nullable=False),
        sa.Column('semestre', sa.Integer, nullable=False),
    )

    op.create_table(
        'surveys',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('codigo', sa.String(120), nullable=False, unique=True),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('periodo_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('periods.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('estado', sa.String(20), nullable=False, server_default='activa'),
        sa.Column('fecha_inicio', sa.Date(), nullable=True),
        sa.Column('fecha_fin', sa.Date(), nullable=True),
    )

    op.create_table(
        'survey_sections',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('survey_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('titulo', sa.String(255), nullable=False),
        sa.Column('orden', sa.Integer, nullable=False),
    )

    op.create_table(
        'questions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('survey_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('survey_sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('codigo', sa.String(10), nullable=False),
        sa.Column('enunciado', sa.Text(), nullable=False),
        sa.Column('orden', sa.Integer, nullable=False),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('peso', sa.Numeric(6,2), nullable=False, server_default='1'),
    )
    op.create_index('uq_questions_code_per_survey', 'questions', ['survey_id','codigo'], unique=True)

    op.create_table(
        'survey_teacher_assignments',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('survey_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
    )
    op.create_index('uq_survey_teacher_once', 'survey_teacher_assignments', ['survey_id','teacher_id'], unique=True)

    op.create_table(
        'user_teacher_permissions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('survey_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
    )
    op.create_index('uq_user_survey_teacher_once', 'user_teacher_permissions', ['survey_id','user_id','teacher_id'], unique=True)

    op.create_table(
        'attempts',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('survey_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('intento_nro', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('estado', sa.String(20), nullable=False, server_default='en_progreso'),
        sa.Column('progreso_json', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index('idx_attempts_user_survey_estado', 'attempts', ['user_id','survey_id','estado'], unique=False)
    op.create_index('uq_attempt_enviado', 'attempts', ['user_id','survey_id','teacher_id'], unique=True,
                    postgresql_where=sa.text("estado = 'enviado'"))

    op.create_table(
        'responses',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('attempt_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('valor_likert', sa.Integer(), nullable=True),
        sa.Column('texto', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('creado_en', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )
    op.create_unique_constraint('uq_response_per_question_attempt', 'responses', ['attempt_id','question_id'])

    op.create_table(
        'attempt_limits',
        sa.Column('survey_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('surveys.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('max_intentos', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('extra_otorgados', sa.Integer(), nullable=False, server_default='0'),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('accion', sa.String(100), nullable=False),
        sa.Column('payload', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('ip', sa.String(64), nullable=True),
        sa.Column('ua', sa.Text(), nullable=True),
        sa.Column('creado_en', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )

def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('attempt_limits')
    op.drop_constraint('uq_response_per_question_attempt', 'responses', type_='unique')
    op.drop_table('responses')
    op.drop_index('uq_attempt_enviado', table_name='attempts')
    op.drop_index('idx_attempts_user_survey_estado', table_name='attempts')
    op.drop_table('attempts')
    op.drop_index('uq_user_survey_teacher_once', table_name='user_teacher_permissions')
    op.drop_table('user_teacher_permissions')
    op.drop_index('uq_survey_teacher_once', table_name='survey_teacher_assignments')
    op.drop_table('survey_teacher_assignments')
    op.drop_index('uq_questions_code_per_survey', table_name='questions')
    op.drop_table('questions')
    op.drop_table('survey_sections')
    op.drop_table('surveys')
    op.drop_table('periods')
    op.drop_table('teachers')
