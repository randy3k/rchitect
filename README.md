# Interoperate R with Python

[![Main](https://github.com/randy3k/rchitect/actions/workflows/main.yml/badge.svg)](https://github.com/randy3k/rchitect/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/randy3k/rchitect/branch/master/graph/badge.svg)](https://codecov.io/gh/randy3k/rchitect)
[![pypi](https://img.shields.io/pypi/v/rchitect.svg)](https://pypi.org/project/rchitect/)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/rchitect.svg)](https://anaconda.org/conda-forge/rchitect)

## Installation

```sh
# install released version
pip install -U rchitect

# or the development version
pip install -U git+https://github.com/randy3k/rchitect
```

## Why reinvent the wheel?

You may be curious why I reinvented the wheel when there is [`rpy2`](https://github.com/rpy2/rpy2)?

The main reason is to drive [`radian`](https://github.com/randy3k/radian).
`rpy2` was not suitable because it is missing some key features for running
the R REPL. Speaking of compatibility, `rchitect` has been thoroughly tested on
multiple platforms such as Windows, macOS and Linux and we also provide binary
wheels for python 3.6+.

## Getting started

```py
from rchitect import *
a = reval("1:5")     # evaluate an R expression in the global environment
b = rcopy(a)         # convert any RObject returned by `reval` to its python type
c = robject(b)       # convert any python object to its R type
d = rcall("sum", c)  # call an R function. Python objects are converted to RObjects implicitly.
```

## FAQ

#### How to switch to a different R or specify the version of R

There are a few options.

- One could expose the path to the R binary in the `PATH` variable
- The environment variable `R_BINARY` could also be used to specify the path to R.
- The environment variable `R_HOME` could also be used to specify R home directory. Note that it is should be set as the result of `R.home()`, not the directory where `R` is located. For example, in Unix

```sh
env R_HOME=/usr/local/lib/R radian
```

#### Cannot find shared library

Please also make sure that R was installed with the R shared library `libR.so` or `libR.dylib` or `libR.dll`. On Linux, the flag `--enable-R-shlib` may be needed to install R from the source.

## Wiki

[reticulate](https://github.com/randy3k/rchitect/wiki/Conversions-between-reticulate-and-rchitect-objects-are-seamless) conversions
