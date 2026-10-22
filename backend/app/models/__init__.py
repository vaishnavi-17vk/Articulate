
# Imports every model so Alembic can find them through Base.metadata.

from app.models.user import User

__all__ = ["User"]
