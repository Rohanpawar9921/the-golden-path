import hashlib, hmac, secrets
try:
    from config.config import PASSWORD_HASH_ROUNDS, PASSWORD_SALT_BYTES, SESSION_TOKEN_BYTES
except ImportError:
    from Project.config.config import PASSWORD_HASH_ROUNDS, PASSWORD_SALT_BYTES, SESSION_TOKEN_BYTES
def hash_password(password, salt=None):
    if isinstance(salt, str):
        salt = bytes.fromhex(salt)
    salt=salt or secrets.token_bytes(PASSWORD_SALT_BYTES); digest=hashlib.pbkdf2_hmac("sha256",str(password).encode(),salt,PASSWORD_HASH_ROUNDS)
    return f"sha256${salt.hex()}${digest.hex()}"
def verify_password(password, encoded):
    try:
        algorithm,salt,digest=encoded.split("$")
        actual=hashlib.pbkdf2_hmac("sha256",str(password).encode(),bytes.fromhex(salt),PASSWORD_HASH_ROUNDS)
        return algorithm=="sha256" and hmac.compare_digest(actual.hex(),digest)
    except (AttributeError,ValueError): return False
def create_session_token(): return secrets.token_urlsafe(SESSION_TOKEN_BYTES)