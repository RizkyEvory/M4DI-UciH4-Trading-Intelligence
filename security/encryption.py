"""
M4DI~UciH4 Trading Intelligence System
Security, Encryption & API Key Masking Utilities
"""
import base64
import hashlib
import os

# Try importing cryptography Fernet for robust authenticated encryption
try:
    from cryptography.fernet import Fernet
    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False


def _get_machine_key() -> bytes:
    """Generate or retrieve a deterministic local machine key for secret encryption"""
    try:
        import platform
        # Combine stable host characteristics
        seed = f"M4DI~UciH4_KEY_SALT_{platform.node()}_{platform.machine()}_{os.environ.get('USERNAME', 'trader')}"
        key_bytes = hashlib.sha256(seed.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(key_bytes)
    except Exception:
        fallback_seed = "M4DI~UciH4_INSTITUTIONAL_FALLBACK_SALT_2026"
        return base64.urlsafe_b64encode(hashlib.sha256(fallback_seed.encode("utf-8")).digest())


def encrypt_secret(plain_text: str) -> str:
    """
    Encrypt sensitive string (such as an API key) for safe local SQLite storage.
    Ensures secrets are not stored in raw plain text.
    """
    if not plain_text:
        return ""
    
    key = _get_machine_key()
    
    if _FERNET_AVAILABLE:
        try:
            f = Fernet(key)
            encrypted = f.encrypt(plain_text.encode("utf-8"))
            return "enc_f:" + encrypted.decode("utf-8")
        except Exception:
            pass
            
    # Standard library reversible obfuscation fallback
    raw_bytes = plain_text.encode("utf-8")
    xor_key = key[:len(raw_bytes)] if len(raw_bytes) <= len(key) else (key * (len(raw_bytes) // len(key) + 1))[:len(raw_bytes)]
    xored = bytes(b ^ k for b, k in zip(raw_bytes, xor_key))
    return "enc_x:" + base64.b64encode(xored).decode("utf-8")


def decrypt_secret(cipher_text: str) -> str:
    """Decrypt stored ciphertext back to plaintext when needed internally"""
    if not cipher_text:
        return ""
        
    key = _get_machine_key()
    
    if cipher_text.startswith("enc_f:") and _FERNET_AVAILABLE:
        try:
            f = Fernet(key)
            payload = cipher_text[6:].encode("utf-8")
            return f.decrypt(payload).decode("utf-8")
        except Exception:
            return ""
            
    if cipher_text.startswith("enc_x:"):
        try:
            raw_bytes = base64.b64decode(cipher_text[6:].encode("utf-8"))
            xor_key = key[:len(raw_bytes)] if len(raw_bytes) <= len(key) else (key * (len(raw_bytes) // len(key) + 1))[:len(raw_bytes)]
            decrypted = bytes(b ^ k for b, k in zip(raw_bytes, xor_key))
            return decrypted.decode("utf-8")
        except Exception:
            return ""
            
    # Unencrypted legacy fallback
    return cipher_text


def mask_api_key(raw_key: str) -> str:
    """
    Format an API key into a secure masked representation.
    Never exposes the full secret to GUI or logs.
    Example:
    'sk_live_1234567890abcdef' -> 'sk_••••••••••••cdef'
    'c7d24810a9f'              -> 'c7•••••••9f'
    """
    if not raw_key:
        return "••••••••"
        
    clean = raw_key.strip()
    length = len(clean)
    
    if length <= 6:
        return "••••••••"
    elif length <= 12:
        return f"{clean[:2]}••••••••{clean[-2:]}"
    elif length <= 20:
        return f"{clean[:3]}••••••••••••{clean[-3:]}"
    else:
        prefix = clean[:4]
        suffix = clean[-4:]
        mask_len = min(length - 8, 16)
        return f"{prefix}{'•' * mask_len}{suffix}"


class SecurityManager:
    """Convenience namespace wrapper for security functions"""
    encrypt = staticmethod(encrypt_secret)
    decrypt = staticmethod(decrypt_secret)
    mask = staticmethod(mask_api_key)

