"""ECDSA P-256 signing of manifest.json.

The app verifies with java.security Signature("SHA256withECDSA") and the embedded public keys.
"""
from __future__ import annotations

import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def generate_pem() -> tuple[bytes, bytes]:
    key = ec.generate_private_key(ec.SECP256R1())
    priv = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption())
    pub = key.public_key().public_bytes(serialization.Encoding.PEM,
                                        serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, pub


def sign(data: bytes, private_pem: bytes) -> str:
    key = serialization.load_pem_private_key(private_pem, password=None)
    return base64.b64encode(key.sign(data, ec.ECDSA(hashes.SHA256()))).decode()


def verify(data: bytes, signature_b64: str, public_pem: bytes) -> bool:
    key = serialization.load_pem_public_key(public_pem)
    try:
        key.verify(base64.b64decode(signature_b64), data, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False
