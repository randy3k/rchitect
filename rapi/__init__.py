from rapi._libR import ffi, lib
import os
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


def which_rhome():
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
        libRdir = os.path.join(rhome, "bin", "x64" if sys.maxsize > 2**32 else "i386")
        libRpath = os.path.join(libRdir, "R.dll")
    elif sys.platform == "darwin":
        libRpath = os.path.join(rhome, "lib", "libR.dylib")
    else:
        libRpath = os.path.join(rhome, "lib", "libR.so")

    if not os.path.exists(libRpath):
        raise RuntimeError("Cannot locate R share library.")

    return libRpath


def init():
    rhome = which_rhome()
    lib.load_libR(libRpath(rhome).encode())
    lib.load_symbols()
    _argv = [ffi.new("char[]", "rapi".encode())]
    argv = ffi.new("char *[]", _argv)
    lib.Rf_initialize_R(len(argv), argv)
    lib.setup_Rmainloop()


def loop():
    lib.run_Rmainloop()
