from __future__ import unicode_literals
import sys
import os
from six.moves import input as six_input

from rchitect._cffi import ffi, lib
from .utils import Rhome, ensure_path, system2utf8
from .callbacks import def_callback, setup_unix_callbacks, setup_rstart


def load_lib_error():
    return"Cannot load shared library: {}".format(
        system2utf8(ffi.string(lib._libR_dl_error_message())))


def load_symbol_error():
    return "Cannot load symbol {}: {}".format(
                system2utf8(ffi.string(lib._libR_last_loaded_symbol())),
                system2utf8(ffi.string(lib._libR_dl_error_message())))


def load_constant_error():
    return "Cannot load constant {}: {}".format(
                system2utf8(ffi.string(lib._libR_last_loaded_symbol())),
                system2utf8(ffi.string(lib._libR_dl_error_message())))


def init(args=None, register_signal_handlers=None):

    if not args:
        args = ["rchitect", "--quiet", "--no-save"]

    if register_signal_handlers is None:
        register_signal_handlers = os.environ.get("RCHITECT_REGISTER_SIGNAL_HANDLERS", "1") == "1"

    rhome = Rhome()
    # microsoft python doesn't load DLL's from PATH
    # we will need to open the DLL's directly in _libR_load
    ensure_path(rhome)

    libR_loaded = lib.Rf_initialize_R != ffi.NULL

    if not libR_loaded:
        # `system2utf8` may not work before `Rf_initialize_R` because locale may not be set
        if not lib._libR_load(rhome.encode("utf-8")):
            raise Exception(load_lib_error())
        if not lib._libR_load_symbols():
            raise Exception(load_symbol_error())

    # _libR_is_initialized only works after _libR_load is run.
    if not lib._libR_is_initialized():

        _argv = [ffi.new("char[]", a.encode("utf-8")) for a in args]
        argv = ffi.new("char *[]", _argv)

        if sys.platform.startswith("win"):
            if register_signal_handlers:
                lib.Rf_initialize_R(len(argv), argv)
                setup_rstart(rhome, args)
            else:
                # Rf_initialize_R will set handler for SIGINT
                # we need to workaround it
                lib.R_SignalHandlers_t[0] = 0
                setup_rstart(rhome, args)
                lib.R_set_command_line_arguments(len(argv), argv)
                lib.GA_initapp(0, ffi.NULL)
            lib.setup_Rmainloop()
            # require R 4.0
            if lib.EmitEmbeddedUTF8_t != ffi.NULL:
                lib.EmitEmbeddedUTF8_t[0] = 1
        else:
            lib.R_SignalHandlers_t[0] = register_signal_handlers
            lib.Rf_initialize_R(len(argv), argv)
            setup_unix_callbacks()
            lib.setup_Rmainloop()

    if not libR_loaded:
        if not lib._libR_load_constants():
            raise Exception(load_constant_error())
        lib._libR_setup_xptr_callback()

        from rchitect.py_tools import inject_py_tools
        inject_py_tools()

        if os.environ.get("RCHITECT_RETICULATE_CONFIG", "1") != "0":
            from rchitect import reticulate
            reticulate.configure()


def loop():
    lib.run_Rmainloop()


def ask_input(s):
    return six_input(s)


@def_callback()
def show_message(buf):
    sys.stdout.write(buf)
    sys.stdout.flush()


@def_callback()
def read_console(p, add_history):
    sys.stdout.flush()
    sys.stderr.flush()
    return ask_input(p)


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
