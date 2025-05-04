# Changelog

## v0.4.8

- switch to pyproject.toml (#38)
- support arm64 windows machine (#39)

## v0.4.7

- allow interruption in write_console
- some symbols are removed

## v0.4.6

- require packaging and python 3.7+

## v0.4.5

- require setuptools for python 3.12

## v0.4.4

- fix incompatible point type error in clang 16

## v0.4.3

- remove Rf_applyClosure to support R devel
- deprecate the use of distutils

## v0.4.2

- try again with WOW6432Node entry
- compare to sys.version_info

## v0.4.1

- require python 3.6+

## v0.3.40

- bump to v0.3.40 for release

## v0.3.39

- bump to v0.3.39 for release

## v0.3.38

- return unmodified python objects in py_set_attr/py_set_item

## v0.3.37

- sys.path insertion no longer needed for reticulate >= 1.19
- allow setting callbacks after R initialization
- disable reticulate in py2
- install also askpass
- fix a bug of reading > 4096 bytes in cb_read_console

## v0.3.36

- improve flush system
- bug fixes for pytools

## v0.3.35

- fix serveral memory related issues

## v0.3.34

- bump version for python 3.10 wheels

## v0.3.32

- fix wheel build

## v0.3.29 - v0.3.31

- Avoid partial argument match
- better reticulate support

## v0.3.28

- a new environemnt variable to stop reticulate code injection

## v0.3.27

- support conda's R

## v0.3.26

  fix a bug in detecting unicode escape sequence in Windows

## v0.3.25

- support R_SignalHandlers
- improve dll loading in windows (microsoft store python should work now)

## v0.3.24

- fix a bug in loading GA_peekevent on windows

## v0.3.23

- fix event processing related functions in windows

## v0.3.22

- better support of event processing

## v0.3.21

- check R_BINARY environmental variable

## v0.3.20

- fix a bug in detecting R_HOME
- support specifying path to R binary via environment variable "R"

## v0.3.19

- support EmitEmbeddedUTF8

## v0.3.18

- use tryCatch in completion

## v0.3.17

- minor fix in console writter

## v0.3.16

- revert the "fix" in v0.3.15

## v0.3.15

- fix some unicode issues in Windows

## v0.3.14

- Support R-devel by removing CON_NR

## v0.3.13

- flush stdout and stderr before each prompt

## v0.3.11 and v0.3.12

- show the last loaded symbol
- catch OSError in py_config

## v0.3.10

- handle fork processes

## v0.3.9

- fix a reticulate bug

## v0.3.8

- improve error message handling
- add completion utils
- tests update

## v0.3.7

- fix a path related bug in Windows

## v0.3.6

- use system2utf8 for decoding
- set ptr_R_WriteConsole to NULL
- set R_Outputfile and R_Consolefile to NULL

## v0.3.5

- use system2utf8 to decode dlerror message
- fix python 3 error
- install python 3.4 from conda-forge

## v0.3.4

- init with no-save

## v0.3.3

- fix reticulate issue in Windows

## v0.3.2

- fix a tarball issue

## v0.3.1

- python 3.8 fix
- rename to rchitect.py_tools
- support &, |, ! in py_tools
- windows fix for 3.6

## v0.3.0

- completely rewritten using cffi

## v0.2.4

- some ipython hook fixes

## v0.2.2

## v0.2.3

- do not depend on multipledispatch
- refactor bootstrap code

## v0.2.2

- start machine with default settings automatically
- set reticulate env variables automatically
- register hook automatically for ipython repl

## v0.2.1

- exclude tests module

## v0.2.0

- rebranded as `rchitect`

## v0.1 - v0.1.4

- do not register py namespace automatically
- support reticulate
- GA_initapp via graphapp

## v0.0.16

  use RTLD_GLOBAL to open libR

## v0.0.15

- bug fix for r_to_py

## v0.0.14

- rename rversion2 to rversion
- support r-devel

  Contributors:

- Randy Lai

## v0.0.13

  A lot of refactoring

  Other:

- py_get_item, py_get_attr, py_set_attr and py_set_item
- added PyClass
- add missing list to INTSXP

  Contributors:

- Randy Lai

## v0.0.12

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

## v0.0.11

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

## v0.0.7

  Other:

- simplify R_ReadConsole
- more conversion methods

  Contributors:

- Randy Lai

## v0.0.6

- switch to circleci
- python 2 fixes
- add unicode test

  Contributors:

- Randy Lai

## v0.0.5

The first public release.
