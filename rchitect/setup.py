from __future__ import unicode_literals
import sys
import signal

from rchitect._cffi import ffi, lib
from .utils import Rhome, libRpath, ensure_path, system2utf8
from .callbacks import def_callback, setup_unix_callbacks, setup_rstart


if sys.version >= "3":
    long = int


def init(args=None):

    if not args:
        args = ["rchitect", "--quiet", "--no-save"]

    rhome = Rhome()
    ensure_path(rhome)

    libR_loaded = lib.Rf_initialize_R != ffi.NULL

    if not libR_loaded:
        # `system2utf8` may not work before `Rf_initialize_R` because locale may not be set
        if not lib._libR_load(libRpath(rhome).encode("utf-8")):
            raise Exception("Cannot load R shared library. {}".format(
                    system2utf8(ffi.string(lib._libR_dl_error_message()))))
        if not lib._libR_load_symbols():
            raise Exception("Cannot load symbol {}: {}".format(
                system2utf8(ffi.string(lib._libR_last_loaded_symbol()))),
                system2utf8(ffi.string(lib._libR_dl_error_message())))

    # _libR_is_initialized only works after _libR_load is run.
    if not lib._libR_is_initialized():

        _argv = [ffi.new("char[]", a.encode("utf-8")) for a in args]
        argv = ffi.new("char *[]", _argv)

        lib.Rf_initialize_R(len(argv), argv)

        if sys.platform.startswith("win"):
            setup_rstart(args)
            lib.setup_Rmainloop()
        else:
            setup_unix_callbacks()
            lib.setup_Rmainloop()

    if not libR_loaded:
        if not lib._libR_load_constants():
            raise Exception("Cannot load constant {}: {}".format(
                system2utf8(ffi.string(lib._libR_last_loaded_symbol()))),
                system2utf8(ffi.string(lib._libR_dl_error_message())))
        lib._libR_setup_xptr_callback()

        from rchitect.py_tools import inject_py_tools
        inject_py_tools()

        from rchitect import reticulate
        reticulate.configure()


def loop():
    lib.run_Rmainloop()


def sigint_handler(signum, frame):
    raise KeyboardInterrupt()


if sys.version >= "3":
    def ask_input(s):
        return input(s)
else:
    def ask_input(s):
        return raw_input(s).decode("utf-8", "backslashreplace")


@def_callback()
def show_message(buf):
    sys.stdout.write(buf)
    sys.stdout.flush()


@def_callback()
def read_console(p, add_history):
    sys.stdout.flush()
    sys.stderr.flush()

    orig_handler = signal.getsignal(signal.SIGINT)
    # allow Ctrl+C to throw KeyboardInterrupt in callback
    signal.signal(signal.SIGINT, sigint_handler)
    try:
        return ask_input(p)
    finally:
        signal.signal(signal.SIGINT, orig_handler)


@def_callback()
def write_console_ex(buf, otype):
    if otype == 0:
        if sys.stdout:
            sys.stdout.write(buf)
            sys.stdout.flush()
    else:
        if sys.stderr:
            sys.stderr.write(buf)
            sys.stderr.flush()


@def_callback()
def busy(which):
    pass


@def_callback()
def polled_events():
    pass


# @def_callback()
# def clean_up(saveact, status, run_last):
#     lib.Rstd_CleanUp(saveact, status, run_last)


@def_callback()
def yes_no_cancel(p):
    while True:
        try:
            result = ask_input("{} [y/n/c]: ".format(p))
            if result in ["Y", "y"]:
                return 1
            elif result in ["N", "n"]:
                return 2
            else:
                return 0
        except EOFError:
            return 0
        except KeyboardInterrupt:
            return 0
        except Exception:
            pass
