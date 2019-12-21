from __future__ import unicode_literals, absolute_import
from rchitect._cffi import lib

import operator
import sys
import importlib
from six import text_type
from types import ModuleType

from .interface import rcopy, robject, rfunction, rcall_p, rcall


def get_p(name, envir):
    return rcall_p(("base", "get"), name, envir=envir)


def inject_py_tools():

    def py_import(module):
        return importlib.import_module(module)

    def py_import_builtins():
        if sys.version >= "3":
            return importlib.import_module("builtins")
        else:
            return importlib.import_module("__builtin__")

    def py_call(fun, *args, **kwargs):
        # todo: suuport .asis and .convert
        if isinstance(fun, text_type):
            fun = eval(fun)
        return fun(*args, **kwargs)

    def py_copy(*args):
        return robject(*args)

    def py_eval(code):
        return eval(code)

    def py_get_attr(obj, key):
        if isinstance(obj, ModuleType):
            try:
                return importlib.import_module("{}.{}".format(obj.__name__, key))
            except ImportError:
                pass
        return getattr(obj, key)

    def py_get_item(obj, key):
        return obj[key]

    def py_names(obj):
        try:
            return list(k for k in obj.__dict__.keys() if not k.startswith("_"))
        except Exception:
            return None

    def py_object(*args):
        if len(args) == 1:
            return robject("PyObject", rcopy(args[0]))
        elif len(args) == 2:
            return robject("PyObject", rcopy(rcopy(object, args[0]), args[1]))

    def py_print(r):
        rcall_p("cat", repr(r) + "\n")

    def py_set_attr(obj, key, value):
        lib.Rf_protect(obj)
        lib.Rf_protect(key)
        lib.Rf_protect(value)
        pyo = rcopy(object, obj)
        try:
            setattr(pyo, rcopy(key), rcopy(value))
        finally:
            lib.Rf_unprotect(3)
        return pyo

    def py_set_item(obj, key, value):
        lib.Rf_protect(obj)
        lib.Rf_protect(key)
        lib.Rf_protect(value)
        pyo = rcopy(object, obj)
        try:
            pyo[rcopy(key)] = rcopy(value)
        finally:
            lib.Rf_unprotect(3)
        return pyo

    def py_dict(**kwargs):
        narg = len(kwargs)
        for key in kwargs:
            lib.Rf_protect(kwargs[key])
        try:
            return {key: rcopy(kwargs[key]) for key in kwargs}
        finally:
            lib.Rf_unprotect(narg)

    def py_tuple(*args):
        narg = len(args)
        for a in args:
            lib.Rf_protect(a)
        try:
            return tuple([rcopy(a) for a in args])
        finally:
            lib.Rf_unprotect(narg)

    def py_unicode(obj):
        return text_type(obj)

    def assign(name, value, envir):
        rcall(("base", "assign"), name, value, envir=envir)

    e = rcall(("base", "new.env"), parent=lib.R_GlobalEnv)
    kwarg = {"rchitect.py_tools": e}
    rcall(("base", "options"), **kwarg)

    assign("import", rfunction(py_import, convert=False), e)
    assign("import_builtins", rfunction(py_import_builtins, convert=False), e)
    assign("py_call", rfunction(py_call, convert=False), e)
    assign("py_copy", rfunction(py_copy, convert=True), e)
    assign("py_eval", rfunction(py_eval, convert=False), e)
    assign("py_get_attr", rfunction(py_get_attr, convert=False), e)
    assign("py_get_item", rfunction(py_get_item, convert=False), e)
    assign("py_object", rfunction(py_object, asis=True, convert=False), e)
    assign("py_set_attr", rfunction(py_set_attr, invisible=True, asis=True, convert=False), e)
    assign("py_set_item", rfunction(py_set_item, invisible=True, asis=True, convert=False), e)
    assign("py_unicode", rfunction(py_unicode, convert=False), e)
    assign("dict", rfunction(py_dict, asis=True, convert=False), e)
    assign("tuple", rfunction(py_tuple, asis=True, convert=False), e)

    assign("names.PyObject", rfunction(py_names, convert=True), e)
    assign("print.PyObject", rfunction(py_print, invisible=True, convert=False), e)
    assign(".DollarNames.PyObject", rfunction(py_names, convert=True), e)
    assign("$.PyObject", rfunction(py_get_attr, convert=True), e)
    assign("[.PyObject", rfunction(py_get_item, convert=True), e)
    assign("$<-.PyObject", rfunction(py_set_attr, invisible=True, asis=True, convert=False), e)
    assign("[<-.PyObject", rfunction(py_set_item, invisible=True, asis=True, convert=False), e)
    assign("&.PyObject", rfunction(operator.and_, invisible=True, convert=False), e)
    assign("|.PyObject", rfunction(operator.or_, invisible=True, convert=False), e)
    assign("!.PyObject", rfunction(operator.not_, invisible=True, convert=False), e)

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
            "!.PyObject"
        ]
        for thing in things:
            assign(thing, get_p(thing, e), parent_frame)

    assign("attach", robject(attach, invisible=True), e)
