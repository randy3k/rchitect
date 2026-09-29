from contextlib import contextmanager
import ctypes
from io import StringIO
import locale
import re
import sys


# =============================================================================
# 1. Console Text & Encoding Helpers
# =============================================================================

DECODE_ERROR_HANDLER = "backslashreplace"
UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe", re.S)

_win_is_utf8_acp = False
if sys.platform == "win32":
    try:
        _win_is_utf8_acp = ctypes.windll.kernel32.GetACP() == 65001
    except Exception:
        pass

if sys.platform == "win32" and not _win_is_utf8_acp:

    def _win_encoding():
        loc = locale.getlocale()[1]
        if not loc:
            return "mbcs"
        if loc in ("UTF-8", "utf8", "65001"):
            return "utf-8"
        if loc.isdigit():
            return "cp" + loc
        return loc

    def system2utf8(buf):
        if buf.isascii():
            return buf.decode("ascii")
        return buf.decode(_win_encoding(), DECODE_ERROR_HANDLER)

    def utf8tosystem(text):
        if text.isascii():
            return text.encode("ascii")
        enc = _win_encoding()
        if enc == "utf-8":
            return text.encode("utf-8", "backslashreplace")
        buf = []
        for c in text:
            try:
                buf.append(c.encode(enc))
            except UnicodeEncodeError:
                buf.append("\\u{{{}}}".format(hex(ord(c))[2:]).encode("ascii"))
        return b"".join(buf)

else:

    def system2utf8(buf):
        return buf.decode("utf-8", DECODE_ERROR_HANDLER)

    def utf8tosystem(text):
        return text.encode("utf-8", "backslashreplace")


def rconsole2str(buf):
    if b"\x02\xff\xfe" not in buf:
        return system2utf8(buf)
    parts = []
    pos = 0
    for m in UTFPATTERN.finditer(buf):
        a, b = m.span()
        if a > pos:
            parts.append(system2utf8(buf[pos:a]))
        parts.append(m.group(1).decode("utf-8", "backslashreplace"))
        pos = b
    if pos < len(buf):
        parts.append(system2utf8(buf[pos:]))
    return "".join(parts)


# =============================================================================
# 2. Console Output & Capture
# =============================================================================

output_buffer = StringIO()
error_buffer = StringIO()
_flushable = True
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
    out = ""
    try:
        b.seek(0)
        out = b.getvalue()
        b.seek(0)
        b.truncate(0)
    except SystemError:
        # catch possible exception
        # see https://github.com/randy3k/radian/issues/288
        pass
    return out


def read_stdout():
    return read_buffer(output_buffer)


def flush_stdout():
    if not _flushable:
        return
    out = read_stdout()
    if out:
        _callback.write_console_ex(out, 0)


def read_stderr():
    return read_buffer(error_buffer)


def flush_stderr():
    if not _flushable:
        return
    err = read_stderr()
    if err:
        _callback.write_console_ex(err, 1)


def flush():
    flush_stdout()
    flush_stderr()


@contextmanager
def capture_console(flushable=True):
    global _capture_state
    global _flushable
    _capture_state_old = _capture_state
    _capture_state = True
    _flushable_old = _flushable
    _flushable = flushable and _flushable
    try:
        yield
    finally:
        _capture_state = _capture_state_old
        if flushable and _capture_state == 0:
            flush()
        _flushable = _flushable_old

