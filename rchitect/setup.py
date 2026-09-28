import sys
import os

from rchitect._cffi import ffi, lib
from .utils import get_rhome
from .callbacks import def_callback, setup_unix_callbacks, setup_rstart


_initialized = False


def init(args=None, register_callbacks=None, register_signal_handlers=None):
    global _initialized

    if not args:
        args = ["rchitect", "--quiet", "--no-save"]

    if register_callbacks is None:
        register_callbacks = os.environ.get("RCHITECT_REGISTER_CALLBACKS", "1") == "1"

    if register_signal_handlers is None:
        register_signal_handlers = (
            os.environ.get("RCHITECT_REGISTER_SIGNAL_HANDLERS", "1") == "1"
        )

    rhome = get_rhome()

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
                lib.R_SignalHandlers = 0
                setup_rstart(rhome, args)
                lib.R_set_command_line_arguments(len(argv), argv)
                lib.GA_initapp(0, ffi.NULL)
            lib.setup_Rmainloop()
            lib.EmitEmbeddedUTF8 = 1
        else:
            lib.R_SignalHandlers = int(bool(register_signal_handlers))
            lib.Rf_initialize_R(len(argv), argv)
            setup_unix_callbacks()
            lib.setup_Rmainloop()

    else:
        # it is to allow `reticulate::import("radian")$main()`.
        if register_callbacks:
            if sys.platform.startswith("win"):
                raise Exception(
                    "setting callbacks after R initialization on Windows is not allowed."
                )
            else:
                setup_unix_callbacks()

    if not _initialized:
        _initialized = True
        lib._libR_setup_xptr_callback()

        from rchitect.py_tools import inject_py_tools

        inject_py_tools()

        if os.environ.get("RCHITECT_RETICULATE_CONFIG", "1") != "0":
            from rchitect import reticulate

            reticulate.configure()


def loop():
    lib.rchitect_run_Rmainloop()


def ask_input(s):
    return input(s)


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
