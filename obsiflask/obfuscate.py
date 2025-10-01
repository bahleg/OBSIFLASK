import json
import os
import hashlib
from pathlib import Path
from base64 import b64decode, b64encode
from Crypto.Cipher import ChaCha20

from obsiflask.app_state import AppState

MAGIC_PHRASE = b'OBF'
SALT_LENGTH = 16


def make_key(password: str,
             salt: bytes,
             iterations: int = 200_000,
             dklen: int = 32) -> bytes:

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


def repeating_key_xor_encrypt(pt: bytes, key: bytes) -> bytes:
    ct = bytes([b ^ key[i % len(key)] for i, b in enumerate(pt)])
    return ct


def repeating_key_xor_decrypt(ct: bytes, key: bytes) -> bytes:
    pt = bytes([b ^ key[i % len(key)] for i, b in enumerate(ct)])
    return pt


def obf_open(file_name: str, vault: str, method: str, obfuscation_mode: str = 'auto', key: str | None = None):
    assert obfuscation_mode in ['obfuscate', 'raw', 'auto']
    assert method in ['r', 'rb', 'w', 'wb']
    if obfuscation_mode == 'auto':
        obfscate = AppState.config.vaults[vault].obfuscation_suffix not in Path(
            file_name).suffixes
    else:
        obfscate = (obfuscation_mode == 'obfuscate')
    if obfscate:
        return open(file_name, method)
    if method in ['rb', 'wb']:
        return ObfuscationBinaryFile(file_name, method, vault, key)
    else:
        return ObfuscationTextFile(file_name, method, vault, key)


class ObfuscationTextFile(object):

    def __init__(self, file_name: Path | str, method, vault: str, key:str | None = None):
        self.key = key or AppState.config.vaults[vault].obfuscation_key
        if Path(file_name).exists():
            self._read_header(file_name)
        else:
            self.salt = os.urandom(SALT_LENGTH)
        self.key = make_key(self.key,
                            self.salt)
        assert method in ['r', 'w']
        fixed_method = method
        if method == 'r':
            fixed_method = 'rb'
        if method == 'w':
            fixed_method = 'wb'

        self.file_obj = open(file_name, fixed_method)

        if fixed_method == 'rb':
            header_length = len(MAGIC_PHRASE) + 1 + SALT_LENGTH
            self.file_obj.seek(header_length)
        else:
            self._write_header()
        self.method = method

    def _read_header(self, file_name: Path | str):
        header_length = len(MAGIC_PHRASE) + 1 + SALT_LENGTH
        with open(file_name, 'rb') as inp:
            header = inp.read(header_length)
            if len(header) < header_length:
                raise ValueError('Incorrect header for obfuscated file')

            assert MAGIC_PHRASE == header[:len(MAGIC_PHRASE)]
            assert header[len(MAGIC_PHRASE)] == 0  # for future versions
            self.salt = header[-SALT_LENGTH:]

    def _write_header(self):
        self.file_obj.write(MAGIC_PHRASE + b'\x00' + self.salt)

    def read(self) -> str:
        result = repeating_key_xor_decrypt(self.file_obj.read(), self.key)
        return result.decode('utf-8')

    def write(self, content: str):
        content = content.encode('utf-8')
        self.file_obj.write(repeating_key_xor_encrypt(content, self.key))

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file_obj.close()


class ObfuscationBinaryFile(object):

    def __init__(self, file_name: Path | str, method, vault: str, key : str | None = None):
        assert method in ['rb', 'wb']
        if method == 'rb':
            fixed_method = 'r'
        if method == 'wb':
            fixed_method = 'w'
        self.file_obj = open(file_name, fixed_method)
        self.method = method
        self.vault = vault
        self.key = key or AppState.config.vaults[self.vault].obfuscation_key

    def read(self) -> bytes:
        result = json.loads(self.file_obj.readline())
        assert result['version'] == 0
        nonce = b64decode(result['nonce'])
        content = b64decode(result['content'])
        salt = b64decode(result['salt'])
        key = make_key(self.key,
                       salt)
        cipher = ChaCha20.new(key=key, nonce=nonce)
        plaintext = cipher.decrypt(content)
        return plaintext

    def write(self, content: bytes):
        salt = os.urandom(16)
        key = make_key(self.key,
                       salt)
        cipher = ChaCha20.new(key=key)
        ciphertext = b64encode(cipher.encrypt(content)).decode('utf-8')
        nonce = b64encode(cipher.nonce).decode('utf-8')
        self.file_obj.write(
            json.dumps({
                'content': ciphertext,
                'nonce': nonce,
                'salt': b64encode(salt).decode('utf-8'),
                'version': 0
            }) + '\n')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file_obj.close()
