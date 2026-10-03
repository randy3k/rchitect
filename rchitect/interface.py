from collections import OrderedDict
import struct
import sys
from types import FunctionType

import rchitect._cffi as _cffi
from rchitect._cffi import ffi, lib
from .console import capture_console, read_stderr, read_stdout, utf8tosystem
from .setup import ensure_initialized


# =============================================================================
# 1. RObject & Conversion
# =============================================================================


_SEXP_CTYPE = ffi.typeof("SEXP")


def _sexp_cdata_to_ptr(x):
    if ffi.typeof(x) is _SEXP_CTYPE:
        return int(ffi.cast("uintptr_t", x))
    return None


class RObject(object):
    __slots__ = ("_ptr", "_s")

    def __init__(self, s):
        if isinstance(s, ffi.CData) and ffi.typeof(s) is _SEXP_CTYPE:
            self._s = s
            self._ptr = int(ffi.cast("uintptr_t", s))
        else:
            raise TypeError("expect SEXP")
        _cffi._c_preserve_sexp(self._ptr)

    @property
    def s(self):
        if self._s is None:
            self._s = ffi.cast("SEXP", self._ptr)
        return self._s

    def __del__(self, _is_finalizing=sys.is_finalizing):
        try:
            if not _is_finalizing():
                _cffi._c_release_sexp(self._ptr)
        except Exception:
            pass

    def __eq__(self, other):
        if isinstance(other, RObject):
            return self._ptr == other._ptr
        return False

    def __repr__(self):
        with capture_console(flushable=False):  # need to capture stdout
            try:
                rprint(self)
            except Exception:
                output = ""
            else:
                output = read_stdout() or ""

        name = "RObject{{{}}}".format(_cffi._c_sexptype_name(self))
        if output:
            return name + "\n" + output.rstrip()
        else:
            return name

    def __call__(self, *args, **kwargs):
        return rcall(self, *args, **kwargs)


def box(x):
    if isinstance(x, RObject):
        return x
    if isinstance(x, ffi.CData) and ffi.typeof(x) is _SEXP_CTYPE:
        return RObject(x)
    raise TypeError("expect SEXP or RObject")


def unbox(x):
    if isinstance(x, RObject):
        return x.s
    elif isinstance(x, ffi.CData) and ffi.typeof(x) is _SEXP_CTYPE:
        return x
    raise TypeError("expect SEXP or RObject")


def _wrap_r_function(r, asis=False, convert=True):
    def f(*args, **kwargs):
        return rcall(r, *args, _asis=asis, _convert=convert, **kwargs)

    f.__robject__ = r
    f.asis = asis
    f.convert = convert
    return f


_cffi._cdata_type = ffi.CData
_cffi._sexp_cdata_to_ptr = _sexp_cdata_to_ptr

lib._rchitect_init_conv(
    ffi.cast("void *", id(_cffi)),
    ffi.cast("void *", id(RObject)),
    ffi.cast("void *", id(OrderedDict)),
    ffi.cast("void *", id(FunctionType)),
    ffi.cast("void *", id(_wrap_r_function)),
)


def rcopy(*args, **kwargs):
    ensure_initialized()
    asis = bool(kwargs.get("asis", False))
    convert = bool(kwargs.get("convert", True))
    if len(args) == 1:
        return _cffi._c_rcopy(None, args[0], asis, convert)
    elif len(args) == 2:
        return _cffi._c_rcopy(args[0], args[1], asis, convert)
    else:
        raise TypeError("wrong number of arguments")


def robject(*args, **kwargs):
    ensure_initialized()
    asis = bool(kwargs.get("asis", False))
    has_convert = "convert" in kwargs and kwargs["convert"] is not None
    convert = bool(kwargs.get("convert", True))
    invisible = int(bool(kwargs.get("invisible", False)))
    if len(args) == 2 and isinstance(args[0], str):
        return _cffi._c_sexp(args[0], args[1], asis, has_convert, convert, invisible)
    elif len(args) == 1:
        return _cffi._c_sexp(None, args[0], asis, has_convert, convert, invisible)
    else:
        raise TypeError("wrong number of arguments or argument types")


def rint(s):
    ensure_initialized()
    return _cffi._c_sexp("integer", int(s))


def rlogical(s):
    ensure_initialized()
    return _cffi._c_sexp("logical", bool(s))


def rdouble(s):
    ensure_initialized()
    return _cffi._c_sexp("numeric", float(s))


def rstring(s):
    ensure_initialized()
    return _cffi._c_sexp("character", s)


def rsym(s, t=None):
    ensure_initialized()
    return _cffi._c_rsym(s, t)


# =============================================================================
# 2. Parsing, Evaluation & Calls
# =============================================================================


def parse_text(s):
    ensure_initialized()
    with capture_console():  # need to capture stderr
        ret, status = _cffi._c_parse_text(utf8tosystem(s))
        if status != lib.PARSE_OK:
            err = read_stderr().strip() or "Error"
        else:
            err = None
        return ret, status, err


def parse_text_incomplete(s):
    ensure_initialized()
    with capture_console(flushable=False):  # need to capture stderr
        return not _cffi._c_parse_text_complete(utf8tosystem(s))


def parse_text_complete(s):
    return not parse_text_incomplete(s)


def rparse(s):
    ret, status, err = parse_text(s)
    if status != lib.PARSE_OK:
        raise RuntimeError("{}".format(err))
    return ret


def reval(s, envir=None):
    ensure_initialized()
    if isinstance(s, str):
        s = rparse(s)
    else:
        s = box(s)

    if envir is not None:
        # `sys.frame()` doesn't work with R_tryEval as it doesn't create R stacks,
        # we use `base::eval` instead.
        return rcall(("base", "eval"), s, _envir=envir)

    with capture_console():  # need to capture stderr
        ret, status = _cffi._c_reval(s)
        if status != 0:
            err = read_stderr().strip() or "Error"
            raise RuntimeError("{}".format(err))
    return ret


def rlang(f, *args, **kwargs):
    ensure_initialized()
    _asis = kwargs.pop("_asis", False)
    return _cffi._c_rlang(f, args, kwargs, bool(_asis))


def rcall(f, *args, **kwargs):
    ensure_initialized()
    _envir = kwargs.pop("_envir", None)
    _asis = kwargs.pop("_asis", False)
    _convert = kwargs.pop("_convert", False)
    with capture_console():  # need to capture stderr
        ret, status = _cffi._c_rcall(f, args, kwargs, _envir, bool(_asis), bool(_convert))
        if status != 0:
            err = read_stderr().strip() or "Error"
            raise RuntimeError("{}".format(err))
    return ret


def rprint(s, envir=None):
    # Bind value to a variable in a local mask environment, mirroring R's
    # internal PrintObjectS3() (`local({ x <- <value>; base::print(x) })`).
    # This avoids evaluating `s` when it is a symbol or language/call object,
    # avoids inlining `s` into the call AST (which would alter `substitute(x)`
    # inside print methods and bloat `sys.calls()`/error messages), and avoids
    # clobbering `x` in `envir`.
    ensure_initialized()
    s_obj = box(s)
    symx = rsym("x")
    mask = new_env(parent=envir)
    lib.Rf_defineVar(symx.s, s_obj.s, mask.s)
    try:
        rcall(("base", "print"), symx, _envir=mask)
    finally:
        lib.Rf_defineVar(symx.s, lib.R_NilValue, mask.s)


# =============================================================================
# 3. Attributes, Classes, Options & Environments
# =============================================================================


def getattrib(s, key):
    ensure_initialized()
    return _cffi._c_getattrib(s, key)


def setattrib(s, key, value):
    ensure_initialized()
    _cffi._c_setattrib(s, key, value)


def rnames(s):
    ensure_initialized()
    return _cffi._c_rnames(s)


def rclass(s, singleString=0):
    ensure_initialized()
    return _cffi._c_rclass(s, bool(singleString))


def setclass(s, classes):
    ensure_initialized()
    _cffi._c_setclass(s, classes)


def getoption(key):
    ensure_initialized()
    return _cffi._c_getoption(key)


def roption(key, default=None):
    ensure_initialized()
    ret = _cffi._c_roption(key)
    return ret if ret is not None else default


def setoption(key, value):
    rcall(("base", "options"), **{key: value})


def new_env(parent=None):
    ensure_initialized()
    return _cffi._c_new_env(parent)


def set_hook(event, fun):
    rcall(("base", "setHook"), event, fun)


def package_event(pkg, event):
    return rcall(("base", "packageEvent"), pkg, event)


# =============================================================================
# 4. Event Loop & Session Info
# =============================================================================


def process_events():
    lib.process_events()


def polled_events():
    lib.polled_events()


def peek_event():
    return lib.peek_event()


def greeting():
    info = rcopy(rcall("R.Version"))
    return '{} -- "{}"\nPlatform: {} ({}-bit)\n'.format(
        info["version.string"],
        info["nickname"],
        info["platform"],
        8 * struct.calcsize("P"),
    )

