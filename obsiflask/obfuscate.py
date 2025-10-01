"""
Basic logic for obfuscation

NOTE: obfuscation != encryption,
the proposed obfuscation scheme (especially for text files) is not sercure and reliealbe.
Use it ony for shallow hiding of the text content.

The pros of this obfuscation that it's git-friendly: if you change a small piece of content, the 
resulting obfuscation content will also be changed insignificantly
"""
import json
import os
import hashlib
from pathlib import Path
from base64 import b64decode, b64encode
import argparse

from Crypto.Cipher import ChaCha20

from obsiflask.app_state import AppState

MAGIC_PHRASE = b'OBF'
"""
This is the start of the obfuscation header.
Just to validate that we are doing everything right
"""
SALT_LENGTH = 16
"""
Length of salt to generate
"""


def make_key(password: str,
             salt: bytes,
             iterations: int = 200_000,
             dklen: int = 32) -> bytes:
    """
    Password to random-like bytes
    """

    password_bytes = password.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256",
                              password_bytes,
                              salt,
                              iterations,
                              dklen=dklen)
    return key


def init_obfuscation():
    """
    A placeholder for obfuscation logic.
    Currently only validates obfuscation keys
    """
    for vault in AppState.config.vaults:
        if AppState.config.vaults[vault].obfuscation_key == '':
            raise ValueError(f'Bad obfuscation key for {vault}')


def repeating_key_xor_encrypt(pt: bytes, key: bytes) -> bytes:
    """
    Xor obfuscation

    Args:
        pt (bytes): bytes to obfuscate
        key (bytes): key for obfuscation

    Returns:
        bytes: resulting obfuscated bytes
    """
    ct = bytes([b ^ key[i % len(key)] for i, b in enumerate(pt)])
    return ct


def repeating_key_xor_decrypt(ct: bytes, key: bytes) -> bytes:
    """
    Xor de-obfuscation

    Args:
        ct (bytes): obfuscated bytes
        key (bytes): key for obfuscation

    Returns:
        bytes: original bytes
    """
    pt = bytes([b ^ key[i % len(key)] for i, b in enumerate(ct)])
    return pt


def obf_open(file_name: str,
             vault: str,
             method: str = 'r',
             obfuscation_mode: str = 'auto',
             key: str | None = None):
    """
    Helper to open files

    Args:
        file_name (str): name of the file
        vault (str): vault name
        method (str, optional): one of ['r', 'rb', 'w', 'wb']. Defaults to 'r'.
        obfuscation_mode (str, optional): one of ['auto', 'obfuscate', 'raw']. Defaults to 'auto'.
        key (str | None, optional): key for obfuscation. If not set, will use it from vault config. Defaults to None.

    Returns:
        file handler: either obfuscated or non-obfuscated, depending on the mode
    """
    assert obfuscation_mode in ['obfuscate', 'raw', 'auto']
    assert method in ['r', 'rb', 'w', 'wb']
    if obfuscation_mode == 'auto':
        obfscate = AppState.config.vaults[
            vault].obfuscation_suffix in Path(file_name).suffixes
    else:
        obfscate = (obfuscation_mode == 'obfuscate')
    if not obfscate:
        return open(file_name, method)
    if method in ['rb', 'wb']:
        return ObfuscationBinaryFile(file_name, method, vault, key)
    else:
        return ObfuscationTextFile(file_name, method, vault, key)


class ObfuscationTextFile(object):
    """
    Helper for handling obfuscated text files
    """

    def __init__(self,
                 file_name: Path | str,
                 method,
                 vault: str,
                 key: str | None = None):
        """
        Constructor

        Args:
            file_name (Path | str): name of the file
            method (_type_): 'r' or 'w'
            vault (str): vault name
            key (str | None, optional): obfuscation key. If not set, will use a key from the vault config. Defaults to None.
        """
        self.key = key or AppState.config.vaults[vault].obfuscation_key
        self._read_header(file_name)    
        self.key = make_key(self.key, self.salt)
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
        """
        Helper for header read

        Args:
            file_name (Path | str): name of the file
        """
        header_length = len(MAGIC_PHRASE) + 1 + SALT_LENGTH
        if not Path(file_name).exists():
            self.salt = os.urandom(SALT_LENGTH)
            return
        with open(file_name, 'rb') as inp:
            header = inp.read(header_length)
            if len(header) == 0:
                self.salt = os.urandom(SALT_LENGTH)
                return
            if len(header) < header_length:
                raise ValueError('Incorrect header for obfuscated file')

            assert MAGIC_PHRASE == header[:len(MAGIC_PHRASE)]
            assert header[len(MAGIC_PHRASE)] == 0  # for future versions
            self.salt = header[-SALT_LENGTH:]

    def _write_header(self):
        """
        Helper for header write
        """
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
    """
    Helper for handling obfuscated text files
    """

    def __init__(self,
                 file_name: Path | str,
                 method,
                 vault: str,
                 key: str | None = None):
        """
        Constructor

        Args:
            file_name (Path | str): name of the file
            method (_type_): 'rb' or 'wb'
            vault (str): vault name
            key (str | None, optional): obfuscation key. If not set, will use a key from the vault config. Defaults to None.
        """
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
        key = make_key(self.key, salt)
        cipher = ChaCha20.new(key=key, nonce=nonce)
        plaintext = cipher.decrypt(content)
        return plaintext

    def write(self, content: bytes):
        salt = os.urandom(16)
        key = make_key(self.key, salt)
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


def deobfuscate_cmd():
    """
    A cmd command for file de-obfuscation.
    Use it if you want to de-obfuscate file that was obfuscated in OBSIFLASK
    """
    parser = argparse.ArgumentParser(
        prog='OBSIFLASK deobfuscation tool',
        description='deobfuscates files obfuscated with OBSIFLASK')
    parser.add_argument('input_filename')
    parser.add_argument('output_filename')
    parser.add_argument('obfuscation_key')
    parser.add_argument('-b', '--binary', action='store_true')
    args = parser.parse_args()
    in_ = args.input_filename
    out_ = args.output_filename
    key = args.obfuscation_key
    binary = args.binary
    if binary:
        mode_suffix = 'b'
    else:
        mode_suffix = ''
    with obf_open(in_,
                  '',
                  'r' + mode_suffix,
                  obfuscation_mode='obfuscate',
                  key=key) as inp:
        data = inp.read()
    with open(out_, 'w' + mode_suffix) as out:
        out.write(data)


if __name__ == '__main__':
    deobfuscate_cmd()
