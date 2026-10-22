
# get_current_user: a FastAPI dependency. Add it to any route to make that route require a valid
# login token.

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.database.session import get_db
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorised = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorised

    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise unauthorised

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise unauthorised

    user = db.get(User, user_id)
    if user is None:
        raise unauthorised
    return user
