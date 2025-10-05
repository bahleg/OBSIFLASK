"""
Setup script for OBSIFLASK
"""
import re
from setuptools import setup, find_packages

from obsiflask.version import get_version

with open('requirements.txt') as inp:
    requirements = '\n'.join(
        re.findall(r'^([^\s^+]+).*$', inp.read(), flags=re.MULTILINE))

setup(
    name="OBSIFLASK",
    version=get_version(),
    author="bahleg",
    author_email="bakhteev.o at gmail.com",
    description=
    "a DIY-service for simple multi-vault multi-user obisidian web view",
    url="https://github.com/bahleg/OBSIFLASK",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "obsiflask=obsiflask.main:run",
            "obsiflask-deobfuscate=obsiflask.encrypt.obfuscate:deobfuscate_cmd",
            "obsiflask-decrypt=obsiflask.encrypt.meld_decrypt:main"
        ]
    },
    include_package_data=True,
    package_data={
        "obsiflask": [
            "templates/*.html",
            "templates/*/*.html",
            "static/*.*",
            "static/*/*.*",
        ],
    },
)
