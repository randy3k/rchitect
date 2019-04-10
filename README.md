# Interoperate R with Python

[![Build Status](https://travis-ci.org/randy3k/rchitect.svg?branch=master)](https://travis-ci.org/randy3k/rchitect)
[![CircleCI](https://circleci.com/gh/randy3k/rchitect/tree/master.svg?style=shield)](https://circleci.com/gh/randy3k/rchitect/tree/master)
[![Build status](https://ci.appveyor.com/api/projects/status/4o9m8q61m755xc2a/branch/master?svg=true)](https://ci.appveyor.com/project/randy3k/rchitect/branch/master)
[![pypi](https://img.shields.io/pypi/v/rchitect.svg)](https://pypi.org/project/rchitect/)


**rchitect is under major update at the moment**

## Installation

```sh
# install released version
pip install -U rchitect

# or the development version
pip install -U git+https://github.com/randy3k/rchitect
```


### Conversions between reticulate and rchitect objects are seamless

Python side

```py
import rchitect; rchitect.init()
from rchitect import *
reval("library(reticulate)");

# py to r  (this direction is not usual in Python)
chars = reval("""
    py_eval("reval('LETTERS')")
""")
rcall("py_to_r", chars)

# r to py
class Foo(object):
    pass

foo = Foo()
rcall("r_to_py", robject(foo))
```

R side

```r
library(reticulate)
py_run_string("from rchitect import *")

# py to r
chars = py_eval("reval('LETTERS')")
py_to_r(chars)

# r to py  (this direction is not usual in R)
py_run_string("class Foo(object): pass")
py_run_string("foo = Foo()")
foo = py_to_r(py_eval("robject(foo)"))
r_to_py(foo)
```
