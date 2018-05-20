from .interface import rexec, rparse, reval, rprint, rlang, rcall, rsym, rstring, rcopy
from .types import RObject
from .machine import Engine

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

__version__ = '0.0.9'


def start(
        arguments=[
            "rapi",
            "--quiet",
            "--no-save",
            "--no-restore"
        ],
        repl=False,
        verbose=True):

    engine = Engine(verbose=verbose)
    engine.start(arguments=arguments)

    if repl:
        engine.run_repl()
