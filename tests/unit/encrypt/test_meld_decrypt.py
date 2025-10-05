from base64 import b64encode, b64decode
import pytest
import json

from obsiflask.encrypt.meld_decrypt import read_encoded_data, decrypt_from_bytes


def test_read_decoded_data(tmp_path):
    with open(tmp_path / "data.json", 'w') as out:
        out.write(
            json.dumps({
                'version': '2.0',
                'encodedData': b64encode(b'abc').decode('utf-8')
            }))
    assert read_encoded_data(tmp_path / 'data.json') == b'abc'

    with open(tmp_path / "data.json", 'w') as out:
        out.write(json.dumps({
            'version': '2.0',
            'encodedData': 'abc'
        }))  # bad b64
    with pytest.raises(Exception):
        read_encoded_data(tmp_path / 'data.json', False)

    with open(tmp_path / "data.json", 'w') as out:
        # bad version
        out.write(
            json.dumps({
                'version': '1.0',
                'encodedData': b64encode(b'abc').decode('utf-8')
            }))
    with pytest.raises(Exception):
        read_encoded_data(tmp_path / 'data.json', False)

    with open(tmp_path / "data.json", 'w') as out:
        # no data
        out.write(json.dumps({
            'version': '2.0',
        }))
    with pytest.raises(Exception):
        read_encoded_data(tmp_path / 'data.json', False)


def test_hardcoded_encyption():

    assert decrypt_from_bytes(
        b64decode(
            'mSUn6ptzznp58IlHK+7qXJjQ96mkEOkX2HhafpaV+wiwVAX9nCtfWtnpUXurpsxp6JosZUUNY74KLAmX'
        ), 'abc', False) == 'Hello world!'
