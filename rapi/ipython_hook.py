from __future__ import unicode_literals
import sys
from .interface import process_events


def register_hook():

    shell = None
    try:
        if hasattr(sys, "ps1"):
            import IPython
            if IPython.__version__ >= "5":
                shell = IPython.get_ipython()
    except ImportError:
        pass

    if shell:
        def inputhook(context):
            while True:
                if context.input_is_ready():
                    break
                process_events()

        IPython.terminal.pt_inputhooks.register("r", inputhook)
