from __future__ import unicode_literals
from rchitect._cffi import ffi, lib
# from future.utils import with_metaclass


_sexpnums = {
    "NILSXP": 0,
    "SYMSXP": 1,
    "LISTSXP": 2,
    "CLOSXP": 3,
    "ENVSXP": 4,
    "PROMSXP": 5,
    "LANGSXP": 6,
    "SPECIALSXP": 7,
    "BUILTINSXP": 8,
    "CHARSXP": 9,
    "LGLSXP": 10,
    "INTSXP": 13,
    "REALSXP": 14,
    "CPLXSXP": 15,
    "STRSXP": 16,
    "DOTSXP": 17,
    "ANYSXP": 18,
    "VECSXP": 19,
    "EXPRSXP": 20,
    "BCODESXP": 21,
    "EXTPTRSXP": 22,
    "WEAKREFSXP": 23,
    "RAWSXP": 24,
    "S4SXP": 25,
    "NEWSXP": 30,
    "FREESXP": 31,
    "FUNSXP": 99
}

_sexpnums_reversed = {v: k for (k, v) in _sexpnums.items()}


class sexptype(type):

    def __new__(cls, *args):
        if len(args) == 1:
            x = args[0]
            assert isinstance(x, ffi.CData)
            assert ffi.typeof(x) == ffi.typeof('SEXP')
            return globals()[_sexpnums_reversed[lib.TYPEOF(x)]]
        else:
            x = str(args[0])
            return super(sexptype, cls).__new__(cls, x, *args[1:])

    def __instancecheck__(self, instance):
        if not isinstance(instance, ffi.CData):
            return False
        if ffi.typeof(instance) != ffi.typeof('SEXP'):
            return False
        if self is SEXP:
            return True
        return _sexpnums[self.__name__] == lib.TYPEOF(instance)

    def __subclasscheck__(self, subclass):
        if subclass == ffi.CData:
            return True
        return super(sexptype, self).__subclasscheck__(subclass)

    def __repr__(self):
        return self.__name__


SEXP = sexptype("SEXP", (object, ), {})
NILSXP = sexptype("NILSXP", (SEXP, ), {})
SYMSXP = sexptype("SYMSXP", (SEXP, ), {})
LISTSXP = sexptype("LISTSXP", (SEXP, ), {})
CLOSXP = sexptype("CLOSXP", (SEXP, ), {})
ENVSXP = sexptype("ENVSXP", (SEXP, ), {})
PROMSXP = sexptype("PROMSXP", (SEXP, ), {})
LANGSXP = sexptype("LANGSXP", (SEXP, ), {})
SPECIALSXP = sexptype("SPECIALSXP", (SEXP, ), {})
BUILTINSXP = sexptype("BUILTINSXP", (SEXP, ), {})
CHARSXP = sexptype("CHARSXP", (SEXP, ), {})
LGLSXP = sexptype("LGLSXP", (SEXP, ), {})
INTSXP = sexptype("INTSXP", (SEXP, ), {})
REALSXP = sexptype("REALSXP", (SEXP, ), {})
CPLXSXP = sexptype("CPLXSXP", (SEXP, ), {})
STRSXP = sexptype("STRSXP", (SEXP, ), {})
DOTSXP = sexptype("DOTSXP", (SEXP, ), {})
ANYSXP = sexptype("ANYSXP", (SEXP, ), {})
VECSXP = sexptype("VECSXP", (SEXP, ), {})
EXPRSXP = sexptype("EXPRSXP", (SEXP, ), {})
BCODESXP = sexptype("BCODESXP", (SEXP, ), {})
EXTPTRSXP = sexptype("EXTPTRSXP", (SEXP, ), {})
WEAKREFSXP = sexptype("WEAKREFSXP", (SEXP, ), {})
RAWSXP = sexptype("RAWSXP", (SEXP, ), {})
S4SXP = sexptype("S4SXP", (SEXP, ), {})
NEWSXP = sexptype("NEWSXP", (SEXP, ), {})
FREESXP = sexptype("FREESXP", (SEXP, ), {})
FUNSXP = sexptype("FUNSXP", (SEXP, ), {})


class RObject(object):
    def __init__(self, s):
        assert isinstance(s, SEXP)
        self.s = s
        lib.R_PreserveObject(self.s)

    def __del__(self):
        try:
            # it might cause AttributeError when the program exits
            lib.R_ReleaseObject(self.s)
        except AttributeError:
            pass


class RClass(object):
    _rclasses = {}

    def __new__(cls, rcls):
        try:
            return cls._rclasses[rcls]
        except KeyError:
            T = type(str("RClass_" + rcls), (RClass,), {"__new__": (lambda cls: None)})
            cls._rclasses[rcls] = T
            return T


class datatype(type):
    """
    We introduce a `datatype` function to allow different values from `datatype(str)` and
    `datatype(int)`.
    """

    _datatypes = {}

    def __new__(cls, *args):
        if len(args) == 1:
            t = args[0]
            try:
                return cls._datatypes[t]
            except KeyError:
                T = datatype(
                    str("datatype_{}".format(t.__name__)),
                    (type,),
                    {"t": t, "__new__": (lambda cls: cls.t)})
                cls._datatypes[t] = T
                return T
        else:
            return super(datatype, cls).__new__(cls, *args)

    def __instancecheck__(self, instance):
        return self.t == instance

    def __subclasscheck__(self, subclass):
        return isinstance(subclass, datatype) and self.t == subclass.t

    def __repr__(self):
        return "datatype({})".format(self.t.__name__)


def box(x):
    if isinstance(x, SEXP):
        return RObject(x)
    elif isinstance(x, RObject):
        return x

    raise TypeError("expect SEXP or RObject")


def unbox(x):
    if isinstance(x, RObject):
        return x.s
    elif isinstance(x, SEXP):
        return x

    raise TypeError("expect SEXP or RObject")
