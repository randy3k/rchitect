import os
import sys
from rchitect._cffi import lib
from rchitect.interface import (
    protected,
    rcall,
    rcall_p,
    rcopy,
    rlogical_p,
    robject,
    rsym_p,
    set_hook,
    package_event,
)
from rchitect.xptr import from_xptr


_pending_py_object = None


def pop_pending_py_object():
    global _pending_py_object
    obj = _pending_py_object
    _pending_py_object = None
    return obj


def _py_to_r_robject(x, *args, **kwargs):
    return robject(x)


def _r_to_py_pyobject(x, convert=None, *args, **kwargs):
    global _pending_py_object
    _pending_py_object = from_xptr(x)
    with protected(x):
        mod = rcall_p(("reticulate", "import"), "rchitect.reticulate", convert=False)
        with protected(mod):
            fn = rcall_p(("reticulate", "py_get_attr"), mod, "pop_pending_py_object")
            with protected(fn):
                res = rcall_p(("reticulate", "py_call"), fn)
                with protected(res):
                    if convert is not None and rcopy(bool, convert):
                        lib.Rf_setAttrib(res, rsym_p("convert"), rlogical_p(True))
                    return res


def configure():
    os.environ["RETICULATE_PYTHON"] = sys.executable
    os.environ["RETICULATE_REMAP_OUTPUT_STREAMS"] = "0"

    def _configure(*args):
        python_path = rcopy(str, rcall_p(("base", "system.file"), "python", package="reticulate"))
        if python_path and python_path not in sys.path:
            sys.path.append(python_path)
        ns = rcall_p(("base", "getNamespace"), "reticulate")
        with protected(ns):
            rcall_p(
                ("base", "registerS3method"),
                "py_to_r",
                "rchitect.types.RObject",
                robject("function", _py_to_r_robject, asis=False, convert=False),
                ns,
            )
            rcall_p(
                ("base", "registerS3method"),
                "r_to_py",
                "PyObject",
                robject("function", _r_to_py_pyobject, asis=True, convert=False),
                ns,
            )

    if "reticulate" in rcopy(rcall(("base", "loadedNamespaces"))):
        _configure()
    else:
        set_hook(package_event("reticulate", "onLoad"), _configure)
