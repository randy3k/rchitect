import sys
from ctypes import py_object, byref, cast, c_void_p, c_int
from ctypes import CFUNCTYPE, Structure, POINTER
from collections import OrderedDict
from six import text_type

from .internals import Rf_protect, Rf_unprotect, Rf_error, R_NilValue, R_GlobalEnv
from .internals import R_ToplevelExec
from .internals import R_ParseVector, Rf_eval
from .internals import Rf_PrintValue
from .internals import Rf_allocVector, SETCAR, CDR, SET_TAG, Rf_install, Rf_mkString
from .internals import LENGTH, TYPEOF, LANGSXP
# from .internals import INTSXP, LGLSXP, REALSXP, CHARSXP, CPLXSXP, RAWSXP, STRSXP, VECSXP
from .internals import INTEGER, LOGICAL, REAL, CHAR, COMPLEX, RAW, STRING_ELT, VECTOR_ELT
from .internals import Rf_GetOption1, Rf_ScalarLogical, Rf_ScalarInteger, Rf_ScalarReal
from .internals import R_data_class
from .internals import R_NamesSymbol, Rf_getAttrib, Rf_isNull
from .internals import R_InputHandlers, R_ProcessEvents, R_checkActivity, R_runHandlers


from .types import SEXP, RObject, SEXPTYPE, SEXPCLASS
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
        Rf_error(("{}: {}".format(type(e).__name__, str(e))).encode())


protectedEval_t = CFUNCTYPE(None, c_void_p)(protectedEval)


def rexec_p(func, *data):
    ret = [None]
    pdata = ProtectedEvalData(py_object(func), py_object(data), py_object(ret))
    if R_ToplevelExec(protectedEval_t, byref(pdata)) == 0:
        raise RuntimeError("rexec encountered an error")
    return sexp(pdata.ret[0])


def rexec(*args, **kwargs):
    ret = rexec_p(*args, **kwargs)
    if isinstance(ret, SEXP):
        ret = RObject(ret)
    return ret


def rparse_p(string):
    buf = string.encode()
    status = c_int()
    s = Rf_protect(Rf_mkString(buf))
    try:
        ret = rexec_p(R_ParseVector, s, -1, status, R_NilValue)
    finally:
        Rf_unprotect(1)
    if status.value != 1:
        raise RuntimeError("rparse error")
    return sexp(ret)


def rparse(*args, **kwargs):
    return RObject(rparse_p(*args, **kwargs))


def reval_p(string, env=R_GlobalEnv):
    expressions = Rf_protect(rparse_p(string))
    ret = R_NilValue
    try:
        for i in range(0, LENGTH(expressions)):
            ret = rexec_p(Rf_eval, VECTOR_ELT(expressions, i), env)
    finally:
        Rf_unprotect(1)
    return sexp(ret)


def reval(*args, **kwargs):
    return RObject(reval_p(*args, **kwargs))


def rlang_p(*args, **kwargs):
    nargs = len(args) + len(kwargs)
    t = Rf_protect(Rf_allocVector(LANGSXP, nargs))
    s = t
    SETCAR(s, args[0])
    for a in args[1:]:
        s = CDR(s)
        SETCAR(s, a)
    for k, v in kwargs.items():
        s = CDR(s)
        SETCAR(s, v)
        SET_TAG(s, Rf_install(k.encode()))
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
        return Rf_install(s.encode())


def rsym(s, t=None):
    if t:
        return rlang_p(rsym_p("::"), rsym_p(s), rsym_p(t))
    else:
        return Rf_install(s.encode())


def rstring_p(s):
    return sexp(Rf_mkString(s.encode()))


def rstring(s):
    return RObject(rstring_p(s))


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
    return RObject(rdouble_p(s))


def rprint(s):
    Rf_protect(s)
    try:
        rexec_p(Rf_PrintValue, s)
    finally:
        Rf_unprotect(1)


def rclass_p(s, singleString=0):
    return sexp(R_data_class(s, singleString))


def rclass(s, singleString=0):
    return RObject(rclass_p(s, singleString))


def rname_p(s):
    return sexp(Rf_getAttrib(s, R_NamesSymbol))


def rname(s):
    return RObject(rname_p(s))


# conversion dispatches

@dispatch(object, SEXPCLASS(SEXPTYPE.NILSXP))
def rcopy(_, s):
    return None


@dispatch(Type(int), SEXPCLASS(SEXPTYPE.INTSXP))
def rcopy(_, s):
    return INTEGER(s)[0]


@dispatch(Type(list), SEXPCLASS(SEXPTYPE.INTSXP))
def rcopy(_, s):
    return [INTEGER(s)[i] for i in range(LENGTH(s))]


@dispatch(Type(bool), SEXPCLASS(SEXPTYPE.LGLSXP))
def rcopy(_, s):
    return bool(LOGICAL(s)[0])


@dispatch(Type(list), SEXPCLASS(SEXPTYPE.LGLSXP))
def rcopy(_, s):
    return [bool(LOGICAL(s)[i]) for i in range(LENGTH(s))]


@dispatch(Type(float), SEXPCLASS(SEXPTYPE.REALSXP))
def rcopy(_, s):
    return REAL(s)[0]


@dispatch(Type(list), SEXPCLASS(SEXPTYPE.REALSXP))
def rcopy(_, s):
    return [REAL(s)[i] for i in range(LENGTH(s))]


@dispatch(Type(complex), SEXPCLASS(SEXPTYPE.CPLXSXP))
def rcopy(_, s):
    z = COMPLEX(s)[0]
    return complex(z.r, z.i)


@dispatch(Type(list), SEXPCLASS(SEXPTYPE.CPLXSXP))
def rcopy(_, s):
    return [complex(COMPLEX(s)[i].r, COMPLEX(s)[i].i) for i in range(LENGTH(s))]


@dispatch(Type(bytes), SEXPCLASS(SEXPTYPE.RAWSXP))
def rcopy(_, s):
    return RAW(s)


@dispatch(Type(text_type), SEXPCLASS(SEXPTYPE.STRSXP))
def rcopy(_, s):
    return CHAR(STRING_ELT(s, 0)).decode()


@dispatch(Type(list), SEXPCLASS(SEXPTYPE.STRSXP))
def rcopy(_, s):
    return [CHAR(STRING_ELT(s, i)).decode() for i in range(LENGTH(s))]


@dispatch(Type(list), SEXPCLASS(SEXPTYPE.VECSXP))
def rcopy(_, s):
    return [rcopy(VECTOR_ELT(s, i)) for i in range(LENGTH(s))]


@dispatch(Type(OrderedDict), SEXPCLASS(SEXPTYPE.VECSXP))
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

@dispatch(object, SEXPCLASS(SEXPTYPE.INTSXP))
def rcopytype(_, s):
    return int if LENGTH(s) == 1 else list


@dispatch(object, SEXPCLASS(SEXPTYPE.LGLSXP))
def rcopytype(_, s):
    return bool if LENGTH(s) == 1 else list


@dispatch(object, SEXPCLASS(SEXPTYPE.REALSXP))
def rcopytype(_, s):
    return float if LENGTH(s) == 1 else list


@dispatch(object, SEXPCLASS(SEXPTYPE.CPLXSXP))
def rcopytype(_, s):
    return complex if LENGTH(s) == 1 else list


@dispatch(object, SEXPCLASS(SEXPTYPE.RAWSXP))
def rcopytype(_, s):
    return bytes


@dispatch(object, SEXPCLASS(SEXPTYPE.STRSXP))
def rcopytype(_, s):
    return text_type if LENGTH(s) == 1 else list


@dispatch(object, SEXPCLASS(SEXPTYPE.VECSXP))
def rcopytype(_, s):
    return list if Rf_isNull(rname_p(s)) else OrderedDict


@dispatch(object, SEXP)
def rcopytype(_, s):
    return object


# Generic behavior

class RClass(object):
    _instances = {}

    def __new__(cls, rcls):
        if rcls in cls._instances:
            return cls._instances[rcls]
        else:
            T = type(
                "RClass(\'{}\')".format(rcls),
                (type,),
                {"__new__": lambda cls: None})
            cls._instances[rcls] = T
        return T



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


@dispatch(SEXP)
def sexp(s):
    return cast(s, SEXPCLASS(TYPEOF(s)))


@dispatch(object)
def sexp(s):
    return s


def get_option(key, default=None):
    ret = rcopy(Rf_GetOption1(Rf_install(key.encode())))
    if ret is None:
        return default
    else:
        return ret


def set_option(key, value):
    kwargs = {}
    if isinstance(value, text_type):
        kwargs[key] = rstring(value)
    elif isinstance(value, bool):
        kwargs[key] = rlogical(int(value))
    elif isinstance(value, int):
        kwargs[key] = rint(value)
    elif isinstance(value, float):
        kwargs[key] = rdouble(value)
    else:
        TypeError("value type is not supported")

    rcall_p(rsym("base", "options"), **kwargs)


def process_events():
    if sys.platform == "win32" or sys.platform == "darwin":
        R_ProcessEvents()
    if sys.platform.startswith("linux") or sys.platform == "darwin":
        what = R_checkActivity(0, 1)
        if what:
            R_runHandlers(R_InputHandlers, what)
