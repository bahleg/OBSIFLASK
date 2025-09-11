version_str = '0.6.0'


def get_version(pep_version=True):
    if pep_version:
        delim_char = '+'
    else:
        delim_char = '-'
    import os
    branch = os.environ.get('GIT_BRANCH', 'local')
    commit = os.environ.get('GIT_COMMIT', '')
    if branch == 'main':
        ver = f'{version_str}{delim_char}{commit}'
    elif branch == 'local':
        ver = f'{version_str}{delim_char}local'
    else:
        ver = f'{version_str}{delim_char}{branch}.{commit}'
    return ver


def bump_version():
    with open(__file__) as inp:
        lines = inp.readlines()
        assert lines[0].startswith('version_str')
        tokens = version_str.split('.')
        new_ver = f'{tokens[0]}.{tokens[1]}.{int(tokens[2])+1}'
        lines[0] = f"version_str = '{new_ver}'\n"
    with open(__file__, 'w') as out:
        out.write(''.join(lines))


if __name__ == '__main__':
    bump_version()
