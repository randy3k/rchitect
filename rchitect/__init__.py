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

__version__ = '0.2.3'


IPYTHON_GUI = "RCHITECT_ENABLE_IPYTHON_GUI"
if hasattr(sys, "ps1") and (IPYTHON_GUI not in os.environ or os.environ[IPYTHON_GUI] != "0"):
    from .ipython_hook import register_hook, enable_gui
    register_hook()
    enable_gui()


def start(
        arguments=[
            "rchitect",
            "--quiet",
            "--no-save",
            "--no-restore"
        ],
        verbose=True):

    rs = RSession(verbose=verbose)
    rs.start(arguments=arguments)


def get_session():
    return RSession.instance


# backward compatability
Machine = RSession
get_machine = get_session
