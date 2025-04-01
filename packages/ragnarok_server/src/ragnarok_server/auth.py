# ragnarok_server/toolkit/auth.py
from fastapi import Depends, HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from ragnarok_server.rdb import APIKey, User
from ragnarok_server.rdb.database import get_db
import hashlib

# Define a security dependency to read API key from header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_key(plaintext: str) -> str:
    """Compute SHA-256 hash of the given plaintext API key (hex digest)."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


async def get_current_user(api_key: str = Security(api_key_header),
                                  db: Session = Depends(get_db)) -> User:
    """Authenticate user by API key. Returns User object if valid, otherwise raises 401."""
    if not api_key:
        # No API key provided
        raise HTTPException(status_code=401, detail="API key required")
    # Compute hash and lookup in database
    key_hash = hash_key(api_key)
    key_record = db.query(APIKey).filter_by(key_hash=key_hash, enabled=True).first()
    if not key_record:
        # Key not found or not enabled
        raise HTTPException(status_code=401, detail="Invalid or disabled API key")
    # Get the associated user
    user = db.query(User).get(key_record.user_id)
    if not user:
        # In case the user was deleted but key remains (shouldn't happen due to cascade delete)
        raise HTTPException(status_code=401, detail="User not found for this API key")
    # Optionally, check if user is active or has any other status
    # if not user.is_active:
    #     raise HTTPException(status_code=401, detail="User account is inactive")
    return user
