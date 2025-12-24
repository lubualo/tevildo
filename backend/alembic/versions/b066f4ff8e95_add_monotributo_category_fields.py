"""add monotributo category fields

Revision ID: b066f4ff8e95
Revises: 9914413f14f5
Create Date: 2025-12-24 20:31:17.552725

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b066f4ff8e95'
down_revision: Union[str, Sequence[str], None] = '9914413f14f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop and recreate monotributo_category_limit table (no data to preserve)
    op.execute("DROP TABLE IF EXISTS monotributo_category_limit")

    op.create_table(
        'monotributo_category_limit',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('version_id', sa.String(), nullable=False),
        sa.Column('category_letter', sa.String(), nullable=False),
        sa.Column('annual_income_limit_services', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('annual_income_limit_goods', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('surface_limit_m2', sa.Integer(), nullable=True),
        sa.Column('electricity_limit_kwh', sa.Integer(), nullable=True),
        sa.Column('annual_rent_limit_ars', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('integrated_tax_services', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('pension_contribution_services', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('social_security_services', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('integrated_tax_goods', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('pension_contribution_goods', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('social_security_goods', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['monotributo_category_version.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_id', 'category_letter', name='uq_version_category')
    )

    # Update monotributo_category_version table
    op.add_column('monotributo_category_version', sa.Column('notes', sa.String(), nullable=True))

    with op.batch_alter_table('monotributo_category_version', schema=None) as batch_op:
        batch_op.drop_column('is_active')


def downgrade() -> None:
    """Downgrade schema."""
    # Revert monotributo_category_version changes
    with op.batch_alter_table('monotributo_category_version', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.INTEGER(), nullable=False, server_default='1'))
        batch_op.drop_column('notes')

    # Revert monotributo_category_limit changes
    with op.batch_alter_table('monotributo_category_limit', schema=None) as batch_op:
        # Add old columns back
        batch_op.add_column(sa.Column('annual_ars_limit', sa.NUMERIC(precision=15, scale=2), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('category_code', sa.VARCHAR(), nullable=False, server_default='A'))

        # Recreate old constraint
        batch_op.drop_constraint('uq_version_category', type_='unique')
        batch_op.create_unique_constraint('uq_version_category', ['version_id', 'category_code'])

        # Drop new columns
        batch_op.drop_column('created_at')
        batch_op.drop_column('social_security_goods')
        batch_op.drop_column('pension_contribution_goods')
        batch_op.drop_column('integrated_tax_goods')
        batch_op.drop_column('social_security_services')
        batch_op.drop_column('pension_contribution_services')
        batch_op.drop_column('integrated_tax_services')
        batch_op.drop_column('annual_rent_limit_ars')
        batch_op.drop_column('electricity_limit_kwh')
        batch_op.drop_column('surface_limit_m2')
        batch_op.drop_column('annual_income_limit_goods')
        batch_op.drop_column('annual_income_limit_services')
        batch_op.drop_column('category_letter')
