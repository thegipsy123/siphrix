# ecdh_encryption.py
# Unified ECDH + AES-GCM encryption module for messages and files

import base64
import os
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

# === Utility ===


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def from_b64url(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded)

# === Key Pair ===


def generate_keypair():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    private_jwk = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ).decode()
    public_jwk = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return private_jwk, public_jwk


def load_private_key(pem: str):
    return serialization.load_pem_private_key(pem.encode(), password=None)


def load_public_key(pem: str):
    return serialization.load_pem_public_key(pem.encode())

# === Derive Shared AES Key ===


def derive_key(private_key_pem: str, public_key_pem: str) -> bytes:
    private_key = load_private_key(private_key_pem)
    public_key = load_public_key(public_key_pem)
    shared = private_key.exchange(ec.ECDH(), public_key)
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'siphrix',
    ).derive(shared)

# === Encrypt & Decrypt Messages ===


def encrypt_message(sender_priv_pem: str, recipient_pub_pem: str, plaintext: str) -> str:
    key = derive_key(sender_priv_pem, recipient_pub_pem)
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    encrypted = aesgcm.encrypt(iv, plaintext.encode(), None)
    return f"{b64url(iv)}.{b64url(encrypted)}"


def decrypt_message(recipient_priv_pem: str, sender_pub_pem: str, ciphertext: str) -> str:
    key = derive_key(recipient_priv_pem, sender_pub_pem)
    aesgcm = AESGCM(key)
    iv_b64, enc_b64 = ciphertext.split(".")
    iv = from_b64url(iv_b64)
    encrypted = from_b64url(enc_b64)
    return aesgcm.decrypt(iv, encrypted, None).decode()

# === Encrypt & Decrypt Files ===


def encrypt_file(sender_priv_pem: str, recipient_pub_pem: str, file_bytes: bytes) -> str:
    key = derive_key(sender_priv_pem, recipient_pub_pem)
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    encrypted = aesgcm.encrypt(iv, file_bytes, None)
    return f"{b64url(iv)}.{b64url(encrypted)}"


def decrypt_file(recipient_priv_pem: str, sender_pub_pem: str, encrypted_blob: str) -> bytes:
    key = derive_key(recipient_priv_pem, sender_pub_pem)
    aesgcm = AESGCM(key)
    iv_b64, enc_b64 = encrypted_blob.split(".")
    iv = from_b64url(iv_b64)
    encrypted = from_b64url(enc_b64)
    return aesgcm.decrypt(iv, encrypted, None)


import hashlib


def calculate_hash(data: bytes) -> str:
    """SHA-256 hash for integrity checking"""
    return hashlib.sha256(data).hexdigest()


from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature


def sign_message(private_key, message):
    signature = private_key.sign(message.encode(), ec.ECDSA(hashes.SHA256()))
    return signature.hex()


def verify_signature(public_key, message, signature_hex):
    signature = bytes.fromhex(signature_hex)
    try:
        public_key.verify(signature, message.encode(), ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False
