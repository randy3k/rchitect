from __future__ import unicode_literals, absolute_import
from rchitect._cffi import lib

import operator
import sys
import importlib
from six import text_type
from types import ModuleType

from .interface import rcopy, robject, rcall_p, rcall, sexp, sexp_as_py_object, \
        sexp_context, getattrib_p, new_env


def get_p(name, envir):
    return rcall_p(("base", "get"), name, envir=envir)


def inject_py_tools():

    def py_import(module, convert=True):
        with sexp_context(convert=convert):
            return sexp(importlib.import_module(module))

    def py_import_builtins(convert=True):
        with sexp_context(convert=convert):
            if sys.version >= "3":
                return sexp(importlib.import_module("builtins"))
            else:
                return sexp(importlib.import_module("__builtin__"))

    def py_call(fun, *args, **kwargs):
        # todo: suuport .asis and .convert
        if isinstance(fun, text_type):
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
        lib.Rf_protect(robj)
        lib.Rf_protect(rkey)
        nprotect = 2
        try:
            obj = rcopy(robj)
            key = rcopy(rkey)
            convert_p = getattrib_p(robj, "convert")
            lib.Rf_protect(convert_p)
            nprotect += 1
            convert = rcopy(convert_p)
            with sexp_context(convert=convert):
                val = py_get_attr(obj, key)
                return sexp(val) if convert else sexp_as_py_object(val)
        finally:
            lib.Rf_unprotect(nprotect)

    def py_get_item(obj, key):
        return obj[key]

    def py_get_item2(robj, rkey):
        lib.Rf_protect(robj)
        lib.Rf_protect(rkey)
        nprotect = 2
        try:
            obj = rcopy(robj)
            key = rcopy(rkey)
            convert_p = getattrib_p(robj, "convert")
            lib.Rf_protect(convert_p)
            nprotect += 1
            convert = rcopy(convert_p)
            with sexp_context(convert=convert):
                val = py_get_item(obj, key)
                return sexp(val) if convert else sexp_as_py_object(val)
        finally:
            lib.Rf_unprotect(nprotect)

    def py_names(obj):
        try:
            return list(k for k in obj.__dict__.keys() if not k.startswith("_"))
        except Exception:
            return None

    def py_object(*args, **kwargs):
        if len(args) == 1:
            lib.Rf_protect(args[0])
            try:
                with sexp_context(**kwargs):
                    return robject("PyObject", rcopy(args[0]))
            finally:
                lib.Rf_unprotect(1)
        elif len(args) == 2:
            lib.Rf_protect(args[1])
            try:
                with sexp_context(**kwargs):
                    return robject("PyObject", rcopy(rcopy(object, args[0]), args[1]))
            finally:
                lib.Rf_unprotect(1)

    def py_print(r, **kwargs):
        rcall_p("cat", repr(r) + "\n")

    def py_set_attr(obj, key, value):
        lib.Rf_protect(obj)
        lib.Rf_protect(key)
        lib.Rf_protect(value)
        try:
            pyo = rcopy(object, obj)
            setattr(pyo, rcopy(key), rcopy(value))
        finally:
            lib.Rf_unprotect(3)
        return obj

    def py_set_item(obj, key, value):
        lib.Rf_protect(obj)
        lib.Rf_protect(key)
        lib.Rf_protect(value)
        try:
            pyo = rcopy(object, obj)
            pyo[rcopy(key)] = rcopy(value)
        finally:
            lib.Rf_unprotect(3)
        return obj

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

    # helper function
    def _rfunction(x, **kwargs):
        return robject("function", x, **kwargs)

    e = new_env(parent=lib.R_GlobalEnv)
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
            "!.PyObject"
        ]
        for thing in things:
            assign(thing, get_p(thing, e), parent_frame)

    assign("attach", robject(attach, invisible=True), e)
