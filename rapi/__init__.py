from rapi._libR import ffi, lib
from .utils import Rhome, libRpath


def init(args=["rapi", "--quiet", "--no-save"]):
    if not lib._libR_load(libRpath(Rhome()).encode()):
        raise Exception("cannot load R library")
    if not lib._libR_load_symbols():
        raise Exception(ffi.string(lib._libR_dl_error_message()).decode())

    _argv = [ffi.new("char[]", a.encode()) for a in args]
    argv = ffi.new("char *[]", _argv)
    lib.Rf_initialize_R(len(argv), argv)
    lib.setup_Rmainloop()
    if not lib._libR_load_constants():
        raise Exception(ffi.string(lib._libR_dl_error_message()).decode())


def loop():
    lib.run_Rmainloop()
