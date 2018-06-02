from ctypes import cast, c_void_p

from . import internals
from .utils import cglobal


def notavaiable(*args):
    raise NotImplementedError("method not avaiable")


def bootstrap(libR, verbose=True):
    # rver = rversion(libR)

    for name, (sign, setter) in internals._function_registry.items():
        try:
            f = getattr(libR, sign.cname)
            f.restype = sign.restype
            if sign.argtypes is not None:
                f.argtypes = sign.argtypes
            setter(f)
        except Exception:
            setter(notavaiable)
            if verbose:
                print("warning: cannot import function {}".format(name))

    for name, (var, vtype) in internals._sexp_registry.items():
        try:
            var.value = cglobal(name, libR, vtype).value
        except Exception:
            if verbose:
                print("warning: cannot import sexp {}".format(name))

    for name, (var, vtype) in internals._constant_registry.items():
        try:
            var.set_constant(cglobal(name, libR, vtype))
        except Exception as e:
            if verbose:
                print("warning: cannot import constant {}".format(name))

    from . import types
    from .types import RObject
    from .internals import R_PreserveObject, R_ReleaseObject, Rf_isNull, LENGTH, TYPEOF
    from .interface import sexp, rlang, rcall, rcopy

    types.sexpnum = lambda s: TYPEOF(s)

    RObject.sexp = lambda self, p: sexp(p)
    RObject.preserve = lambda self, p: R_PreserveObject(p)
    RObject.release = lambda self, p: R_ReleaseObject(p)

    def _repr(self):
        output = rcall("capture.output", rlang("print", self.p))
        name = "<class 'RObject{{{}}}'>\n".format(str(type(self.p).__name__))
        if not Rf_isNull(sexp(output)) and LENGTH(sexp(output)) > 0:
            return name + "\n".join(rcopy(list, output))
        else:
            return name

    RObject.__repr__ = _repr

    from .internals import R_CallMethodDef
    from .interface import rapi_callback

    dll = internals.R_getEmbeddingDllInfo()
    CallEntries = (R_CallMethodDef * 2)()
    CallEntries[0] = R_CallMethodDef(b"rapi_callback", cast(rapi_callback, c_void_p), 3)
    CallEntries[1] = R_CallMethodDef(None, None, 0)
    internals.R_registerRoutines(dll, None, CallEntries, None, None)
