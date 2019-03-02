import os
import re
import subprocess
import sys

if sys.platform.startswith('win'):
    if sys.version_info[0] >= 3:
        from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ
    else:
        from _winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ


def read_registry(key, valueex):
    reg_key = OpenKey(HKEY_LOCAL_MACHINE, key, 0, KEY_READ)
    return QueryValueEx(reg_key, valueex)


def Rhome():
    if 'R_HOME' not in os.environ:
        try:
            rhome = subprocess.check_output(["R", "RHOME"]).decode("utf-8").strip()
        except Exception:
            rhome = ""
        try:
            if sys.platform.startswith("win") and not rhome:
                rhome = read_registry("Software\\R-Core\\R", "InstallPath")[0]
        except Exception:
            rhome = ""

        if rhome:
            os.environ['R_HOME'] = rhome
    else:
        rhome = os.environ['R_HOME']

    return rhome


def libRpath(rhome):
    if sys.platform.startswith("win"):
        path = os.path.join(rhome, "bin", "x64" if sys.maxsize > 2**32 else "i386", "R.dll")
    elif sys.platform == "darwin":
        path = os.path.join(rhome, "lib", "libR.dylib")
    else:
        path = os.path.join(rhome, "lib", "libR.so")

    if not os.path.exists(path):
        raise RuntimeError("Cannot locate R share library.")

    return path


UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe")


def rconsole2str(buf):
    ret = ""
    m = UTFPATTERN.search(buf)
    while m:
        a, b = m.span()
        ret += system2utf8(buf[:a]) + m.group(1).decode("utf-8", "backslashreplace")
        buf = buf[b:]
        m = UTFPATTERN.search(buf)
    ret += system2utf8(buf)
    return ret


if sys.platform == "win32":
    import ctypes

    mbtowc = ctypes.cdll.msvcrt.mbtowc
    mbtowc.argtypes = [
        ctypes.POINTER(ctypes.c_wchar),
        ctypes.POINTER(ctypes.c_char),
        ctypes.c_size_t]
    mbtowc.restype = ctypes.c_int

    wctomb = ctypes.cdll.msvcrt.wctomb
    wctomb.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_wchar]
    wctomb.restype = ctypes.c_int

    def system2utf8(buf):
        wcbuf = ctypes.create_unicode_buffer(1)
        text = ""
        while buf:
            n = mbtowc(wcbuf, buf, len(buf))
            if n <= 0:
                break
            text += wcbuf[0]
            buf = buf[n:]
        return text

    def utf8tosystem(text):
        s = ctypes.create_string_buffer(10)
        buf = b""
        for c in text:
            n = wctomb(s, c)
            if n > 0:
                buf += s[:n]
            else:
                buf += "\\u{{{}}}".format(hex(ord(c))[2:]).encode("ascii")
        return buf

else:
    def system2utf8(buf):
        return buf.decode("utf-8", "backslashreplace")

    def utf8tosystem(text):
        return text.encode("utf-8", "backslashreplace")
