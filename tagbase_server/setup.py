# coding: utf-8

import pathlib
import pkg_resources
import sys
from setuptools import setup, find_packages

NAME = "tagbase_server"
VERSION = "v0.12.0"

with open("README.md", "r") as fh:
    long_description = fh.read()

with pathlib.Path("requirements.txt").open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement in pkg_resources.parse_requirements(requirements_txt)
    ]

setup(
    name=NAME,
    version=VERSION,
    description="tagbase-server API",
    author_email="tagtuna@gmail.com",
    url="https://github.com/tagbase/tagbase-server/",
    keywords=["OpenAPI", "tagbase-server API"],
    install_requires=install_requires,
    packages=find_packages(),
    package_data={"": ["openapi/openapi.yaml"]},
    include_package_data=True,
    entry_points={"console_scripts": ["tagbase_server=tagbase_server.__main__:app"]},
    long_description=long_description,
)
