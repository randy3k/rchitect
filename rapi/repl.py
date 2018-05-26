# a simple repl loop suitable used within python console

from .interface import rprint, reval
import sys

def repl_r():
    while True:
        try:
            if sys.version >= "3":
                text = str(input("> "))
            else:
                text = raw_input("> ")
            rprint(reval(text))
        except EOFError:
            break
        except Exception:
            pass
