"""add monedas admin and skin prices

Revision ID: 0001_gamification_admin
Revises: 
Create Date: 2026-08-07 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_gamification_admin'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Agregar control de monedas y rol admin a la tabla usuarios
    op.add_column('usuarios', sa.Column('monedas', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('usuarios', sa.Column('es_admin', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    
    # 2. Agregar precio en monedas a la tabla skins
    op.add_column('skins', sa.Column('precio_monedas', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('skins', 'precio_monedas')
    op.drop_column('usuarios', 'es_admin')
    op.drop_column('usuarios', 'monedas')
