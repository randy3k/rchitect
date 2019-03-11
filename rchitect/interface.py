from __future__ import unicode_literals
from rchitect._libR import ffi, lib
from .dispatch import dispatch
from .types import RObject, SEXP, RClass, sexptype, datatype
from .types import NILSXP, CLOSXP, ENVSXP, LGLSXP, INTSXP, REALSXP, CPLXSXP, STRSXP, \
    VECSXP, EXPRSXP, EXTPTRSXP, RAWSXP, S4SXP
from contextlib import contextmanager
from six import text_type, string_types
from types import FunctionType
from collections import OrderedDict


dispatch.add_dispatch_policy(type, datatype)
dispatch.add_dispatch_policy(
    ffi.CData,
    lambda x: sexptype(x) if ffi.typeof(x) == ffi.typeof('SEXP') else ffi.CData)


@contextmanager
def protected(*args):
    nprotect = 0
    for a in args:
        if isinstance(a, SEXP):
            lib.Rf_protect(a)
            nprotect += 1
    try:
        yield
    finally:
        lib.Rf_unprotect(nprotect)


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


def rint_p(s):
    return lib.Rf_ScalarInteger(s)


def rint(s):
    return box(rint_p(s))


def rlogical_p(s):
    return lib.Rf_ScalarLogical(s)


def rlogical(s):
    return box(rlogical_p(s))


def rdouble_p(s):
    return lib.Rf_ScalarReal(s)


def rdouble(s):
    return box(rdouble_p(s))


def rchar_p(s):
    isascii = all(ord(c) < 128 for c in s)
    b = s.encode("utf-8")
    return lib.Rf_mkCharLenCE(b, len(b), lib.CE_NATIVE if isascii else lib.CE_UTF8)


def rchar(s):
    return box(rchar_p(s))


def rstring_p(s):
    return lib.Rf_ScalarString(rchar_p(s))


def rstring(s):
    return box(rstring_p(s))


def rsym_p(s, t=None):
    if t:
        return rlang_p("::", rsym_p(s), rsym_p(t))
    else:
        return lib.Rf_install(s.encode("utf-8"))


def rsym(s, t=None):
    return box(rsym_p(s, t))


def rparse_p(s):
    status = ffi.new("ParseStatus[1]")
    s = rstring_p(s)
    with protected(s):
        ret = lib.R_ParseVector(s, -1, status, lib.R_NilValue)
        if status[0] != lib.PARSE_OK:
            raise Exception("Parse error")
    return ret


def rparse(s):
    return box(rparse_p(s))


@dispatch(EXPRSXP)
def reval_p(s):
    ret = lib.R_NilValue
    status = ffi.new("int[1]")
    with protected(s):
        for i in range(0, lib.Rf_length(s)):
            ret = lib.R_tryEval(lib.VECTOR_ELT(s, i), lib.R_GlobalEnv, status)
            if status[0] != 0:
                raise RuntimeError("reval error")
    return ret


@dispatch(RObject)  # noqa
def reval_p(s):
    return reval_p(unbox(s))


@dispatch(text_type)  # noqa
def reval_p(s):
    return reval_p(rparse_p(s))


def reval(s):
    return box(reval_p(s))


def as_call(x):
    if isinstance(x, SEXP):
        return x
    elif isinstance(x, RObject):
        return unbox(x)
    elif isinstance(x, text_type):
        return rsym_p(x)
    elif isinstance(x, tuple) and len(x) == 2:
        return rsym_p(*x)

    raise TypeError("unexpected function")


def rlang_p(*args, **kwargs):
    with protected(*args, *(kwargs.items())):
        nargs = len(args) + len(kwargs)
        t = lib.Rf_allocVector(lib.LANGSXP, nargs)
        with protected(t):
            s = t
            lib.SETCAR(s, as_call(args[0]))

            for a in args[1:]:
                s = lib.CDR(s)
                lib.SETCAR(s, unbox(a))
            for k, v in kwargs.items():
                s = lib.CDR(s)
                lib.SETCAR(s, unbox(v))
                lib.SET_TAG(s, lib.Rf_install(k.encode("utf-8")))

            ret = t
    return ret


def rlang(*args, **kwargs):
    return box(rlang_p(*args, **kwargs))


def rcall_p(*args, _envir=None, **kwargs):
    # TODO: convert arguments
    if _envir:
        _envir = unbox(_envir)
    else:
        _envir = lib.R_GlobalEnv
    with protected(_envir):
        status = ffi.new("int[1]")
        val = lib.R_tryEval(rlang_p(*args, **kwargs), _envir, status)
        if status[0] != 0:
            raise RuntimeError("rcall error.")

    return val


def rcall(*args, **kwargs):
    return RObject(rcall_p(*args, **kwargs))


@dispatch(SEXP)
def rprint(s):
    new_env = rcall("new.env")
    lib.Rf_defineVar(rsym_p("x"), unbox(s), unbox(new_env))
    with protected(s):
        try:
            rcall(("base", "print"), rsym("x"), _envir=new_env)
        finally:
            lib.Rf_defineVar(rsym_p("x"), lib.R_NilValue, unbox(new_env))


@dispatch(RObject)  # noqa
def rprint(x):
    rprint(unbox(x))


def getattrib_p(s, key):
    return lib.Rf_getAttrib(unbox(s), rsym_p(key) if isinstance(key, text_type) else key)


def getnames_p(s):
    return getattrib_p(s, lib.R_NamesSymbol)


def getnames(s):
    return box(getnames_p(s))


def rnames(s):
    return rcopy(list, getnames_p(s))


def getclass_p(s, singleString=0):
    return lib.R_data_class(unbox(s), singleString)


def getclass(s, singleString=0):
    return box(getclass_p(s, singleString))


def rclass(s, singleString=0):
    return rcopy(text_type if singleString else list, getclass_p(s, singleString))


# R to Py


@dispatch(datatype(type(None)), NILSXP)  # noqa
def rcopy(_, s):
    return None


@dispatch(datatype(list), NILSXP)  # noqa
def rcopy(_, s):
    return []


@dispatch(datatype(int), INTSXP)  # noqa
def rcopy(_, s):
    return lib.INTEGER(s)[0]


@dispatch(datatype(list), INTSXP)  # noqa
def rcopy(_, s):
    return [lib.INTEGER(s)[i] for i in range(lib.Rf_length(s))]


@dispatch(datatype(bool), LGLSXP)  # noqa
def rcopy(_, s):
    return bool(lib.LOGICAL(s)[0])


@dispatch(datatype(list), LGLSXP)  # noqa
def rcopy(_, s):
    return [bool(lib.LOGICAL(s)[i]) for i in range(lib.Rf_length(s))]


@dispatch(datatype(float), REALSXP)  # noqa
def rcopy(_, s):
    return lib.REAL(s)[0]


@dispatch(datatype(list), REALSXP)  # noqa
def rcopy(_, s):
    return [lib.REAL(s)[i] for i in range(lib.Rf_length(s))]


@dispatch(datatype(complex), CPLXSXP)  # noqa
def rcopy(_, s):
    z = lib.COMPLEX(s)[0]
    return complex(z.r, z.i)


@dispatch(datatype(list), CPLXSXP)  # noqa
def rcopy(_, s):
    return [complex(lib.COMPLEX(s)[i].r, lib.COMPLEX(s)[i].i) for i in range(lib.Rf_length(s))]


def _string(s):
    return text_type(ffi.string(lib.Rf_translateCharUTF8(s)).decode())


@dispatch(datatype(bytes), RAWSXP)  # noqa
def rcopy(_, s):
    return ffi.string(lib.RAW(s), lib.Rf_length(s))


@dispatch(datatype(text_type), STRSXP)  # noqa
def rcopy(_, s):
    return _string(lib.STRING_ELT(s, 0))


@dispatch(datatype(list), STRSXP)  # noqa
def rcopy(_, s):
    return [_string(lib.STRING_ELT(s, i)) for i in range(lib.Rf_length(s))]


@dispatch(datatype(list), VECSXP)  # noqa
def rcopy(_, s):
    return [rcopy(lib.VECTOR_ELT(s, i)) for i in range(lib.Rf_length(s))]


@dispatch(datatype(tuple), VECSXP)  # noqa
def rcopy(_, s):
    return tuple(rcopy(list, s))


@dispatch(datatype(dict), VECSXP)  # noqa
def rcopy(_, s):
    ret = dict()
    names = rnames(s)
    for i in range(lib.Rf_length(s)):
        ret[names[i]] = rcopy(lib.VECTOR_ELT(s, i))
    return ret


@dispatch(datatype(OrderedDict), VECSXP)  # noqa
def rcopy(_, s):
    ret = OrderedDict()
    names = rnames(s)
    for i in range(lib.Rf_length(s)):
        ret[names[i]] = rcopy(lib.VECTOR_ELT(s, i))
    return ret


@dispatch(datatype(FunctionType), CLOSXP)  # noqa
def rcopy(_, s, _envir=None, _convert=True):
    # TODO: convert arguments

    r = RObject(s)  # preserve the closure

    def _(*args, **kwargs):
        ret = rcall(r, *args, _envir=_envir, **kwargs)
        if _convert:
            return rcopy(ret)
        else:
            return ret
    return _


@dispatch(datatype(RObject), SEXP)  # noqa
def rcopy(_, s):
    return box(s)


@dispatch(datatype(RObject), RObject)  # noqa
def rcopy(_, s):
    return s


@dispatch(object, RObject)  # noqa
def rcopy(t, r, **kwargs):
    return rcopy(t, unbox(r), **kwargs)


# default conversions
default = RClass("default")


@dispatch(SEXP)  # noqa
def rcopy(s, **kwargs):
    for cls in rclass(s):
        T = rcopytype(RClass(cls), s)
        if T is not RObject:
            return rcopy(T, s, **kwargs)
    T = rcopytype(default, s)
    return rcopy(T, s, **kwargs)


@dispatch(RObject)  # noqa
def rcopy(r, **kwargs):
    return rcopy(unbox(r), **kwargs)


@dispatch(datatype(default), NILSXP)  # noqa
def rcopytype(_, s):
    return type(None)


@dispatch(datatype(default), INTSXP)  # noqa
def rcopytype(_, s):
    return int if lib.Rf_length(s) == 1 else list


@dispatch(datatype(default), LGLSXP)  # noqa
def rcopytype(_, s):
    return bool if lib.Rf_length(s) == 1 else list


@dispatch(datatype(default), REALSXP)  # noqa
def rcopytype(_, s):
    return float if lib.Rf_length(s) == 1 else list


@dispatch(datatype(default), CPLXSXP)  # noqa
def rcopytype(_, s):
    return complex if lib.Rf_length(s) == 1 else list


@dispatch(datatype(default), RAWSXP)  # noqa
def rcopytype(_, s):
    return bytes


@dispatch(datatype(default), STRSXP)  # noqa
def rcopytype(_, s):
    return text_type if lib.Rf_length(s) == 1 else list


@dispatch(datatype(default), VECSXP)  # noqa
def rcopytype(_, s):
    return list if lib.Rf_isNull(getnames_p(s)) else OrderedDict


@dispatch(datatype(default), CLOSXP)  # noqa
def rcopytype(_, s):
    return FunctionType


@dispatch(object, SEXP)  # noqa
def rcopytype(_, s):
    return RObject


# Py to R


# python to r conversions

@dispatch(datatype(RClass("NULL")), type(None))  # noqa
def sexp(_, n):
    return lib.R_NilValue


@dispatch(datatype(RClass("logical")), bool)  # noqa
def sexp(_, s):
    return rlogical_p(s)


@dispatch(datatype(RClass("integer")), int)  # noqa
def sexp(_, s):
    return rint_p(s)


@dispatch(datatype(RClass("numeric")), float)  # noqa
def sexp(_, s):
    return rdouble_p(s)


@dispatch(datatype(RClass("complex")), complex)  # noqa
def sexp(_, s):
    c = ffi.new("Rcomplex")
    c.r = s.real
    c.i = s.imag
    return lib.Rf_ScalarComplex(c)


@dispatch(datatype(RClass("character")), string_types)  # noqa
def sexp(_, s):
    return rstring_p(s)


@dispatch(datatype(RClass("raw")), bytes)  # noqa
def sexp(_, s):
    n = len(s)
    x = lib.Rf_allocVector(lib.RAWSXP, n)
    with protected(x):
        p = lib.RAW(x)
        for i in range(n):
            p[i] = s[i]
    return x


@dispatch(datatype(RClass("logical")), list)  # noqa
def sexp(_, s):
    n = len(s)
    x = lib.Rf_allocVector(lib.LGLSXP, n)
    with protected(x):
        p = lib.LOGICAL(x)
        for i in range(n):
            p[i] = s[i]
    return x


@dispatch(datatype(RClass("integer")), list)  # noqa
def sexp(_, s):
    n = len(s)
    x = lib.Rf_allocVector(lib.INTSXP, n)
    with protected(x):
        p = lib.INTEGER(x)
        for i in range(n):
            p[i] = s[i]
    return x


@dispatch(datatype(RClass("numeric")), list)  # noqa
def sexp(_, s):
    n = len(s)
    x = lib.Rf_allocVector(lib.REALSXP, n)
    with protected(x):
        p = lib.REAL(x)
        for i in range(n):
            p[i] = s[i]
    return x


@dispatch(datatype(RClass("complex")), list)  # noqa
def sexp(_, s):
    n = len(s)
    x = lib.Rf_allocVector(lib.CPLXSXP, n)
    with protected(x):
        p = lib.COMPLEX(x)
        for i in range(n):
            p[i].r = s[i].real
            p[i].i = s[i].imag
    return x


@dispatch(datatype(RClass("character")), list)  # noqa
def sexp(_, s):
    n = len(s)
    x = lib.Rf_allocVector(lib.STRSXP, n)
    with protected(x):
        for i in range(n):
            isascii = all(ord(c) < 128 for c in s[i])
            b = s[i].encode("utf-8")
            lib.SET_STRING_ELT(x, i, lib.Rf_mkCharLenCE(b, len(b), 0 if isascii else 1))
    return x



@dispatch(datatype(RClass("list")), (list, tuple))  # noqa
def sexp(_, s):
    n = len(s)
    x = lib.Rf_allocVector(lib.VECSXP, n)
    with protected(x):
        for i in range(n):
            lib.SET_VECTOR_ELT(x, i, sexp(s[i]))
    return x


@dispatch(datatype(RClass("list")), (dict, OrderedDict))  # noqa
def sexp(_, s):
    v = sexp(RClass("list"), list(s.values()))
    with protected(v):
        k = sexp(RClass("character"), list(s.keys()))
        with protected(k):
            lib.Rf_setAttrib(v, lib.R_NamesSymbol, k)
    return v

  # noqa
# def sexp_dots():
#     s = Rf_protect(Rf_list1(R_MissingArg))
#     SET_TAG(s, R_DotsSymbol)
#     Rf_unprotect(1)
#     return s

  # noqa
# def sexp_py_object(obj):
#     if inspect.isclass(obj):
#         return sexp(RClass("PyClass"), obj)
#     if callable(obj):
#         return sexp(RClass("PyCallable"), obj)
#     else:
#         return sexp(RClass("PyObject"), obj)


# @CFUNCTYPE(SEXP, SEXP, SEXP, SEXP, SEXP)
# def rchitect_callback(exptr, arglist, _convert_args, _convert_return):
#     convert_args = rcopy(bool, sexp(_convert_args))
#     convert_return = rcopy(bool, sexp(_convert_return))
#     f = to_pyo(exptr).value
#     args = []
#     kwargs = {}
#     names = rnames(arglist)
#     try:
#         if convert_args:
#             for i in range(LENGTH(arglist)):
#                 if names and names[i]:
#                     kwargs[names[i]] = rcopy(VECTOR_ELT(arglist, i))
#                 else:
#                     args.append(rcopy(VECTOR_ELT(arglist, i)))
#         else:
#             for i in range(LENGTH(arglist)):
#                 if names and names[i]:
#                     kwargs[names[i]] = sexp(VECTOR_ELT(arglist, i))
#                 else:
#                     args.append(sexp(VECTOR_ELT(arglist, i)))
#         if convert_return:
#             return sexp(f(*args, **kwargs)).value
#         else:
#             ret = f(*args, **kwargs)
#             return sexp_py_object(ret).value
#     except Exception as e:
#         return rcall_p(("base", "simpleError"), str(e)).value


# @dispatch(datatype(RClass("function")), Callable)  # noqa
# def sexp(_, f, convert_args=True, convert_return=True, invisible=False):
#     fextptr = rextptr(f)
#     dotlist = rlang_p("list", R_DotsSymbol)
#     body = rlang_p(".Call", "rchitect_callback", fextptr, dotlist, convert_args, convert_return)
#     if invisible:
#         body = rlang_p("invisible", body)
#     lang = rlang_p(rsym("function"), sexp_dots(), body)
#     status = c_int()
#     val = R_tryEval(lang, R_GlobalEnv, status)
#     return sexp(val)


# @dispatch(datatype(RClass("PyObject")), object)  # noqa
# def sexp(_, s):
#     if (isinstance(s, RObject) or isinstance(s, SEXP)) and "PyObject" in rclass(s):
#         return sexp(s)
#     p = rextptr(s)
#     setclass(p, "PyObject")
#     return p


# @dispatch(datatype(RClass("PyCallable")), Callable)  # noqa
# def sexp(_, f, convert_args=True, convert_return=False, invisible=False):
#     p = Rf_protect(sexp(RClass("function"), f,
#                         convert_args=convert_args,
#                         convert_return=convert_return,
#                         invisible=invisible))
#     setattrib(p, "py_object", sexp(RClass("PyObject"), f))
#     setclass(p, ["PyCallable", "PyObject"])
#     Rf_unprotect(1)
#     return p


# @dispatch(datatype(RClass("PyClass")), object)  # noqa
# def sexp(_, s):
#     p = Rf_protect(sexp(RClass("PyCallable"), s))
#     setclass(p, ["PyClass", "PyCallable", "PyObject"])
#     Rf_unprotect(1)
#     return p


# default conversions


@dispatch(type(None))  # noqa
def sexp(n):
    return lib.R_NilValue


@dispatch(RObject)  # noqa
def sexp(r):
    return unbox(r)


@dispatch(object)  # noqa
def sexp(s, **kwargs):
    rcls = sexpclass(s)
    return sexp(RClass(rcls), s, **kwargs)


@dispatch(bool)  # noqa
def sexpclass(s):
    return "logical"


@dispatch(int)  # noqa
def sexpclass(s):
    return "integer"


@dispatch(float)  # noqa
def sexpclass(s):
    return "numeric"


@dispatch(complex)  # noqa
def sexpclass(s):
    return "complex"


@dispatch(string_types)  # noqa
def sexpclass(s):
    return "character"


@dispatch(list)  # noqa
def sexpclass(s):
    if all(isinstance(x, int) for x in s):
        return "integer"
    elif all(isinstance(x, bool) for x in s):
        return "logical"
    elif all(isinstance(x, float) for x in s):
        return "numeric"
    elif all(isinstance(x, complex) for x in s):
        return "complex"
    elif all(isinstance(x, string_types) for x in s):
        return "character"

    return "list"


@dispatch((tuple, dict, OrderedDict))  # noqa
def sexpclass(s):
    return "list"


# @dispatch(type)  # noqa
# def sexpclass(f):
#     return "PyClass"


# @dispatch(Callable)  # noqa
# def sexpclass(f):
#     return "PyCallable"


# @dispatch(object)  # noqa
# def sexpclass(f):
#     return "PyObject"
