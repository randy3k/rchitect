from __future__ import unicode_literals
from rchitect._libR import ffi, lib
from .dispatch import dispatch
from .types import RObject, SEXP, EXPRSXP, sexptype, datatype

from contextlib import contextmanager
from six import string_types


dispatch.add_dispatch_policy(type, datatype)
dispatch.add_dispatch_policy(
    ffi.CData,
    lambda x: sexptype(x) if ffi.typeof(x) == ffi.typeof('SEXP') else ffi.CData)


@contextmanager
def protected(*args):
    nprotect = 0
    for a in args:
        if isinstance(a, SEXP):
            lib.Rf_protect(a)
            nprotect += 1
    try:
        yield
    finally:
        lib.Rf_unprotect(nprotect)


def box(x):
    if isinstance(x, SEXP):
        return RObject(x)
    elif isinstance(x, RObject):
        return x

    raise TypeError("expect SEXP or RObject")


def unbox(x):
    if isinstance(x, RObject):
        return x.s
    elif isinstance(x, SEXP):
        return x

    raise TypeError("expect SEXP or RObject")


def rint_p(s):
    return lib.Rf_ScalarInteger(s)


def rint(s):
    return box(rint_p(s))


def rlogical_p(s):
    return lib.Rf_ScalarLogical(s)


def rlogical(s):
    return box(rlogical_p(s))


def rdouble_p(s):
    return lib.Rf_ScalarReal(s)


def rdouble(s):
    return box(rdouble_p(s))


def rchar_p(s):
    isascii = all(ord(c) < 128 for c in s)
    b = s.encode("utf-8")
    return lib.Rf_mkCharLenCE(b, len(b), lib.CE_NATIVE if isascii else lib.CE_UTF8)


def rchar(s):
    return box(rchar_p(s))


def rstring_p(s):
    return lib.Rf_ScalarString(rchar_p(s))


def rstring(s):
    return box(rstring_p(s))


def rsym_p(s, t=None):
    if t:
        return rlang_p("::", rsym_p(s), rsym_p(t))
    else:
        return lib.Rf_install(s.encode("utf-8"))


def rsym(s, t=None):
    return box(rsym_p(s, t))


def rparse_p(s):
    status = ffi.new("ParseStatus[1]")
    s = rstring_p(s)
    with protected(s):
        ret = lib.R_ParseVector(s, -1, status, lib.R_NilValue)
        if status[0] != lib.PARSE_OK:
            raise Exception("Parse error")
    return ret


def rparse(s):
    return box(rparse_p(s))


@dispatch(EXPRSXP)
def reval_p(s):
    ret = lib.R_NilValue
    status = ffi.new("int[1]")
    with protected(s):
        for i in range(0, lib.Rf_length(s)):
            ret = lib.R_tryEval(lib.VECTOR_ELT(s, i), lib.R_GlobalEnv, status)
            if status[0] != 0:
                raise RuntimeError("reval error")
    return ret


@dispatch(RObject)  # noqa
def reval_p(s):
    return reval_p(unbox(s))


@dispatch(string_types)  # noqa
def reval_p(s):
    return reval_p(rparse_p(s))


def reval(s):
    return box(reval_p(s))


def as_call(x):
    if isinstance(x, SEXP):
        return x
    elif isinstance(x, RObject):
        return unbox(x)
    elif isinstance(x, string_types):
        return rsym_p(x)
    elif isinstance(x, tuple) and len(x) == 2:
        return rsym_p(*x)

    raise TypeError("unexpected function")


def rlang_p(*args, **kwargs):
    with protected(*args, *(kwargs.items())):
        nargs = len(args) + len(kwargs)
        t = lib.Rf_allocVector(lib.LANGSXP, nargs)
        with protected(t):
            s = t
            lib.SETCAR(s, as_call(args[0]))

            for a in args[1:]:
                s = lib.CDR(s)
                lib.SETCAR(s, unbox(a))
            for k, v in kwargs.items():
                s = lib.CDR(s)
                lib.SETCAR(s, unbox(v))
                lib.SET_TAG(s, lib.Rf_install(k.encode("utf-8")))

            ret = t
    return ret


def rlang(*args, **kwargs):
    return box(rlang_p(*args, **kwargs))


def rcall_p(*args, _envir=None, **kwargs):
    if _envir:
        _envir = unbox(_envir)
    else:
        _envir = lib.R_GlobalEnv
    with protected(_envir):
        status = ffi.new("int[1]")
        val = lib.R_tryEval(rlang_p(*args, **kwargs), _envir, status)
        if status[0] != 0:
            raise RuntimeError("rcall error.")

    return val


def rcall(*args, **kwargs):
    return RObject(rcall_p(*args, **kwargs))


@dispatch(SEXP)
def rprint(s):
    new_env = rcall("new.env")
    lib.Rf_defineVar(rsym_p("x"), unbox(s), unbox(new_env))
    with protected(s):
        try:
            rcall(("base", "print"), rsym("x"), _envir=new_env)
        finally:
            lib.Rf_defineVar(rsym_p("x"), lib.R_NilValue, unbox(new_env))


@dispatch(RObject)  # noqa
def rprint(x):
    rprint(unbox(x))


# R to Py

@dispatch(RObject)
def robject(x):
    return x


@dispatch(SEXP)  # noqa
def robject(x):
    return RObject(x)


# Py to R

@dispatch(SEXP)
def sexp(x):
    return x


@dispatch(RObject)  # noqa
def sexp(x):
    return x.s
