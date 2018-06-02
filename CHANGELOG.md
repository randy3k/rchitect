# v0.0.12

Changes since v0.0.11:

  Other:
   - use pythonapi to protect pyobject vis Py_IncRef/Py_DecRef
   - add _convert arguemnt in rcall
   - register py namespace
   - py_eval, py_call, py_import etc via namespace py
   - allow copy as PyCallable and PyObject objects
   - allow to make invisible R function
   - various improvements in object conversion

  Contributors:
   - Randy Lai


# v0.0.11

Changes since v0.0.7:

  Other:
   - use Rf_translateCharUTF8
   - refactor registry
   - rename get_rhome and get_libR
   - add ipython eventloop
   - check if R has been initialized
   - create namespace
   - add get_attrib and set_attrib
   - repl

  Contributors:
   - Randy Lai


# v0.0.7

Changes since v0.0.6:

  Other:
   - simplify R_ReadConsole
   - more conversion methods

  Contributors:
   - Randy Lai


# v0.0.6

Changes since v0.0.5:
   - switch to circleci
   - python 2 fixes
   - add unicode test

  Contributors:
   - Randy Lai


# v0.0.5

The first public release.