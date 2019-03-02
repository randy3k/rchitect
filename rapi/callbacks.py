from rapi._libR import ffi, lib
from contextlib import contextmanager
from .utils import rconsole2str, utf8tosystem


def def_callback(name=None):
    def _(fun):
        fname = name
        if fname is None:
            fname = fun.__name__
        globals()[fname] = fun
        setattr(lib._libR_callbacks, fname, getattr(lib, "cb_" + fname))

    return _

def on_read_console_error(exception, exc_value, traceback):
    if exception == KeyboardInterrupt:
        lib.read_console_interuupted = 1
    elif exception == EOFError:
        pass
    else:
        print(exception, exc_value)


@ffi.def_extern()
def cb_show_message(buf):
    buf = rconsole2str(buf)
    show_message(buf)


@ffi.def_extern(error=0, onerror=on_read_console_error)
def cb_read_console(p, buf, buflen, add_history):
    text = read_console(rconsole2str(ffi.string(p)), add_history)

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
    write_console_ex(rconsole2str(ffi.string(buf)), otype)
