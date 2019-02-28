from rapi._libR import ffi, lib
from .utils import Rhome, libRpath


def init():
    lib._libR_load(libRpath(Rhome()).encode())
    lib._libR_load_symbols()
    _argv = [ffi.new("char[]", "rapi".encode())]
    argv = ffi.new("char *[]", _argv)
    lib.Rf_initialize_R(len(argv), argv)
    lib.setup_Rmainloop()


def loop():
    lib.run_Rmainloop()
