import os
import re
import sys
from setuptools import setup, find_packages


def get_long_description():
    with open('README.md', 'rb') as f:
        desc = f.read().decode('utf-8')

    return desc


def get_version(package):
    """
    Return package version as listed in `__version__` in `__init__.py`.
    """
    path = os.path.join(os.path.dirname(__file__), package, '__init__.py')
    with open(path, 'rb') as f:
        init_py = f.read().decode('utf-8')
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


install_requires = [
    'cffi>=1.10.0',
    'six>=1.9.0'
]

if sys.version_info[0] == 2:
    install_requires.append("backports.shutil_which>=3")

setup(
    name='rchitect',
    author='Randy Lai',
    author_email="randy.cs.lai@gmail.com",
    version=get_version("rchitect"),
    url='https://github.com/randy3k/rchitect',
    description='Mapping R API to Python',
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages('.', exclude=["tests"]),
    package_data={'rchitect': ['reticulate/*.R', 'src/*']},
    cffi_modules=["rchitect/src/build.py:ffibuilder"],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    install_requires=install_requires,
    setup_requires=[
        'cffi>=1.10.0',
        "pytest-runner"
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-mock",
            "pytest-cov"
        ]
    }
)
