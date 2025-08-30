import re
from setuptools import setup, find_packages
from flobsidian.version import get_version

with open('requirements.txt') as inp:
    requirements = '\n'.join(
        re.findall(r'^([^\s^+]+).*$', inp.read(), flags=re.MULTILINE))

setup(
    name="FLOBSIDIAN",
    version=get_version(),
    author="bahleg",
    author_email="bakhteev.o at gmail.com",
    description=
    "a DIY-service for simple multi-vault multi-user obisidian web view",
    url="https://github.com/bahleg/flobsidian",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={"console_scripts": ["flobsidian=flobsidian.main:run"]},
    include_package_data=True,  # важно!
    package_data={
        "flobsidian": [
            "templates/*.html",
            "static/*.*",
        ],
    },
)
