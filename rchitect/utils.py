from __future__ import unicode_literals
import os
import re
import subprocess
import sys
import ctypes
from distutils.version import LooseVersion
if sys.version_info[0] >= 3:
    from shutil import which
else:
    from backports.shutil_which import which

if sys.platform.startswith('win'):
    if sys.version_info[0] >= 3:
        from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ
    else:
        from _winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ


def read_registry(key, valueex):
    reg_key = OpenKey(HKEY_LOCAL_MACHINE, key, 0, KEY_READ)
    return QueryValueEx(reg_key, valueex)


def getRhome(path, throw=False):
    rhome = ""

    if sys.platform.startswith("win") and path and not path.endswith(".exe"):
        path = path + ".exe"

    if not which(path):
        return None
    try:
        rhome = subprocess.check_output([path, "RHOME"]).decode("utf-8").strip()
    except Exception:
        rhome = None

    return rhome


def verify_Rhome(rhome):
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
        raise RuntimeError("R share library ({}) does not exist.".format(path))


def Rhome():
    rhome = None

    if 'R_BINARY' in os.environ:
        rhome = getRhome(os.environ['R_BINARY'], throw=True)
        if not rhome:
            raise RuntimeError("R binary ({}) does not exist.".format(os.environ['R_BINARY']))

    if not rhome and 'R_HOME' in os.environ:
        rhome = os.environ['R_HOME']
        if not os.path.isdir(rhome):
            raise RuntimeError("R_HOME ({}) does not exist.".format(rhome))
        return rhome

    if not rhome:
        rhome = getRhome("R")

    try:
        if sys.platform.startswith("win") and not rhome:
            rhome = read_registry("Software\\R-Core\\R", "InstallPath")[0]
    except Exception:
        rhome = ""

    if rhome:
        os.environ['R_HOME'] = rhome
    else:
        raise RuntimeError("Cannot determine R HOME.")

    verify_Rhome(rhome)

    return rhome


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


def rversion(rhome=None):
    if not rhome:
        rhome = Rhome()
    try:
        output = subprocess.check_output(
            [os.path.join(rhome, "bin", "R"), "--slave", "-e", "cat(as.character(getRversion()))"],
            stderr=subprocess.STDOUT).decode("utf-8").strip()
        version = LooseVersion(output)
    except Exception:
        version = LooseVersion("1000.0.0")
    return version


UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe", re.S)
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
