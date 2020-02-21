from __future__ import unicode_literals
import os
import re
import subprocess
import sys
import ctypes
from distutils.version import LooseVersion


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
        if sys.platform.startswith("win"):
            another_path = os.path.join(
                rhome, "bin", "i386" if sys.maxsize > 2**32 else "x64", "R.dll")
            if os.path.exists(another_path):
                raise RuntimeError("R and python architectures do not match.")
        raise RuntimeError("Cannot locate R share library.")

    return path


def ensure_path(rhome=None):
    if not rhome:
        rhome = Rhome()
    if sys.platform.startswith("win"):
        libRdir = os.path.join(rhome, "bin", "x64" if sys.maxsize > 2**32 else "i386")

        # make sure Rblas.dll can be reached
        try:
            msvcrt = ctypes.cdll.msvcrt
            msvcrt._wgetenv.restype = ctypes.c_wchar_p
            path = msvcrt._wgetenv(ctypes.c_wchar_p("PATH"))
            if libRdir not in path:
                path = libRdir + ";" + path
                msvcrt._wputenv(ctypes.c_wchar_p("PATH={}".format(path)))
        except Exception as e:
            print(e)
            pass


R_RELEASE = re.compile(r"R version ([0-9]+\.[0-9]+\.[0-9]+)")
R_DEVEL = re.compile(r"R Under development \(unstable\) \(([^)]*)\)")


def rversion(rhome=None):
    if not rhome:
        rhome = Rhome()
    try:
        output = subprocess.check_output(
            [os.path.join(rhome, "bin", "R"), "--version"],
            stderr=subprocess.STDOUT).decode("utf-8").strip()
        m = R_RELEASE.match(output)
        if not m:
            m = R_DEVEL.match(output)
        version = LooseVersion(m.group(1))
    except Exception:
        version = LooseVersion("1000.0.0")
    return version


UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe")
if sys.version_info[0] >= 3:
    DECODE_ERROR_HANDLER = "backslashreplace"
else:
    DECODE_ERROR_HANDLER = "replace"


def rconsole2str(buf):
    ret = ""
    m = UTFPATTERN.search(buf)
    while m:
        a, b = m.span()
        ret += system2utf8(buf[:a]) + m.group(1).decode("utf-8", DECODE_ERROR_HANDLER)
        buf = buf[b:]
        m = UTFPATTERN.search(buf)
    ret += system2utf8(buf)
    return ret


if sys.platform == "win32":
    """
    The following only works after setlocale in C and
    R will initialize it for us. To mimic the behaviour, consider
    ```
    ctypes.cdll.msvcrt.setlocale(0, ctypes.c_char_p("chinese-traditional"))
    ```
    """

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
            try:
                n = wctomb(s, c)
            except Exception:
                n = -1

            if n > 0:
                buf += s[:n]
            else:
                buf += "\\u{{{}}}".format(hex(ord(c))[2:]).encode("ascii")
        return buf

else:
    def system2utf8(buf):
        return buf.decode("utf-8", DECODE_ERROR_HANDLER)

    def utf8tosystem(text):
        return text.encode("utf-8", "backslashreplace")


def id_str(x):
    return str(id(x))
