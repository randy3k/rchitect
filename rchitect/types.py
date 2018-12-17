from __future__ import unicode_literals
from ctypes import c_void_p, c_double, c_int, c_int32, c_int64
from ctypes import Structure
from ctypes import sizeof


class SEXP(c_void_p):
    pass


class SEXPTYPE(object):
    _fields = [
        "NILSXP", "SYMSXP", "LISTSXP", "CLOSXP", "ENVSXP", "PROMSXP", "LANGSXP",
        "SPECIALSXP", "BUILTINSXP", "CHARSXP", "LGLSXP", "INTSXP", "REALSXP",
        "CPLXSXP", "STRSXP", "DOTSXP", "ANYSXP", "VECSXP", "EXPRSXP", "BCODESXP",
        "EXTPTRSXP", "WEAKREFSXP", "RAWSXP", "S4SXP", "NEWSXP", "FREESXP", "FUNSXP"]
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

    _sexptype_map = {}

    for name in _fields:
        v = locals()[name]
        t = type(str(name), (SEXP,), {})
        globals()[name] = t
        _sexptype_map[v] = t

    @classmethod
    def from_sexpnum(cls, num):
        return cls._sexptype_map[num]


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


class RObject(object):
    p = None

    def sexp(self, p):
        # to be injected by bootstrap
        return p

    def preserve(self):
        # to be injected by bootstrap
        pass

    def release(self):
        # to be injected by bootstrap
        pass

    def __init__(self, p):
        p = self.sexp(p)
        if not isinstance(p, SEXP):
            raise Exception("p is not a SEXP or cannot be converted to a SEXP")
        self.p = p
        self.preserve(p)

    def __del__(self):
        self.release(self.p)


class RClass(object):
    _rclasses = {}

    def __new__(cls, rcls):
        try:
            return cls._rclasses[rcls]
        except KeyError:
            T = type(str("RClass." + rcls), (type,), {})
            cls._rclasses[rcls] = T
            setattr(RClass, rcls,  T)
            return T
