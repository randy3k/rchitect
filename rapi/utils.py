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
