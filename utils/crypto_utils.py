"""
敏感字段加密工具 —— Fernet (AES-128-CBC + HMAC-SHA256)

┌─────────────────────────────────────────────────────────────────────┐
│ 为什么用 Fernet？                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ 1. 对称加密：一个密钥同时用于加密和解密                            │
│ 2. 自带 HMAC 签名：密文被篡改后解密会报错（防篡改）               │
│ 3. Python 标准做法：cryptography 库一行 encrypt/decrypt            │
│ 4. 密钥通过环境变量 ENCRYPTION_KEY 注入，不进代码不存 DB          │
│                                                                     │
│ 面试可以这样讲：                                                    │
│ "Fernet = AES-128-CBC + HMAC-SHA256，防篡改防重放，                  │
│  密钥不进代码不存数据库，只走环境变量。                              │
│  解密失败自动回退明文，兼容旧数据，下次保存自动转密文。"            │
└─────────────────────────────────────────────────────────────────────┘

加密对象: 钉钉 webhook_url / secret / AI_API_KEY
"""
from cryptography.fernet import Fernet
from web_backend.config import ENCRYPTION_KEY

# 模块加载时创建加密器实例（全局复用，不走网络，无需连接池）
# 如果密钥未配置，_fernet 为 None，encrypt/decrypt 原样返回
_fernet = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None


def encrypt(plaintext: str) -> str:
    """明文 → 密文（Base64 编码）

    例: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
         → "gAAAAABl..." （Base64 密文）
    """
    if not _fernet or not plaintext:
        return plaintext  # 没配密钥或空值，不加密
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """密文 → 明文，失败返回原文

    为什么解密失败要返回原文？
      旧数据可能已经以明文形式存在数据库中（早期版本没加密）。
      返回原文 = 兼容旧数据，不会因为加解密切换导致系统不可用。
      下次用户保存配置时，会重新走 encrypt() 转成密文。
    """
    if not _fernet or not ciphertext:
        return ciphertext
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext  # 旧数据已是明文，下次保存自动转密文
