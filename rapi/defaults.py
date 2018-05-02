import sys
import re
import ctypes

ENCODING = "utf-8"
UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe")


def rconsole2str(buf, encoding):
    ret = ""
    m = UTFPATTERN.search(buf)
    while m:
        a, b = m.span()
        ret += buf[:a].decode(encoding) + m.group(1).decode("utf-8")
        buf = buf[b:]
        m = UTFPATTERN.search(buf)
    ret += buf.decode(encoding)
    return ret


def set_encoding(encoding):
    global ENCODING
    ENCODING = encoding


def R_ShowMessage(buf):
    buf = rconsole2str(buf, ENCODING)
    sys.stdout.write(buf)
    sys.stdout.flush()


def R_ReadConsole(p, buf, buflen, add_history):
    while True:
        try:
            text = str(input(p.decode(ENCODING)))
            addr = ctypes.addressof(buf.contents)
            c = (ctypes.c_char * buflen).from_address(addr)
            nb = min(len(text), buflen - 2)
            c[:(nb + 2)] = text.encode(ENCODING)[:nb] + b'\n\0'  # truncate input
            return 1
        except EOFError:
            return 0


def R_WriteConsoleEx(buf, buflen, otype):
    buf = rconsole2str(buf, ENCODING)
    if otype == 0:
        sys.stdout.write(buf)
        sys.stdout.flush()
    else:
        sys.stderr.write(buf)
        sys.stderr.flush()


def R_Busy(which):
    pass


def R_CleanUp(save_type, status, runlast):
    pass


def R_PolledEvents():
    pass


def YesNoCancel(string):
    while True:
        try:
            result = str(input("{} [y/n/c]: ".format(string.decode(ENCODING))))
            if result in ["Y", "y"]:
                return 1
            elif result in ["N", "n"]:
                return 2
            else:
                return 0
        except EOFError:
            return 0
        except KeyboardInterrupt:
            return 0
        except Exception:
            print("")
            pass
