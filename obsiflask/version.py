"""
Version handling module
"""
import subprocess
import os 
version_str = '0.6.0'


def get_version(pep_version=True) -> str:
    delim_char = '+' if pep_version else '-'

    # пытаемся получить git commit
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        # проверяем, есть ли несохранённые изменения
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True
        ).strip()
        if dirty:
            commit += ".dirty"
    except Exception:
        commit = None

    if commit:
        ver = f"{version_str}{delim_char}{commit}"
    else:
        ver = f"{version_str}{delim_char}local"

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
