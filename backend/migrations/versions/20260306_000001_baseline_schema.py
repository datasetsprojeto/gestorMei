"""baseline schema marker

Revision ID: 20260306_000001
Revises: 
Create Date: 2026-03-06 00:00:01
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260306_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Existing environments are currently bootstrapped by SQLAlchemy metadata.
    # New revisions must be incremental from this baseline.
    op.execute("SELECT 1")


def downgrade():
    op.execute("SELECT 1")
