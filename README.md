# rchitect — Interoperate R with Python

[![Main](https://github.com/randy3k/rchitect/actions/workflows/main.yml/badge.svg)](https://github.com/randy3k/rchitect/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/randy3k/rchitect/branch/master/graph/badge.svg)](https://codecov.io/gh/randy3k/rchitect)
[![pypi](https://img.shields.io/pypi/v/rchitect.svg)](https://pypi.org/project/rchitect/)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/rchitect.svg)](https://anaconda.org/conda-forge/rchitect)

`rchitect` is a lightweight, high-performance bridge for embedding R in Python and interoperating between Python and R objects. It is the core engine powering [`radian`](https://github.com/randy3k/radian).

## Features

- **Low-overhead CFFI bridge**: Dynamically links `libR` at runtime and converts between Python objects and R `SEXP`s directly in C.
- **Full R console & event loop callbacks**: Supports `read_console`, `write_console_ex`, `polled_events`, `process_events`, `busy`, `show_message`, `yes_no_cancel`, and interrupt-safe console execution.
- **Bidirectional Python ↔ R calls**: Call R functions directly from Python (`rcall`, `reval`), pass Python callables into R as native R closures, or import and call Python modules from R via `rchitect.py_tools`.
- **Seamless [`reticulate`](https://rstudio.github.io/reticulate/) integration**: Automatically registers S3 methods so `RObject` and `PyObject` convert transparently across `rchitect` and `reticulate`.
- **Cross-platform binary wheels**: Prebuilt wheels for Linux (`x86_64`, `aarch64`), macOS (`x86_64`, `arm64`), and Windows (`AMD64`, `ARM64`) across Python 3.10+, including a native Windows UTF-8 host (`rchitect/host.exe`) for R >= 4.2.

## Requirements

- **Python** >= 3.10
- **R** >= 4.2.0 (built with the R shared library `libR.so` / `libR.dylib` / `R.dll`)

## Installation

```sh
# Install the latest release from PyPI
pip install -U rchitect

# Or via conda-forge
conda install -c conda-forge rchitect

# Or install the development version from GitHub
pip install -U git+https://github.com/randy3k/rchitect
```

## Quick Start

### Evaluating R Expressions and Calling R Functions

```python
from rchitect import rcall, rcopy, reval, rlang, robject, rparse, rprint

# Evaluate an R expression in R_GlobalEnv (returns an RObject)
x = reval("1:5")
rprint(x)

# Convert an RObject to a Python object
py_list = rcopy(x)              # [1, 2, 3, 4, 5]
py_int = rcopy(int, reval("1L")) # 1

# Convert a Python object to an RObject
r_vec = robject([10, 20, 30])

# Call an R function (Python arguments are converted to RObjects automatically)
total = rcall("sum", [1, 2, 3, 4, 5])
print(rcopy(total))  # 15

# Call a namespaced R function using a (pkg, fn) tuple
pkg_path = rcall(("base", "find.package"), "stats", _convert=True)

# Construct and evaluate an R language call
expr = rlang("seq", 1, 10, by=2)
print(rcopy(reval(expr)))  # [1, 3, 5, 7, 9]
```

### Passing Python Functions to R

Python callables can be converted to R functions via `robject`:

```python
from rchitect import rcall, rcopy, robject

r_add = robject(lambda a, b: a + b, convert=True)
res = rcall(r_add, 3, 4)
print(rcopy(res))  # 7
```

### Calling Python from R (`rchitect.py_tools`)

Inside an embedded R session initialized by `rchitect`, Python modules and objects can be accessed directly from R:

```r
getOption("rchitect.py_tools")$attach()

math <- import("math")
math$sqrt(16)        # 4.0

builtins <- import_builtins()
builtins$abs(-42L)   # 42L
```

### Interoperating with `reticulate`

When `reticulate` is loaded in R, `rchitect` automatically registers `py_to_r` and `r_to_py` S3 methods so objects created by `rchitect` and `reticulate` can be mixed freely:

```python
from rchitect import rcall, rcopy, reval

reval("library(reticulate)")
math = reval("import('math', convert = FALSE)")
sqrt = rcall("$", math, "sqrt")
res = rcall(sqrt, 16)
print(rcopy(res))  # 4.0
```

### Customizing Console Callbacks & Hosting an R REPL

Applications that embed an interactive R REPL (such as `radian`) can customize R's console callbacks with `@def_callback()` and run the R event loop with `rchitect.loop()`:

```python
import sys
import rchitect
from rchitect import def_callback


@def_callback(name="read_console")
def read_console(prompt, add_history):
    sys.stdout.flush()
    sys.stderr.flush()
    return input(prompt)


@def_callback(name="write_console_ex")
def write_console_ex(buf, otype):
    stream = sys.stdout if otype == 0 else sys.stderr
    stream.write(buf)
    stream.flush()


rchitect.init(args=["rchitect", "--quiet", "--no-save"])
rchitect.loop()
```

## Selecting an R Installation

`rchitect` locates R in the following order:

1. **`R_HOME`**: Path to the R home directory (i.e., the output of `R RHOME` or `R.home()`, not the `bin/` directory):
   ```sh
   R_HOME=/usr/local/lib/R radian
   ```
2. **`R_BINARY`**: Path to a specific `R` executable:
   ```sh
   R_BINARY=/opt/R/4.5.0/bin/R radian
   ```
3. **`PATH`**: The `R` executable on your system `PATH` (or the Windows Registry if `R` is not on `PATH`).

> **Note for Linux users building R from source**: Make sure R is configured and compiled with `--enable-R-shlib` so that `libR.so` is available.
