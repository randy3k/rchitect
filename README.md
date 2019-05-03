# Interoperate R with Python

[![CircleCI](https://circleci.com/gh/randy3k/rchitect/tree/master.svg?style=shield)](https://circleci.com/gh/randy3k/rchitect/tree/master)
[![Build status](https://ci.appveyor.com/api/projects/status/4o9m8q61m755xc2a/branch/master?svg=true)](https://ci.appveyor.com/project/randy3k/rchitect/branch/master)
[![codecov](https://codecov.io/gh/randy3k/rchitect/branch/master/graph/badge.svg)](https://codecov.io/gh/randy3k/rchitect)
[![pypi](https://img.shields.io/pypi/v/rchitect.svg)](https://pypi.org/project/rchitect/)


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
wheels for user convenience.

## Getting started

```py
from rchitect import *
a = reval("1:5")     # evaluate an R expression in the global environment
b = rcopy(a)         # convert any RObject returned by `reval` to its python type
c = robject(b)       # convert any python object to its R type
d = rcall("sum", c)  # call an R function. Python objects are converted to RObjects implicitly.
```

## FAQ

If `rchitect` fails to open the R shared library, user should first
try to expose the path to R to the `PATH` vaiable.

In Linux/macOS, you could also export the environment variable `R_HOME`. For example,
```sh
$ export R_HOME=/usr/local/lib/R
$ radian
```
Sometimes, you may also need to futher specify `LD_LIBRARY_PATH` if R fails to find some shared libraries,
```sh
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:`R RHOME`/lib"
```

Please also make sure that R was installed with the R shared library `libR.so` or `libR.dylib` or `libR.dll`. On Linux, the flag `--enable-R-shlib` may be needed to install R from the source.

## Wiki

[reticulate](https://github.com/randy3k/rchitect/wiki/Conversions-between-reticulate-and-rchitect-objects-are-seamless) conversions
