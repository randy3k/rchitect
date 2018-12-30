from __future__ import unicode_literals


def register_hook():
    from rchitect import get_session
    from rchitect.interface import process_events

    shell = None
    try:
        import IPython
        if IPython.__version__ >= "5":
            shell = IPython.get_ipython()
    except ImportError:
        pass

    if shell:
        def inputhook(context):
            rs = get_session()
            if rs:
                while True:
                    if context.input_is_ready():
                        break
                    process_events()

        IPython.terminal.pt_inputhooks.register("r", inputhook)


def enable_gui():
    shell = None
    try:
        import IPython
        if IPython.__version__ >= "5":
            shell = IPython.get_ipython()
    except ImportError:
        pass
    if shell:
        shell.enable_gui('r')
