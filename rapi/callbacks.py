from rapi._libR import ffi, lib
from .utils import rconsole2str, utf8tosystem


class CallbackDef(object):
    suicide = None
    show_message = None
    read_console = None
    write_console = None
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

    def __setattr__(self, item, value):
        if item not in self:
            raise KeyError()
        super(CallbackDef).__setattr__(self, item, value)


def def_callback(name=None):
    def _(fun):
        fname = name
        if fname is None:
            fname = fun.__name__
        setattr(CallbackDef, fname, fun)

    return _


def undef_callback(name):
    setattr(CallbackDef, name, None)


def setup_callback(p, name, cb_name=None):
    cb_name = cb_name if cb_name is not None else "cb_" + name
    if getattr(CallbackDef, name):
        lib._libR_set_callback(p.encode(), ffi.addressof(lib, cb_name))


def setup_callbacks():
    setup_callback("ptr_R_Suicide", "suicide")
    setup_callback("ptr_R_ShowMessage", "show_message")
    setup_callback("ptr_R_ReadConsole", "read_console", "cb_show_message_interruptible")
    setup_callback("ptr_R_WriteConsole", "write_console")
    setup_callback("ptr_R_WriteConsoleEx", "write_console_ex")
    setup_callback("ptr_R_ResetConsole", "reset_console")
    setup_callback("ptr_R_FlushConsole", "flush_console")
    setup_callback("ptr_R_ClearerrConsole", "clearerr_console")
    setup_callback("ptr_R_Busy", "busy")
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
    setup_callback("R_PolledEvents", "polled_events")


def on_read_console_error(exception, exc_value, traceback):
    if exception == KeyboardInterrupt:
        lib.read_console_interrupted = 1
    elif exception == EOFError:
        pass
    else:
        print(exception, exc_value)


@ffi.def_extern()
def cb_show_message(buf):
    buf = rconsole2str(buf)
    CallbackDef.show_message(buf)


@ffi.def_extern(error=0, onerror=on_read_console_error)
def cb_read_console(p, buf, buflen, add_history):
    text = CallbackDef.read_console(rconsole2str(ffi.string(p)), add_history)

    code = utf8tosystem(text)
    buf = ffi.cast("char*", buf)

    nb = min(len(code), buflen - 2)
    buf[0:nb] = code[0:nb]
    if nb < buflen - 2:
        buf[nb] = b'\n'
        buf[nb + 1] = b'\x00'
    return 1


@ffi.def_extern()
def cb_write_console_ex(buf, buflen, otype):
    CallbackDef.write_console_ex(rconsole2str(ffi.string(buf)), otype)


@ffi.def_extern()
def cb_busy(which):
    CallbackDef.busy(which)


@ffi.def_extern()
def cb_clean_up(saveact, status, run_last):
    CallbackDef.clean_up(saveact, status, run_last)
