from six import text_type

from .internals import Rf_protect, Rf_unprotect, Rf_setAttrib
from .internals import R_NameSymbol, R_NamesSymbol, R_BaseNamespace, R_NamespaceRegistry
from .interface import rcall_p, reval_p, rsym_p, rstring_p, sexp


def new_env_p(parent, hash=True):
    return rcall_p(rsym_p("base", "new.env"), parent=parent, hash=hash)


def assign(name, value, envir):
    rcall_p(rsym_p("base", "assign"), name, value, envir=envir)


def set_namespace_info(ns, which, val):
    rcall_p(rsym_p("base", "setNamespaceInfo"), ns, which, val)


# mirror https://github.com/wch/r-source/blob/trunk/src/library/base/R/namespace.R
def make_namespace(name, version=None, lib=None):
    nprotect = 0
    try:
        version = text_type(version) if version else None
        impenv = Rf_protect(new_env_p(R_BaseNamespace))
        nprotect = nprotect + 1
        Rf_setAttrib(impenv, R_NameSymbol, rstring_p("imports:{}".format(name)))
        env = Rf_protect(new_env_p(impenv))
        nprotect = nprotect + 1
        info = Rf_protect(new_env_p(R_BaseNamespace))
        nprotect = nprotect + 1
        assign(".__NAMESPACE__.", info, envir=env)
        spec = Rf_protect(sexp([name, version] if version else name))
        nprotect = nprotect + 1
        Rf_setAttrib(spec, R_NamesSymbol, sexp(["name", "version"] if version else name))
        assign("spec", spec, envir=info)
        exportenv = Rf_protect(new_env_p(R_BaseNamespace))
        nprotect = nprotect + 1
        set_namespace_info(env, "exports", exportenv)
        dimpenv = Rf_protect(new_env_p(R_BaseNamespace))
        nprotect = nprotect + 1
        Rf_setAttrib(dimpenv, R_NameSymbol, rstring_p("lazydata:{}".format(name)))
        set_namespace_info(env, "lazydata", dimpenv)
        set_namespace_info(env, "imports", {"base": True})
        set_namespace_info(env, "path", lib)
        set_namespace_info(env, "dynlibs", None)
        set_namespace_info(env, "S3methods", reval_p("matrix(NA_character_, 0L, 3L)"))
        s3methodstableenv = Rf_protect(new_env_p(R_BaseNamespace))
        nprotect = nprotect + 1
        assign(".__S3MethodsTable__.", s3methodstableenv, envir=env)
        assign(name, env, envir=R_NamespaceRegistry)
    finally:
        Rf_unprotect(nprotect)
    return env
