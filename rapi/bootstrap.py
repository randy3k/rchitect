from . import internals
from . import types
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

    for name, (var, vtype) in internals._global_registry.items():
        try:
            var.value = cglobal(name, libR, vtype).value
        except Exception:
            if verbose:
                print("warning: cannot import global {}".format(name))

    from . import interface
    types.internals = internals
    types.interface = interface
