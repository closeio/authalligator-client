# workaround for open() with encoding='' python2/3 compability
import sys
from io import open

from setuptools import setup

with open("README.md", encoding="utf-8") as file:
    long_description = file.read()

install_requires = [
    "attrs",
    "requests",
    "structlog",
    'typing;python_version<"3.5"',
    "ciso8601",
]

if sys.version_info < (3, 3):
    install_requires += ["enum34"]

tests_require = install_requires + ["pytest", "flake8", "mock<4"]

setup(
    name="authalligator_client",
    version="0.1",
    url="http://github.com/closeio/authalligator-client",
    license="MIT",
    description="Python AuthAlligator client",
    long_description=long_description,
    test_suite="tests",
    tests_require=tests_require,
    install_requires=install_requires,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["authalligator_client"],
    extras_require={"tests": tests_require},
)
