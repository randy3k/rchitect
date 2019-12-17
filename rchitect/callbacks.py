from __future__ import unicode_literals
from rchitect._cffi import ffi, lib
from .utils import rconsole2str, utf8tosystem
from . import console


class Callback(object):
    suicide = None
    show_message = None
    read_console = None
    write_console_ex = None
    reset_console = None
    flush_console = None
    clearerr_console = None
    busy = None
    clean_up = None
    show_files = None
    choose_file = None
    edit_file = None
    loadhistory = None
    savehistory = None
    addhistory = None
    edit_files = None
    do_selectlist = None
    do_dataentry = None
    do_dataviewer = None
    process_events = None
    polled_events = None
    yes_no_cancel = None

    def __setattr__(self, item, value):
        if item not in Callback.__dict__.keys():
            raise KeyError()
        self.__dict__[item] = value


callback = Callback()
console.reg_callback(callback)


def def_callback(name=None):
    def _(fun):
        fname = name
        if fname is None:
            fname = fun.__name__
        setattr(callback, fname, fun)

    return _


def undef_callback(name):
    setattr(callback, name, None)


# prevent rstart being gc'ed
_protected = {}


def setup_rstart(args):
    rstart = ffi.new("Rstart")
    _protected["rstart"] = rstart
    SA_NORESTORE = 0
    SA_RESTORE = 1
    # SA_DEFAULT = 2
    SA_NOSAVE = 3
    SA_SAVE = 4
    SA_SAVEASK = 5
    # SA_SUICIDE = 6
    lib.R_DefParams(rstart)
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
    rhome = ffi.new("char[]", ffi.string(lib.get_R_HOME()))
    _protected["rhome"] = rhome
    rstart.rhome = rhome
    home = ffi.new("char[]", ffi.string(lib.getRUser()))
    _protected["home"] = home
    rstart.home = home
    rstart._ReadConsole = ffi.addressof(lib, "cb_read_console_interruptible")
    rstart._WriteConsole = ffi.NULL
    rstart.CallBack = ffi.addressof(lib, "cb_polled_events")
    rstart.ShowMessage = ffi.addressof(lib, "cb_show_message")
    rstart.YesNoCancel = ffi.addressof(lib, "cb_yes_no_cancel")
    rstart.Busy = ffi.addressof(lib, "cb_busy")
    # we cannot get it to RGui, otherwise `do_system` will clear the standard handlers
    rstart.CharacterMode = 1  # RTerm
    rstart.WriteConsoleEx = ffi.addressof(lib, "cb_write_console_capturable")
    lib.R_SetParams(rstart)


def setup_callback(p, name, cb_name=None):
    if name is None:
        lib._libR_set_callback(p.encode(), ffi.NULL)
    elif getattr(callback, name):
        cb_name = cb_name if cb_name is not None else "cb_" + name
        lib._libR_set_callback(p.encode(), ffi.addressof(lib, str(cb_name)))


def setup_unix_callbacks():
    setup_callback("R_Outputfile", None)
    setup_callback("R_Consolefile", None)

    setup_callback("ptr_R_Suicide", "suicide")
    setup_callback("ptr_R_ShowMessage", "show_message")
    setup_callback("ptr_R_ReadConsole", "read_console", "cb_read_console_interruptible")
    setup_callback("ptr_R_WriteConsole", None)
    setup_callback("ptr_R_WriteConsoleEx", "write_console_ex", "cb_write_console_safe")
    setup_callback("ptr_R_ResetConsole", "reset_console")
    setup_callback("ptr_R_FlushConsole", "flush_console")
    setup_callback("ptr_R_ClearerrConsole", "clearerr_console")
    setup_callback("ptr_R_Busy", "busy", "cb_busy_safe")
    setup_callback("ptr_R_CleanUp", "clean_up")
    setup_callback("ptr_R_ShowFiles", "show_files")
    setup_callback("ptr_R_ChooseFile", "choose_file")
    setup_callback("ptr_R_EditFile", "edit_file")
    setup_callback("ptr_R_loadhistory", "loadhistory")
    setup_callback("ptr_R_savehistory", "savehistory")
    setup_callback("ptr_R_addhistory", "addhistory")
    setup_callback("ptr_R_EditFiles", "edit_files")
    setup_callback("ptr_do_selectlist", "do_selectlist")
    setup_callback("ptr_do_dataentry", "do_dataentry")
    setup_callback("ptr_do_dataviewer", "do_dataviewer")
    setup_callback("ptr_R_ProcessEvents", "process_events")
    setup_callback("R_PolledEvents", "polled_events", "cb_polled_events_safe")


@ffi.def_extern()
def cb_show_message(buf):
    callback.show_message(rconsole2str(ffi.string(buf)))


def on_read_console_error(exception, exc_value, traceback):
    if exception == KeyboardInterrupt:
        lib.cb_read_console_interrupted = 1
    elif exception == EOFError:
        pass
    else:
        print(exception, exc_value)


_code = [""]


@ffi.def_extern(error=0, onerror=on_read_console_error)
def cb_read_console(p, buf, buflen, add_history):
    # cache the code as buflen is limited to 4096
    if _code[0]:
        code = _code[0]
    else:
        text = callback.read_console(rconsole2str(ffi.string(p)), add_history)
        if text is None:
            return 0
        code = utf8tosystem(text)
        _code[0] = code

    buf = ffi.cast("char*", buf)
    nb = min(len(code), buflen - 2)
    buf[0:nb] = code[0:nb]
    if nb < buflen - 2:
        buf[nb] = b'\n'
        buf[nb + 1] = b'\x00'

    _code[0] = _code[0][nb:]
    return 1


@ffi.def_extern()
def cb_write_console_capturable(buf, bufline, otype):
    text = rconsole2str(ffi.string(buf))
    console.write_console(text, otype)


@ffi.def_extern()
def cb_busy(which):
    callback.busy(which)


@ffi.def_extern()
def cb_clean_up(saveact, status, run_last):
    callback.clean_up(saveact, status, run_last)


@ffi.def_extern()
def cb_polled_events():
    console.flush()
    callback.polled_events()


@ffi.def_extern()
def cb_yes_no_cancel(p):
    return callback.yes_no_cancel(rconsole2str(ffi.string(p)))
