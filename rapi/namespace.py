import tempfile
import os
from six import text_type

from .internals import R_NameSymbol, R_NamesSymbol, R_BaseNamespace, R_NamespaceRegistry
from .interface import rtopy, rcall, reval, rsym, setattrib, sexp


def new_env(parent, hash=True):
    return rcall(rsym("base", "new.env"), parent=parent, hash=hash)


def assign(name, value, envir):
    rcall(rsym("base", "assign"), name, value, envir=envir)


def get(name, envir):
    rcall(rsym("base", "get"), name, envir=envir)


def set_namespace_info(ns, which, val):
    rcall(rsym("base", "setNamespaceInfo"), ns, which, val)


# mirror https://github.com/wch/r-source/blob/trunk/src/library/base/R/namespace.R
def make_namespace(name, version=None, lib=None):
    if not version:
        version = "0.0.1"
    else:
        version = text_type(version)
    if not lib:
        lib = os.path.join(tempfile.TemporaryDirectory().name, name)
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
    sealed = rtopy(rcall(rsym("base", "environmentIsLocked"), ns))
    if sealed:
        name = rtopy(rcall(rsym("base", "getNamespaceName"), ns))
        raise Exception("namespace {} is already sealed".format(name))
    rcall(rsym("base", "lockEnvironment"), ns, True)
    parent = rcall(rsym("base", "parent.env"), ns)
    rcall(rsym("base", "lockEnvironment"), parent, True)


def namespace_export(ns, vs):
    rcall(rsym("base", "namespaceExport"), ns, vs)
