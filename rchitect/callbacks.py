import sys

from rchitect._cffi import ffi, lib
from . import console
from .console import rconsole2str, utf8tosystem


# =============================================================================
# 1. Callback Registry & Default Callbacks
# =============================================================================

_CALLBACK_NAMES = frozenset(
    {
        "suicide",
        "show_message",
        "read_console",
        "write_console_ex",
        "reset_console",
        "flush_console",
        "clearerr_console",
        "busy",
        "clean_up",
        "show_files",
        "choose_file",
        "edit_file",
        "loadhistory",
        "savehistory",
        "addhistory",
        "edit_files",
        "do_selectlist",
        "do_dataentry",
        "do_dataviewer",
        "process_events",
        "polled_events",
        "yes_no_cancel",
    }
)

_UNIX_CALLBACKS = {
    "suicide": ("ptr_R_Suicide", None),
    "show_message": ("ptr_R_ShowMessage", None),
    "read_console": ("ptr_R_ReadConsole", "cb_read_console_safe"),
    "write_console_ex": ("ptr_R_WriteConsoleEx", "cb_write_console_ex_safe"),
    "reset_console": ("ptr_R_ResetConsole", None),
    "flush_console": ("ptr_R_FlushConsole", None),
    "clearerr_console": ("ptr_R_ClearerrConsole", None),
    "busy": ("ptr_R_Busy", "cb_busy_safe"),
    "clean_up": ("ptr_R_CleanUp", None),
    "show_files": ("ptr_R_ShowFiles", None),
    "choose_file": ("ptr_R_ChooseFile", None),
    "edit_file": ("ptr_R_EditFile", None),
    "loadhistory": ("ptr_R_loadhistory", None),
    "savehistory": ("ptr_R_savehistory", None),
    "addhistory": ("ptr_R_addhistory", None),
    "edit_files": ("ptr_R_EditFiles", None),
    "do_selectlist": ("ptr_do_selectlist", None),
    "do_dataentry": ("ptr_do_dataentry", None),
    "do_dataviewer": ("ptr_do_dataviewer", None),
    "process_events": ("ptr_R_ProcessEvents", None),
    "polled_events": ("R_PolledEvents", "cb_polled_events_safe"),
}

_unix_callbacks_initialized = False
_default_unix_callbacks = {}


class Callback:
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
        if item not in _CALLBACK_NAMES:
            raise KeyError()
        self.__dict__[item] = value


callback = Callback()
console.reg_callback(callback)


def def_callback(name=None):
    def _(fun):
        fname = name if name is not None else fun.__name__
        setattr(callback, fname, fun)
        if _unix_callbacks_initialized and fname in _UNIX_CALLBACKS:
            p, cb_name = _UNIX_CALLBACKS[fname]
            setup_callback(p, fname, cb_name)

    return _


def undef_callback(name):
    setattr(callback, name, None)
    if _unix_callbacks_initialized and name in _UNIX_CALLBACKS:
        p, cb_name = _UNIX_CALLBACKS[name]
        setup_callback(p, name, cb_name)


def ask_input(s):
    return input(s)


@def_callback()
def show_message(buf):
    sys.stdout.write(buf)
    sys.stdout.flush()


@def_callback()
def read_console(p, add_history):
    sys.stdout.flush()
    sys.stderr.flush()
    return ask_input(p)


@def_callback()
def write_console_ex(buf, otype):
    if otype == 0:
        if sys.stdout:
            sys.stdout.write(buf)
            sys.stdout.flush()
    else:
        if sys.stderr:
            sys.stderr.write(buf)
            sys.stderr.flush()


@def_callback()
def reset_console():
    pass


@def_callback()
def busy(which):
    pass


@def_callback()
def polled_events():
    pass


@def_callback()
def yes_no_cancel(p):
    while True:
        try:
            result = ask_input("{} [y/n/c]: ".format(p))
            if result in ["Y", "y"]:
                return 1
            elif result in ["N", "n"]:
                return 2
            else:
                return 0
        except EOFError:
            return 0
        except KeyboardInterrupt:
            return 0
        except Exception:
            pass


# =============================================================================
# 2. R Startup & Callback Wiring
# =============================================================================

# prevent rstart being gc'ed
_protected = {}


def setup_rstart(rhome, args):
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
    rstart.R_Slave = "--no-echo" in args or "--slave" in args
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
    rhome = ffi.new("char[]", rhome.encode("utf-8"))
    _protected["rhome"] = rhome
    rstart.rhome = rhome
    home = ffi.new("char[]", ffi.string(lib.getRUser()))
    _protected["home"] = home
    rstart.home = home
    rstart._ReadConsole = ffi.addressof(lib, "cb_read_console_safe")
    rstart._WriteConsole = ffi.NULL
    rstart.CallBack = ffi.addressof(lib, "cb_polled_events_safe")
    rstart.ShowMessage = ffi.addressof(lib, "cb_show_message")
    rstart.YesNoCancel = ffi.addressof(lib, "cb_yes_no_cancel")
    rstart.Busy = ffi.addressof(lib, "cb_busy_safe")
    # we cannot get it to RGui, otherwise `do_system` will clear the standard handlers
    rstart.CharacterMode = 1  # RTerm
    rstart.WriteConsoleEx = ffi.addressof(lib, "cb_write_console_ex_safe")
    lib.rchitect_record_main_thread()
    console.record_main_thread()
    lib.R_SetParams(rstart)


def setup_callback(p, name, cb_name=None):
    if p not in _default_unix_callbacks:
        _default_unix_callbacks[p] = getattr(lib, p)
    if name is None:
        setattr(lib, p, ffi.NULL)
    elif getattr(callback, name):
        cb_name = cb_name if cb_name is not None else "cb_" + name
        setattr(lib, p, ffi.addressof(lib, str(cb_name)))
    else:
        setattr(lib, p, _default_unix_callbacks[p])


def setup_unix_callbacks():
    global _unix_callbacks_initialized
    _unix_callbacks_initialized = True
    lib.rchitect_record_main_thread()
    console.record_main_thread()
    setup_callback("R_Outputfile", None)
    setup_callback("R_Consolefile", None)
    setup_callback("ptr_R_WriteConsole", None)

    for name, (p, cb_name) in _UNIX_CALLBACKS.items():
        setup_callback(p, name, cb_name)


# =============================================================================
# 3. CFFI Callback Trampolines
# =============================================================================


@ffi.def_extern()
def cb_show_message(buf):
    callback.show_message(rconsole2str(ffi.string(buf)))


def on_callback_error(exception, exc_value, traceback):
    _code[0] = b""
    if exception == KeyboardInterrupt:
        lib.cb_interrupted = 1
    elif exception == EOFError:
        pass
    else:
        print("callback error:", exception, exc_value)


_code = [b""]


@ffi.def_extern(error=0, onerror=on_callback_error)
def cb_read_console(p, buf, buflen, add_history):
    console.flush()
    # cache the code as buflen is limited to 4096
    if _code[0]:
        code = _code[0]
    else:
        text = callback.read_console(rconsole2str(ffi.string(p)), add_history)
        if text is None:
            return 0
        code = utf8tosystem(text) + b"\n"
        _code[0] = code

    buf = ffi.cast("char*", buf)

    if len(code) < buflen:
        nb = len(code)
    else:
        nb = buflen - 1
        while nb > 0 and (code[nb] & 0xC0) == 0x80:
            nb -= 1
        if nb == 0:
            nb = buflen - 1

    buf[0:nb] = code[0:nb]
    buf[nb] = b'\x00'

    _code[0] = code[nb:]
    return 1


@ffi.def_extern(error=None, onerror=on_callback_error)
def cb_write_console_ex(buf, bufline, otype):
    text = rconsole2str(ffi.string(buf))
    console.write_console(text, otype)


@ffi.def_extern(error=None, onerror=on_callback_error)
def cb_reset_console():
    _code[0] = b""
    callback.reset_console()


@ffi.def_extern()
def cb_busy(which):
    console.flush()
    callback.busy(which)


@ffi.def_extern()
def cb_clean_up(saveact, status, run_last):
    callback.clean_up(saveact, status, run_last)


@ffi.def_extern(error=None, onerror=on_callback_error)
def cb_polled_events():
    console.flush()  # needed for reval
    callback.polled_events()


@ffi.def_extern()
def cb_yes_no_cancel(p):
    return callback.yes_no_cancel(rconsole2str(ffi.string(p)))
