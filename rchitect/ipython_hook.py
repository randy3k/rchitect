from __future__ import unicode_literals
from rchitect.interface import process_events


def register_hook():
    import IPython
    shell = IPython.get_ipython()
    if not shell:
        return

    def inputhook(context):
        from rchitect import get_session
        rs = get_session()
        if not rs:
            return
        while True:
            if context.input_is_ready():
                break
            process_events()

    IPython.terminal.pt_inputhooks.register("r", inputhook)
