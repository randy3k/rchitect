from __future__ import unicode_literals, absolute_import
from rchitect._cffi import ffi, lib
from .dispatch import dispatch
from .types import RObject, SEXP, RClass, sexptype, datatype
from .types import NILSXP, CLOSXP, ENVSXP, BUILTINSXP, LGLSXP, INTSXP, REALSXP, CPLXSXP, STRSXP, \
    VECSXP, EXPRSXP, EXTPTRSXP, RAWSXP, S4SXP
from .types import box, unbox
from .xptr import new_xptr, new_xptr_p, from_xptr
from .console import capture_console, read_stdout, read_stderr
from .utils import utf8tosystem


import sys
import ctypes
import struct
from contextlib import contextmanager
from six import text_type, string_types
from types import FunctionType
from collections import OrderedDict
if sys.version >= "3":
    from collections.abc import Callable
    long = int
else:
    from collections import Callable

dispatch.add_dispatch_policy(type, datatype)
dispatch.add_dispatch_policy(
    ffi.CData,
    lambda x: sexptype(x) if ffi.typeof(x) == ffi.typeof('SEXP') else ffi.CData)


def extract(kwargs, key, default=None):
    if key in kwargs:
        value = kwargs[key]
        del kwargs[key]
    else:
        value = default
    return value


def ensure_initialized():
    if lib.Rf_initialize_R == ffi.NULL:
        from .setup import init
        init()


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
    b = s.encode('utf-8')
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
        return lib.Rf_install(utf8tosystem(s))


def rsym(s, t=None):
    return box(rsym_p(s, t))


def rparse_p(s):
    ensure_initialized()
    status = ffi.new("ParseStatus[1]")
    s = lib.Rf_mkString(utf8tosystem(s))
    with protected(s):
        with capture_console():
            ret = lib.R_ParseVector(s, -1, status, lib.R_NilValue)
            if status[0] != lib.PARSE_OK:
                err = read_stderr().strip() or "Error"
                raise RuntimeError("{}".format(err))
    return ret


def rparse(s):
    return box(rparse_p(s))


@dispatch(EXPRSXP)
def reval_p(s, envir=None):
    ensure_initialized()
    if envir:
        # `sys.frame()` doesn't work with R_tryEval as it doesn't create R stacks,
        # we use `base::eval` instead.
        ret = rcall_p(("base", "eval"), s, _envir=envir)
    else:
        ret = lib.R_NilValue
        status = ffi.new("int[1]")
        with protected(s):
            with capture_console():
                for i in range(0, lib.Rf_length(s)):
                    ret = lib.R_tryEval(lib.VECTOR_ELT(s, i), lib.R_GlobalEnv, status)
                    if status[0] != 0:
                        err = read_stderr().strip() or "Error"
                        raise RuntimeError("{}".format(err))
    return ret


@dispatch(RObject)  # noqa
def reval_p(s, envir=None):
    with protected(envir):
        return reval_p(unbox(s), envir=envir)


@dispatch(string_types)  # noqa
def reval_p(s, envir=None):
    with protected(envir):
        return reval_p(rparse_p(s), envir=envir)


def reval(s, envir=None):
    return box(reval_p(s, envir=envir))


def as_call(x):
    if isinstance(x, SEXP):
        return x
    elif isinstance(x, RObject):
        return unbox(x)
    elif isinstance(x, string_types):
        return rsym_p(x)
    elif isinstance(x, tuple) and len(x) == 2:
        return rsym_p(*x)

    raise TypeError("unexpected function")


def rlang_p(f, *args, **kwargs):
    ensure_initialized()
    argslist = list(args) + list(kwargs.items())
    with protected(*argslist):
        nargs = len(args) + len(kwargs)
        t = lib.Rf_allocVector(lib.LANGSXP, nargs + 1)

        with protected(t):
            s = t
            lib.SETCAR(s, as_call(f))

            for a in args:
                s = lib.CDR(s)
                lib.SETCAR(s, unbox(a))
            for k, v in kwargs.items():
                s = lib.CDR(s)
                lib.SETCAR(s, unbox(v))
                lib.SET_TAG(s, lib.Rf_install(utf8tosystem(k)))

            ret = t
    return ret


def rlang(*args, **kwargs):
    return box(rlang_p(*args, **kwargs))


@contextmanager
def sexp_args(args, kwargs, asis=False):
    nprotect = 0
    try:
        _args = []
        for a in args:
            _a = sexp_as_py_object(a) if asis else sexp(a)
            if isinstance(_a, SEXP):
                lib.Rf_protect(_a)
                nprotect += 1
            _args.append(_a)

        _kwargs = {}
        for k, v in kwargs.items():
            _v = sexp_as_py_object(v) if asis else sexp(v)
            if isinstance(_v, SEXP):
                lib.Rf_protect(_v)
                nprotect += 1
            _kwargs[k] = _v

        yield _args, _kwargs
    finally:
        lib.Rf_unprotect(nprotect)


def rcall_p(f, *args, **kwargs):
    ensure_initialized()
    _envir = extract(kwargs, "_envir")
    _asis = extract(kwargs, "_asis")
    if _envir:
        _envir = unbox(_envir)
    else:
        _envir = lib.R_GlobalEnv

    with protected(_envir):
        with sexp_args(args, kwargs, _asis) as (a, k):
            with capture_console():
                status = ffi.new("int[1]")
                val = lib.R_tryEval(rlang_p(f, *a, **k), _envir, status)
                if status[0] != 0:
                    err = read_stderr().strip() or "Error"
                    raise RuntimeError("{}".format(err))
    return val


def rcall(*args, **kwargs):
    _convert = extract(kwargs, "_convert")
    s = rcall_p(*args, **kwargs)
    return rcopy(s) if _convert else box(s)


def rprint(s):
    new_env = rcall(("base", "new.env"))
    lib.Rf_defineVar(rsym_p("x"), unbox(s), unbox(new_env))
    with protected(s):
        try:
            rcall(("base", "print"), rsym("x"), _envir=new_env)
        finally:
            lib.Rf_defineVar(rsym_p("x"), lib.R_NilValue, unbox(new_env))


def _repr(self):
    s = self.s
    new_env = rcall(("base", "new.env"))
    lib.Rf_defineVar(rsym_p("x"), unbox(s), unbox(new_env))
    with capture_console(flushable=False):
        try:
            rcall(("base", "print"), rsym_p("x"), _envir=new_env)
        finally:
            lib.Rf_defineVar(rsym_p("x"), lib.R_NilValue, unbox(new_env))
        output = read_stdout() or ""

    name = "RObject{{{}}}".format(str(sexptype(s)))
    if output:
        return name + "\n" + output.rstrip()
    else:
        return name


RObject.__repr__ = _repr


def getoption_p(key):
    return lib.Rf_GetOption1(rsym_p(key))


def getoption(key):
    return box(getoption_p(key))


def roption(key, default=None):
    ret = rcopy(getoption_p(key))
    return ret if ret is not None else default


def setoption(key, value):
    kwargs = {key: value}
    rcall_p(("base", "options"), **kwargs)


def getattrib_p(s, key):
    return lib.Rf_getAttrib(unbox(s), rsym_p(key) if isinstance(key, string_types) else key)


def setattrib(s, key, value):
    with protected(s, value):
        lib.Rf_setAttrib(unbox(s), rsym_p(key) if isinstance(key, string_types) else key, value)


def getnames_p(s):
    return getattrib_p(s, lib.R_NamesSymbol)


def rnames(s):
    return rcopy(list, getnames_p(s))


def getclass_p(s, singleString):
    return lib.R_data_class(unbox(s), singleString)


def setclass(s, classes):
    with protected(s):
        setattrib(s, lib.R_ClassSymbol, sexp(RClass("character"), classes))


def rclass(s, singleString=0):
    return rcopy(text_type if singleString else list, getclass_p(s, singleString))


def process_events():
    lib.process_events()


def polled_events():
    lib.polled_events()


def peek_event():
    return lib.peek_event()


def set_hook(event, fun):
    rcall(("base", "setHook"), event, fun)


def package_event(pkg, event):
    return rcall(("base", "packageEvent"), pkg, event)


def greeting():
    info = rcopy(rcall("R.Version"))
    return "{} -- \"{}\"\nPlatform: {} ({}-bit)\n".format(
        info["version.string"], info["nickname"], info["platform"], 8 * struct.calcsize("P"))


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
    return text_type(ffi.string(lib.Rf_translateCharUTF8(s)).decode("utf-8"))


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


@dispatch(datatype(FunctionType), (CLOSXP, BUILTINSXP))  # noqa
def rcopy(_, s, envir=None, asis=False, convert=True):
    r = RObject(s)  # preserve the closure

    def _(*args, **kwargs):
        return rcall(r, *args, _envir=envir, _asis=asis, _convert=convert, **kwargs)

    return _


# PyObject
@dispatch(datatype(object), EXTPTRSXP)  # noqa
def rcopy(_, s):
    return from_xptr(s)


# reticulate's python.builtin.object
@dispatch(datatype(object), ENVSXP)  # noqa
def rcopy(_, s):
    x = rcall(("base", "get"), "pyobj", s)
    p = ffi.cast("uintptr_t", lib.R_ExternalPtrAddr(unbox(x)))
    d = long(p)
    obj = ctypes.cast(d, ctypes.py_object)
    return obj.value


# PyCallable or reticulate's python.builtin.function
@dispatch(datatype(object), CLOSXP)  # noqa
def rcopy(_, s):
    return rcopy(getattrib_p(s, "py_object"))


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
    ensure_initialized()
    for cls in rclass(s):
        T = rcopytype(RClass(cls), s)
        if T is not RObject:
            return rcopy(T, s, **kwargs)
    T = rcopytype(default, s)
    return rcopy(T, s, **kwargs)


@dispatch(RObject)  # noqa
def rcopy(r, **kwargs):
    return rcopy(unbox(r), **kwargs)


# PyObject
@dispatch(datatype(RClass("PyObject")), EXTPTRSXP)  # noqa
def rcopytype(_, s):
    return object


# PyCallable
@dispatch(datatype(RClass("PyCallable")), CLOSXP)  # noqa
def rcopytype(_, s):
    return object


# reticulate class
@dispatch(datatype(RClass("python.builtin.object")), ENVSXP)  # noqa
def rcopytype(_, s):
    return object


# reticulate function
@dispatch(datatype(RClass("python.builtin.function")), CLOSXP)  # noqa
def rcopytype(_, s):
    return object


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


@dispatch(datatype(default), BUILTINSXP)  # noqa
def rcopytype(_, s):
    return FunctionType


@dispatch(datatype(default), CLOSXP)  # noqa
def rcopytype(_, s):
    return FunctionType


@dispatch(datatype(default), EXTPTRSXP)  # noqa
def rcopytype(_, s):
    return RObject


@dispatch(object, SEXP)  # noqa
def rcopytype(_, s):
    return RObject


# Py to R


# python to r conversions

def robject(*args, **kwargs):
    ensure_initialized()
    if len(args) == 2 and isinstance(args[0], string_types):
        return RObject(sexp(RClass(args[0]), args[1], **kwargs))
    elif len(args) == 1:
        return RObject(sexp(args[0], **kwargs))
    else:
        raise TypeError("wrong number of arguments or argument types")


def rfunction(x, **kwargs):
    return robject("function", x, **kwargs)


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
    c = ffi.new("Rcomplex*")
    c.r = s.real
    c.i = s.imag
    return lib.Rf_ScalarComplex(c[0])


@dispatch(datatype(RClass("character")), string_types)  # noqa
def sexp(_, s):
    return rstring_p(s)


if sys.version >= "3":
    @dispatch(datatype(RClass("raw")), bytes)  # noqa
    def sexp(_, s):
        n = len(s)
        x = lib.Rf_allocVector(lib.RAWSXP, n)
        with protected(x):
            p = lib.RAW(x)
            for i in range(n):
                p[i] = s[i]
        return x
else:
    @dispatch(datatype(RClass("raw")), bytes)  # noqa
    def sexp(_, s):
        n = len(s)
        x = lib.Rf_allocVector(lib.RAWSXP, n)
        with protected(x):
            p = lib.RAW(x)
            for i in range(n):
                p[i] = ord(s[i])
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
            b = s[i].encode('utf-8')
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


def sexp_dots():  # noqa
    s = lib.Rf_list1(lib.R_MissingArg)
    with protected(s):
        lib.SET_TAG(s, lib.R_DotsSymbol)
    return s


def sexp_as_py_object(obj):
    if callable(obj):
        return sexp(RClass("PyCallable"), obj)
    else:
        return sexp(RClass("PyObject"), obj)


def on_xptr_callback_error(exception, exc_value, traceback):
    lib.xptr_callback_error_occured = 1
    lib.xptr_callback_error_message = utf8tosystem(str(exc_value)[0:100])


@ffi.def_extern(error=ffi.NULL, onerror=on_xptr_callback_error)
def xptr_callback(exptr, arglist, asis, convert):
    asis = rcopy(bool, asis)
    convert = rcopy(bool, convert)
    f = from_xptr(exptr)
    args = []
    kwargs = {}
    names = rnames(arglist)
    for i in range(lib.Rf_length(arglist)):
        if asis:
            if names and names[i]:
                kwargs[names[i]] = lib.VECTOR_ELT(arglist, i)
            else:
                args.append(lib.VECTOR_ELT(arglist, i))
        else:
            if names and names[i]:
                kwargs[names[i]] = rcopy(lib.VECTOR_ELT(arglist, i))
            else:
                args.append(rcopy(lib.VECTOR_ELT(arglist, i)))

    ret = f(*args, **kwargs)
    return sexp(ret) if convert else sexp_as_py_object(ret)


@dispatch(datatype(RClass("function")), Callable)  # noqa
def sexp(_, f, invisible=False, asis=False, convert=True):
    fextptr = new_xptr(f)
    dotlist = rlang("list", lib.R_DotsSymbol)
    body = rlang(
        ".Call", rstring("_libR_xptr_callback"), fextptr, dotlist,
        rlogical(asis), rlogical(convert))
    if invisible:
        body = rlang("invisible", body)
    lang = rlang_p(rsym("function"), sexp_dots(), body)
    status = ffi.new("int[1]")
    val = lib.R_tryEval(lang, lib.R_GlobalEnv, status)
    return val


@dispatch(datatype(RClass("PyObject")), object)  # noqa
def sexp(_, s):
    if (isinstance(s, RObject) or isinstance(s, SEXP)) and "PyObject" in rclass(s):
        return unbox(s)
    p = new_xptr_p(s)
    setclass(p, "PyObject")
    return p


@dispatch(datatype(RClass("PyCallable")), Callable)  # noqa
def sexp(_, f, invisible=False, asis=False, convert=True):
    p = sexp(RClass("function"), f, invisible=invisible, asis=asis, convert=convert)
    setattrib(p, "py_object", sexp(RClass("PyObject"), f))
    setclass(p, ["PyCallable", "PyObject"])
    return p


# default conversions


@dispatch(type(None))  # noqa
def sexp(n):
    return lib.R_NilValue


@dispatch(SEXP)  # noqa
def sexp(x):
    return x


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
    if all(isinstance(x, bool) for x in s):
        return "logical"
    elif all(isinstance(x, int) for x in s):
        return "integer"
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


@dispatch(Callable)  # noqa
def sexpclass(f):
    return "PyCallable"


@dispatch(object)  # noqa
def sexpclass(f):
    return "PyObject"
