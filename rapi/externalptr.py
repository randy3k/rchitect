from ctypes import py_object, c_void_p, cast, pointer, CFUNCTYPE, POINTER, pythonapi
from .internals import R_MakeExternalPtr, R_ExternalPtrAddr, R_RegisterCFinalizerEx, R_NilValue
from .types import SEXP

extptrs = {}


@CFUNCTYPE(None, SEXP)
def finalizer(s):
    ptr = cast(R_ExternalPtrAddr(s), POINTER(py_object))
    fpy = ptr.contents
    pythonapi.Py_DecRef(fpy)


def rextptr(f):
    fpy = py_object(f)
    pythonapi.Py_IncRef(fpy)
    s = R_MakeExternalPtr(cast(pointer(fpy), c_void_p), R_NilValue, R_NilValue)
    R_RegisterCFinalizerEx(s, finalizer, 1)
    return s
