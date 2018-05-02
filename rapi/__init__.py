from __future__ import unicode_literals

import os
import sys
import re
import subprocess
from ctypes import PyDLL
from distutils.version import LooseVersion

from .utils import read_registry
from . import embedded, defaults


__version__ = '0.0.1.dev0'

rhome = None
libR = None


def get_rhome():
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


def get_libR(rhome):
    if sys.platform.startswith("win"):
        libRdir = os.path.join(rhome, "bin", "x64" if sys.maxsize > 2**32 else "i386")
        libRpath = os.path.join(libRdir, "R.dll")
    elif sys.platform == "darwin":
        libRpath = os.path.join(rhome, "lib", "libR.dylib")
    elif sys.platform.startswith("linux"):
        libRpath = os.path.join(rhome, "lib", "libR.so")

    if not os.path.exists(libRpath):
        raise RuntimeError("Cannot locate R share library.")

    return PyDLL(str(libRpath))


def get_rversion(rhome):
    try:
        output = subprocess.check_output(
            [os.path.join(rhome, "bin", "R"), "--version"],
            stderr=subprocess.STDOUT).decode("utf-8").strip()
        m = re.match(r"R version ([0-9]+\.[0-9]+\.[0-9]+)", output)
        rversion = LooseVersion(m.group(1))
    except Exception as e:
        rversion = LooseVersion("1000.0.0")
    return rversion


def init(arguments=["rapi", "--quiet", "--no-save"], repl=False):
    global rhome, libR
    rhome = get_rhome()
    libR = get_libR(rhome)

    embedded.set_callback("R_ShowMessage", defaults.R_ShowMessage)
    embedded.set_callback("R_ReadConsole", defaults.R_ReadConsole)
    embedded.set_callback("R_WriteConsoleEx", defaults.R_WriteConsoleEx)
    embedded.set_callback("R_Busy", defaults.R_Busy)
    embedded.set_callback("R_PolledEvents", defaults.R_PolledEvents)
    embedded.set_callback("YesNoCancel", defaults.YesNoCancel)

    embedded.start(libR, arguments=arguments, repl=repl)
