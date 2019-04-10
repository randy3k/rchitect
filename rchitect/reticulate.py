import os
import sys
from .interface import rcall


def set_hook(event, fun):
    rcall(("base", "setHook"), event, fun)


def package_event(pkg, event):
    return rcall(("base", "packageEvent"), pkg, event)


def set_hooks():
    def hooks(x, y):
        os.environ["RETICULATE_PYTHON"] = sys.executable

        rcall(
            ("base", "source"),
            os.path.join(os.path.dirname(__file__), "R", "reticulate.R"),
            rcall(("base", "new.env")))

    set_hook(package_event("reticulate", "onLoad"), hooks)
