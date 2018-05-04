from ctypes import py_object, pointer, cast, c_void_p, c_int
from ctypes import CFUNCTYPE, Structure, POINTER

from .internals import Rf_protect, Rf_unprotect, Rf_error, R_NilValue, R_GlobalEnv
from .internals import R_ToplevelExec
from .internals import Rf_mkString, R_ParseVector, R_tryEval
from .internals import LENGTH, VECTOR_ELT
from .internals import Rf_PrintValue
from .internals import Rf_allocVector, LANGSXP, SETCAR, CDR, SET_TAG, Rf_install

from .types import SEXP


class ProtectedEvalData(Structure):
    _fields_ = [
        ('func', py_object),
        ('data', py_object),
        ('ret', py_object)
    ]


def protectedEval(pdata_t):
    pdata = cast(pdata_t, POINTER(ProtectedEvalData)).contents
    data = pdata.data
    try:
        ret = pdata.func(*data)
        if isinstance(ret, SEXP):
            # not sure why, it is neccessary for py_object(ret)
            ret.value = cast(ret, c_void_p).value
        pdata.ret = py_object(ret)
    except Exception as e:
        Rf_error(("{}: {}".format(type(e).__name__, str(e))).encode())


protectedEval_t = CFUNCTYPE(None, c_void_p)(protectedEval)


def rexec(func, *data):
    pdata = ProtectedEvalData()
    pdata.func = py_object(func)
    pdata.data = py_object(data)
    pdata.ret = None
    if R_ToplevelExec(protectedEval_t, pointer(pdata)) == 0:
        raise RuntimeError("rexec encountered an error")
    return pdata.ret


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


def rsym(s):
    return Rf_install(s.encode())


def rstring(s):
    return Rf_mkString(s.encode())


def rprint(s):
    rexec(Rf_PrintValue, s)
