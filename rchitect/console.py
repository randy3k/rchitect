import atexit
from collections import deque
from contextlib import contextmanager
import ctypes
import locale
import re
import sys
import threading


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

_buffer = deque()
_flushable = True
_capture_state = False
_callback = None
_main_thread_ident = threading.main_thread().ident


def reg_callback(callback):
    global _callback
    _callback = callback


def record_main_thread():
    global _main_thread_ident
    _main_thread_ident = threading.get_ident()


def write_console(buf, otype):
    is_main = threading.get_ident() == _main_thread_ident
    if _capture_state or not is_main:
        _buffer.append((buf, otype, is_main))
    else:
        if _buffer:
            flush()
        _callback.write_console_ex(buf, otype)


def _read_by_otype(target_otype):
    if not _buffer:
        return ""
    out = []
    remaining = []
    while _buffer:
        buf, otype, capturable = _buffer.popleft()
        if capturable and (otype == 0) == (target_otype == 0):
            out.append(buf)
        else:
            remaining.append((buf, otype, capturable))
    if remaining:
        _buffer.extendleft(reversed(remaining))
    return "".join(out)


def read_stdout():
    return _read_by_otype(0)


def flush_stdout():
    if not _flushable or threading.get_ident() != _main_thread_ident:
        return
    out = read_stdout()
    if out:
        _callback.write_console_ex(out, 0)


def read_stderr():
    return _read_by_otype(1)


def flush_stderr():
    if not _flushable or threading.get_ident() != _main_thread_ident:
        return
    err = read_stderr()
    if err:
        _callback.write_console_ex(err, 1)


def flush():
    if not _buffer or not _flushable or threading.get_ident() != _main_thread_ident:
        return
    chunks = []
    while _buffer:
        buf, otype, _ = _buffer.popleft()
        norm_otype = 0 if otype == 0 else 1
        if chunks and chunks[-1][1] == norm_otype:
            chunks[-1][0].append(buf)
        else:
            chunks.append(([buf], norm_otype))
    for bufs, otype in chunks:
        text = "".join(bufs)
        if text:
            _callback.write_console_ex(text, otype)


@contextmanager
def capture_console(flushable=True):
    global _capture_state
    global _flushable
    flush()
    _capture_state_old = _capture_state
    _capture_state = True
    _flushable_old = _flushable
    _flushable = flushable and _flushable
    try:
        yield
    finally:
        if not flushable:
            kept = []
            while _buffer:
                item = _buffer.popleft()
                if not item[2]:
                    kept.append(item)
            if kept:
                _buffer.extendleft(reversed(kept))
        _capture_state = _capture_state_old
        _flushable = _flushable_old
        if not _capture_state and _flushable:
            flush()


atexit.register(flush)



