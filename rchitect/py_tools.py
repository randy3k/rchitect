import importlib
import operator
import re
from types import ModuleType

import rchitect._cffi as _cffi
from rchitect._cffi import lib
from .interface import (
    rcopy,
    robject,
    rcall,
    rsym,
    getattrib,
    new_env,
    setoption,
    set_hook,
    package_event,
    unbox,
)


def py_import(module, convert=True):
    return robject("PyObject", importlib.import_module(module), convert=convert)


def py_import_builtins(convert=True):
    return robject("PyObject", importlib.import_module("builtins"), convert=convert)


def py_call(fun, *args, **kwargs):
    if isinstance(fun, str):
        fun = eval(fun)
    return fun(*args, **kwargs)


def py_copy(*args, **kwargs):
    return robject(*args, **kwargs)


def py_eval(code):
    return eval(code)


def py_get_attr(obj, key):
    if isinstance(obj, ModuleType):
        try:
            return importlib.import_module("{}.{}".format(obj.__name__, key))
        except ImportError:
            pass
    return getattr(obj, key)


def _dollar_pyobject(robj, rkey):
    obj = rcopy(robj)
    key = rcopy(rkey)
    convert = bool(rcopy(getattrib(robj, "convert")))
    val = py_get_attr(obj, key)
    if convert:
        return robject(val, convert=True)
    return _cffi._c_sexp_as_py_object(val, False, True, False, 0)


def py_get_item(obj, key):
    return obj[key]


def _bracket_pyobject(robj, rkey):
    obj = rcopy(robj)
    key = rcopy(rkey)
    convert = bool(rcopy(getattrib(robj, "convert")))
    val = py_get_item(obj, key)
    if convert:
        return robject(val, convert=True)
    return _cffi._c_sexp_as_py_object(val, False, True, False, 0)


def py_names(obj, pattern=None):
    try:
        names = [k for k in obj.__dict__.keys() if not k.startswith("_")]
    except Exception:
        return None
    if pattern:
        names = [k for k in names if re.search(pattern, k)]
    return names


def py_object(*args, **kwargs):
    kw = {k: rcopy(v) for k, v in kwargs.items()}
    if len(args) == 1:
        return robject("PyObject", rcopy(args[0]), **kw)
    elif len(args) == 2:
        return robject("PyObject", rcopy(rcopy(object, args[0]), args[1]), **kw)


def py_print(r, **kwargs):
    rcall("cat", repr(r) + "\n")


def py_set_attr(obj, key, value):
    pyo = rcopy(object, obj)
    setattr(pyo, rcopy(key), rcopy(value))
    return obj


def py_set_item(obj, key, value):
    pyo = rcopy(object, obj)
    pyo[rcopy(key)] = rcopy(value)
    return obj


def py_dict(**kwargs):
    return {key: rcopy(kwargs[key]) for key in kwargs}


def py_tuple(*args):
    return tuple([rcopy(a) for a in args])


def py_unicode(obj):
    return str(obj)


def _rfunction(x, **kwargs):
    return robject("function", x, **kwargs)


def _define_vars(env, mapping):
    env_s = unbox(env)
    for name, val in mapping.items():
        lib.Rf_defineVar(rsym(name).s, unbox(val), env_s)


def inject_py_tools():
    s3_methods = {
        "names": _rfunction(py_names, convert=True),
        "print": _rfunction(py_print, invisible=True, convert=False),
        "$": _rfunction(_dollar_pyobject, asis=True, convert=True),
        "[": _rfunction(_bracket_pyobject, asis=True, convert=True),
        "$<-": _rfunction(py_set_attr, invisible=True, asis=True, convert=False),
        "[<-": _rfunction(py_set_item, invisible=True, asis=True, convert=False),
        "&": _rfunction(operator.and_, invisible=True, convert=False),
        "|": _rfunction(operator.or_, invisible=True, convert=False),
        "!": _rfunction(operator.not_, invisible=True, convert=False),
    }
    base_ns = rcall(("base", "baseenv"))
    for gen, fn in s3_methods.items():
        rcall(("base", "registerS3method"), gen, "PyObject", fn, base_ns)

    dollar_names_fn = _rfunction(py_names, convert=True)

    def _register_dollar_names(*args):
        utils_ns = rcall(("base", "asNamespace"), "utils")
        rcall(
            ("base", "registerS3method"),
            ".DollarNames",
            "PyObject",
            dollar_names_fn,
            utils_ns,
        )

    if "utils" in rcopy(rcall(("base", "loadedNamespaces"))):
        _register_dollar_names()
    else:
        set_hook(package_event("utils", "onLoad"), _register_dollar_names)

    exported_tools = {
        "import": _rfunction(py_import, convert=False),
        "import_builtins": _rfunction(py_import_builtins, convert=False),
        "py_call": _rfunction(py_call, convert=False),
        "py_copy": _rfunction(py_copy, convert=True),
        "py_eval": _rfunction(py_eval, convert=False),
        "py_get_attr": _rfunction(py_get_attr, convert=False),
        "py_get_item": _rfunction(py_get_item, convert=False),
        "py_object": _rfunction(py_object, asis=True, convert=False),
        "py_set_attr": _rfunction(py_set_attr, invisible=True, asis=True, convert=False),
        "py_set_item": _rfunction(py_set_item, invisible=True, asis=True, convert=False),
        "py_unicode": _rfunction(py_unicode, convert=False),
        "dict": _rfunction(py_dict, asis=True, convert=False),
        "tuple": _rfunction(py_tuple, asis=True, convert=False),
    }

    def attach(envir=None):
        if envir is None:
            envir = rcall(("base", "sys.frame"), -1)
        _define_vars(envir, exported_tools)

    e = new_env()
    _define_vars(e, exported_tools)
    lib.Rf_defineVar(rsym("attach").s, robject(attach, invisible=True).s, e.s)
    setoption("rchitect.py_tools", e)
