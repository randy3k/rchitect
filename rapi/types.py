from rapi._libR import ffi, lib


def is_sexp(s):
    return isinstance(s, ffi.CData) and ffi.typeof(s).cname == 'struct SEXPREC *'


def is_robject(s):
    return isinstance(s, RObject)


class RObject(object):
    def __init__(self, s):
        if not is_sexp(s):
            raise TypeError("expect an SEXP object")
        self.s = s
        lib.R_PreserveObject(self.s)

    def __del__(self):
        lib.R_ReleaseObject(self.s)


def robject(s):
    return RObject(s)


def sexp(s):
    if is_sexp(s):
        return s
    elif is_robject(s):
        return s.s
    else:
        raise NotImplementedError()
