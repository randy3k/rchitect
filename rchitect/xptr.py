from __future__ import unicode_literals

from rchitect._cffi import ffi, lib
from .types import box, unbox


_global_set = dict()


@ffi.def_extern()
def xptr_finalizer(s):
    h = lib.R_ExternalPtrAddr(s)
    del _global_set[h]


def new_xptr_p(x):
    h = ffi.new_handle(x)
    hp = ffi.cast("void*", h)
    _global_set[hp] = h
    s = lib.R_MakeExternalPtr(hp, lib.R_NilValue, lib.R_NilValue)
    lib.R_RegisterCFinalizerEx(s, ffi.addressof(lib, "xptr_finalizer"), 1)
    return s


def new_xptr(x):
    return box(new_xptr_p(x))


def from_xptr(s):
    return ffi.from_handle(lib.R_ExternalPtrAddr(unbox(s)))
