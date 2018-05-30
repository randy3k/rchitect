from ctypes import py_object, c_void_p, cast, byref, CFUNCTYPE
from .internals import R_MakeExternalPtr, R_ExternalPtrAddr, R_RegisterCFinalizerEx, R_NilValue
from .types import SEXP


extptrs = {}


@CFUNCTYPE(None, SEXP)
def finalizer(s):
    if s.value in extptrs:
        del extptrs[s.value]


def rextptr(f):
    pyo = py_object(f)
    s = R_MakeExternalPtr(byref(pyo), R_NilValue, R_NilValue)
    extptrs[s.value] = pyo
    R_RegisterCFinalizerEx(s, finalizer, 1)
    return s
