import hashlib

from Crypto.Cipher import ChaCha20

from obsiflask.app_state import AppState

SALT = b'obsiflask-salt'
NONCE_LEN = 8


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
        AppState.obfuscate_keys[vault] = make_key(
            AppState.config.vaults[vault].obfuscation_key)


def obfuscate_read(stream, vault: str, obfuscate: bool = False, binary: bool = False) -> str | bytes:
    if not obfuscate:
        bts = stream.read()
        if not binary:
            return bts.decode('utf-8')
        return bts
    else:
        result = stream.read()
        nonce = result[:NONCE_LEN]
        text = result[NONCE_LEN:]
        cipher = ChaCha20.new(key=AppState.obfuscate_keys[vault], nonce=nonce)
        plaintext = cipher.decrypt(text)
        if binary:
            return plaintext
        return plaintext.decode('utf-8')


def obfuscate_write(stream, text: str, vault: str, obfuscate: bool = False):
    if not obfuscate:
        return stream.write(text.encode('utf-8'))
    else:
        cipher = ChaCha20.new(key=AppState.obfuscate_keys[vault])

        ciphertext = cipher.encrypt(text.encode('utf-8'))
        assert len(
            cipher.nonce) == NONCE_LEN, f'nonce length is {len(cipher.nonce)}'
        stream.write(cipher.nonce + ciphertext)
