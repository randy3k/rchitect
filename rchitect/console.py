from six import StringIO
from contextlib import contextmanager


output_buffer = StringIO()
error_buffer = StringIO()
_capture_state = False
_callback = None


def reg_callback(callback):
    global _callback
    _callback = callback


def write_console(buf, otype):
    if _capture_state:
        if otype == 0:
            output_buffer.write(buf)
        else:
            error_buffer.write(buf)
    else:
        _callback.write_console_ex(buf, otype)


def read_buffer(b):
    b.seek(0)
    out = b.getvalue()
    b.seek(0)
    b.truncate(0)
    return out


def read_stdout():
    return read_buffer(output_buffer)


def flush_stdout():
    out = read_stdout()
    if out:
        _callback.write_console_ex(out, 0)


def read_stderr():
    return read_buffer(error_buffer)


def flush_stderr():
    err = read_stderr()
    if err:
        _callback.write_console_ex(err, 1)


def flush():
    flush_stdout()
    flush_stderr()


@contextmanager
def capture_console():
    global _capture_state
    _capture_state = True
    try:
        yield
    finally:
        _capture_state = False
        flush()
