from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ragnarok_server.rdb import User, APIKey
from ragnarok_server.auth import get_current_user  # Auth dependency to get current logged-in user
import secrets, hashlib
from sqlalchemy import func
from datetime import datetime

from ragnarok_server.rdb.database import get_db

router = APIRouter(prefix="/api/keys", tags=["API Keys"])

# Pydantic schemas
from pydantic import BaseModel

class APIKeyInfo(BaseModel):
    id: int
    remark: str | None = None
    enabled: bool
    created_at: datetime  # Use datetime; FastAPI automatically serializes to ISO format

    class Config:
        orm_mode = True
        from_attributes = True

class APIKeyCreateResponse(BaseModel):
    id: int
    api_key: str       # the plaintext key (only shown once)
    created_at: datetime
    remark: str | None = None

    class Config:
        orm_mode = True
        from_attributes = True

# Define a Pydantic model for the update request body.
class APIKeyUpdate(BaseModel):
    enabled: bool | None = None
    remark: str | None = None

def _hash_key(plaintext: str) -> str:
    """Hash the API key plaintext using SHA-256 and return hex digest."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()

@router.post("/", response_model=APIKeyCreateResponse)
def create_api_key(
    remark: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Generate a secure random API key (plaintext)
    plaintext = secrets.token_urlsafe(32)  # ~256-bit random token
    key_hash = _hash_key(plaintext)
    # Create new APIKey record and save to DB
    new_key = APIKey(user_id=current_user.id, key_hash=key_hash, enabled=True, remark=remark)
    db.add(new_key)
    db.commit()
    db.refresh(new_key)  # Refresh to get new ID and created_at timestamp
    # Return the plaintext key and meta info
    return APIKeyCreateResponse(
        id=new_key.id,
        api_key=plaintext,
        created_at=new_key.created_at,
        remark=new_key.remark
    )

@router.get("/", response_model=list[APIKeyInfo])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Query all API keys belonging to the current user
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return api_keys

@router.delete("/{key_id}", status_code=204)
def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find the API key record for the current user
    api_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == current_user.id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    db.delete(api_key)
    db.commit()
    return  # Return 204 No Content

@router.patch("/{key_id}", response_model=APIKeyInfo)
def update_api_key(
    key_id: int,
    update: APIKeyUpdate,  # Accept request body as a Pydantic model
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Partial update: allow toggling enabled and updating remark
    api_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == current_user.id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    if update.enabled is not None:
        api_key.enabled = update.enabled
    if update.remark is not None:
        api_key.remark = update.remark
    db.commit()
    db.refresh(api_key)
    return APIKeyInfo.from_orm(api_key)

@router.post("/{key_id}/rotate", response_model=APIKeyCreateResponse)
def rotate_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find the API key record for the current user
    api_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == current_user.id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    # Optionally allow rotation of disabled keys; here we allow it.
    new_plaintext = secrets.token_urlsafe(32)
    new_hash = _hash_key(new_plaintext)
    # Update the record with the new hash and set created_at to current UTC time.
    api_key.key_hash = new_hash
    api_key.created_at = datetime.utcnow()  # Update timestamp to current time
    api_key.enabled = True  # Automatically enable the key after rotation.
    db.commit()
    db.refresh(api_key)
    return APIKeyCreateResponse(
        id=api_key.id,
        api_key=new_plaintext,
        created_at=api_key.created_at,
        remark=api_key.remark
    )
