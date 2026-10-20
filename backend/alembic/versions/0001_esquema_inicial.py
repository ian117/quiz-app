"""esquema inicial

Revision ID: 0001
Revises: 
Create Date: 2026-10-20 12:19:32.822836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('mode', sa.String(length=50), nullable=False),
    sa.Column('plan', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('score', sa.Integer(), server_default='0', nullable=False),
    sa.Column('total', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_session'))
    )
    op.create_table('tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tag')),
    sa.UniqueConstraint('slug', name=op.f('uq_tag_slug'))
    )
    op.create_table('topic',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('area', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_topic')),
    sa.UniqueConstraint('slug', name=op.f('uq_topic_slug'))
    )
    op.create_index(op.f('ix_topic_area'), 'topic', ['area'], unique=False)
    op.create_table('question',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=200), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('prompt_md', sa.Text(), nullable=False),
    sa.Column('explanation_md', sa.Text(), nullable=False),
    sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['topic_id'], ['topic.id'], name=op.f('fk_question_topic_id_topic')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_question')),
    sa.UniqueConstraint('key', name=op.f('uq_question_key'))
    )
    op.create_index(op.f('ix_question_topic_id'), 'question', ['topic_id'], unique=False)
    op.create_table('option',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('text_md', sa.Text(), nullable=False),
    sa.Column('is_correct', sa.Boolean(), nullable=False),
    sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], name=op.f('fk_option_question_id_question')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_option')),
    sa.UniqueConstraint('question_id', 'text_md', name='uq_option_question_id_text_md')
    )
    op.create_table('question_tag',
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], name=op.f('fk_question_tag_question_id_question')),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], name=op.f('fk_question_tag_tag_id_tag')),
    sa.PrimaryKeyConstraint('question_id', 'tag_id', name=op.f('pk_question_tag'))
    )
    op.create_table('session_question',
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], name=op.f('fk_session_question_question_id_question')),
    sa.ForeignKeyConstraint(['session_id'], ['session.id'], name=op.f('fk_session_question_session_id_session')),
    sa.PrimaryKeyConstraint('session_id', 'question_id', name=op.f('pk_session_question'))
    )
    op.create_table('answer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('option_id', sa.Integer(), nullable=False),
    sa.Column('is_correct', sa.Boolean(), nullable=False),
    sa.Column('time_ms', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['option_id'], ['option.id'], name=op.f('fk_answer_option_id_option')),
    sa.ForeignKeyConstraint(['session_id', 'question_id'], ['session_question.session_id', 'session_question.question_id'], name=op.f('fk_answer_session_id_session_question')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_answer')),
    sa.UniqueConstraint('session_id', 'question_id', name='uq_answer_session_id_question_id')
    )
    op.create_index(op.f('ix_answer_question_id'), 'answer', ['question_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_answer_question_id'), table_name='answer')
    op.drop_table('answer')
    op.drop_table('session_question')
    op.drop_table('question_tag')
    op.drop_table('option')
    op.drop_index(op.f('ix_question_topic_id'), table_name='question')
    op.drop_table('question')
    op.drop_index(op.f('ix_topic_area'), table_name='topic')
    op.drop_table('topic')
    op.drop_table('tag')
    op.drop_table('session')
