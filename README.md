# Minimal R API for Python

[![CircleCI](https://circleci.com/gh/randy3k/rapi/tree/master.svg?style=shield)](https://circleci.com/gh/randy3k/rapi/tree/master)
[![Build status](https://ci.appveyor.com/api/projects/status/4o9m8q61m755xc2a/branch/master?svg=true)](https://ci.appveyor.com/project/randy3k/rapi/branch/master)
[![pypi](https://img.shields.io/pypi/v/rapi.svg)](https://pypi.org/project/rapi/)

```py
import rapi
from rapi import rcopy, reval
rapi.start()
rcopy(reval("R.version"))
```

## Installation

```sh
# install released version
pip install -U rapi

# or the development version
pip install -U git+https://github.com/randy3k/rapi
```

## Why?

Why another R interface when there is [`rpy2`](https://rpy2.readthedocs.io/)?

1. `rapi` is 100% python

`rapi` is primarily used by [`rtichoke`](https://github.com/randy3k/rtichoke) which is an alternate R console. `rpy2` was not an option because it requires compilations and who wants to compile!?

2. `rapi` is portable

At stated above, `rpy2` requires tool chains to install which makes it not portable. `rapi` on the other hand is lightweight and portable.

3. `rapi` is lightweight

`rpy2` supports a large number of python and R packages, such as numpy, scipy, ggplot2 etc. But there are situations a user may just want to compute a simple thing from R. Additionally, I found that the interface of `rpy2` is not very discoverable.

4. `rapi` is a brother of `RCall.jl`

I am the same developer behind the Julia package [`RCall.jl`](https://github.com/JuliaInterop/RCall.jl) which allows Julia to communicate with R. `rapi` and `RCall.jl` share a very similar design. For example, `rcopy(reval("1"))` works for both `rapi` and `RCall.jl`.
 

5. `rapi` is compatible with [`reticulate`](https://github.com/rstudio/reticulate). Objects can be converted seamlessly between `rapi` and `reticulate`. Check the section for `reticuate` below.

## FAQ

Sometimes, `rapi` may fail to open the shared library.

- On Linux

First, try to expose R to PATH.
```sh
export R_HOME=/usr/local/lib/R
```
Note that it should be the path to `R_HOME`, not the path to the R binary. The
folder should contain a file called `COPYING`. In some cases, you may need to
futher specify `LD_LIBRARY_PATH`,

```sh
$ export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:`R RHOME`/lib"
```

- On Windows

Make sure that the path(s) to `R.exe` and `R.dll` is in the `PATH` variable.

## Very minimal API

```py
import rapi
rapi.start()
from rapi import rcopy, robject, reval, rcall
```

- `reval` - evaluate an R expression in the global environment

```py
a = reval("1:5")
```

- `rcopy` - convert any RObject returned by `reval` to its python type

```py
b = rcopy(a)
```

- `robject` - convert any python object to its R type

```py
c = robject(b)
```

- `rcall` - call an R function. Python objects are converted to RObjects implicitly.

```py
d = rcall("sum", c)
```

## R Eventloop in IPython

When running interactively in IPython, R events such as showing graphical 
devices could be handled by the `r` eventloop. Simply enter in IPython
```
%gui r
```

## reticulate

Python Side
```py
# some preparation work
# Unix users may need this PR: https://github.com/rstudio/reticulate/pull/279
# Windows + Python 2.7 users may need this PR: https://github.com/rstudio/reticulate/pull/335
# See also https://github.com/randy3k/rtichoke#how-to-specify-r_home-location

import os
import sys
os.environ["RETICULATE_PYTHON"] = sys.executable
os.environ["RETICULATE_REMAP_OUTPUT_STREAMS"] = "0"

import rapi
rapi.start()
from rapi import *

reval("library(reticulate)");
py_object = reval("r_to_py(LETTERS)")
rcopy(py_object)

class Foo(object):
    pass

foo = Foo()
rcall("r_to_py", robject(foo))

```

R side
```r
library(reticulate)
py_run_string("import rapi")
py_run_string("rapi.start()")
py_run_string("from rapi import *")
r_object = py_eval("reval('LETTERS')")
py_to_r(r_object)

py_run_string("class Foo(object): pass")
py_run_string("foo = Foo()")
py_object = py_eval("robject(foo)")
r_to_py(py_to_r(py_object))
```
