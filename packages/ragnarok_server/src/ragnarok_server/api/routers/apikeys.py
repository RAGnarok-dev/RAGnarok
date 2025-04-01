# ragnarok_server/api/routes/apikeys.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ragnarok_server.rdb import models
from ragnarok_server.toolkit.auth import get_current_user  # Auth dependency to get current logged-in user
import secrets, hashlib

router = APIRouter(prefix="/api/keys", tags=["API Keys"])

# Pydantic schema for API Key output (excluding sensitive fields)
from pydantic import BaseModel
class APIKeyInfo(BaseModel):
    id: int
    remark: str | None = None
    enabled: bool
    created_at: str  # or datetime, which will be JSON-serialized
    class Config:
        orm_mode = True

class APIKeyCreateResponse(BaseModel):
    id: int
    api_key: str       # the plaintext key
    created_at: str
    remark: str | None = None

def _hash_key(plaintext: str) -> str:
    """Hash the API key plaintext using SHA-256 and return hex digest."""
    return hashlib.sha256(plaintext.encode('utf-8')).hexdigest()

@router.post("/", response_model=APIKeyCreateResponse)
def create_api_key(remark: str | None = None, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    # 1. Generate a secure random API key (plaintext)
    plaintext = secrets.token_urlsafe(32)  # Generate a 256-bit random token (43 char Base64-like string)
    key_hash = _hash_key(plaintext)
    # 2. Create APIKey object and save to DB
    new_key = models.APIKey(user_id=current_user.id, key_hash=key_hash, enabled=True, remark=remark)
    db.add(new_key)
    db.commit()
    db.refresh(new_key)  # refresh to get new ID and timestamps
    # 3. Return the plaintext to the user (along with meta info)
    return APIKeyCreateResponse(id=new_key.id, api_key=plaintext, created_at=new_key.created_at.isoformat(), remark=new_key.remark)

@router.get("/", response_model=list[APIKeyInfo])
def list_api_keys(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Query all API keys belonging to the current user
    api_keys = db.query(models.APIKey).filter_by(user_id=current_user.id).all()
    return api_keys  # FastAPI will use Pydantic model to filter fields

@router.delete("/{key_id}", status_code=204)
def delete_api_key(key_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Find the API key by ID and user_id to ensure ownership
    api_key = db.query(models.APIKey).filter_by(id=key_id, user_id=current_user.id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    db.delete(api_key)
    db.commit()
    return  # 204 No Content

@router.patch("/{key_id}")
def update_api_key(key_id: int, enabled: bool | None = None, remark: str | None = None,
                   db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Partial update: allow toggling enabled and updating remark
    api_key = db.query(models.APIKey).filter_by(id=key_id, user_id=current_user.id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    if enabled is not None:
        api_key.enabled = enabled
    if remark is not None:
        api_key.remark = remark
    db.commit()
    db.refresh(api_key)
    return APIKeyInfo.from_orm(api_key)  # Return the updated info

@router.post("/{key_id}/rotate", response_model=APIKeyCreateResponse)
def rotate_api_key(key_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Find the API key record
    api_key = db.query(models.APIKey).filter_by(id=key_id, user_id=current_user.id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    if not api_key.enabled:
        # Optionally, decide whether a disabled key can be rotated. Here we allow it.
        pass
    # Generate a new plaintext and hash
    new_plaintext = secrets.token_urlsafe(32)
    new_hash = _hash_key(new_plaintext)
    # Update the existing record with new hash and reset timestamp
    api_key.key_hash = new_hash
    api_key.created_at = func.now()  # will set to current timestamp on commit
    api_key.enabled = True  # rotating could automatically enable the key
    db.commit()
    db.refresh(api_key)
    # Return the new plaintext key to the user
    return APIKeyCreateResponse(id=api_key.id, api_key=new_plaintext, created_at=api_key.created_at.isoformat(), remark=api_key.remark)
