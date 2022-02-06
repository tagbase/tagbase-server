# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "tagbase_server"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion>=2.0.2",
    "swagger-ui-bundle>=0.0.2",
    "python_dateutil>=2.6.0"
]

setup(
    name=NAME,
    version=VERSION,
    description="tagbase-server API",
    author_email="tagtuna@gmail.com",
    url="",
    keywords=["OpenAPI", "tagbase-server API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['openapi/openapi.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['tagbase_server=tagbase_server.__main__:main']},
    long_description="""\
    tagbse-server provides HTTP endpoints for ingestion of various files into the Tagbase SQL database. Input file support includes eTUFF (see [here](https://doi.org/10.6084/m9.figshare.10032848.v4) and [here](https://doi.org/10.6084/m9.figshare.10159820.v1)) and [nc-eTAG](https://github.com/oceandatainterop/nc-eTAG/) files; a metadata and data interoperability standard for (non-acoustic) electronic tagging datasets. The REST API complies with [OpenAPI v3.0.3](https://spec.openapis.org/oas/v3.0.3.html) until the tooling for OpenAPI v3.1.0 improves.
    """
)
