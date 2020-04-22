from __future__ import unicode_literals

import rchitect
import sys

if sys.platform.startswith("win"):
    from ctypes import WinDLL
    rchitect.utils.ensure_path()
    p = rchitect.utils.libRgapath(rchitect.utils.Rhome())
    lib = WinDLL(p)
    print(lib.GA_peekevent)
    print(lib.GA_peekevent())

rchitect.init()
