from .bootstrap import bootstrap
from .utils import get_rhome, get_libR, ensure_path
from .interface import rexec, rparse, reval, rprint, rlang, rcall, rsym, rstring, rcopy
from . import embedded, defaults
from .types import RObject

__all__ = [
    "rexec",
    "rparse",
    "reval",
    "rprint",
    "rlang",
    "rcall",
    "rsym",
    "rstring",
    "rcopy",
    "RObject"
]

__version__ = '0.0.7'


def start(
        arguments=[
            "rapi",
            "--quiet",
            "--no-save",
            "--no-restore"
        ],
        repl=False,
        verbose=True):

    rhome = get_rhome()
    ensure_path(rhome)

    libR = get_libR(rhome)

    embedded.set_callback("R_ShowMessage", defaults.R_ShowMessage)
    embedded.set_callback("R_ReadConsole", defaults.R_ReadConsole)
    embedded.set_callback("R_WriteConsoleEx", defaults.R_WriteConsoleEx)
    embedded.set_callback("R_Busy", defaults.R_Busy)
    embedded.set_callback("R_PolledEvents", defaults.R_PolledEvents)
    embedded.set_callback("R_YesNoCancel", defaults.R_YesNoCancel)

    embedded.initialize(libR, arguments=arguments)

    bootstrap(libR, verbose=verbose)

    if repl:
        embedded.run_loop(libR)
