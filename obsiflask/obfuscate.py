import json
import os
import hashlib
from pathlib import Path
from base64 import b64decode, b64encode
from Crypto.Cipher import ChaCha20

from obsiflask.app_state import AppState

MAGIC_PHRASE = b'OBF'
SALT_LENGTH = 16
DEFAULT_SALT = b'obsiflask-salt-d'


def make_key(password: str,
             salt: bytes = DEFAULT_SALT,
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


def obf_open(file_name: str, vault: str, method: str):
    assert method in ['r', 'rb', 'w', 'wb']
    if AppState.config.vaults[vault].obfuscation_suffix not in Path(
            file_name).suffixes:
        return open(file_name, method)
    if method in ['rb', 'wb']:
        return ObfuscationBinaryFile(file_name, method, vault)
    else:
        return ObfuscationTextFile(file_name, method, vault)


class ObfuscationTextFile(object):

    def __init__(self, file_name: Path | str, method, vault: str):
        if Path(file_name).exists():
            self._read_header(file_name, vault)
        else:
            self.salt = os.urandom(SALT_LENGTH)
        self.key = make_key(AppState.config.vaults[vault].obfuscation_key,
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

    def _read_header(self, file_name: Path | str, vault: str):
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

    def write(self, content: str | bytes):
        content = content.encode('utf-8')
        self.file_obj.write(repeating_key_xor_encrypt(content, self.key))

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file_obj.close()


class ObfuscationBinaryFile(object):

    def __init__(self, file_name: Path | str, method, vault: str):
        assert method in ['rb', 'wb']
        if method == 'rb':
            fixed_method = 'r'
        if method == 'wb':
            fixed_method = 'w'
        self.file_obj = open(file_name, fixed_method)
        self.method = method
        self.key = make_key(AppState.config.vaults[vault].obfuscation_key)

    def read(self) -> str:
        result = json.loads(self.file_obj.readline())
        nonce = b64decode(result['nonce'])
        content = b64decode(result['content'])
        cipher = ChaCha20.new(key=self.key, nonce=nonce)
        plaintext = cipher.decrypt(content)
        return plaintext

    def write(self, content: bytes):
        cipher = ChaCha20.new(key=self.key)
        ciphertext = b64encode(cipher.encrypt(content)).decode('utf-8')
        nonce = b64encode(cipher.nonce).decode('utf-8')
        self.file_obj.write(
            json.dumps({
                'content': ciphertext,
                'nonce': nonce
            }) + '\n')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.file_obj.close()
