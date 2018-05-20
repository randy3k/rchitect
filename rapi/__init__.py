from .interface import rexec, rparse, reval, rprint, rlang, rcall, rsym, rstring, rcopy
from .interface import process_events
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

    try:
        import IPython
        shell = IPython.get_ipython()
    except ImportError:
        shell = None

    if shell and IPython.__version__ >= "5":
        def inputhook(context):
            while True:
                if context.input_is_ready():
                    break
                process_events()

        IPython.terminal.pt_inputhooks.register("r", inputhook)
