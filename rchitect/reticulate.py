import atexit
import os
import sys
from rchitect.interface import (
    rcall,
    rcopy,
    robject,
    setattrib,
    set_hook,
    package_event,
)


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
    _pending_py_object = rcopy(object, x)
    mod = rcall(("reticulate", "import"), "rchitect.reticulate", convert=False)
    fn = rcall(("reticulate", "py_get_attr"), mod, "pop_pending_py_object")
    res = rcall(("reticulate", "py_call"), fn)
    if convert is not None and rcopy(bool, convert):
        setattrib(res, "convert", True)
    return res


def _finalize_reticulate():
    try:
        ns = rcall(("base", "getNamespace"), "reticulate")
        if rcopy(bool, rcall(("base", "exists"), "py_finalize", envir=ns, inherits=False)):
            if not rcopy(bool, rcall(("reticulate", ":::", "was_python_initialized_by_reticulate"))):
                rcall(("reticulate", ":::", "py_finalize"))
    except Exception:
        pass


def configure():
    os.environ["RETICULATE_PYTHON"] = sys.executable
    os.environ["RETICULATE_REMAP_OUTPUT_STREAMS"] = "0"

    def _configure(*args):
        python_path = rcopy(str, rcall(("base", "system.file"), "python", package="reticulate"))
        if python_path and python_path not in sys.path:
            sys.path.append(python_path)
        ns = rcall(("base", "getNamespace"), "reticulate")
        rcall(
            ("base", "registerS3method"),
            "py_to_r",
            "rchitect.interface.RObject",
            robject("function", _py_to_r_robject, asis=False, convert=False),
            ns,
        )
        rcall(
            ("base", "registerS3method"),
            "r_to_py",
            "PyObject",
            robject("function", _r_to_py_pyobject, asis=True, convert=False),
            ns,
        )
        atexit.register(_finalize_reticulate)

    if "reticulate" in rcopy(rcall(("base", "loadedNamespaces"))):
        _configure()
    else:
        set_hook(package_event("reticulate", "onLoad"), _configure)
