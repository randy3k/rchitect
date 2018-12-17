# a simple repl loop suitable used within python console

from .interface import rprint, reval_with_visible
from prompt_toolkit.shortcuts import prompt
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
            result = reval_with_visible(text)
            if result["visible"]:
                rprint(result["value"])
        except RuntimeError as e:
            raise e
        except EOFError:
            break
        except KeyboardInterrupt:
            pass
        except Exception:
            pass
