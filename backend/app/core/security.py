import json
import base64
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from app.core.config import settings

def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a secure 16-byte random salt.
    Format: pbkdf2:sha256:100000$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a stored PBKDF2-HMAC-SHA256 hash using constant-time comparison.
    """
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3:
            return False
        header, salt, expected_hex = parts
        method, alg, iterations_str = header.split(':')
        iterations = int(iterations_str)

        key = hashlib.pbkdf2_hmac(
            alg,
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        return secrets.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4)) if len(data) % 4 != 0 else ''
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a cryptographically signed HMAC-SHA256 JWT access token.
    Payload includes standard claims: sub (user_id), tenant_id, role, email, iat, exp.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

    to_encode["iat"] = int(now.timestamp())
    to_encode["exp"] = int(expire.timestamp())

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64url_encode(json.dumps(to_encode, separators=(',', ':')).encode('utf-8'))

    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    secret = getattr(settings, "SECRET_KEY", "bayora-secret-key-change-in-production-2026").encode('utf-8')
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Validates signature, expiration, and payload structure.
    Raises ValueError on invalid signature, expired token, or malformed data.
    """
    parts = token.strip().split('.')
    if len(parts) != 3:
        raise ValueError("Malformed token structure: must have 3 segments.")

    header_b64, payload_b64, sig_b64 = parts

    # Verify signature in constant time
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    secret = getattr(settings, "SECRET_KEY", "bayora-secret-key-change-in-production-2026").encode('utf-8')
    expected_sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    
    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception:
        raise ValueError("Invalid signature encoding.")

    if not secrets.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature.")

    # Decode payload
    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
    except Exception:
        raise ValueError("Invalid token payload JSON.")

    # Check expiration
    exp = payload.get("exp")
    if not exp or not isinstance(exp, (int, float)):
        raise ValueError("Token missing or invalid 'exp' claim.")

    now_ts = int(datetime.now(timezone.utc).timestamp())
    if now_ts > exp:
        raise ValueError("Token has expired.")

    # Check required subject
    if not payload.get("sub"):
        raise ValueError("Token missing required 'sub' claim.")

    return payload
