from ctypes import py_object, pointer, cast, c_void_p
from ctypes import CFUNCTYPE, Structure, POINTER

from .internals import R_ToplevelExec


class ProtectedEvalData(Structure):
    _fields_ = [
        ('func', py_object),
        ('data', py_object),
        ('ret', py_object)
    ]


def protectedEval(pdata_t):
    pdata = cast(pdata_t, POINTER(ProtectedEvalData)).contents
    data = pdata.data
    pdata.ret = py_object(pdata.func(*data))


protectedEval_t = CFUNCTYPE(None, c_void_p)(protectedEval)


def rexec(func, *data):
    pdata = ProtectedEvalData()
    pdata.func = py_object(func)
    pdata.data = py_object(data)
    pdata.ret = None
    R_ToplevelExec(protectedEval_t, pointer(pdata))
    return pdata.ret
