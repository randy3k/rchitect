# v0.2.4

   - some ipython hook fixes

# v0.2.2

# v0.2.3

   - do not depend on multipledispatch
   - refactor bootstrap code

# v0.2.2

   - start machine with default settings automatically
   - set reticulate env variables automatically
   - register hook automatically for ipython repl


# v0.2.1

  - exclude tests module

# v0.2.0

  - rebranded as `rchitect`

# v0.1 - v0.1.4

   - do not register py namespace automatically
   - support reticulate
   - GA_initapp via graphapp

# v0.0.16

  use RTLD_GLOBAL to open libR

# v0.0.15

  - bug fix for r_to_py

# v0.0.14

   - rename rversion2 to rversion
   - support r-devel

  Contributors:
   - Randy Lai


# v0.0.13

  A lot of refactoring

  Other:
   - py_get_item, py_get_attr, py_set_attr and py_set_item
   - added PyClass
   - add missing list to INTSXP

  Contributors:
   - Randy Lai


# v0.0.12


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


  Other:
   - simplify R_ReadConsole
   - more conversion methods

  Contributors:
   - Randy Lai


# v0.0.6

   - switch to circleci
   - python 2 fixes
   - add unicode test

  Contributors:
   - Randy Lai


# v0.0.5

The first public release.