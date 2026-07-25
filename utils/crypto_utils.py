"""敏感字段加密工具 —— Fernet (AES-128-CBC + HMAC-SHA256)"""
from cryptography.fernet import Fernet
from web_backend.config import ENCRYPTION_KEY

_fernet = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None


def encrypt(plaintext: str) -> str:
    """明文 → 密文（Base64）"""
    if not _fernet or not plaintext:
        return plaintext
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """密文 → 明文，失败返回原文（兼容旧数据）"""
    if not _fernet or not ciphertext:
        return ciphertext
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext  # 旧数据已是明文，下次保存自动转密文
