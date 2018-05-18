from ctypes import cast, c_void_p

from . import internals
from . import types
from .utils import cglobal
from .internals import R_CallMethodDef


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

    for name, (var, vtype) in internals._global_registry.items():
        try:
            if vtype == types.SEXP:
                var.value = cglobal(name, libR, vtype).value
            else:
                var.set_constant(cglobal(name, libR, vtype))
        except Exception:
            if verbose:
                print("warning: cannot import global {}".format(name))

    from . import interface
    types.internals = internals
    types.interface = interface

    from .interface import rapi_callback
    dll = internals.R_getEmbeddingDllInfo()
    CallEntries = (R_CallMethodDef * 2)()
    CallEntries[0] = R_CallMethodDef(b"rapi_callback", cast(rapi_callback, c_void_p), 2)
    CallEntries[1] = R_CallMethodDef(None, None, 0)
    internals.R_registerRoutines(dll, None, CallEntries, None, None)
