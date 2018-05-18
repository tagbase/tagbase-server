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

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="Tagbase API",
    author_email="oiip@jpl.nasa.gov",
    url="https://oiip.jpl.nasa.gov",
    keywords=["Swagger", "Tagbase API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['swagger/swagger.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['swagger_server=swagger_server.__main__:main']},
    long_description="""\
    Tagbase is a [Flask](http://flask.pocoo.org/) application which provides HTTP endpoints for ingestion of various files into the tagbase SQL database.
    """
)

