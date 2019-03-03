import sys
import signal

from rapi._libR import ffi, lib
from .utils import Rhome, libRpath, ensure_path
from .callbacks import def_callback, setup_callbacks


def init(args=["rapi", "--quiet", "--no-save"]):
    rhome = Rhome()
    ensure_path(rhome)
    if not lib._libR_load(libRpath(rhome).encode()):
        raise Exception("cannot load R library")
    if not lib._libR_load_symbols():
        raise Exception(ffi.string(lib._libR_dl_error_message()).decode())

    _argv = [ffi.new("char[]", a.encode()) for a in args]
    argv = ffi.new("char *[]", _argv)

    if sys.platform.startswith("win"):
        lib.Rf_initialize_R(len(argv), argv)
        lib.setup_Rmainloop()
    else:
        lib.Rf_initialize_R(len(argv), argv)
        lib.setup_Rmainloop()
        setup_callbacks()
    if not lib._libR_load_constants():
        raise Exception(ffi.string(lib._libR_dl_error_message()).decode())


def loop():
    lib.run_Rmainloop()


def sigint_handler(signum, frame):
    raise KeyboardInterrupt()


@def_callback()
def read_console(p, add_history):
    orig_handler = signal.getsignal(signal.SIGINT)
    # allow Ctrl+C to throw KeyboardInterrupt in callback
    signal.signal(signal.SIGINT, sigint_handler)
    try:
        if sys.version >= "3":
            return input(p)
        else:
            return raw_input(p).decode("utf-8", "backslashreplace")

    finally:
        signal.signal(signal.SIGINT, orig_handler)


@def_callback()
def write_console_ex(buf, otype):
    if otype == 0:
        sys.stdout.write(buf)
        sys.stdout.flush()
    else:
        sys.stderr.write(buf)
        sys.stderr.flush()


@def_callback()
def show_message(buf):
    sys.stdout.write(buf)
    sys.stdout.flush()


# @def_callback()
# def clean_up(saveact, status, run_last):
#     lib.Rstd_CleanUp(saveact, status, run_last)
