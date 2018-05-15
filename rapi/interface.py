from __future__ import unicode_literals

import sys
from ctypes import py_object, byref, cast, c_void_p, c_int
from ctypes import CFUNCTYPE, Structure, POINTER, string_at
from collections import OrderedDict
from six import text_type

from .internals import Rf_protect, Rf_unprotect, Rf_error, R_NilValue, R_GlobalEnv
from .internals import R_ToplevelExec
from .internals import R_ParseVector, Rf_eval
from .internals import Rf_PrintValue
from .internals import Rf_allocVector, SETCAR, CDR, SET_TAG, Rf_install
from .internals import LENGTH, TYPEOF, LANGSXP
from .internals import INTSXP, LGLSXP, REALSXP, CPLXSXP, RAWSXP, STRSXP, VECSXP
from .internals import INTEGER, LOGICAL, REAL, CHAR, COMPLEX, RAW, STRING_ELT, VECTOR_ELT
from .internals import Rf_GetOption1
from .internals import Rf_ScalarLogical, Rf_ScalarInteger, Rf_ScalarReal, Rf_ScalarComplex
from .internals import Rf_ScalarString, R_data_class
from .internals import R_NamesSymbol, Rf_getAttrib, Rf_isNull
from .internals import R_InputHandlers, R_ProcessEvents, R_checkActivity, R_runHandlers
from .internals import SET_STRING_ELT, SET_VECTOR_ELT, Rf_mkCharLenCE


from .types import SEXP, RObject, RClass, SEXPTYPE, sexptype, Rcomplex
from .dispatch import dispatch, Type


__all__ = [
    "rexec",
    "rparse",
    "reval",
    "rprint",
    "rlang",
    "rcall",
    "rsym",
    "rstring",
    "rclass",
    "rname",
    "rcopy"
]


class ProtectedEvalData(Structure):
    _fields_ = [
        ('func', py_object),
        ('data', py_object),
        ('ret', py_object)
    ]


def protectedEval(pdata_t):
    pdata = cast(pdata_t, POINTER(ProtectedEvalData)).contents
    func = pdata.func
    data = pdata.data
    try:
        pdata.ret[0] = func(*data)
    except Exception as e:
        Rf_error(("{}: {}".format(type(e).__name__, str(e))).encode('utf-8'))


protectedEval_t = CFUNCTYPE(None, c_void_p)(protectedEval)


def rexec_p(func, *data):
    ret = [None]
    pdata = ProtectedEvalData(py_object(func), py_object(data), py_object(ret))
    if R_ToplevelExec(protectedEval_t, byref(pdata)) == 0:
        raise RuntimeError("rexec encountered an error")
    return sexp(pdata.ret[0])


def rexec(func, *data):
    ret = rexec_p(func, *data)
    if isinstance(ret, SEXP):
        ret = RObject(ret)
    return ret


def rparse_p(string):
    status = c_int()
    s = Rf_protect(rstring_p(string))
    try:
        ret = rexec_p(R_ParseVector, s, -1, status, R_NilValue)
    finally:
        Rf_unprotect(1)
    if status.value != 1:
        raise RuntimeError("rparse error")
    return sexp(ret)


def rparse(string):
    return RObject(rparse_p(string))


def reval_p(string, env=R_GlobalEnv):
    expressions = Rf_protect(rparse_p(string))
    ret = R_NilValue
    try:
        for i in range(0, LENGTH(expressions)):
            ret = rexec_p(Rf_eval, VECTOR_ELT(expressions, i), env)
    finally:
        Rf_unprotect(1)
    return sexp(ret)


def reval(string, env=R_GlobalEnv):
    return RObject(reval_p(string, env=R_GlobalEnv))


def rlang_p(*args, **kwargs):
    nargs = len(args) + len(kwargs)
    t = Rf_protect(Rf_allocVector(LANGSXP, nargs))
    s = t
    SETCAR(s, sexp(args[0]))
    for a in args[1:]:
        s = CDR(s)
        SETCAR(s, sexp(a))
    for k, v in kwargs.items():
        s = CDR(s)
        SETCAR(s, sexp(v))
        SET_TAG(s, Rf_install(k.encode('utf-8')))
    Rf_unprotect(1)
    return sexp(t)


def rlang(*args, **kwargs):
    return RObject(rlang_p(*args, **kwargs))


def rcall_p(*args, **kwargs):
    return rexec_p(Rf_eval, rlang_p(*args, **kwargs), R_GlobalEnv)


def rcall(*args, **kwargs):
    return RObject(rcall_p(*args, **kwargs))


def rsym_p(s, t=None):
    if t:
        return rlang(rsym_p("::"), rsym_p(s), rsym_p(t))
    else:
        return Rf_install(s.encode('utf-8'))


def rsym(s, t=None):
    if t:
        return rlang_p(rsym_p("::"), rsym_p(s), rsym_p(t))
    else:
        return Rf_install(s.encode('utf-8'))


def rint_p(s):
    return sexp(Rf_ScalarInteger(s))


def rint(s):
    return RObject(rint_p(s))


def rlogical_p(s):
    return sexp(Rf_ScalarLogical(s))


def rlogical(s):
    return RObject(rlogical_p(s))


def rdouble_p(s):
    return sexp(Rf_ScalarReal(s))


def rdouble(s):
    return RObject(sexp(s))


def rstring_p(s):
    isascii = all(ord(c) < 128 for c in s)
    b = s.encode('utf-8')
    return sexp(Rf_ScalarString(Rf_mkCharLenCE(b, len(b), 0 if isascii else 0)))


def rstring(s):
    return RObject(rstring_p(s))


def rprint(s):
    s = sexp(s)
    Rf_protect(s)
    try:
        rexec_p(Rf_PrintValue, s)
    finally:
        Rf_unprotect(1)


def rclass_p(s, singleString=0):
    return sexp(R_data_class(sexp(s), singleString))


def rclass(s, singleString=0):
    return RObject(rclass_p(s, singleString))


def rname_p(s):
    return sexp(Rf_getAttrib(sexp(s), R_NamesSymbol))


def rname(s):
    return RObject(rname_p(s))


# conversion dispatches

@dispatch(object, sexptype(SEXPTYPE.NILSXP))
def rcopy(_, s):
    return None


@dispatch(Type(int), sexptype(SEXPTYPE.INTSXP))
def rcopy(_, s):
    return INTEGER(s)[0]


@dispatch(Type(list), sexptype(SEXPTYPE.INTSXP))
def rcopy(_, s):
    return [INTEGER(s)[i] for i in range(LENGTH(s))]


@dispatch(Type(bool), sexptype(SEXPTYPE.LGLSXP))
def rcopy(_, s):
    return bool(LOGICAL(s)[0])


@dispatch(Type(list), sexptype(SEXPTYPE.LGLSXP))
def rcopy(_, s):
    return [bool(LOGICAL(s)[i]) for i in range(LENGTH(s))]


@dispatch(Type(float), sexptype(SEXPTYPE.REALSXP))
def rcopy(_, s):
    return REAL(s)[0]


@dispatch(Type(list), sexptype(SEXPTYPE.REALSXP))
def rcopy(_, s):
    return [REAL(s)[i] for i in range(LENGTH(s))]


@dispatch(Type(complex), sexptype(SEXPTYPE.CPLXSXP))
def rcopy(_, s):
    z = COMPLEX(s)[0]
    return complex(z.r, z.i)


@dispatch(Type(list), sexptype(SEXPTYPE.CPLXSXP))
def rcopy(_, s):
    return [complex(COMPLEX(s)[i].r, COMPLEX(s)[i].i) for i in range(LENGTH(s))]


@dispatch(Type(bytes), sexptype(SEXPTYPE.RAWSXP))
def rcopy(_, s):
    return string_at(RAW(s), LENGTH(s))


@dispatch(Type(text_type), sexptype(SEXPTYPE.STRSXP))
def rcopy(_, s):
    return CHAR(STRING_ELT(s, 0)).decode("utf-8")


@dispatch(Type(list), sexptype(SEXPTYPE.STRSXP))
def rcopy(_, s):
    return [CHAR(STRING_ELT(s, i)).decode("utf-8") for i in range(LENGTH(s))]


@dispatch(Type(list), sexptype(SEXPTYPE.VECSXP))
def rcopy(_, s):
    return [rcopy(VECTOR_ELT(s, i)) for i in range(LENGTH(s))]


@dispatch(Type(OrderedDict), sexptype(SEXPTYPE.VECSXP))
def rcopy(_, s):
    ret = OrderedDict()
    names = rcopy(list, rname_p(s))
    for i in range(LENGTH(s)):
        ret[names[i]] = rcopy(VECTOR_ELT(s, i))
    return ret


@dispatch(object, SEXP)
def rcopy(_, s):
    return s


# default conversion

@dispatch(object, sexptype(SEXPTYPE.INTSXP))
def rcopytype(_, s):
    return int if LENGTH(s) == 1 else list


@dispatch(object, sexptype(SEXPTYPE.LGLSXP))
def rcopytype(_, s):
    return bool if LENGTH(s) == 1 else list


@dispatch(object, sexptype(SEXPTYPE.REALSXP))
def rcopytype(_, s):
    return float if LENGTH(s) == 1 else list


@dispatch(object, sexptype(SEXPTYPE.CPLXSXP))
def rcopytype(_, s):
    return complex if LENGTH(s) == 1 else list


@dispatch(object, sexptype(SEXPTYPE.RAWSXP))
def rcopytype(_, s):
    return bytes


@dispatch(object, sexptype(SEXPTYPE.STRSXP))
def rcopytype(_, s):
    return text_type if LENGTH(s) == 1 else list


@dispatch(object, sexptype(SEXPTYPE.VECSXP))
def rcopytype(_, s):
    return list if Rf_isNull(rname_p(s)) else OrderedDict


@dispatch(object, SEXP)
def rcopytype(_, s):
    return object


@dispatch(SEXP)
def rcopy(s):
    s = sexp(s)
    T = rcopytype(RClass(rcopy(text_type, rclass_p(s, 1))), s)
    return rcopy(T, s)


@dispatch(object, RObject)
def rcopy(t, r):
    return rcopy(t, sexp(r))


@dispatch(RObject)
def rcopy(r):
    r = sexp(r)
    T = rcopytype(RClass(rcopy(text_type, rclass_p(r, 1))), r)
    return rcopy(T, r)


@dispatch(object)
def rcopy(r):
    return r


@dispatch(int)
def sexp(s):
    return rint_p(s)


@dispatch(float)
def sexp(s):
    return rdouble_p(s)


@dispatch(bool)
def sexp(s):
    return rlogical_p(s)


@dispatch(complex)
def sexp(s):
    return sexp(Rf_ScalarComplex(Rcomplex(r=s.real, i=s.imag)))


@dispatch(text_type)
def sexp(s):
    return rstring_p(s)


@dispatch(bytes)
def sexp(s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(RAWSXP, n))
    try:
        for i in range(n):
            RAW(x)[i] = s[i]
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(Type(RClass("integer")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(INTSXP, n))
    try:
        for i in range(n):
            INTEGER(x)[i] = s[i]
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(Type(RClass("logical")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(LGLSXP, n))
    try:
        for i in range(n):
            LOGICAL(x)[i] = s[i]
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(Type(RClass("numeric")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(REALSXP, n))
    try:
        for i in range(n):
            REAL(x)[i] = s[i]
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(Type(RClass("complex")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(CPLXSXP, n))
    try:
        for i in range(n):
            xi = COMPLEX(x)[i]
            z = s[i]
            xi.r = z.real
            xi.i = z.imag
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(Type(RClass("character")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(STRSXP, n))
    try:
        for i in range(n):
            isascii = all(ord(c) < 128 for c in s[i])
            b = s[i].encode('utf-8')
            SET_STRING_ELT(x, i, Rf_mkCharLenCE(b, len(b), 0 if isascii else 1))
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(Type(RClass("list")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(VECSXP, n))
    try:
        for i in range(n):
            SET_VECTOR_ELT(x, i, sexp(s[i]))
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(list)
def sexp(s):
    if all(isinstance(x, int) for x in s):
        x = sexp(RClass("integer"), s)
    elif all(isinstance(x, bool) for x in s):
        x = sexp(RClass("logical"), s)
    elif all(isinstance(x, float) for x in s):
        x = sexp(RClass("numeric"), s)
    elif all(isinstance(x, complex) for x in s):
        x = sexp(RClass("complex"), s)
    elif all(isinstance(x, text_type) for x in s):
        x = sexp(RClass("character"), s)
    else:
        x = sexp(RClass("list"), s)
    return x


@dispatch(SEXP)
def sexp(s):
    return cast(s, sexptype(TYPEOF(s)))


@dispatch(RObject)
def sexp(r):
    return r.p


@dispatch(object)
def sexp(s):
    return s


def get_option(key, default=None):
    ret = rcopy(Rf_GetOption1(Rf_install(key.encode('utf-8'))))
    if ret is None:
        return default
    else:
        return ret


def set_option(key, value):
    kwargs = {}
    kwargs[key] = Rf_protect(sexp(value))
    try:
        rcall_p(rsym("base", "options"), **kwargs)
    finally:
        Rf_unprotect(1)


def _process_events():
    if sys.platform == "win32" or sys.platform == "darwin":
        R_ProcessEvents()
    if sys.platform.startswith("linux") or sys.platform == "darwin":
        what = R_checkActivity(0, 1)
        if what:
            R_runHandlers(R_InputHandlers, what)


def process_events():
    rexec(_process_events)
