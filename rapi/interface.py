from rapi._libR import ffi, lib

def rchar(s):
    isascii = all(ord(c) < 128 for c in s)
    b = s.encode("utf-8")
    return lib.Rf_mkCharLenCE(b, len(b), lib.CE_NATIVE if isascii else lib.CE_UTF8)


def rstring(s):
    return lib.Rf_ScalarString(rchar(s))


def rparse(s):
    status = ffi.new("ParseStatus[1]")
    s = lib.Rf_protect(rstring(s))
    ret = lib.R_ParseVector(s, -1, status, lib.R_NilValue)
    try:
        if status[0] != lib.PARSE_OK:
            raise Exception("Parse error")
    finally:
        lib.Rf_unprotect(1)
    return ret
