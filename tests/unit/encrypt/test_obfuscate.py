from obsiflask.encrypt.obfuscate import obf_open


def test_obf_open_no_obfuscate(tmp_path):
    with obf_open(tmp_path / "out.txt", '', 'w', 'raw') as out:
        out.write('test')
    with obf_open(tmp_path / "out.txt", '', 'r', 'raw') as inp:
        assert inp.read() == 'test'

    with obf_open(tmp_path / "out.txt", '', 'wb', 'raw') as out:
        out.write(b'test\x01')
    with obf_open(tmp_path / "out.txt", '', 'rb', 'raw') as inp:
        assert inp.read() == b'test\x01'


def test_obf_open_text(tmp_path):
    with obf_open(tmp_path / "out.md", '', 'w', 'obfuscate', key='key') as out:
        out.write('test')
    with obf_open(tmp_path / "out.md", '', 'rb', 'raw') as inp:
        assert inp.read() != b'test'
    with obf_open(tmp_path / "out.md", '', 'r', 'obfuscate', key='key') as inp:
        assert inp.read() == 'test'


def test_obf_open_bin(tmp_path):
    with obf_open(tmp_path / "out.bin", '', 'wb', 'obfuscate',
                  key='key') as out:
        out.write(b'test\x01')
    with obf_open(tmp_path / "out.bin", '', 'rb', 'raw') as inp:
        assert inp.read() != b'test\x01'
    with obf_open(tmp_path / "out.bin", '', 'rb', 'obfuscate',
                  key='key') as inp:
        assert inp.read() == b'test\x01'


def test_hardcoded_bin(tmp_path):
    with open(tmp_path / 'out.bin', 'wb') as out:
        out.write(
            b'{"content": "UF2DPEU=", "nonce": "s2czyEk2VgU=", "salt": "VvyDVBHadlDJDf9RW2yaVQ==", "version": 0}'
        )
    with obf_open(tmp_path / "out.bin", '', 'rb', 'obfuscate',
                  key='key') as inp:
        assert inp.read() == b'test\x01'


def test_hardcoded_text(tmp_path):
    with open(tmp_path / 'out.md', 'wb') as out:
        out.write(
            b'OBF\x00\xc2\x02cOq\xe7`\x13_\x98\xc2\xd2\xa1\xe1\xf68\xe6\x9fj\x9e'
        )
    with obf_open(tmp_path / "out.md", '', 'r', 'obfuscate', key='key') as inp:
        assert inp.read() == 'test'
