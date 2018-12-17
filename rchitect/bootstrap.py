from __future__ import unicode_literals

import sys

from ctypes import c_int, c_size_t, c_char, c_char_p, c_void_p, cast, pointer
from ctypes import POINTER, CFUNCTYPE, PYFUNCTYPE, Structure

from .types import SEXP
from .utils import which_rhome, find_libR, find_libRgraphapp, ensure_path, ccall, cglobal


callback_dict = {
    "R_Suicide": None,
    "R_ShowMessage": None,
    "R_ReadConsole": None,
    "R_WriteConsole":  None,
    "R_WriteConsoleEx": None,
    "R_ResetConsole": None,
    "R_FlushConsole": None,
    "R_ClearerrConsole": None,
    "R_Busy": None,
    "R_CleanUp": None,
    "R_ShowFiles": None,
    "R_ChooseFile": None,
    "R_EditFile": None,
    "R_loadhistory": None,
    "R_savehistory": None,
    "R_addhistory": None,
    "R_EditFiles": None,
    "do_selectlist": None,
    "do_dataentry": None,
    "do_dataviewer": None,
    "R_ProcessEvents": None,
    "R_PolledEvents": None,
    "R_YesNoCancel": None  # windows only
}

callback_signature = {
    "R_Suicide": CFUNCTYPE(None, c_char_p),
    "R_ShowMessage": CFUNCTYPE(None, c_char_p),
    "R_ReadConsole": CFUNCTYPE(c_int, c_char_p, POINTER(c_char), c_int, c_int),
    "R_WriteConsole":  CFUNCTYPE(None, c_char_p, c_int),
    "R_WriteConsoleEx": CFUNCTYPE(None, c_char_p, c_int, c_int),
    "R_ResetConsole": CFUNCTYPE(None),
    "R_FlushConsole": CFUNCTYPE(None),
    "R_ClearerrConsole": CFUNCTYPE(None),
    "R_Busy": CFUNCTYPE(None, c_int),
    "R_CleanUp": CFUNCTYPE(None, c_int, c_int, c_int),
    "R_ShowFiles": CFUNCTYPE(c_int, c_int, POINTER(c_char_p), POINTER(c_char_p), c_char_p, c_int, c_char_p),
    "R_ChooseFile": CFUNCTYPE(c_int, c_int, POINTER(c_char), c_int),
    "R_EditFile": CFUNCTYPE(c_int, c_char_p),
    "R_loadhistory": CFUNCTYPE(None, SEXP, SEXP, SEXP, SEXP),
    "R_savehistory": CFUNCTYPE(None, SEXP, SEXP, SEXP, SEXP),
    "R_addhistory": CFUNCTYPE(None, SEXP, SEXP, SEXP, SEXP),
    "R_EditFiles": CFUNCTYPE(c_int, POINTER(c_char_p), POINTER(c_char_p), POINTER(c_char_p)),
    "do_selectlist": CFUNCTYPE(SEXP, SEXP, SEXP, SEXP, SEXP),
    "do_dataentry": CFUNCTYPE(None, SEXP, SEXP, SEXP, SEXP),
    "do_dataviewer": CFUNCTYPE(None, SEXP, SEXP, SEXP, SEXP),
    "R_ProcessEvents": CFUNCTYPE(None),
    "R_PolledEvents": CFUNCTYPE(None),
    "R_YesNoCancel": CFUNCTYPE(c_int, c_char_p)  # windows only
}


class RStart(Structure):
    _fields_ = [
        ('R_Quiet', c_int),
        ('R_Slave', c_int),
        ('R_Interactive', c_int),
        ('R_Verbose', c_int),
        ('LoadSiteFile', c_int),
        ('LoadInitFile', c_int),
        ('DebugInitFile', c_int),
        ('RestoreAction', c_int),
        ('SaveAction', c_int),
        ('vsize', c_size_t),
        ('nsize', c_size_t),
        ('max_vsize', c_size_t),
        ('max_nsize', c_size_t),
        ('ppsize', c_size_t),
        ('NoRenviron', c_int),
        ('rhome', POINTER(c_char)),
        ('home', POINTER(c_char)),
        ('ReadConsole', callback_signature["R_ReadConsole"]),
        ('WriteConsole', callback_signature["R_WriteConsole"]),
        ('CallBack', callback_signature["R_PolledEvents"]),
        ('ShowMessage', callback_signature["R_ShowMessage"]),
        ('YesNoCancel', callback_signature["R_YesNoCancel"]),
        ('Busy', callback_signature["R_Busy"]),
        ('CharacterMode', c_int),
        ('WriteConsoleEx', callback_signature["R_WriteConsoleEx"])
    ]


callback_pointer = []


def get_cb_ptr(name):
    if callback_dict[name]:
        return callback_signature[name](callback_dict[name])
    else:
        return cast(None, callback_signature[name])


def set_posix_cb_ptr(libR, ptrname, name):
    if callback_dict[name]:
        cb_ptr = get_cb_ptr(name)
        # prevent gc
        callback_pointer.append(cb_ptr)
        c_void_p.in_dll(libR, ptrname).value = cast(cb_ptr, c_void_p).value


def setup_posix(libR):

    set_posix_cb_ptr(libR, "ptr_R_Suicide", "R_Suicide")
    set_posix_cb_ptr(libR, "ptr_R_ShowMessage", "R_ShowMessage")
    set_posix_cb_ptr(libR, "ptr_R_ReadConsole", "R_ReadConsole")
    set_posix_cb_ptr(libR, "ptr_R_WriteConsole", "R_WriteConsole")
    set_posix_cb_ptr(libR, "ptr_R_WriteConsoleEx", "R_WriteConsoleEx")
    set_posix_cb_ptr(libR, "ptr_R_ResetConsole", "R_ResetConsole")
    set_posix_cb_ptr(libR, "ptr_R_FlushConsole", "R_FlushConsole")
    set_posix_cb_ptr(libR, "ptr_R_ClearerrConsole", "R_ClearerrConsole")
    set_posix_cb_ptr(libR, "ptr_R_Busy", "R_Busy")

    if callback_dict["R_CleanUp"]:
        ptr_R_CleanUp = c_void_p.in_dll(libR, 'ptr_R_CleanUp')
        orig_cleanup = PYFUNCTYPE(None, c_int, c_int, c_int)(ptr_R_CleanUp.value)

        def _handler(save_type, status, runlast):
            callback_dict["R_CleanUp"](save_type, status, runlast)
            orig_cleanup(save_type, status, runlast)

        ptr_new_R_CleanUp = PYFUNCTYPE(None, c_int, c_int, c_int)(_handler)
        callback_pointer.append(ptr_new_R_CleanUp)
        ptr_R_CleanUp.value = cast(ptr_new_R_CleanUp, c_void_p).value

    set_posix_cb_ptr(libR, "ptr_R_ShowFiles", "R_ShowFiles")
    set_posix_cb_ptr(libR, "ptr_R_ChooseFile", "R_ChooseFile")
    set_posix_cb_ptr(libR, "ptr_R_EditFile", "R_EditFile")
    set_posix_cb_ptr(libR, "ptr_R_loadhistory", "R_loadhistory")
    set_posix_cb_ptr(libR, "ptr_R_savehistory", "R_savehistory")
    set_posix_cb_ptr(libR, "ptr_R_addhistory", "R_addhistory")
    set_posix_cb_ptr(libR, "ptr_R_EditFiles", "R_EditFiles")
    set_posix_cb_ptr(libR, "ptr_do_selectlist", "do_selectlist")
    set_posix_cb_ptr(libR, "ptr_do_dataentry", "do_dataentry")
    set_posix_cb_ptr(libR, "ptr_do_dataviewer", "do_dataviewer")
    set_posix_cb_ptr(libR, "ptr_R_ProcessEvents", "R_ProcessEvents")
    set_posix_cb_ptr(libR, "ptr_do_dataviewer", "do_dataviewer")
    set_posix_cb_ptr(libR, "R_PolledEvents", "R_PolledEvents")


def setup_win32(libR, rhome, args):
    SA_NORESTORE = 0
    SA_RESTORE = 1
    # SA_DEFAULT = 2
    SA_NOSAVE = 3
    SA_SAVE = 4
    SA_SAVEASK = 5
    # SA_SUICIDE = 6

    libR.R_setStartTime()
    rstart = RStart()
    libR.R_DefParams(pointer(rstart))

    rstart.R_Quiet = "--quiet" in args
    rstart.R_Slave = "--slave" in args
    rstart.R_Interactive = 1
    rstart.R_Verbose = "--verbose" in args
    rstart.LoadSiteFile = "--no-site-file" not in args
    rstart.LoadInitFile = "--no-init-file" not in args
    if "--no-restore" in args:
        rstart.RestoreAction = SA_NORESTORE
    else:
        rstart.RestoreAction = SA_RESTORE
    if "--no-save" in args:
        rstart.SaveAction = SA_NOSAVE
    elif "--save" in args:
        rstart.SaveAction = SA_SAVE
    else:
        rstart.SaveAction = SA_SAVEASK
    rstart.NoRenviron = "--no-environ" in args
    rstart.rhome = ccall("get_R_HOME", libR, POINTER(c_char), [])
    rstart.home = ccall("getRUser", libR, POINTER(c_char), [])
    rstart.ReadConsole = get_cb_ptr("R_ReadConsole")
    rstart.WriteConsole = get_cb_ptr("R_WriteConsole")
    rstart.CallBack = get_cb_ptr("R_PolledEvents")
    rstart.ShowMessage = get_cb_ptr("R_ShowMessage")
    rstart.YesNoCancel = get_cb_ptr("R_YesNoCancel")
    rstart.Busy = get_cb_ptr("R_Busy")
    rstart.CharacterMode = 0
    rstart.WriteConsoleEx = get_cb_ptr("R_WriteConsoleEx")

    libR.R_SetParams(pointer(rstart))

    try:
        libRgraphapp = find_libRgraphapp(rhome)
        libRgraphapp.GA_initapp(0, 0)
        libR.readconsolecfg()
    except RuntimeError:
        print("Cannot locate Rgraphapp share library.")

    # prevent gc
    RStart.rstart = rstart


class Machine(object):
    instance = None
    libR = None
    bootstrapped = False

    def __init__(self, rhome=None, set_default_callbacks=True, verbose=False):

        if not self.instance:
            Machine.instance = self

        self.verbose = verbose

        if not rhome:
            rhome = which_rhome()

        ensure_path(rhome)
        libR = find_libR(rhome)

        self.rhome = rhome
        self.libR = libR

        if set_default_callbacks:
            from . import callbacks
            self.set_callback("R_ShowMessage", callbacks.show_message)
            self.set_callback("R_ReadConsole", callbacks.read_console)
            self.set_callback("R_WriteConsoleEx", callbacks.write_console_ex)
            self.set_callback("R_Busy", callbacks.busy)
            self.set_callback("R_PolledEvents", callbacks.polled_events)
            self.set_callback("R_YesNoCancel", callbacks.ask_yes_no_cancel)

    def set_callback(self, name, func):
        if name not in callback_dict:
            raise ValueError("method not found")
        callback_dict[name] = func

    def start(self, arguments=[
                "rchitect",
                "--quiet",
                "--no-save",
                "--no-restore"
            ]):

        if self.instance and self.instance.bootstrapped:
            raise RuntimeError("R has been started.")

        initialized = cglobal("R_NilValue", self.libR).value is not None

        if not initialized:
            argn = len(arguments)
            argv = (c_char_p * argn)()
            for i, a in enumerate(arguments):
                argv[i] = c_char_p(a.encode('utf-8'))

            if sys.platform.startswith("win"):
                setup_win32(self.libR, self.rhome, arguments)
                self.libR.R_set_command_line_arguments(argn, argv)
            else:
                self.libR.Rf_initialize_R(argn, argv)
                setup_posix(self.libR)

            self.libR.setup_Rmainloop()

        bootstrap(self.libR, verbose=self.verbose)

        import rchitect.namespace
        rchitect.namespace.set_hook_for_reticulate()
        rchitect.namespace.inject_rchitect_environment()

        self.bootstrapped = True

    def run_loop(self):
        self.libR.run_Rmainloop()


def notavaiable(*args):
    raise NotImplementedError("method not avaiable")


def bootstrap(libR, verbose=True):
    from .types import RObject
    from .internals import _function_registry, _sexp_registry, _constant_registry
    from .internals import R_PreserveObject, R_ReleaseObject, Rf_isNull, LENGTH
    from .interface import sexp, rlang, rcall, rcopy

    for name, (sign, setter) in _function_registry.items():
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

    for name, (var, vtype) in _sexp_registry.items():
        try:
            var.value = cglobal(name, libR, vtype).value
        except Exception:
            if verbose:
                print("warning: cannot import sexp {}".format(name))

    for name, (var, vtype) in _constant_registry.items():
        try:
            var.set_constant(cglobal(name, libR, vtype))
        except Exception:
            if verbose:
                print("warning: cannot import constant {}".format(name))

    RObject.sexp = lambda self, p: sexp(p)
    RObject.preserve = lambda self, p: R_PreserveObject(p)
    RObject.release = lambda self, p: R_ReleaseObject(p)

    def _repr(self):
        output = rcall("capture.output", rlang("print", self.p))
        name = "<class 'RObject{{{}}}'>\n".format(str(type(self.p).__name__))
        if not Rf_isNull(sexp(output)) and LENGTH(sexp(output)) > 0:
            try:
                return name + "\n".join(rcopy(list, output))
            except Exception:
                pass
        return name

    RObject.__repr__ = _repr

    from .internals import R_CallMethodDef, R_getEmbeddingDllInfo, R_registerRoutines
    from .interface import rchitect_callback

    dll = R_getEmbeddingDllInfo()
    CallEntries = (R_CallMethodDef * 2)()
    CallEntries[0] = R_CallMethodDef(b"rchitect_callback", cast(rchitect_callback, c_void_p), 4)
    CallEntries[1] = R_CallMethodDef(None, None, 0)
    R_registerRoutines(dll, None, CallEntries, None, None)
