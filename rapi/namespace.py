from six import text_type

from .internals import R_NameSymbol, R_NamesSymbol, R_BaseNamespace, R_NamespaceRegistry
from .interface import rcopy, rcall, reval, rsym, setattrib, sexp


def new_env(parent, hash=True):
    return rcall(rsym("base", "new.env"), parent=parent, hash=hash)


def assign(name, value, envir):
    rcall(rsym("base", "assign"), name, value, envir=envir)


def set_namespace_info(ns, which, val):
    rcall(rsym("base", "setNamespaceInfo"), ns, which, val)


# mirror https://github.com/wch/r-source/blob/trunk/src/library/base/R/namespace.R
def make_namespace(name, version=None, lib=None):
    version = text_type(version) if version else None
    impenv = new_env(R_BaseNamespace)
    setattrib(impenv, R_NameSymbol, "imports:{}".format(name))
    env = new_env(impenv)
    info = new_env(R_BaseNamespace)
    assign(".__NAMESPACE__.", info, envir=env)
    spec = sexp([name, version] if version else name)
    assign("spec", spec, envir=info)
    setattrib(spec, R_NamesSymbol, ["name", "version"] if version else "name")
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
    sealed = rcopy(rcall(rsym("base", "environmentIsLocked"), ns))
    if sealed:
        name = rcopy(rcall(rsym("base", "getNamespaceName"), ns))
        raise Exception("namespace {} is already sealed".format(name))
    rcall(rsym("base", "lockEnvironment"), ns, True)
    parent = rcall(rsym("base", "parent.env"), ns)
    rcall(rsym("base", "lockEnvironment"), parent, True)
