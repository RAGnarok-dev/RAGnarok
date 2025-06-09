"""add avatar_url to users and tenants

Revision ID: 20250605_add_avatar_url
Revises: 868cffb7278e
Create Date: 2025-06-05 14:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = '20250605_add_avatar_url'
down_revision = '868cffb7278e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=False,
              server_default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"))
    op.add_column('tenants', sa.Column('avatar_url', sa.String(), nullable=False,
              server_default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"))


def downgrade():
    op.drop_column('users', 'avatar_url')
    op.drop_column('tenants', 'avatar_url')
