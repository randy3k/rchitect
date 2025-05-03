import os
import re
import subprocess
import sys
import platform
import ctypes
import locale
from shutil import which

from packaging.version import parse as parse_version

if sys.platform.startswith("win"):
    from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ


def is_arm():
    return platform.machine().lower() == "arm64"


def is_64bit():
    return sys.maxsize > 2**32


def read_registry(key, valueex):
    reg_key = OpenKey(HKEY_LOCAL_MACHINE, key, 0, KEY_READ)
    return QueryValueEx(reg_key, valueex)


def _get_rhome(path, throw=False):
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


def path_for_libR(rhome):
    # TODO: better support R_ARCH
    if sys.platform.startswith("win"):
        if is_arm():
            return os.path.join(rhome, "bin", "R.dll")
        elif is_64bit():
            return os.path.join(rhome, "bin", "x64", "R.dll")
        else:
            return os.path.join(rhome, "bin", "i386", "R.dll")
    elif sys.platform == "darwin":
        return os.path.join(rhome, "lib", "libR.dylib")
    else:
        return os.path.join(rhome, "lib", "libR.so")


# Do not use this, use get_rhome() instead!
def Rhome():
    return get_rhome()


# use this instead!
def get_rhome():
    rhome = None

    if "R_BINARY" in os.environ:
        rhome = _get_rhome(os.environ["R_BINARY"], throw=True)
        if not rhome:
            raise RuntimeError(
                "R binary ({}) does not exist.".format(os.environ["R_BINARY"])
            )

    if not rhome and "R_HOME" in os.environ:
        rhome = os.environ["R_HOME"]
        if not os.path.isdir(rhome):
            raise RuntimeError("R_HOME ({}) does not exist.".format(rhome))
        return rhome

    if not rhome:
        rhome = _get_rhome("R")

    try:
        if sys.platform.startswith("win") and not rhome:
            rhome = read_registry("Software\\R-Core\\R", "InstallPath")[0]
    except Exception:
        rhome = ""

    try:
        if sys.platform.startswith("win") and not rhome:
            rhome = read_registry("Software\\WOW6432Node\\R-Core\\R", "InstallPath")[0]
    except Exception:
        rhome = ""

    if rhome:
        os.environ["R_HOME"] = rhome
    else:
        raise RuntimeError("Cannot determine R HOME.")

    libR_path = path_for_libR(rhome)
    if not os.path.exists(libR_path):
        raise RuntimeError("R share library ({}) does not exist.".format(libR_path))

    return rhome


def ensure_path(rhome=None):
    if not rhome:
        rhome = get_rhome()
    if sys.platform.startswith("win"):
        libRdir = os.path.dirname(path_for_libR(rhome))
        try:
            # make sure Rblas.dll can be reachable
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
        rhome = get_rhome()
    try:
        output = (
            subprocess.check_output(
                [
                    os.path.join(rhome, "bin", "R"),
                    "--no-echo",
                    "-e",
                    "cat(as.character(getRversion()))",
                ],
                stderr=subprocess.STDOUT,
            )
            .decode("utf-8")
            .strip()
        )
        version = parse_version(output)
    except Exception:
        version = parse_version("1000.0.0")
    return version


UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe", re.S)


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
        ctypes.c_size_t,
    ]
    mbtowc.restype = ctypes.c_int

    wctomb = ctypes.cdll.msvcrt.wctomb
    wctomb.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_wchar]
    wctomb.restype = ctypes.c_int

    def system2utf8(buf):
        loc = locale.getlocale()
        if loc[1] == "UTF-8" or loc[1] == "utf8" or loc[1] == "65001":
            return buf.decode("utf-8", DECODE_ERROR_HANDLER)

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
        loc = locale.getlocale()
        if loc[1] == "UTF-8" or loc[1] == "utf8" or loc[1] == "65001":
            return text.encode("utf-8", "backslashreplace")

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
