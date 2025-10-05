"""
Decoder for Meld-cp encryption file.
Originally from https://gist.github.com/mclang/4c3347d217ae6f542e309eb2a0184025
"""
import base64
import getpass
import json
import sys
import traceback
import argparse

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Constants and AES-256-GCM decryption logic taken from:
# - https://github.com/meld-cp/obsidian-encrypt/blob/main/src/services/CryptoHelperFactory.ts
# - https://github.com/meld-cp/obsidian-encrypt/blob/main/src/services/CryptoHelper2304.ts
ITERATIONS = 210000
VECTOR_SIZE = 16
SALT_SIZE = 16
TAG_SIZE = 16


def derive_key(password: str, salt: bytes) -> bytes:
    return PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,  # AES-256 key size
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()).derive(password.encode())


def decrypt_from_bytes(encrypted_bytes: bytes, password: str, exit: bool = True) -> str:
    if len(encrypted_bytes) < (VECTOR_SIZE + SALT_SIZE + TAG_SIZE):
        print("ERROR: Encrypted data is too short to be valid!")
        sys.exit(1)

    vector = encrypted_bytes[:VECTOR_SIZE]
    salt = encrypted_bytes[VECTOR_SIZE:VECTOR_SIZE + SALT_SIZE]
    tag = encrypted_bytes[-TAG_SIZE:]
    encrypted_text_bytes = encrypted_bytes[VECTOR_SIZE + SALT_SIZE:-TAG_SIZE]
    key = derive_key(password, salt)

    try:
        cipher = Cipher(algorithms.AES(key),
                        modes.GCM(vector, tag),
                        backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_bytes = decryptor.update(
            encrypted_text_bytes) + decryptor.finalize()
        return decrypted_bytes.decode()

    except Exception as e:
        if not exit:
            raise e
        print("ERROR: Decrypting data failed!")
        print(f"- Vector (IV): {vector.hex()}")
        print(f"- Salt:        {salt.hex()}")
        print(f"- Tag:         {tag.hex()}")
        print(f"- Derived Key: {key.hex()}")
        print(f"- Encrypted text length: {len(encrypted_text_bytes)}\n")
        traceback.print_exc()
        sys.exit(1)


def read_encoded_data(file_path: str, exit: bool = True) -> bytes:
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            if data["version"] != "2.0":
                raise ValueError("Only v2.0 supported!")
            if "encodedData" not in data:
                raise ValueError("Missing 'encodedData' key in JSON file")
            return base64.b64decode(data.get("encodedData").strip())

    except base64.binascii.Error as e:
        if not exit:
            raise e
        print(f"ERROR: Decoding Base64 failed: {e}")
    except json.JSONDecodeError as e:
        if not exit:
            raise e
        print(
            f"ERROR: Parsing JSON from '{file_path}' (line {e.lineno}, column {e.colno}) failed: {e.msg} "
        )
    except Exception as e:
        if not exit:
            raise e
        print(
            f"ERROR: Parsing 'encodedData' field from '{file_path}' failed: {e}"
        )
    if exit:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog='meld decryptor',
        description=
        "Originally from https://gist.github.com/mclang/4c3347d217ae6f542e309eb2a0184025"
    )
    parser.add_argument('input', help='path to file or line, if "-e" is set')
    parser.add_argument('-e',
                        '--encoded_line',
                        action='store_true',
                        help='if set, will read encoded line')
    parser.add_argument('output')
    args = parser.parse_args()
    if args.encoded_line:
        encrypted_bytes = base64.b64decode(args.input.strip())
    else:
        encrypted_bytes = read_encoded_data(sys.argv[1])
    password = getpass.getpass("Enter decryption password: ")
    plaintext = decrypt_from_bytes(encrypted_bytes, password)
    with open(args.output, 'w') as out:
        out.write(plaintext)


if __name__ == "__main__":
    main()
