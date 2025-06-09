# ragnarok_server/auth.py.py

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from ragnarok_toolkit.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from ragnarok_server.rdb.repositories.user import UserRepository
from ragnarok_server.rdb.repositories.tenant import TenantRepository
from ragnarok_server.rdb.models import User, Tenant
from ragnarok_server.exceptions import NoResultFoundError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth.py"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth.py/token")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    principal_id: int
    principal_type: str
    exp: datetime


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# todo: tenant need a similar method
@router.post("auth.py/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Exchange username+password for a JWT.
    Assumes UserRepository.authenticate returns (user_id, tenant_id) on success.
    """
    user_repo = UserRepository()
    user = await user_repo.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    # choose principal_type=user; you could decide tenant login similarly
    token = create_access_token(
        principal_id=user.id,
        principal_type="user",
    )
    return Token(access_token=token)


def create_access_token(
    *,
    principal_id: int,
    principal_type: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT including:
      - principal_id: user or tenant ID
      - principal_type: "user" or "tenant"
      - exp: expiry timestamp
    """
    to_encode = {"principal_id": principal_id, "principal_type": principal_type}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def decode_access_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Decode and validate a JWT, raising 401 if invalid.
    Returns TokenData with principal_id, principal_type, exp.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        pid = payload.get("principal_id")
        ptype = payload.get("principal_type")
        exp = payload.get("exp")
        if pid is None or ptype is None or exp is None:
            raise credentials_exception
        return TokenData(
            principal_id=int(pid),
            principal_type=str(ptype),
            exp=datetime.utcfromtimestamp(exp),
        )
    except JWTError as e:
        logger.warning("JWT decode error", exc_info=e)
        raise credentials_exception


# New get_current_user function
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        user_repo: UserRepository = Depends(),  # Inject the UserRepository
) -> User:
    """
    Get the current user from the decoded JWT token.
    This function is used as a dependency in routes that need the current authenticated user.
    """
    token_data = await decode_access_token(token)  # Decode the token
    user = await user_repo.get_user_by_id(token_data.principal_id)  # Get the user from the database

    if not user or token_data.principal_type != "user":
        raise NoResultFoundError  # If no user found, raise an exception

    return user  # Return the user object


async def get_current_tenant(
        token: str = Depends(oauth2_scheme),
        tenant_repo: TenantRepository = Depends(),
) -> Tenant:
    """
    Get the current tenant from the decoded JWT token.
    This function is used as a dependency in routes that need the current authenticated tenant.
    """
    token_data = await decode_access_token(token)
    tenant = await tenant_repo.get_tenant_by_id(token_data.principal_id)

    return tenant



# # Usage in a route
# @router.get("/users/me", response_model=User)
# async def read_users_me(current_user: dict = Depends(get_current_user)):
#     """
#     Retrieve the current logged-in user.
#     """
#     return current_user
