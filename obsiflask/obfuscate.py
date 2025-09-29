import json
from base64 import b64encode, b64decode
from Crypto.Cipher import ChaCha20
from obsiflask.app_state import AppState
import hashlib

SALT = b'obsiflask-salt'


def make_key(password: str,
             salt: bytes = None,
             iterations: int = 200_000,
             dklen: int = 32) -> bytes:
    if salt is None:
        salt = SALT

    password_bytes = password.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256",
                              password_bytes,
                              salt,
                              iterations,
                              dklen=dklen)
    return key


def init_obfuscation():
    for vault in AppState.config.vaults:
        if AppState.config.vaults[vault].obfuscation_key == '':
            raise ValueError(f'Bad obfuscation key for {vault}')


def obfuscate_read(stream, vault: str, obfuscate: bool = False) -> str:
    if not obfuscate:
        return stream.read()
    else:
        result = json.loads(stream.read())
        nonce = b64decode(result['nonce'])
        cipher = ChaCha20.new(key=make_key(
            AppState.config.vaults[vault].obfuscation_key),
                              nonce=nonce)
        ciphertext = b64decode(result['ciphertext'])
        plaintext = cipher.decrypt(ciphertext).decode('utf-8')
        return plaintext


def obfuscate_write(stream, text: str, vault: str, obfuscate: bool = False):
    if not obfuscate:
        return stream.write(text)
    else:
        cipher = ChaCha20.new(
            key=make_key(AppState.config.vaults[vault].obfuscation_key))

        ciphertext = cipher.encrypt(text.encode('utf-8'))
        stream.write(
            json.dumps({
                'nonce': b64encode(cipher.nonce).decode('utf-8'),
                'ciphertext': b64encode(ciphertext).decode('utf-8')
            }))
