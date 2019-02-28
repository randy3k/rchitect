from setuptools import setup, find_packages

setup(
    name = 'rapi',
    version = '0.5',
    packages=find_packages('.', exclude=["tests"]),
    cffi_modules=["src/build.py:ffibuilder"]
)
