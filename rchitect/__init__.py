import os
import sys

from .interface import rexec, rparse, reval, rprint, rlang, rcall, rsym, rstring, rcopy, robject
from .bootstrap import RSession


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
    "robject"
]

__version__ = '0.2.2'


try:
    gui_flag = "RCHITECT_ENABLE_IPYTHON_GUI"
    if hasattr(sys, "ps1") and (gui_flag not in os.environ or os.environ[gui_flag] != "0"):
        from .ipython_hook import register_hook, enable_gui
        register_hook()
        enable_gui()
except ImportError:
    pass


def start(
        arguments=[
            "rchitect",
            "--quiet",
            "--no-save",
            "--no-restore"
        ],
        verbose=True):

    m = RSession(verbose=verbose)
    m.start(arguments=arguments)


def get_session():
    return RSession.instance


# backward compatability
Machine = RSession
get_machine = get_session
