import os
import sys
import ctypes

from rchitect._libR import ffi, lib
from .interface import rcall, unbox


def set_hook(event, fun):
    rcall(("base", "setHook"), event, fun)


def package_event(pkg, event):
    return rcall(("base", "packageEvent"), pkg, event)


def set_hooks():
    def hooks(x, y):
        rcall(
            ("base", "source"),
            os.path.join(os.path.dirname(__file__), "R", "reticulate.R"),
            rcall(("base", "new.env")))

    set_hook(package_event("reticulate", "onLoad"), hooks)


def py_to_r(x):
    p = ffi.cast("uintptr_t", lib.R_ExternalPtrAddr(unbox(x)))
    d = int(p) if sys.version >= "3" else long(p)
    x = ctypes.cast(d, ctypes.py_object)
    return x.value


def id_str(x):
    return str(id(x))
