from ctypes import py_object, c_void_p, cast, pointer, CFUNCTYPE, pythonapi
from .internals import R_MakeExternalPtr, R_ExternalPtrAddr, R_RegisterCFinalizerEx, R_NilValue
from .types import SEXP


@CFUNCTYPE(None, SEXP)
def finalizer(s):
    pyo = cast(R_ExternalPtrAddr(s), py_object)
    pythonapi.Py_DecRef(pyo)


def rextptr(x):
    pyo = cast(id(x), py_object)
    pythonapi.Py_IncRef(pyo)
    s = R_MakeExternalPtr(id(x), R_NilValue, R_NilValue)
    R_RegisterCFinalizerEx(s, finalizer, 1)
    return s
