"""modify skin descripcion to text

Revision ID: 0002_skin_descripcion_text
Revises: 0001_gamification_admin
Create Date: 2026-08-08 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_skin_descripcion_text'
down_revision = '0001_gamification_admin'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cambiar descripcion de VARCHAR(255) a TEXT para admitir descripciones largas
    op.alter_column(
        'skins',
        'descripcion',
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        'skins',
        'descripcion',
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=True
    )
