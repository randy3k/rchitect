from ctypes import py_object, byref, cast, c_void_p, c_int
from ctypes import CFUNCTYPE, Structure, POINTER
from collections import OrderedDict
from six import text_type

from .internals import Rf_protect, Rf_unprotect, Rf_error, R_NilValue, R_GlobalEnv
from .internals import R_ToplevelExec
from .internals import R_ParseVector, R_tryEval
from .internals import Rf_PrintValue
from .internals import Rf_allocVector, SETCAR, CDR, SET_TAG, Rf_install, Rf_mkString
from .internals import LENGTH, TYPEOF, LANGSXP
from .internals import INTSXP, LGLSXP, REALSXP, CHARSXP, CPLXSXP, RAWSXP, STRSXP, VECSXP
from .internals import INTEGER, LOGICAL, REAL, CHAR, COMPLEX, RAW, STRING_ELT, VECTOR_ELT
from .internals import Rf_GetOption1, Rf_ScalarLogical, Rf_ScalarInteger, Rf_ScalarReal


__all__ = [
    "rexec",
    "rparse",
    "reval",
    "rprint",
    "rlang",
    "rcall",
    "rsym",
    "rstring",
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


def rexec(func, *data):
    ret = [None]
    pdata = ProtectedEvalData(py_object(func), py_object(data), py_object(ret))
    if R_ToplevelExec(protectedEval_t, byref(pdata)) == 0:
        raise RuntimeError("rexec encountered an error")
    return pdata.ret[0]


def rparse(string):
    buf = string.encode()
    status = c_int()
    s = Rf_protect(Rf_mkString(buf))
    try:
        ret = rexec(R_ParseVector, s, -1, status, R_NilValue)
    finally:
        Rf_unprotect(1)
    if status.value != 1:
        raise RuntimeError("rparse error")
    return ret


def reval(string, env=R_GlobalEnv):
    status = c_int()
    expressions = Rf_protect(rparse(string))
    ret = R_NilValue
    try:
        for i in range(0, LENGTH(expressions)):
            ret = R_tryEval(VECTOR_ELT(expressions, i), env, status)
            if status.value != 0:
                raise RuntimeError("reval error")
    finally:
        Rf_unprotect(1)
    return ret


def rlang(*args, **kwargs):
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
    return t


def rcall(*args, **kwargs):
    status = c_int()
    val = R_tryEval(rlang(*args, **kwargs), R_GlobalEnv, status)
    if status.value != 0:
        raise RuntimeError("rcall error.")
    return val


def rsym(s, t=None):
    if t:
        return rlang(rsym("::"), rsym(s), rsym(t))
    else:
        return Rf_install(s.encode())


def rstring(s):
    return Rf_mkString(s.encode())


def rprint(s):
    rexec(Rf_PrintValue, s)


def rcopy(s, auto_unbox=True):
    Rf_protect(s)
    ret = None
    typ = TYPEOF(s)
    if typ == VECSXP:
        names = rcopy(rcall(rsym("base", "names"), s))
        if names:
            ret = OrderedDict()
            for i in range(LENGTH(s)):
                ret[names[i]] = rcopy(VECTOR_ELT(s, i), auto_unbox=auto_unbox)
        else:
            ret = []
            for i in range(LENGTH(s)):
                ret.append(rcopy(VECTOR_ELT(s, i), auto_unbox=auto_unbox))

    elif typ == STRSXP:
        ret = []
        for i in range(LENGTH(s)):
            ret.append(CHAR(STRING_ELT(s, i)).decode())
        if auto_unbox and len(ret) == 1:
            ret = ret[0]
    elif typ == LGLSXP:
        ret = []
        sp = LOGICAL(s)
        for i in range(LENGTH(s)):
            ret.append(bool(sp[i]))
        if auto_unbox and len(ret) == 1:
            ret = ret[0]
    elif typ == INTSXP:
        ret = []
        sp = INTEGER(s)
        for i in range(LENGTH(s)):
            ret.append(int(sp[i]))
        if auto_unbox and len(ret) == 1:
            ret = ret[0]
    elif typ == REALSXP:
        ret = []
        sp = REAL(s)
        for i in range(LENGTH(s)):
            ret.append(sp[i])
        if auto_unbox and len(ret) == 1:
            ret = ret[0]
    elif typ == CHARSXP:
        ret = CHAR(s).decode()
    elif typ == RAWSXP:
        ret = []
        sp = RAW(s)
        for i in range(LENGTH(s)):
            ret.append(int(sp[i]))
        if auto_unbox and len(ret) == 1:
            ret = ret[0]
    elif typ == CPLXSXP:
        ret = []
        sp = COMPLEX(s)
        for i in range(LENGTH(s)):
            z = sp[i]
            ret.append(complex(z.r, z.i))
        if auto_unbox and len(ret) == 1:
            ret = ret[0]
    Rf_unprotect(1)
    return ret


def get_option(key, default=None):
    ret = rcopy(Rf_GetOption1(Rf_install(key.encode())), auto_unbox=True)
    if ret is None:
        return default
    else:
        return ret


def set_option(key, value):
    kwargs = {}
    if isinstance(value, text_type):
        kwargs[key] = Rf_mkString(value)
    elif isinstance(value, bool):
        kwargs[key] = Rf_ScalarLogical(int(value))
    elif isinstance(value, int):
        kwargs[key] = Rf_ScalarInteger(value)
    elif isinstance(value, float):
        kwargs[key] = Rf_ScalarReal(value)
    else:
        TypeError("value type is not supported")

    rcall(rsym("base", "options"), **kwargs)
