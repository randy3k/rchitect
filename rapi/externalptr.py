from __future__ import unicode_literals

from ctypes import py_object, cast, CFUNCTYPE, pythonapi
from .internals import R_MakeExternalPtr, R_ExternalPtrAddr, R_RegisterCFinalizerEx, R_NilValue
from .types import SEXP


def to_pyo(s):
    return cast(R_ExternalPtrAddr(s), py_object)


@CFUNCTYPE(None, SEXP)
def finalizer(s):
    pythonapi.Py_DecRef(to_pyo(s))


def rextptr(x):
    pyo = cast(id(x), py_object)
    pythonapi.Py_IncRef(pyo)
    s = R_MakeExternalPtr(id(x), R_NilValue, R_NilValue)
    R_RegisterCFinalizerEx(s, finalizer, 1)
    return s
