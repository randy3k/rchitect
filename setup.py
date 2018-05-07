import os
import re
from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except Exception:
    long_description = ''


def get_version(package):
    """
    Return package version as listed in `__version__` in `__init__.py`.
    """
    path = os.path.join(os.path.dirname(__file__), package, '__init__.py')
    with open(path, 'rb') as f:
        init_py = f.read().decode('utf-8')
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


setup(
    name='rapi',
    author='Randy Lai',
    author_email="randy.cs.lai@gmail.com",
    version=get_version("rapi"),
    url='https://github.com/randy3k/rapi',
    description='A minial R API for Python',
    long_description=long_description,
    packages=find_packages('.'),
    install_requires=[
        "multipledispatch",
        'enum34;python_version<"3.4"',
    ]
)
