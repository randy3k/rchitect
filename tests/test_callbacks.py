# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import reval, rcopy
from rchitect._cffi import lib, ffi
import pytest
import sys


def test_read_console(mocker):
    mocker.patch("rchitect.setup.ask_input", return_value="hello")
    ret = reval("readline('> ')")
    assert rcopy(ret) == "hello"


def test_read_console_long(mocker):
    s = "a" * 5000
    mocker.patch("rchitect.setup.ask_input", return_value=s)
    ret = reval("readline('> ')")
    assert rcopy(ret) == s


def test_read_console_interrupt(mocker):
    mocker.patch("rchitect.setup.ask_input", side_effect=KeyboardInterrupt())
    with pytest.raises(Exception) as excinfo:
        reval("readline('> ')")
    if sys.version_info[0] >= 3:
        assert str(excinfo.value).startswith("Error")
    else:
        assert str(excinfo).startswith("Error")


def test_yes_no_cancel(mocker):
    for (a, v) in [('y', 1), ('n', 2), ('c', 0)]:
        mocker.patch("rchitect.setup.ask_input", return_value=a)
        ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
        assert ret == v
    mocker.resetall()


def test_yes_no_cancel_exceptions(mocker):
    count = [0]

    def throw_on_first_run(_):
        if count[0] == 0:
            count[0] += 1
            raise Exception()
        else:
            return "y"

    mocker.patch("rchitect.setup.ask_input", side_effect=throw_on_first_run)
    ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
    assert ret == 1

    mocker.patch("rchitect.setup.ask_input", side_effect=EOFError())
    ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
    assert ret == 0

    mocker.patch("rchitect.setup.ask_input", side_effect=KeyboardInterrupt())
    ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
    assert ret == 0
