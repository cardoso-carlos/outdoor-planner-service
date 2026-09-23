from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from .config import (JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM,
                     JWT_SECRET_KEY)

password_hash = PasswordHash.recommended()
def hash_password(password: str) -> str: 
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool: 
    return password_hash.verify(password, hashed)

def create_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "email": email, "type": "access", "iat": now, "exp": now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict: 
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
