from .interface import rexec, rparse, reval, rprint, rlang, rcall, rsym, rstring, rcopy
from .interface import process_events
from .types import RObject
from .setup import Machine


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

__version__ = '0.0.11'


def start(
        arguments=[
            "rapi",
            "--quiet",
            "--no-save",
            "--no-restore"
        ],
        verbose=True):

    m = Machine(verbose=verbose)
    m.start(arguments=arguments)

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
