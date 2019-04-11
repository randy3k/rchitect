# a simple repl loop suitable used within python console
from __future__ import unicode_literals

from prompt_toolkit.shortcuts import prompt

from .interface import rprint, rcopy, reval, rcall
from .interface import process_events


__all__ = ["repl_r"]


def inputhook(context):
    while True:
        if context.input_is_ready():
            break
        process_events()


def repl_r():
    while True:
        try:
            text = prompt("> ", inputhook=inputhook)
            result = reval("withVisible({{{}}})".format(text))
            if rcopy(rcall("$", result, "visible")):
                rprint(rcall("$", result, "value"))
        except RuntimeError:
            pass
        except EOFError:
            break
        except KeyboardInterrupt:
            pass
        except Exception as e:
            raise e
