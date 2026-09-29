from rchitect import reval, rcopy
from rchitect._cffi import lib, ffi
import sys
import pytest


@pytest.mark.skipif(not sys.platform.startswith("win") and not sys.stdout.isatty(), reason="not tty")
def test_read_console(mocker, gctorture):
    mocker.patch("rchitect.callbacks.ask_input", return_value="hello")
    ret = reval("readline('> ')")
    assert rcopy(ret) == "hello"


@pytest.mark.skipif(not sys.platform.startswith("win") and not sys.stdout.isatty(), reason="not tty")
def test_read_console_long(mocker, gctorture):
    for h in [2000, 4094, 4095, 4096, 4097, 5000]:
        s = "b" * h
        mocker.patch("rchitect.callbacks.ask_input", return_value=s)
        ret = reval("readline('> ')")
        assert rcopy(ret) == s
        assert len(rcopy(ret)) == len(s)


def test_read_console_long_utf8(mocker, gctorture):
    mocker.patch("rchitect.callbacks.utf8tosystem", side_effect=lambda x: x.encode("utf-8"))
    for offset in [0, 1, 2]:
        s = ("a" * offset) + ("文字" * 1000)
        mocker.patch("rchitect.callbacks.ask_input", return_value=s)
        buf = ffi.new("char[4096]")
        chunks = []
        while True:
            lib.cb_read_console(ffi.new("char[]", b"> "), buf, 4096, 0)
            chunk = ffi.string(buf).decode("utf-8")
            chunks.append(chunk)
            if chunk.endswith("\n"):
                break
        assert "".join(chunks) == s + "\n"



@pytest.mark.skipif(not sys.platform.startswith("win") and not sys.stdout.isatty(), reason="not tty")
def test_read_console_interrupt(mocker, gctorture):
    mocker.patch("rchitect.callbacks.ask_input", side_effect=KeyboardInterrupt())
    with pytest.raises(Exception) as excinfo:
        reval("readline('> ')")
    assert str(excinfo.value).startswith("Error")


def test_write_console(mocker, gctorture):
    mocker_write_console = mocker.patch("rchitect.console.write_console")
    reval("cat('helloworld')")
    mocker_write_console.assert_called_once_with('helloworld', 0)


def test_write_console_utf8(mocker, gctorture):
    mocker_write_console = mocker.patch("rchitect.console.write_console")
    # windows still doesn't like `𐐀`
    reval("cat('文字')")
    mocker_write_console.assert_called_once_with('文字', 0)


def test_write_console_stderr(mocker, gctorture):
    mocker_write_console = mocker.patch("rchitect.console.write_console")
    reval("cat('helloworld', file = stderr())")
    mocker_write_console.assert_called_once_with('helloworld', 1)


def test_yes_no_cancel(mocker, gctorture):
    for (a, v) in [('y', 1), ('n', 2), ('c', 0)]:
        mocker.patch("rchitect.callbacks.ask_input", return_value=a)
        ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
        assert ret == v
    mocker.resetall()


def test_yes_no_cancel_exceptions(mocker, gctorture):
    count = [0]

    def throw_on_first_run(_):
        if count[0] == 0:
            count[0] += 1
            raise Exception()
        else:
            return "y"

    mocker.patch("rchitect.callbacks.ask_input", side_effect=throw_on_first_run)
    ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
    assert ret == 1

    mocker.patch("rchitect.callbacks.ask_input", side_effect=EOFError())
    ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
    assert ret == 0

    mocker.patch("rchitect.callbacks.ask_input", side_effect=KeyboardInterrupt())
    ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
    assert ret == 0
