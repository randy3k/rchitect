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


## Examples to work with `reticulate`

Python side

```py
import rchitect; rchitect.init()
from rchitect import *

reval("library(reticulate)");
py_object = reval("r_to_py(LETTERS)")
rcopy(py_object)

class Foo(object):
    pass

foo = Foo()
rcall("r_to_py", robject(foo), _convert=True)
```

R side

```r
library(reticulate)
py_run_string("import rchitect; rchitect.init()")
py_run_string("from rchitect import *")
r_object = py_eval("reval('LETTERS')")
py_to_r(r_object)

py_run_string("class Foo(object): pass")
py_run_string("foo = Foo()")
py_object = py_eval("robject(foo)")
r_to_py(py_to_r(py_object))
```
