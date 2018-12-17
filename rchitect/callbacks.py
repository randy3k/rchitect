from __future__ import unicode_literals
import sys
from .utils import rconsole2str, utf8tosystem


if sys.version >= "3":
    def ask_input(s):
        return input(s)
else:
    def ask_input(s):
        return raw_input(s).decode("utf-8", "backslashreplace")


def read_console(p, buf, buflen, add_history):
    text = None
    while text is None:
        try:
            text = ask_input(rconsole2str(p))
        except EOFError:
            return 0

    code = utf8tosystem(text)

    nb = min(len(code), buflen - 2)
    for i in range(nb):
        buf[i] = code[i]
    if nb < buflen - 2:
        buf[nb] = b'\n'
        buf[nb + 1] = b'\0'
    return 1


def write_console_ex(buf, buflen, otype):
    buf = rconsole2str(buf)
    if otype == 0:
        sys.stdout.write(buf)
        sys.stdout.flush()
    else:
        if sys.stderr:
            sys.stderr.write(buf)
            sys.stderr.flush()
    pass


def busy(which):
    pass


def clean_up(save_type, status, runlast):
    pass


def polled_events():
    pass


def show_message(buf):
    buf = rconsole2str(buf)
    sys.stdout.write(buf)
    sys.stdout.flush()


def ask_yes_no_cancel(p):
    while True:
        try:
            result = ask_input("{} [y/n/c]: ".format(rconsole2str(p)))
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
            pass
