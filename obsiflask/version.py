"""
Version handling module
"""
import subprocess

version_str = '0.7.2'


def get_version(pep_version=True, short: bool = False) -> str:
    """
    Returns version in two options: version as version_str and with additional suffix, if
    we see that git repo is dirty (doesn't contain unchanged git version)

    Args:
        pep_version (bool, optional): if set, will use "+" as delimiter. Defaults to True.
        short (bool, optional): if set, will use a semver-like version without git suffix. Defaults to False.

    Returns:
        str: formatted version
    """
    delim_char = '+' if pep_version else '-'

    # checking git commit
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True).strip()
        # checking if our commit is dirty
        dirty = subprocess.check_output(["git", "status", "--porcelain"],
                                        text=True).strip()
        if dirty:
            commit += ".local"
    except Exception as e:
        commit = None

    if short:
        return version_str

    if not dirty:
        ver = version_str
    else:
        ver = f"{version_str}{delim_char}{commit}"

    return ver


def bump_version(path_to_save: str | None = None) -> str:
    """
    Updates version
    

    Args:
        rewrite_file (str, optional): if set, will rewrite this file to the new location. 
        Otherwise will rewrite file

    """
    with open(__file__) as inp:
        lines = inp.readlines()
        found = False
        for v_id, version_line in enumerate(lines):
            if version_line.startswith('version_str'):
                found = True
                break
        if not found:
            raise ValueError('Could not find version line')
        tokens = version_str.split('.')
        new_ver = f'{tokens[0]}.{tokens[1]}.{int(tokens[2])+1}'
        lines[v_id] = f"version_str = '{new_ver}'\n"
    result = ''.join(lines)
    path_to_save = path_to_save or __file__
    with open(path_to_save, 'w') as out:
        out.write(result)


if __name__ == '__main__':
    bump_version()
