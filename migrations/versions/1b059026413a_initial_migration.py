"""Initial migration.

Revision ID: 1b059026413a
Revises: 
Create Date: 2023-08-23 01:49:14.280783

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b059026413a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'u_name',
               existing_type=sa.VARCHAR(length=128),
               nullable=False)
    op.create_unique_constraint(None, 'user', ['u_name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='unique')
    op.alter_column('user', 'u_name',
               existing_type=sa.VARCHAR(length=128),
               nullable=True)
    # ### end Alembic commands ###
