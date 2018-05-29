# a simple repl loop suitable used within python console

from .interface import rprint, reval_with_visible
import sys
from prompt_toolkit import prompt


def repl_r():
    while True:
        try:
            text = prompt("> ")
            result = reval_with_visible(text)
            if result["visible"]:
                rprint(result["value"])
        except EOFError:
            break
        except KeyboardInterrupt:
            pass
        except Exception:
            pass
