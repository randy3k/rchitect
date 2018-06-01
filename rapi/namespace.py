from __future__ import unicode_literals

import tempfile
import os
from six import text_type

from .internals import R_NameSymbol, R_NamesSymbol, R_BaseNamespace, R_NamespaceRegistry
from .internals import Rf_allocMatrix, SET_STRING_ELT, Rf_mkChar, Rf_protect, Rf_unprotect
from .interface import rcopy, robject, rcall_p, rcall, reval, rsym, setattrib, invisiblize, sexp
from .types import RClass, SEXPTYPE
from .externalptr import to_pyo


def new_env(parent, hash=True):
    return rcall(("base", "new.env"), parent=parent, hash=hash)


def assign(name, value, envir):
    rcall(("base", "assign"), name, value, envir=envir)


def get_p(name, envir):
    return rcall_p(("base", "get"), name, envir=envir)


def get(name, envir):
    return rcall(("base", "get"), name, envir=envir)


def set_namespace_info(ns, which, val):
    rcall(("base", "setNamespaceInfo"), ns, which, val)


def get_namespace_info(ns, which):
    return rcall(("base", "getNamespaceInfo"), ns, which)


# mirror https://github.com/wch/r-source/blob/trunk/src/library/base/R/namespace.R
def make_namespace(name, version=None, lib=None):
    if not version:
        version = "0.0.1"
    else:
        version = text_type(version)
    if not lib:
        lib = os.path.join(tempfile.mkdtemp(), name)
        os.makedirs(lib)
        description = os.path.join(lib, "DESCRIPTION")
        with open(description, "w") as f:
            f.write("Package: {}\n".format(name))
            f.write("Version: {}\n".format(version))
    impenv = new_env(R_BaseNamespace)
    setattrib(impenv, R_NameSymbol, "imports:{}".format(name))
    env = new_env(impenv)
    info = new_env(R_BaseNamespace)
    assign(".__NAMESPACE__.", info, envir=env)
    spec = sexp([name, version])
    assign("spec", spec, envir=info)
    setattrib(spec, R_NamesSymbol, ["name", "version"])
    exportenv = new_env(R_BaseNamespace)
    set_namespace_info(env, "exports", exportenv)
    dimpenv = new_env(R_BaseNamespace)
    setattrib(dimpenv, R_NameSymbol, "lazydata:{}".format(name))
    set_namespace_info(env, "lazydata", dimpenv)
    set_namespace_info(env, "imports", {"base": True})
    set_namespace_info(env, "path", lib)
    set_namespace_info(env, "dynlibs", None)
    set_namespace_info(env, "S3methods", reval("matrix(NA_character_, 0L, 3L)"))
    s3methodstableenv = new_env(R_BaseNamespace)
    assign(".__S3MethodsTable__.", s3methodstableenv, envir=env)
    assign(name, env, envir=R_NamespaceRegistry)
    return env


def seal_namespace(ns):
    sealed = rcopy(rcall(("base", "environmentIsLocked"), ns))
    if sealed:
        name = rcopy(rcall(("base", "getNamespaceName"), ns))
        raise Exception("namespace {} is already sealed".format(name))
    rcall(("base", "lockEnvironment"), ns, True)
    parent = rcall(("base", "parent.env"), ns)
    rcall(("base", "lockEnvironment"), parent, True)


def namespace_export(ns, vs):
    rcall(rsym("base", "namespaceExport"), ns, vs)


def register_s3_methods(ns, methods):
    name = rcopy(get_namespace_info(ns, "spec"))[0]
    m = Rf_protect(Rf_allocMatrix(SEXPTYPE.STRSXP, len(methods), 3))
    for i in range(len(methods)):
        generic = methods[i][0]
        cls = methods[i][1]
        SET_STRING_ELT(m, 0 * len(methods) + i, Rf_mkChar(generic.encode("utf-8")))
        SET_STRING_ELT(m, 1 * len(methods) + i, Rf_mkChar(cls.encode("utf-8")))
        SET_STRING_ELT(m, 2 * len(methods) + i, Rf_mkChar((generic + "." + cls).encode("utf-8")))

    rcall(("base", "registerS3methods"), m, name, ns)
    Rf_unprotect(1)


def register_s3_method(pkg, generic, cls, fun):
    rcall(
        ("base", "registerS3method"),
        generic, cls, fun,
        envir=rcall(rsym("asNamespace"), pkg))


def set_hook(event, fun):
    rcall(("base", "setHook"), event, fun)


def package_event(pkg, event):
    return rcall(("base", "packageEvent"), pkg, event)


# rapi namespace

def make_py_namespace():
    # py namespace
    import rapi

    def py_import(module):
        import importlib
        i = importlib.import_module(module)
        return sexp(RClass("PyObject"), i)

    def py_call(fun, *args, **kwargs):
        ret = fun(*args, **kwargs)
        return sexp(RClass("PyObject"), ret)

    def py_copy(*args):
        return sexp(*args)

    def py_eval(code):
        return sexp(RClass("PyObject"), eval(code))

    def py_object(*args):
        if len(args) == 1:
            return sexp(RClass("PyObject"), rcopy(args[0]))
        elif len(args) == 2:
            return sexp(RClass("PyObject"), rcopy(rcopy(object, args[0]), args[1]))

    def py_print(s):
        rcall_p(rsym("cat"), repr(s) + "\n")

    def py_getattr(obj, key):
        child = getattr(obj, key)
        if callable(child):
            return sexp(RClass("PyCallable"), child)
        else:
            return sexp(RClass("PyObject"), child)

    def py_names(obj, pattern=""):
        try:
            return list(k for k in obj.__dict__.keys() if not k.startswith("_"))
        except Exception:
            return None

    ns = make_namespace("py", version=rapi.__version__)
    assign("py_import", py_import, ns)
    assign("py_call", py_call, ns)
    assign("py_copy", py_copy, ns)
    assign("py_eval", py_eval, ns)
    assign("py_object", robject(py_object, convert_args=False), ns)
    assign("names.PyObject", py_names, ns)
    assign("print.PyObject", invisiblize(py_print), ns)
    assign(".DollarNames.PyObject", py_names, ns)
    assign("$.PyObject", py_getattr, ns)
    namespace_export(ns, [
        "py_import",
        "py_call",
        "py_copy",
        "py_eval",
        "py_object"
    ])
    register_s3_methods(ns, [
        ["names", "PyObject"],
        ["print", "PyObject"],
        [".DollarNames", "PyObject"],
        ["$", "PyObject"]
    ])

    def reticulate_s3_methods(pkgname, pkgpath):
        def py_to_r(obj):
            pyobj = get_p("pyobj", obj)
            a = to_pyo(pyobj)
            return a.value

        ctypes = rcall(("reticulate", "import"), "ctypes")
        cast = rcall("$", ctypes, "cast")
        py_object = rcall("$", ctypes, "py_object")

        def r_to_py(obj):
            p = id(obj)
            addr = Rf_protect(rcall_p(("reticulate", "py_eval"), str(p), convert=False))
            ret = Rf_protect(rcall_p(("reticulate", "py_call"), cast, addr, py_object))
            value = rcall_p(("reticulate", "py_getattr"), ret, "value")
            Rf_unprotect(2)
            return value

        register_s3_method("reticulate", "py_to_r", "rapi.types.RObject", py_to_r)
        register_s3_method("reticulate", "r_to_py", "PyObject", r_to_py)

    set_hook(package_event("reticulate", "onLoad"), reticulate_s3_methods)
