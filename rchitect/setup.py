import os
import subprocess
import sys

from rchitect._cffi import ffi, lib
from . import console
from .callbacks import setup_rstart, setup_unix_callbacks
from .utils import get_rhome


_initialized = False


def _setup_r_env_vars(rhome):
    doc_dir = os.environ.get("R_DOC_DIR") or os.path.join(rhome, "doc")
    include_dir = os.environ.get("R_INCLUDE_DIR") or os.path.join(rhome, "include")
    share_dir = os.environ.get("R_SHARE_DIR") or os.path.join(rhome, "share")
    if not (
        os.path.isdir(doc_dir)
        and os.path.isdir(include_dir)
        and os.path.isdir(share_dir)
    ):
        try:
            paths = subprocess.check_output(
                [
                    os.path.join(rhome, "bin", "R"),
                    "--no-echo",
                    "--vanilla",
                    "-e",
                    "cat(paste(R.home('doc'), R.home('include'), R.home('share'), sep='\\n'))",
                ]
            )
            doc_dir, include_dir, share_dir = paths.decode("utf-8", "ignore").splitlines()
        except Exception:
            pass

    os.environ["R_DOC_DIR"] = doc_dir
    os.environ["R_INCLUDE_DIR"] = include_dir
    os.environ["R_SHARE_DIR"] = share_dir


def _set_utf8():
    if sys.platform.startswith("win"):
        import ctypes

        try:
            if ctypes.windll.kernel32.GetACP() == 65001:
                return
        except Exception:
            pass
        if not os.environ.get("LANG", ""):
            os.environ["LANG"] = "en_US.UTF-8"
        from .interface import setoption

        setoption("encoding", "UTF-8")


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
    _setup_r_env_vars(rhome)

    lib.rchitect_record_main_thread()
    console.record_main_thread()

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

        if sys.platform.startswith("win"):
            _set_utf8()

        from .py_tools import inject_py_tools

        inject_py_tools()

        if os.environ.get("RCHITECT_RETICULATE_CONFIG", "1") != "0":
            from . import reticulate

            reticulate.configure()


def ensure_initialized():
    if not _initialized:
        init(register_callbacks=False, register_signal_handlers=False)


def loop():
    console.record_main_thread()
    lib.rchitect_run_Rmainloop()


