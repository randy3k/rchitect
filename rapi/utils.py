from __future__ import unicode_literals
from ctypes import c_void_p, c_char_p, cast
import os
import sys
import re
import subprocess
from distutils.version import LooseVersion


if sys.platform.startswith('win'):
    if sys.version_info[0] >= 3:
        from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ
    else:
        from _winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ


def cfunction(fname, lib, restype, argtypes):
    f = getattr(lib, fname)
    f.restype = restype
    f.argtypes = argtypes
    return f


def cglobal(vname, lib, vtype=c_void_p):
    return vtype.in_dll(lib, vname)


def ccall(fname, lib, restype, argtypes, *args):
    f = getattr(lib, fname)
    f.restype = restype
    f.argtypes = argtypes
    res = f(*args)
    if restype == c_void_p or restype == c_char_p:
        return cast(res, restype)
    else:
        return res


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def read_registry(key, valueex):
    reg_key = OpenKey(HKEY_LOCAL_MACHINE, key, 0, KEY_READ)
    return QueryValueEx(reg_key, valueex)


def rversion(libR):
    """
    Only work after initialization
    """
    libR.Rf_install.argtypes = [c_char_p]
    libR.Rf_install.restype = c_void_p
    libR.Rf_eval.argtypes = [c_void_p, c_void_p]
    libR.Rf_eval.restype = c_void_p
    libR.Rf_asChar.argtypes = [c_void_p]
    libR.Rf_asChar.restype = c_void_p
    libR.R_CHAR.argtypes = [c_void_p]
    libR.R_CHAR.restype = c_char_p

    sym = libR.Rf_install("R.version.string".encode())
    ret = libR.Rf_eval(sym, cglobal("R_GlobalEnv", libR, c_void_p))
    rversion_string = libR.R_CHAR(libR.Rf_asChar(ret)).decode()

    m = re.match(r"R version ([0-9]+\.[0-9]+\.[0-9]+)", rversion_string)
    version = LooseVersion(m.group(1))
    return version


def rversion2(rhome):
    try:
        output = subprocess.check_output(
            [os.path.join(rhome, "bin", "R"), "--version"],
            stderr=subprocess.STDOUT).decode("utf-8").strip()
        m = re.match(r"R version ([0-9]+\.[0-9]+\.[0-9]+)", output)
        version = LooseVersion(m.group(1))
    except Exception as e:
        version = LooseVersion("1000.0.0")
    return version
