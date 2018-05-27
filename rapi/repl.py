# a simple repl loop suitable used within python console

from .interface import rprint, reval
import sys
from prompt_toolkit import prompt

def repl_r():
    while True:
        try:
            text = prompt("> ")
            rprint(reval(text))
        except EOFError:
            break
        except KeyboardInterrupt:
            pass
        except Exception:
            pass
