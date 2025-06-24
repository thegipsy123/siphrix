from nacl.public import PrivateKey, PublicKey, Box
from nacl.encoding import Base64Encoder
import base64
import hashlib

# ✅ Generate a new keypair (private & public)
def generate_keypair():
    private_key = PrivateKey.generate()
    public_key = private_key.public_key
    return (
        private_key.encode(encoder=Base64Encoder).decode(),
        public_key.encode(encoder=Base64Encoder).decode()
    )

# ✅ Base64 validation helper
def is_valid_base64(data: str) -> bool:
    try:
        base64.b64decode(data)
        return True
    except Exception:
        return False

# ✅ Hashing (SHA-256) for integrity check
def calculate_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verify_hash(data: bytes, expected_hash: str) -> bool:
    return calculate_hash(data) == expected_hash

# ✅ Encrypt a message using sender's private key and recipient's public key
def encrypt_message(sender_private_key_b64: str, recipient_public_key_b64: str, message: str) -> str:
    if not is_valid_base64(sender_private_key_b64) or not is_valid_base64(recipient_public_key_b64):
        raise ValueError("Invalid base64 key(s) provided for encryption.")

    sender_private = PrivateKey(sender_private_key_b64, encoder=Base64Encoder)
    recipient_public = PublicKey(recipient_public_key_b64, encoder=Base64Encoder)
    box = Box(sender_private, recipient_public)
    encrypted = box.encrypt(message.encode(), encoder=Base64Encoder)
    return encrypted.decode()

# ✅ Decrypt a message using recipient's private key and sender's public key
def decrypt_message(recipient_private_key_b64: str, sender_public_key_b64: str, encrypted_message_b64: str) -> str:
    if not is_valid_base64(recipient_private_key_b64) or not is_valid_base64(sender_public_key_b64):
        raise ValueError("Invalid base64 key(s) provided for decryption.")
    if not is_valid_base64(encrypted_message_b64):
        raise ValueError("Invalid base64 encrypted message.")

    try:
        recipient_private = PrivateKey(recipient_private_key_b64, encoder=Base64Encoder)
        sender_public = PublicKey(sender_public_key_b64, encoder=Base64Encoder)
        box = Box(recipient_private, sender_public)
        decrypted = box.decrypt(encrypted_message_b64.encode(), encoder=Base64Encoder)
        return decrypted.decode()
    except Exception as e:
        raise Exception(f"❌ Decryption failed: {str(e)}")

# ✅ Encrypt a binary file
def encrypt_file(sender_private_b64, recipient_public_b64, file_bytes: bytes) -> str:
    sender_private = PrivateKey(sender_private_b64, encoder=Base64Encoder)
    recipient_public = PublicKey(recipient_public_b64, encoder=Base64Encoder)
    box = Box(sender_private, recipient_public)
    encrypted = box.encrypt(file_bytes, encoder=Base64Encoder)
    return encrypted.decode()

# ✅ Decrypt a binary file
def decrypt_file(recipient_private_b64, sender_public_b64, encrypted_b64: str) -> bytes:
    recipient_private = PrivateKey(recipient_private_b64, encoder=Base64Encoder)
    sender_public = PublicKey(sender_public_b64, encoder=Base64Encoder)
    box = Box(recipient_private, sender_public)
    decrypted = box.decrypt(encrypted_b64.encode(), encoder=Base64Encoder)
    return decrypted
