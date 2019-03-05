from rapi._libR import ffi, lib
from six import string_types

from .types import RObject, robject, sexp, is_sexp


def rchar_p(s):
    isascii = all(ord(c) < 128 for c in s)
    b = s.encode("utf-8")
    return lib.Rf_mkCharLenCE(b, len(b), lib.CE_NATIVE if isascii else lib.CE_UTF8)

def rchar(s):
    return robject(rchar_p(s))


def rstring_p(s):
    return lib.Rf_ScalarString(rchar_p(s))


def rstring(s):
    return robject(rstring_p(s))


def rparse_p(s):
    status = ffi.new("ParseStatus[1]")
    s = lib.Rf_protect(rstring_p(s))
    ret = lib.R_ParseVector(s, -1, status, lib.R_NilValue)
    try:
        if status[0] != lib.PARSE_OK:
            raise Exception("Parse error")
    finally:
        lib.Rf_unprotect(1)
    return ret


def rparse(s):
    return robject(rparse_p(s))


def reval_p(s):
    if isinstance(s, string_types):
        expressions = rparse_p(s)
    elif isinstance(s, RObject) and lib.TYPEOF(sexp(s)) == lib.EXPRSXP:
        expressions = sexp(s)
    elif is_sexp(s) and lib.TYPEOF(s) == lib.EXPRSXP:
        expressions = s

    lib.Rf_protect(expressions)
    ret = lib.R_NilValue
    status = ffi.new("int[1]")
    try:
        for i in range(0, lib.Rf_length(expressions)):
            ret = lib.R_tryEval(lib.VECTOR_ELT(expressions, i), lib.R_GlobalEnv, status)
            if status[0] != 0:
                raise RuntimeError("reval error")
    finally:
        lib.Rf_unprotect(1)
    return ret


def reval(s):
    return robject(reval_p(s))
