"""phone number added

Revision ID: eee2b2b6f638
Revises: 
Create Date: 2025-02-27 16:33:46.238478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eee2b2b6f638'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Sütün tablo ekleyeceğimiz fonks.
def upgrade() -> None:
    # Örneğin models'deki User sınıfına phone_number değişkeni eklemiştik. Burada da ekliyoruz
    op.add_column('Users', sa.Column('phone_number', sa.String(length=11), nullable=True))

# Sütün tablo sileceğimiz fonks.
def downgrade() -> None:
    # op.drop_column('Users', 'phone_number')
    pass
