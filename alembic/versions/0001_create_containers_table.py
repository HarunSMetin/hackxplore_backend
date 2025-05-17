from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'containers',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location_lat', sa.Float, nullable=False),
        sa.Column('location_lng', sa.Float, nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('capacity', sa.Integer, nullable=False),
        sa.Column('current_fill', sa.Integer, nullable=False),
        sa.Column('last_updated', sa.DateTime, nullable=False),
    )

def downgrade():
    op.drop_table('containers') 