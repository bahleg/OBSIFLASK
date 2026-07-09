"""
Version handling module
"""


version_str = '0.20.1'



def get_version() -> str:
    return version_str


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
