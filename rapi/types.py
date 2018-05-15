from __future__ import unicode_literals
from ctypes import c_void_p, c_double, c_int, c_int32, c_int64
from ctypes import Structure
from ctypes import sizeof

from enum import Enum

# to be injected by bootstrap
internals = None
interface = None


__all__ = [
    "SEXP",
    "SEXPTYPE",
    "SEXPCLASS",
    "RObject",
    "Rcomplex",
    "R_len_t",
    "R_xlen_t"
]


class SEXP(c_void_p):

    pass


class SEXPTYPE(Enum):
    NILSXP = 0
    SYMSXP = 1
    LISTSXP = 2
    CLOSXP = 3
    ENVSXP = 4
    PROMSXP = 5
    LANGSXP = 6
    SPECIALSXP = 7
    BUILTINSXP = 8
    CHARSXP = 9
    LGLSXP = 10
    INTSXP = 13
    REALSXP = 14
    CPLXSXP = 15
    STRSXP = 16
    DOTSXP = 17
    ANYSXP = 18
    VECSXP = 19
    EXPRSXP = 20
    BCODESXP = 21
    EXTPTRSXP = 22
    WEAKREFSXP = 23
    RAWSXP = 24
    S4SXP = 25
    NEWSXP = 30
    FREESXP = 31
    FUNSXP = 99


for n in SEXPTYPE._member_names_:
    globals()[n] = type(n, (SEXP,), {})


def SEXPCLASS(enum):
    return globals()[SEXPTYPE(enum).name]


class RObject(SEXP):
    def __init__(self, s):
        if not isinstance(s, SEXP):
            s = interface.sexp(s)
        if not isinstance(s, SEXP):
            raise Exception("s is not a SEXP and cannot be converted to a SEXP")
        self.value = s.value
        internals.R_PreserveObject(s.value)

    def __del__(self):
        internals.R_ReleaseObject(self.value)


class Rcomplex(Structure):
    _fields_ = [
        ('r', c_double),
        ('i', c_double),
    ]


if sizeof(c_void_p) == 4:
    ptrdiff_t = c_int32
elif sizeof(c_void_p) == 8:
    ptrdiff_t = c_int64

R_len_t = c_int

R_xlen_t = ptrdiff_t
