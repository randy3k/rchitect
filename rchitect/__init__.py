import os
import sys

from .interface import rexec, rparse, reval, rprint, rlang, rcall, rsym, rstring, rcopy, robject
from .bootstrap import RSession
from .ipython_hook import register_hook


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

__version__ = '0.2.1'


def start(
        arguments=[
            "rchitect",
            "--quiet",
            "--no-save",
            "--no-restore"
        ],
        verbose=True):

    os.environ["RETICULATE_PYTHON"] = sys.executable
    os.environ["RETICULATE_REMAP_OUTPUT_STREAMS"] = "0"

    m = RSession(verbose=verbose)
    m.start(arguments=arguments)
    register_hook()


def get_session():
    return RSession.instance


# backward compatability
Machine = RSession
get_machine = get_session
