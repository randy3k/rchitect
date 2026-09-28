import importlib
import operator
from types import ModuleType

import rchitect._cffi as _cffi
from .interface import rcopy, robject, rcall, getattrib, new_env


def get_var(name, envir):
    return rcall(("base", "get"), name, envir=envir)


def inject_py_tools():

    def py_import(module, convert=True):
        return robject("PyObject", importlib.import_module(module), convert=convert)

    def py_import_builtins(convert=True):
        return robject("PyObject", importlib.import_module("builtins"), convert=convert)

    def py_call(fun, *args, **kwargs):
        # todo: support .asis and .convert
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

    def py_get_attr2(robj, rkey):
        obj = rcopy(robj)
        key = rcopy(rkey)
        convert = bool(rcopy(getattrib(robj, "convert")))
        val = py_get_attr(obj, key)
        if convert:
            return robject(val, convert=True)
        else:
            return _cffi._c_sexp_as_py_object(val, False, True, False, 0)

    def py_get_item(obj, key):
        return obj[key]

    def py_get_item2(robj, rkey):
        obj = rcopy(robj)
        key = rcopy(rkey)
        convert = bool(rcopy(getattrib(robj, "convert")))
        val = py_get_item(obj, key)
        if convert:
            return robject(val, convert=True)
        else:
            return _cffi._c_sexp_as_py_object(val, False, True, False, 0)

    def py_names(obj):
        try:
            return list(k for k in obj.__dict__.keys() if not k.startswith("_"))
        except Exception:
            return None

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

    def assign(name, value, envir):
        rcall(("base", "assign"), name, value, envir=envir)

    # helper function
    def _rfunction(x, **kwargs):
        return robject("function", x, **kwargs)

    e = new_env()
    kwarg = {"rchitect.py_tools": e}
    rcall(("base", "options"), **kwarg)

    assign("import", _rfunction(py_import, convert=False), e)
    assign("import_builtins", _rfunction(py_import_builtins, convert=False), e)
    assign("py_call", _rfunction(py_call, convert=False), e)
    assign("py_copy", _rfunction(py_copy, convert=True), e)
    assign("py_eval", _rfunction(py_eval, convert=False), e)
    assign("py_get_attr", _rfunction(py_get_attr, convert=False), e)
    assign("py_get_item", _rfunction(py_get_item, convert=False), e)
    assign("py_object", _rfunction(py_object, asis=True, convert=False), e)
    assign("py_set_attr", _rfunction(py_set_attr, invisible=True, asis=True, convert=False), e)
    assign("py_set_item", _rfunction(py_set_item, invisible=True, asis=True, convert=False), e)
    assign("py_unicode", _rfunction(py_unicode, convert=False), e)
    assign("dict", _rfunction(py_dict, asis=True, convert=False), e)
    assign("tuple", _rfunction(py_tuple, asis=True, convert=False), e)

    assign("names.PyObject", _rfunction(py_names, convert=True), e)
    assign("print.PyObject", _rfunction(py_print, invisible=True, convert=False), e)
    assign(".DollarNames.PyObject", _rfunction(py_names, convert=True), e)
    assign("$.PyObject", _rfunction(py_get_attr2, asis=True, convert=True), e)
    assign("[.PyObject", _rfunction(py_get_item2, asis=True, convert=True), e)
    assign("$<-.PyObject", _rfunction(py_set_attr, invisible=True, asis=True, convert=False), e)
    assign("[<-.PyObject", _rfunction(py_set_item, invisible=True, asis=True, convert=False), e)
    assign("&.PyObject", _rfunction(operator.and_, invisible=True, convert=False), e)
    assign("|.PyObject", _rfunction(operator.or_, invisible=True, convert=False), e)
    assign("!.PyObject", _rfunction(operator.not_, invisible=True, convert=False), e)

    def attach():
        parent_frame = rcall("sys.frame", -1)
        things = [
            "import",
            "import_builtins",
            "py_call",
            "py_copy",
            "py_eval",
            "py_get_attr",
            "py_get_item",
            "py_object",
            "py_set_attr",
            "py_set_item",
            "py_unicode",
            "dict",
            "tuple",
            "names.PyObject",
            "print.PyObject",
            ".DollarNames.PyObject",
            "$.PyObject",
            "[.PyObject",
            "$<-.PyObject",
            "[<-.PyObject",
            "&.PyObject",
            "|.PyObject",
            "!.PyObject",
        ]
        for thing in things:
            assign(thing, get_var(thing, e), parent_frame)

    assign("attach", robject(attach, invisible=True), e)
