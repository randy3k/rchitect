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
    from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER


def is_arm():
    return platform.machine().lower() == "arm64"


def is_64bit():
    return sys.maxsize > 2**32


def read_registry_from_local_machine(key, valueex):
    return QueryValueEx(OpenKey(HKEY_LOCAL_MACHINE, key), valueex)


def read_registry_from_current_user(key, valueex):
    return QueryValueEx(OpenKey(HKEY_CURRENT_USER, key), valueex)


def read_registry(key, valueex):
    try:
        return read_registry_from_current_user(key, valueex)
    except Exception:
        return read_registry_from_local_machine(key, valueex)


def read_r_install_path_from_registry():
    try:
        return read_registry("Software\\WOW6432Node\\R-Core\\R", "InstallPath")[0]
    except Exception:
        pass
    try:
        return read_registry("Software\\R-Core\\R", "InstallPath")[0]
    except Exception:
        pass
    return None


DECODE_ERROR_HANDLER = "backslashreplace"



def get_rhome_from_binary(rbinary):
    if sys.platform.startswith("win"):
        if rbinary and not rbinary.endswith(".exe"):
            rbinary = rbinary + ".exe"

    if not which(rbinary):
        return None
    try:
        return subprocess.check_output([rbinary, "RHOME"]).decode("utf-8").strip()
    except Exception:
        pass
    return None

# Do not use this, use get_rhome() instead!
def Rhome():
    return get_rhome()


def get_rhome():
    rhome = None

    if "R_BINARY" in os.environ:
        rbinary = os.environ["R_BINARY"]
        rhome = get_rhome_from_binary(rbinary)
        if not rhome:
            raise RuntimeError(
                "R binary ({}) does not exist.".format(rbinary)
            )
        return rhome

    if "R_HOME" in os.environ:
        rhome = os.environ["R_HOME"]
        if not os.path.isdir(rhome):
            raise RuntimeError("R_HOME ({}) does not exist.".format(rhome))
        return rhome

    rhome = get_rhome_from_binary("R")

    if not rhome:
        if sys.platform.startswith("win"):
            rhome = read_r_install_path_from_registry()        

    if rhome:
        os.environ["R_HOME"] = rhome
    else:
        raise RuntimeError("Cannot determine R HOME.")

    return rhome


def get_libr_path(rhome, ensure_path=False):
    # TODO: better support R_ARCH
    if sys.platform.startswith("win"):
        if is_arm():
            libr_path = os.path.join(rhome, "bin", "R.dll")
        elif is_64bit():
            libr_path = os.path.join(rhome, "bin", "x64", "R.dll")
        else:
            libr_path = os.path.join(rhome, "bin", "i386", "R.dll")
    elif sys.platform == "darwin":
        libr_path = os.path.join(rhome, "lib", "libR.dylib")
    else:
        libr_path = os.path.join(rhome, "lib", "libR.so")
    
    if not os.path.exists(libr_path):
        raise RuntimeError("R share library ({}) does not exist.".format(libr_path))
    
    # microsoft python doesn't load DLL's from PATH
    # we will need to open the DLL's directly in _libR_load    
    if sys.platform.startswith("win"):
        if ensure_path:
            ensure_path_for_dll(libr_path)

    return libr_path


def ensure_path_for_dll(libr_path):
    libr_dir = os.path.dirname(libr_path)
    try:
        # make sure Rblas.dll can be reachable
        msvcrt = ctypes.cdll.msvcrt
        msvcrt._wgetenv.restype = ctypes.c_wchar_p
        path = msvcrt._wgetenv(ctypes.c_wchar_p("PATH"))
        if libr_dir not in path:
            path = libr_dir + ";" + path
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
