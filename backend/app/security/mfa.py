from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Dict, List, Set

import bcrypt
import pyotp


ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
BACKUP_CODE_LENGTH = 8
BACKUP_CODES_TOTAL = 10


@dataclass
class MfaRecord:
    email: str
    secret: str
    backup_code_hashes: List[bytes]
    used_backup_codes: Set[bytes] = field(default_factory=set)


_records: Dict[str, MfaRecord] = {}
_latest_codes: Dict[str, List[str]] = {}


def _normalize(email: str) -> str:
    return (email or "").strip().lower()


def _generate_secret() -> str:
    return pyotp.random_base32()


def _generate_backup_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(BACKUP_CODE_LENGTH))


def _hash_backup_code(code: str) -> bytes:
    return bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt())


def is_enrolled(email: str) -> bool:
    return _normalize(email) in _records


def enroll(email: str) -> MfaRecord:
    normalized = _normalize(email)
    secret = _generate_secret()
    codes = [_generate_backup_code() for _ in range(BACKUP_CODES_TOTAL)]
    hashes = [_hash_backup_code(code) for code in codes]
    record = MfaRecord(email=email, secret=secret, backup_code_hashes=hashes)
    _records[normalized] = record
    _latest_codes[normalized] = codes
    return record


def provisioning_uri(email: str, issuer: str = "EVP") -> str:
    normalized = _normalize(email)
    record = _records.get(normalized)
    if not record:
        raise ValueError("MFA not enrolled for this email")
    totp = pyotp.TOTP(record.secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_totp(email: str, code: str, valid_window: int = 1) -> bool:
    normalized = _normalize(email)
    record = _records.get(normalized)
    if not record or not code:
        return False
    totp = pyotp.TOTP(record.secret)
    try:
        return bool(totp.verify(code, valid_window=valid_window))
    except Exception:
        return False


def try_backup_code(email: str, code: str) -> bool:
    normalized = _normalize(email)
    record = _records.get(normalized)
    if not record or not code:
        return False
    code_bytes = code.encode("utf-8")
    for hashed in record.backup_code_hashes:
        if hashed in record.used_backup_codes:
            continue
        if bcrypt.checkpw(code_bytes, hashed):
            record.used_backup_codes.add(hashed)
            return True
    return False


def latest_backup_codes(email: str) -> List[str]:
    """Return the most recently generated backup codes for an email."""
    return list(_latest_codes.get(_normalize(email), []))


__all__ = [
    "MfaRecord",
    "is_enrolled",
    "enroll",
    "provisioning_uri",
    "verify_totp",
    "try_backup_code",
    "latest_backup_codes",
]
