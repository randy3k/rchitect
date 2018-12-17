from __future__ import unicode_literals, absolute_import

import sys
import importlib
from six import text_type
from types import ModuleType

from .internals import R_GlobalEnv, Rf_protect, Rf_unprotect
from .interface import rcopy, robject, rcall_p, rcall, rsym, setoption
from .externalptr import to_pyo


def get_p(name, envir):
    return rcall_p(("base", "get"), name, envir=envir)


def new_env(parent=R_GlobalEnv, hash=True):
    return rcall(("base", "new.env"), parent=parent, hash=hash)


def set_hook(event, fun):
    rcall(("base", "setHook"), event, fun)


def package_event(pkg, event):
    return rcall(("base", "packageEvent"), pkg, event)


def register_s3_method(generic, cls, fun, envir):
    rcall(("base", "registerS3method"), generic, cls, fun, envir)


def inject_rchitect_environment(register_s3_methods=False):

    # py namespace
    def py_import(module):
        return importlib.import_module(module)

    def py_import_builtins():
        if sys.version >= "3":
            return importlib.import_module("builtins")
        else:
            return importlib.import_module("__builtin__")

    def py_call(fun, *args, **kwargs):
        # todo: suuport .convert_args and .convert_return
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
        Rf_protect(obj)
        Rf_protect(key)
        Rf_protect(value)
        try:
            setattr(rcopy(object, obj), rcopy(key), rcopy(value))
        finally:
            Rf_unprotect(3)
        return obj

    def py_set_item(obj, key, value):
        Rf_protect(obj)
        Rf_protect(key)
        Rf_protect(value)
        try:
            rcopy(object, obj)[rcopy(key)] = rcopy(value)
        finally:
            Rf_unprotect(3)
        return obj

    def py_dict(**kwargs):
        narg = len(kwargs)
        for key in kwargs:
            Rf_protect(kwargs[key])
        try:
            return {key: rcopy(kwargs[key]) for key in kwargs}
        finally:
            Rf_unprotect(narg)

    def py_tuple(*args):
        narg = len(args)
        for a in args:
            Rf_protect(a)
        try:
            return tuple([rcopy(a) for a in args])
        finally:
            Rf_unprotect(narg)

    def py_unicode(obj):
        return text_type(obj)

    def assign(name, value, envir):
        rcall(("base", "assign"), name, value, envir=envir)

    e = new_env()
    setoption("rchitect_environment", e)

    assign("import", py_import, e)
    assign("import_builtins", py_import_builtins, e)
    assign("py_call", py_call, e)
    assign("py_copy", robject(py_copy, convert_return=True), e)
    assign("py_eval", py_eval, e)
    assign("py_get_attr", py_get_attr, e)
    assign("py_get_item", py_get_item, e)
    assign("py_object", robject(py_object, convert_args=False), e)
    assign("py_set_attr", robject(py_set_attr, convert_args=False), e)
    assign("py_set_item", robject(py_set_item, convert_args=False), e)
    assign("py_unicode", py_unicode, e)
    assign("dict", robject(py_dict, convert_args=False), e)
    assign("tuple", robject(py_tuple, convert_args=False), e)
    assign("names.PyObject", robject(py_names, convert_return=True), e)
    assign("print.PyObject", robject(py_print, invisible=True), e)
    assign(".DollarNames.PyObject", robject(py_names, convert_return=True), e)
    assign("$.PyObject", robject(py_get_attr, convert_return=True), e)
    assign("[.PyObject", robject(py_get_item, convert_return=True), e)
    assign("$<-.PyObject", robject(py_set_attr, convert_args=False), e)
    assign("[<-.PyObject", robject(py_set_item, convert_args=False), e)

    def register():
        register_s3_method("names", "PyObject", get_p("names.PyObject", e), e)
        register_s3_method("print", "PyObject", get_p("print.PyObject", e), e)
        register_s3_method(".DollarNames", "PyObject", get_p(".DollarNames.PyObject", e), e)
        register_s3_method("$", "PyObject", get_p("$.PyObject", e), e)
        register_s3_method("[", "PyObject", get_p("[.PyObject", e), e)
        register_s3_method("$<-", "PyObject", get_p("$<-.PyObject", e), e)
        register_s3_method("[<-", "PyObject", get_p("[<-.PyObject", e), e)

    assign("register", robject(register, invisible=True), e)
    if register_s3_methods:
        register()


def register_reticulate_s3_methods():
    def py_to_r(obj):
        pyobj = get_p("pyobj", obj)
        a = to_pyo(pyobj)
        return a.value

    def r_to_py(obj):
        ctypes = rcall(("reticulate", "import"), "ctypes")
        cast = rcall("$", ctypes, "cast")
        py_object = rcall("$", ctypes, "py_object")
        p = id(obj)
        addr = Rf_protect(rcall_p(("reticulate", "py_eval"), str(p), convert=False))
        ret = Rf_protect(rcall_p(("reticulate", "py_call"), cast, addr, py_object))
        value = rcall_p(("reticulate", "py_get_attr"), ret, "value")
        Rf_unprotect(2)
        return value

    reticulatens = rcall(rsym("asNamespace"), "reticulate")
    register_s3_method(
        "py_to_r", "rchitect.types.RObject",
        robject(py_to_r, convert_args=False, convert_return=True),
        reticulatens)
    register_s3_method(
        "r_to_py", "PyObject",
        robject(r_to_py, convert_args=True, convert_return=True),
        reticulatens)


def set_hook_for_reticulate():

    if "reticulate" in rcopy(rcall(("base", "loadedNamespaces"))):
        register_reticulate_s3_methods()
    else:
        set_hook(
            package_event("reticulate", "onLoad"),
            lambda x, y: register_reticulate_s3_methods()
        )
