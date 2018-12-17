from __future__ import unicode_literals

from ctypes import c_int
from .internals import PROTECT, UNPROTECT, Rf_mkString, R_ParseVector, R_NilValue
from .internals import LENGTH, Rf_eval, VECTOR_ELT, Rf_error, Rf_isExpression


def R_ParseEvalString(buf, env):
    s = PROTECT(Rf_mkString(buf))
    status = c_int()
    ps = PROTECT(R_ParseVector(s, -1, status, R_NilValue))
    if (status.value != 1 or Rf_isExpression(ps) or LENGTH(ps) != 1):
        UNPROTECT(2)
        raise Rf_error("parse error".encode("utf-8"))

    val = Rf_eval(VECTOR_ELT(ps, 0), env)
    UNPROTECT(2)
    return val
