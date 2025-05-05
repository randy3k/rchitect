# Changelog

## 0.4.8 - 2025-05-04

### Other

* Cast function to expected type ([#37](https://github.com/randy3k/rchitect/issues/37))
* switch to pyproject.toml ([#38](https://github.com/randy3k/rchitect/issues/38))
* update radian config name
* support arm64 windows machine ([#39](https://github.com/randy3k/rchitect/issues/39))
* remove .vscode/
* also build linux arm wheels
* also build for windows arm

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.4.7...v0.4.8

## 0.4.7 - 2024-08-15

### Other

* on main and master branch only
* use concurrency
* push on tags
* allow interruption in write_console
* use concurrency
* symbols are removed from r-devel
* update CHANGELOG
* push on tags

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.4.6...v0.4.7

## 0.4.6 - 2024-01-17

### Bug Fixes

* fix install_requires
* fix rversion

### Other

* require packaging
* fix python 3.12 build ([#33](https://github.com/randy3k/rchitect/issues/33))
* Update changelog
* update github actions

### Testing

* test python 3.12

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.4.5...v0.4.6

## 0.4.5 - 2024-01-12

### Bug Fixes

* fix bracket

### Other

* unify load_symbol and load_constant
* require setuptools for python 3.12
* update changelog

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.4.4...v0.4.5

## 0.4.4 - 2023-10-18

### Bug Fixes

* fix incompatible pointer types

### Other

* cast function pointer explicitly
* add comment for _libR_load_constants

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.4.3...v0.4.4

## 0.4.3 - 2023-10-18

### Other

* bump to v0.4.2 ([#28](https://github.com/randy3k/rchitect/issues/28))
* remove Rf_applyClosure
* use parse_version ([#29](https://github.com/randy3k/rchitect/issues/29))
* remove Rf_applyClosure and use parse_version ([#30](https://github.com/randy3k/rchitect/issues/30))

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.4.2...v0.4.3

## 0.4.2 - 2023-08-30

### Other

* try again with WOW6432Node entry
* compare to sys.version_info ([#27](https://github.com/randy3k/rchitect/issues/27))

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.4.1...v0.4.2

## 0.4.1 - 2023-07-25

### Other

* update to cibuildwheel 2.14.0
* remove python 2.7 container
* R 3.6 is too old
* Check agsinst R 4.1
* update to cibuildwheel 2.14.0 ([#25](https://github.com/randy3k/rchitect/issues/25))
* use macos-13
* more macos-13
* use startsWith
* Update main.yml
* require python 3.6+
* bump to 0.4.1 ([#26](https://github.com/randy3k/rchitect/issues/26))

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.40...v0.4.1

## 0.3.40 - 2023-01-05

### Other

* upgrade setuptools

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.39...v0.3.40

## 0.3.38 - 2022-10-04

### Other

* rename parse_text
* added parse_text_complete
* return unmodified python objects
* Update CHANGELOG

### Testing

* test with rchitect module

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.37...v0.3.38

## 0.3.37 - 2022-08-16

### Bug Fixes

* fix typo
* fix a bug of reading > 4096 bytes in cb_read_console

### Other

* sys.path insertion no longer needed for reticulate >= 1.19
* we still need it for on windows
* allow setting callbacks after R initialization
* disable reticulate in py2
* install also askpass
* do not test radian on python 2.7
* use \x00

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.36...v0.3.37

## 0.3.36 - 2022-02-25

### Other

* respect convert=FALSE
* do not make external pointer twice
* update badge [no ci]
* complete code has already been tryCatch'ed
* remove appveyor.yml
* flush buffered stdio before readconsole
* with sexp_content
* improve flush system
* Use py2 branch of radian
* Update NEWS

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.35...v0.3.36

## 0.3.35 - 2021-12-17

### Bug Fixes

* fix some gc issue
* fix gc errors

### Other

* move conversion inside try
* make sure two way conversions
* allow kwargs in py_copy and py_object
* make RObject callable
* hide robject
* protect all already sexp first
* need to fix memory leak
* use py_tools from rchitect
* do not pass asis and convert to all rcopy dispatches
* improve sexp conversion
* use v2 setup-python
* use setup-r@v2
* use macos-10.15 to build python2.7 and 3.5 wheels
* do not inline external pointer
* use c api Rf_NewEnvironment
* Update CHANGELOG

### Testing

* test with gctorture

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.34...v0.3.35

## 0.3.34 - 2021-12-04

### Bug Fixes

* fix github action

### Other

* move noqa lines
* improve dispatch ordering
* install radian v0.5.12 for python 2
* build wheels

### Testing

* test with R 3.6

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.33...v0.3.34

## 0.3.33 - 2021-10-11

### Bug Fixes

* fix radian test

### Other

* use actions to install python and r
* consolidate jobs
* improve tests for testing radian
* do not need codecov here
* install jedi
* use cleanup
* remove circleci config
* show r version in job names
* move job name
* install Microsoft Visual C++
* show r and py versions
* better job name
* with toolset 9
* add DISTUTILS_USE_SDK and MSSdk
* move setup-r after microsoft visual c++
* split install and test
* remove microsoft/setup-msbuild
* swap order
* better debug message
* a workaround for radian#288

### Testing

* test python 2.7

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.32...v0.3.33

## 0.3.32 - 2021-06-03

### Other

* missing runs-on

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.31...v0.3.32

## 0.3.31 - 2021-06-03

### Bug Fixes

* fix some pointer conversion issues
* fix R binary urls

### Other

* reticulate 1.18.9008 has included a patch for fix this
* make sure the binary is intel based
* check if we need to insert path
* bump version
* wrong version number
* support UTF-8 locale
* move build to top level to make path discovery easier
* use joerick/cibuildwheel
* disable windows codecov
* use master branch cibuildwheel
* try without -s flag
* use RADIAN_NO_INPUTHOOK
* use R instead of Rscript
* use homebrew to install libpng
* install libpng for R devel on macOS
* use v1.11.1
* upgrade cibuildwheel
* build apple silican wheels
* revert back to cibuildwheel to support python 2.7
* build python 2.7 wheels with previous version of cibuildwheel
* upgrade setuptools
* do not build arm64 build
* install cffi from source
* forgot to use bash
* changelog
* build python 3.5 wheels too
* use default toolchain for py35

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.30...v0.3.31

## 0.3.30 - 2021-02-05

### Other

* use GITHUB_PATH, ::add-path:: is defuncted
* Avoid partial argument match ([#12](https://github.com/randy3k/rchitect/issues/12))
* Avoid partial argument match ([#13](https://github.com/randy3k/rchitect/issues/13))
* use new style callback
* use jedi 0.17.2
* Include license file with package.
* Include license file with package. ([#14](https://github.com/randy3k/rchitect/issues/14))
* tag 0.3.30
* update year

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.29...v0.3.30

## 0.3.29 - 2020-10-29

### Other

* help syntax highlighter
* support reticulate 1.17+
* do not bound cibuildwheel

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.28...v0.3.29

## 0.3.28 - 2020-06-25

### Bug Fixes

* fix for windows

### Other

* more than two options
* allow disabling code injection to reticulate

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.27...v0.3.28

## 0.3.27 - 2020-05-19

### Other

* do not use these flag
* fallback when failed to open R.dll
* added some comments in load_dll
* added changelog

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.26...v0.3.27

## 0.3.26 - 2020-05-15

### Bug Fixes

* fix appveyor script
* fix windows test

### Other

* set register_signal_handlers default to False
* append exe extension on windows
* workaround to not register SIGINT handler on windows
* make polled_events interrupt safe
* do not skip for R 4.0
* use https
* install jedi
* set $ErrorActionPreference = "Continue"
* use version field
* use rhome from rchitect
* encode rhome
* allow codecov in prs
* do not need libffi6
* match line break

### Testing

* test radian master branch

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.25...v0.3.26

## 0.3.25 - 2020-05-02

### Other

* these are not necessary
* support R_SignalHandlers=0
* use manylinux1 images
* a workaround to work with microsoft store python
* Microsoft Store python is now supported
* update appveyor config

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.24...v0.3.25

## 0.3.24 - 2020-04-23

### Bug Fixes

* fix error message

### Other

* update README
* use dwFlags
* forgot to return 1;

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.23...v0.3.24

## 0.3.23 - 2020-04-22

### Bug Fixes

* fix github windows actions
* fix github windows config
* fix typos
* fix badge [ci skip]

### Other

* safer polled_events and peek_event
* donot need it anymore
* do not suppress error in pytest
* reactivate appveyor
* use exact path to Rgraphapp.dll
* check also mangled names
* python 3.4 is not supported
* visual c++ didn't like it
* add github actions badge

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.22...v0.3.23

## 0.3.22 - 2020-04-21

### Other

* actually print the exception
* add peek_event function
* polled_events

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.21...v0.3.22

## 0.3.21 - 2020-04-19

### Bug Fixes

* fix issues on python 2.7

### Other

* respect environmental variable "R"
* support R_BINARY
* tiny refactor
* updated changelog

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.20...v0.3.21

## 0.3.20 - 2020-04-09

### Other

* use pytest.mark.skipif
* multiline match
* return directly

### Refactor

* refactor Rhome

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.19...v0.3.20

## 0.3.19 - 2020-03-16

### Bug Fixes

* fix cffi warnings

### Other

* use six.moves.input
* support EmitEmbeddedUTF8
* add changelog
* disable ci
* set LD_LIBRARY_PATH
* only if tty
* add wheels
* update config
* tag dev0
* restore circleci config
* continue anyway
* pass env variable
* install python 3.7
* same block
* codecov token is not needed

### Testing

* test github actions

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.18...v0.3.19

## 0.3.18 - 2020-02-28

### Other

* use 'replace' error handler in py 2.7 ([#11](https://github.com/randy3k/rchitect/issues/11))
* catch error in completion
* start 0.3.18 dev cycle

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.17...v0.3.18

## 0.3.17 - 2020-02-09

### Bug Fixes

* fix a bug in load_constant
* fix circleci config

### Other

* add changelog
* support asis in rcopy
* it's the job of the callback to flush
* flush buffer before write console callback first
* not relevent now
* windows compiler doesn't like it
* better message when architectures don't match
* drop python 3.4 test

### Refactor

* refactor error messages

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.16...v0.3.17

## 0.3.16 - 2019-12-19

### Other

* start dev version
* revert to RTerm CharacterMode
* skip test_write_console_utf8 in windows
* try testing in windows

### Testing

* test python 3.8

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.15...v0.3.16

## 0.3.15 - 2019-12-16

### Other

* a note about microsoft store python
* windows paths are always unicode
* CharacterMode back to RGUI
* add utf8 output test
* assert_called_once doesn't work < 3.6
* improve console interaction in windows
* use Rf_mkString + utf8tosystem to parse code
* start 0.3.15 cycle
* remove debug print
* fun could be a string
* get rid of utils.identity

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.14...v0.3.15

## 0.3.14 - 2019-12-08

### Other

* do not pin cibuildwheel
* update
* better debug message
* CON_NR is no longer exported
* install pycparser first

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.13...v0.3.14

## 0.3.13 - 2019-11-05

### Other

* flush everything before prompt

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.12...v0.3.13

## 0.3.12 - 2019-10-23

### Other

* catch OSError
* more debug notes

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.11...v0.3.12

## 0.3.11 - 2019-10-17

### Other

* add a note for system2utf8
* don't ask
* do no load some symbols before Rf_initialize_R
* show the last loaded symbol
* wrong note

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.10...v0.3.11

## 0.3.10 - 2019-09-23

### Other

* update mac install script
* only process polled events on main process
* remove unused include
* do not capture output of forks
* use R_ToplevelExec to run process_events
* abort child imediately
* better handling forked processes
* need to define these for windows

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.9...v0.3.10

## 0.3.9 - 2019-09-16

### Bug Fixes

* fix package_data

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.8...v0.3.9

## 0.3.8 - 2019-09-16

### Bug Fixes

* fix python 2 test bug

### Other

* improve error message handling
* remove unused import
* add completion utils
* tests update
* add parse test
* specify namespace
* do not protect prase result

### Refactor

* refactor reticulate code

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.7...v0.3.8

## 0.3.7 - 2019-09-12

### Bug Fixes

* fix windows bug

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.6...v0.3.7

## 0.3.6 - 2019-09-12

### Other

* suppress stderr
* Revert "suppress stderr"
* use system2utf8 for decoding
* set ptr_R_WriteConsole to NULL
* set R_Outputfile and R_Consolefile to NULL

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.5...v0.3.6

## 0.3.5 - 2019-08-21

### Bug Fixes

* fix python 3 error

### Other

* use system2utf8 to decode dlerror message
* drop testing python 3.4
* Revert "drop testing python 3.4"
* install python 3.4 from conda-forge
* tag 0.3.5

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.4...v0.3.5

## 0.3.4 - 2019-05-18

### Other

* init with no-save

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.3...v0.3.4

## 0.3.3 - 2019-05-09

### Bug Fixes

* fix passing envir variable in Windows

### Other

* update circleci config
* upload-wheels requires upload-tarball
* update appveyor config
* catch AttributeError in R_ReleaseObject
* no indent
* update circleci config
* add osx tests
* add changelog

### Testing

* test parametric job

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.2...v0.3.3

## 0.3.2 - 2019-05-03

### Other

* ship src files with tarball
* use circle ci to build wheels

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.1...v0.3.2

## 0.3.1 - 2019-04-27

### Bug Fixes

* fix py_tools tests

### Other

* python 3.8 fix
* some text update [ci skip]
* rename to rchitect.py_tools
* Update readmd [ci skip]
* support & and | in py_tools
* support ! in py_tools
* windows fix for 3.6

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.3.0...v0.3.1

## 0.3.0 - 2019-04-15

### Bug Fixes

* fix reval_with_visible
* fix FormatMessage
* fix python
* fix read_console_interrupted
* fix duplicate symbols
* fix R_tryEval
* fix windows bug
* fix window callback
* fix windows CallBack
* fix complex number conversion and more tests
* fix raw in py2

### Other

* add is_active binding
* migrating away from R_ToplevelExec
* move to R_tryCatch
* various fixes
* escape
* remove statements
* begin rewrite
* lint fix
* add more functions
* more symbols
* more
* callbacks
* use _libR_has_callback
* move callback setup to python
* initial support of Windows
* windows support completed
* add README
* add ci scripts
* use virtualenv
* add a foo test
* install libffi in circle
* add rparse
* include parse.h
* support basic parsing and evaluation
* rlang
* remove py2 code
* Revert "remove py2 code"
* use 0.3.0.dev0
* Update README.md
* unicode_literals
* move rapi in place
* dispatch system
* remove tests
* allow dispatch ffi.CData
* use six.string_types
* rcall and rprint
* clean code
* r to py basics
* basic py to R
* more conversions
* function callback
* better repr
* PyCallable and PyObject
* RObject repr method
* repl
* inject code
* variable things needed by radian
* check for nullness of stdout and stderr
* major update
* add travis ci badge [ci skip]
* inject
* gli lock
* improve support of reticulate
* improve reticulate conversions
* improve init code
* ensure_initialized
* add FQA
* improve callback error handling
* python2 support
* prepare 0.3.0.dev0
* Revert "remove tests"
* add tests
* Update appveyor.yml
* only for unix
* install libpython-dev
* more fix for reticulate
* pytest -s
* explictly codec
* support R 3.4.4
* update version of R
* changelog
* coverage
* more rcopy coverage
* appveyor uploads coverage
* add codecov badge [ci skip]
* more tests
* declare encoding
* more tests
* more tests
* more tests
* more py tools tests
* remove test_yes_no_cancel
* more callback tests
* simple README [ci skip]

### Refactor

* refactor

### Testing

* test list of complexs
* test read_console
* test yes/no/cancel

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.2.4...v0.3.0

## 0.2.4 - 2018-12-30

### Bug Fixes

* fix repl and ipython hook

### Other

* do not need to start manually
* do not start ipython hook when R has not started
* renaming
* more renaming
* fixup

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.2.3...v0.2.4

## 0.2.3 - 2018-12-30

### Other

* do not depend on multipledispatch
* lint fix
* change log

### Refactor

* refactor bootstrap code

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.2.2...v0.2.3

## 0.2.2 - 2018-12-28

### Other

* update references
* start machine with default settings automatically
* do not verbose when start implictly
* some renamings
* set reticulate env variables automatically
* Update README.md examples
* register hook automatically for ipython repl

### Refactor

* refactor hooks
* refactor bootstrap code

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.2.1...v0.2.2

## 0.2.1 - 2018-12-18

### Bug Fixes

* fix typo

### Other

* update title
* exclude tests module

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.2.0...v0.2.1

## 0.2.0 - 2018-12-17

### Other

* use patched reticulate
* Revert "use patched reticulate"
* allow rdevel to fail
* use options("pytools_environment")
* invisible return
* rename as rchitect

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.1.4...v0.2.0

## 0.1.4 - 2018-12-16

### Other

* support ipyhon 7
* unicode_literals are not needed
* use environment instead of hacking a namespace

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.1.3...v0.1.4

## 0.1.3 - 2018-09-18

### Other

* FreeBSD compatibility patch. ([#2](https://github.com/randy3k/rchitect/issues/2))
* use libR for anything else
* add FAQ
* add python 2 compatibility note
* support string_types function symbol
* Update README

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.1.2...v0.1.3

## 0.1.2 - 2018-08-29

### Other

* more information about reticulate
* search also the current process
* install reticulate
* Revert "search also the current process"
* add license
* GA_initapp via graphapp
* also install ssh

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.1.1...v0.1.2

## 0.1.1 - 2018-08-13

### Bug Fixes

* fix py_to_r
* fix r_to_py

### Other

* why
* support reticulate
* add API
* installation methods [ci skip]
* namespace update
* do not need register_reticulate_s3_methods
* remove lines

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.1.0...v0.1.1

## 0.1.0 - 2018-08-12

### Other

* remove unused variable
* do not register py namespace automatically

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.16...v0.1.0

## 0.0.16 - 2018-06-20

### Other

* add Makefile
* use RTLD_GLOBAL to fix some loading issues

### Testing

* test also release version

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.15...v0.0.16

## 0.0.15 - 2018-06-09

### Other

* move ctypes code into r_to_py

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.14...v0.0.15

## 0.0.14 - 2018-06-08

### Other

* rename rversion
* support r-devel

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.13...v0.0.14

## 0.0.13 - 2018-06-08

### Other

* use instance to store instance
* py_getitem
* getitem and getattr
* do not convert arguments of py_setattr and py_setitem
* move ipython hook to module
* remove unused
* add convert_return option
* use as_py_object
* preserve the R function
* convert to PyCallable
* added PyClass and fix a bug of r_to_py
* add missing list to INTSXP
* covert class to PyClass
* mimic reticulate names
* suuport string_types
* make sure text_type
* improve PyObject conversion
* add convert_args option for function conversion
* kwargs goes to the end
* more conversion rules
* add note to py_call
* add py_unicode
* default to R_GlobalEnv
* use extras_require
* added appveyor config
* avoid conversion error
* move utils

### Refactor

* refactor namespace register code
* refactor bootstrap code

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.12...v0.0.13

## 0.0.12 - 2018-06-02

### Bug Fixes

* fix NoneType
* fix r_to_py.PyObject

### Other

* check test result
* update callbacks
* improve ask input
* add get_machine
* create namespace DESCRIPTION
* use pythonapi to protect pyobject
* rtopy instead rcopy
* more than one arg
* rcopy only takes sexp
* use mkdtemp which is python 2 compatible
* fallback to the dict approach
* use Py_IncRef/Py_DecRef pair
* add _convert argument
* cast to py_object
* register rapi namespace
* PyObject to python
* pyeval and pycall
* switch back to rcopy
* py::import
* dispatch like s3 methods
* add PyCallable
* export LD_LIBRARY_PATH
* rcopy PyCallable
* do nothing for unknown conversions
* python 2 fix
* add pynames
* more pyobject improvement
* more protective rlang
* simplify rcopy logic
* use object represents python object
* use RObject as default
* use underscore function names to match reticulate
* make invisible an option of sexp
* some fixups
* rename as rcopyrule
* revert as sexptype
* perpare the future sexprule
* print all lines
* more informative repr
* inject to RObject directly
* sexpclass to dispatch robject conversion
* SEXPTYPE refactor
* less expensive to use try except to catch KeyError
* save parametric type into the class

### Refactor

* refactor DataType

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.11...v0.0.12

## 0.0.11 - 2018-05-29

### Bug Fixes

* fix rsym return type
* fix roption bug

### Other

* add a simple repl
* seal_namespace
* repl uses prompt_toolkit
* basic infrastructure for namespace creation
* encode error message
* reval with visible
* convert R function to python function
* remove repl option
* process events in repl
* rename class
* use r-ver latest

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.10...v0.0.11

## 0.0.10 - 2018-05-23

### Other

* use DataType
* rename functions
* add ipython eventloop
* add note for R eventloop
* these functions are not in R 3.4.4
* check if R has been initialized
* let bootstrap inject them
* these are not exported on linux
* create namespace
* remove enum
* add lambda function test
* add get_attrib and set_attrib
* more consistent interface code

### Refactor

* refactor SEXPTYPE

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.9...v0.0.10

## 0.0.8 - 2018-05-20

### Other

* import absolute_import
* load them anyway
* remove unused ctypes
* use Rf_translateCharUTF8
* unicode ce_type should be 1
* _register_global doesn't work with non-pointers
* remove global libR and rhome
* _register_sexp
* _register_constant
* rename get_rhome and get_libR
* set_callback in engine

### Refactor

* refactor registry
* refactor embedded code

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.7...v0.0.8

## 0.0.7 - 2018-05-16

### Other

* my ocd
* single workflow
* simplify R_ReadConsole
* more conversion methods
* sexp calls rint/rdouble etc
* RObject conversion
* move registry to internals
* function callback
* Update changlog
* don't import itself
* `from .types import FunctionType` confuses python 2

### Refactor

* refactor RObject

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.6...v0.0.7

## 0.0.6 - 2018-05-14

### Other

* update travis.sh
* revert .travis.yml
* use linuxbrew bottles to install old versions of R
* echo $PATH to .profile
* add linuxbrew to PATH
* use linuxbrew python
* set PATH in before_install
* use circleci instead
* add deploy-to-pypi
* use shield style
* python2 fixes
* add unicode test
* deploy on tag
* install twine
* update circleci config
* install dependencies before checkout
* need sudo

### Testing

* test against 2.7 and 3.5
* test both R 3.5 and 3.4
* test circleci
* test both python2 and python3

**Full Changelog**: https://github.com/randy3k/rchitect/compare/v0.0.5...v0.0.6

## 0.0.5 - 2018-05-11

### Bug Fixes

* fix windows bug
* fix typo
* fix windows command line args

### Other

* init repo
* bug fixes
* use default R_ReadConsole
* allow repl in init()
* update setup.py
* redirect stderr to stdout for windows
* cast None
* define callbacks in __init__
* use noop as default
* more refactoring
* move code to utils
* add rexec to avoid longjmp
* use protectedEval_t
* more interface functions
* add rcopy method
* some improvements for rexec
* add get_option and set_option
* rename functions
* allow verbose
* use sign.cname
* reorganize bootstrap
* add RObject
* add __all__
* return RObject
* improve reval
* multiple dispatch
* dispatch correctly
* introduce rcopytype
* dispatch list
* convert NILSXP
* add pypi badge
* various bug fixes
* use interface functions
* try import globals
* start 0.0.4.dev0
* ensure path first
* change default arguments
* interactive should be 1
* use markdown readme
* start 0.0.5.dev0
* use rexec to run process_events
* these functions are unix only
* these are not exported on windows
* R_CheckUserInterrupt
* _register_global now supports non-sexp
* add travis badge
* install rapi
* add changelog.md
* update secure

### Refactor

* refactor callbacks

<!-- generated by git-cliff -->
