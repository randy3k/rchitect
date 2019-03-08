from __future__ import unicode_literals

from rchitect._libR import ffi, lib
from .types import robject, sexp, is_robject, is_sexp


def rint_p(s):
    return sexp(Rf_ScalarInteger(s))


def rint(s):
    return RObject(rint_p(s))


def rlogical_p(s):
    return sexp(Rf_ScalarLogical(s))


def rlogical(s):
    return RObject(rlogical_p(s))


def rdouble_p(s):
    return sexp(Rf_ScalarReal(s))


def rdouble(s):
    return RObject(sexp(s))


def rstring_p(s):
    isascii = all(ord(c) < 128 for c in s)
    b = s.encode("utf-8")
    return sexp(Rf_ScalarString(Rf_mkCharLenCE(b, len(b), 0 if isascii else 1)))


def rstring(s):
    return RObject(rstring_p(s))


def rprint(s):
    new_env = rcall("new.env")
    Rf_defineVar(rsym_p("x"), sexp(s), new_env.p)
    s = sexp(s)
    Rf_protect(s)
    try:
        rcall(("base", "print"), rsym("x"), _envir=new_env)
    finally:
        Rf_defineVar(rsym_p("x"), R_NilValue, new_env.p)
        Rf_unprotect(1)


# r to python conversions

@dispatch(datatype(type(None)), NILSXP)
def rcopy(_, s):
    return None


@dispatch(datatype(list), NILSXP)
def rcopy(_, s):
    return []


@dispatch(datatype(int), INTSXP)
def rcopy(_, s):
    return INTEGER(s)[0]


@dispatch(datatype(list), INTSXP)
def rcopy(_, s):
    return [INTEGER(s)[i] for i in range(LENGTH(s))]


@dispatch(datatype(bool), LGLSXP)
def rcopy(_, s):
    return bool(LOGICAL(s)[0])


@dispatch(datatype(list), LGLSXP)
def rcopy(_, s):
    return [bool(LOGICAL(s)[i]) for i in range(LENGTH(s))]


@dispatch(datatype(float), REALSXP)
def rcopy(_, s):
    return REAL(s)[0]


@dispatch(datatype(list), REALSXP)
def rcopy(_, s):
    return [REAL(s)[i] for i in range(LENGTH(s))]


@dispatch(datatype(complex), CPLXSXP)
def rcopy(_, s):
    z = COMPLEX(s)[0]
    return complex(z.r, z.i)


@dispatch(datatype(list), CPLXSXP)
def rcopy(_, s):
    return [complex(COMPLEX(s)[i].r, COMPLEX(s)[i].i) for i in range(LENGTH(s))]


@dispatch(datatype(bytes), RAWSXP)
def rcopy(_, s):
    return string_at(RAW(s), LENGTH(s))


@dispatch(datatype(text_type), STRSXP)
def rcopy(_, s):
    return text_type(Rf_translateCharUTF8(STRING_ELT(s, 0)).decode("utf-8"))


@dispatch(datatype(list), STRSXP)
def rcopy(_, s):
    return [text_type(Rf_translateCharUTF8(STRING_ELT(s, i)).decode("utf-8")) for i in range(LENGTH(s))]


@dispatch(datatype(list), VECSXP)
def rcopy(_, s):
    return [rcopy(VECTOR_ELT(s, i)) for i in range(LENGTH(s))]


@dispatch(datatype(tuple), VECSXP)
def rcopy(_, s):
    return tuple(rcopy(list, s))


@dispatch(datatype(dict), VECSXP)
def rcopy(_, s):
    ret = dict()
    names = rnames(s)
    for i in range(LENGTH(s)):
        ret[names[i]] = rcopy(VECTOR_ELT(s, i))
    return ret


@dispatch(datatype(OrderedDict), VECSXP)
def rcopy(_, s):
    ret = OrderedDict()
    names = rnames(s)
    for i in range(LENGTH(s)):
        ret[names[i]] = rcopy(VECTOR_ELT(s, i))
    return ret


@dispatch(datatype(FunctionType), CLOSXP)
def rcopy(_, s, convert_args=True, convert_return=True, envir=R_GlobalEnv):
    r = RObject(s)

    def _(*args, **kwargs):
        return rcall(
            r, *args,
            _convert_args=convert_args,
            _convert_return=convert_return,
            _envir=envir, **kwargs)
    return _


@dispatch(datatype(object), EXTPTRSXP)
def rcopy(_, s):
    return to_pyo(s).value


@dispatch(datatype(object), CLOSXP)
def rcopy(_, s):
    return to_pyo(getattrib_p(s, "py_object")).value


# reticulate type
@dispatch(datatype(object), ENVSXP)
def rcopy(_, s):
    ret = to_pyo(Rf_findVarInFrame(s, rsym_p("pyobj"))).value
    return ret


@dispatch(datatype(RObject), SEXP)
def rcopy(_, s):
    return RObject(sexp(s))


@dispatch(object, RObject)
def rcopy(t, r, **kwargs):
    ret = rcopy(t, sexp(r), **kwargs)
    if isinstance(ret, SEXP):
        return RObject(ret)
    else:
        return ret


@dispatch(datatype(RObject), RObject)
def rcopy(_, s):
    return s


# default conversions

default = RClass("default")


@dispatch(datatype(default), NILSXP)
def rcopytype(_, s):
    return type(None)


@dispatch(datatype(default), INTSXP)
def rcopytype(_, s):
    return int if LENGTH(s) == 1 else list


@dispatch(datatype(default), LGLSXP)
def rcopytype(_, s):
    return bool if LENGTH(s) == 1 else list


@dispatch(datatype(default), REALSXP)
def rcopytype(_, s):
    return float if LENGTH(s) == 1 else list


@dispatch(datatype(default), CPLXSXP)
def rcopytype(_, s):
    return complex if LENGTH(s) == 1 else list


@dispatch(datatype(default), RAWSXP)
def rcopytype(_, s):
    return bytes


@dispatch(datatype(default), STRSXP)
def rcopytype(_, s):
    return text_type if LENGTH(s) == 1 else list


@dispatch(datatype(default), VECSXP)
def rcopytype(_, s):
    return list if Rf_isNull(getnames_p(s)) else OrderedDict


@dispatch(datatype(default), CLOSXP)
def rcopytype(_, s):
    return FunctionType


@dispatch(datatype(RClass("PyObject")), EXTPTRSXP)
def rcopytype(_, s):
    return object


@dispatch(datatype(RClass("PyCallable")), CLOSXP)
def rcopytype(_, s):
    return object


@dispatch(datatype(RClass("python.builtin.object")), ENVSXP)
def rcopytype(_, s):
    return object


@dispatch(object, SEXP)
def rcopytype(_, s):
    return RObject


@dispatch(SEXP)
def rcopy(s, **kwargs):
    s = sexp(s)
    for cls in rclass(s):
        T = rcopytype(RClass(cls), s)
        if T is not RObject:
            return rcopy(T, s, **kwargs)
    T = rcopytype(default, s)
    return rcopy(T, s, **kwargs)


@dispatch(RObject)
def rcopy(r, **kwargs):
    ret = rcopy(sexp(r), **kwargs)
    if isinstance(ret, SEXP):
        return RObject(ret)
    else:
        return ret


@dispatch(object)
def rcopy(r):
    return r


# python to r conversions

@dispatch(datatype(RClass("NULL")), type(None))
def sexp(_, n):
    return R_NilValue


@dispatch(datatype(RClass("logical")), bool)
def sexp(_, s):
    return rlogical_p(s)


@dispatch(datatype(RClass("integer")), int)
def sexp(_, s):
    return rint_p(s)


@dispatch(datatype(RClass("numeric")), float)
def sexp(_, s):
    return rdouble_p(s)


@dispatch(datatype(RClass("complex")), complex)
def sexp(_, s):
    return sexp(Rf_ScalarComplex(Rcomplex(r=s.real, i=s.imag)))


@dispatch(datatype(RClass("character")), string_types)
def sexp(_, s):
    return rstring_p(s)


@dispatch(datatype(RClass("raw")), bytes)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(SEXPTYPE.RAWSXP, n))
    try:
        for i in range(n):
            RAW(x)[i] = s[i]
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(datatype(RClass("logical")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(SEXPTYPE.LGLSXP, n))
    try:
        for i in range(n):
            LOGICAL(x)[i] = s[i]
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(datatype(RClass("integer")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(SEXPTYPE.INTSXP, n))
    try:
        for i in range(n):
            INTEGER(x)[i] = s[i]
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(datatype(RClass("numeric")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(SEXPTYPE.REALSXP, n))
    try:
        for i in range(n):
            REAL(x)[i] = s[i]
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(datatype(RClass("complex")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(SEXPTYPE.CPLXSXP, n))
    try:
        for i in range(n):
            xi = COMPLEX(x)[i]
            z = s[i]
            xi.r = z.real
            xi.i = z.imag
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(datatype(RClass("character")), list)
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(SEXPTYPE.STRSXP, n))
    try:
        for i in range(n):
            isascii = all(ord(c) < 128 for c in s[i])
            b = s[i].encode("utf-8")
            SET_STRING_ELT(x, i, Rf_mkCharLenCE(b, len(b), 0 if isascii else 1))
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(datatype(RClass("list")), (list, tuple))
def sexp(_, s):
    n = len(s)
    x = Rf_protect(Rf_allocVector(SEXPTYPE.VECSXP, n))
    try:
        for i in range(n):
            SET_VECTOR_ELT(x, i, sexp(s[i]))
    finally:
        Rf_unprotect(1)
    return sexp(x)


@dispatch(datatype(RClass("list")), (dict, OrderedDict))
def sexp(_, s):
    v = Rf_protect(sexp(RClass("list"), list(s.values())))
    try:
        Rf_setAttrib(v, R_NamesSymbol, sexp(RClass("character"), list(s.keys())))
    finally:
        Rf_unprotect(1)
    return v


def sexp_dots():
    s = Rf_protect(Rf_list1(R_MissingArg))
    SET_TAG(s, R_DotsSymbol)
    Rf_unprotect(1)
    return s


def sexp_py_object(obj):
    if inspect.isclass(obj):
        return sexp(RClass("PyClass"), obj)
    if callable(obj):
        return sexp(RClass("PyCallable"), obj)
    else:
        return sexp(RClass("PyObject"), obj)


@CFUNCTYPE(SEXP, SEXP, SEXP, SEXP, SEXP)
def rchitect_callback(exptr, arglist, _convert_args, _convert_return):
    convert_args = rcopy(bool, sexp(_convert_args))
    convert_return = rcopy(bool, sexp(_convert_return))
    f = to_pyo(exptr).value
    args = []
    kwargs = {}
    names = rnames(arglist)
    try:
        if convert_args:
            for i in range(LENGTH(arglist)):
                if names and names[i]:
                    kwargs[names[i]] = rcopy(VECTOR_ELT(arglist, i))
                else:
                    args.append(rcopy(VECTOR_ELT(arglist, i)))
        else:
            for i in range(LENGTH(arglist)):
                if names and names[i]:
                    kwargs[names[i]] = sexp(VECTOR_ELT(arglist, i))
                else:
                    args.append(sexp(VECTOR_ELT(arglist, i)))
        if convert_return:
            return sexp(f(*args, **kwargs)).value
        else:
            ret = f(*args, **kwargs)
            return sexp_py_object(ret).value
    except Exception as e:
        return rcall_p(("base", "simpleError"), str(e)).value


@dispatch(datatype(RClass("function")), Callable)
def sexp(_, f, convert_args=True, convert_return=True, invisible=False):
    fextptr = rextptr(f)
    dotlist = rlang_p("list", R_DotsSymbol)
    body = rlang_p(".Call", "rchitect_callback", fextptr, dotlist, convert_args, convert_return)
    if invisible:
        body = rlang_p("invisible", body)
    lang = rlang_p(rsym("function"), sexp_dots(), body)
    status = c_int()
    val = R_tryEval(lang, R_GlobalEnv, status)
    return sexp(val)


@dispatch(datatype(RClass("PyObject")), object)
def sexp(_, s):
    if (isinstance(s, RObject) or isinstance(s, SEXP)) and "PyObject" in rclass(s):
        return sexp(s)
    p = rextptr(s)
    setclass(p, "PyObject")
    return p


@dispatch(datatype(RClass("PyCallable")), Callable)
def sexp(_, f, convert_args=True, convert_return=False, invisible=False):
    p = Rf_protect(sexp(RClass("function"), f,
                        convert_args=convert_args,
                        convert_return=convert_return,
                        invisible=invisible))
    setattrib(p, "py_object", sexp(RClass("PyObject"), f))
    setclass(p, ["PyCallable", "PyObject"])
    Rf_unprotect(1)
    return p


@dispatch(datatype(RClass("PyClass")), object)
def sexp(_, s):
    p = Rf_protect(sexp(RClass("PyCallable"), s))
    setclass(p, ["PyClass", "PyCallable", "PyObject"])
    Rf_unprotect(1)
    return p


# default conversions

def sexpnum(s):
    return TYPEOF(s)


@dispatch(SEXP)
def sexptype(s):
    return SEXPTYPE.from_sexpnum(sexpnum(s))


@dispatch(bool)
def sexpclass(s):
    return "logical"


@dispatch(int)
def sexpclass(s):
    return "integer"


@dispatch(float)
def sexpclass(s):
    return "numeric"


@dispatch(complex)
def sexpclass(s):
    return "complex"


@dispatch(string_types)
def sexpclass(s):
    return "character"


@dispatch(list)
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


@dispatch((tuple, dict, OrderedDict))
def sexpclass(s):
    return "list"


@dispatch(type)
def sexpclass(f):
    return "PyClass"


@dispatch(Callable)
def sexpclass(f):
    return "PyCallable"


@dispatch(object)
def sexpclass(f):
    return "PyObject"


@dispatch(type(None))
def sexp(n):
    return R_NilValue


@dispatch(SEXP)
def sexp(s):
    return cast(s, sexptype(s))


@dispatch(RObject)
def sexp(r):
    return r.p


@dispatch(object)
def sexp(s, **kwargs):
    rcls = sexpclass(s)
    return sexp(RClass(rcls), s, **kwargs)


def robject(*args, **kwargs):
    if len(args) == 2 and isinstance(args[0], text_type):
        return RObject(sexp(RClass(args[0]), args[1], **kwargs))
    elif len(args) == 1:
        return RObject(sexp(args[0], **kwargs))
    else:
        raise TypeError("wrong number of arguments or argument types")


# misc functions

def getoption_p(key):
    return Rf_GetOption1(Rf_install(key.encode("utf-8")))


def getoption(key):
    return RObject(getoption_p(key))


def roption(key, default=None):
    ret = rcopy(getoption_p(key))
    return ret if ret is not None else default


def setoption(key, value):
    kwargs = {key: value}
    rcall_p(("base", "options"), **kwargs)


def getattrib_p(s, key):
    s = sexp(s)
    return sexp(Rf_getAttrib(s, rsym_p(key) if isinstance(key, text_type) else key))


def getattrib(s, key):
    return RObject(getattrib_p(s, key))


def setattrib(s, key, value):
    s = sexp(s)
    v = Rf_protect(sexp(value))
    try:
        Rf_setAttrib(s, rsym_p(key) if isinstance(key, text_type) else key, v)
    finally:
        Rf_unprotect(1)


def getnames_p(s):
    return sexp(getattrib_p(s, R_NamesSymbol))


def getnames(s):
    return RObject(getnames_p(s))


def rnames(s):
    return rcopy(list, getnames_p(s))


def setnames(s, names):
    setattrib(s, R_NamesSymbol, names)


def getclass_p(s, singleString=0):
    return sexp(R_data_class(sexp(s), singleString))


def getclass(s, singleString=0):
    return RObject(getclass_p(s, singleString))


def rclass(s, singleString=0):
    return rcopy(text_type if singleString else list, getclass_p(s, singleString))


def setclass(s, classes):
    setattrib(s, R_ClassSymbol, classes)


def _process_events():
    if sys.platform == "win32" or sys.platform == "darwin":
        R_ProcessEvents()
    if sys.platform.startswith("linux") or sys.platform == "darwin" or os.name == "posix":
        what = R_checkActivity(0, 1)
        if what:
            R_runHandlers(R_InputHandlers, what)


def process_events():
    try:
        rexec_p(_process_events)
    except Exception:
        pass
