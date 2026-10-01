import atexit
import os
import sys
from rchitect.interface import (
    rcall,
    rcopy,
    reval,
    robject,
    setattrib,
    set_hook,
    package_event,
)


_pending_py_object = None
_py_repl_active_fn = None


def is_installed():
    return len(rcall(("base", "find.package"), "reticulate", quiet=True, _convert=True)) > 0


def is_loaded():
    return "reticulate" in rcall(("base", "loadedNamespaces"), _convert=True)


def on_load(callback):
    if is_loaded():
        callback()
    else:
        set_hook(package_event("reticulate", "onLoad"), lambda *args: callback())


def py_repl_active():
    global _py_repl_active_fn
    if _py_repl_active_fn is None:
        _py_repl_active_fn = reval("reticulate:::py_repl_active")
    return bool(rcall(_py_repl_active_fn, _convert=True))


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
        if sys.platform.startswith("win"):
            # On native Windows ARM64 builds of R (R >= 4.4), R is built without
            # subarchitectures so `.Platform$r_arch` is `""` instead of `"x64"`.
            # `reticulate:::current_python_arch()` only checks for `"i386"` and
            # `"x64"` and otherwise returns `"Unknown"`, causing
            # `reticulate:::is_incompatible_arch()` to reject 64-bit ARM64 Python.
            try:
                if (
                    rcopy(bool, rcall(("base", "exists"), "current_python_arch", envir=ns, inherits=False))
                    and rcopy(str, rcall(("reticulate", ":::", "current_python_arch"))) == "Unknown"
                ):
                    rcall(
                        ("utils", "assignInNamespace"),
                        "current_python_arch",
                        reval("function() '64bit'"),
                        "reticulate",
                    )
            except Exception:
                pass
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

    on_load(_configure)
