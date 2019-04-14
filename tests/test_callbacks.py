# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import reval, rcopy, rcall


def test_read_console(mocker):
    mocker.patch("rchitect.setup.ask_input", return_value="hello")
    ret = reval("readline('> ')")
    assert rcopy(ret) == "hello"


def test_read_console_long(mocker):
    s = "a" * 5000
    mocker.patch("rchitect.setup.ask_input", return_value=s)
    ret = reval("readline('> ')")
    assert rcopy(ret) == s


def test_yes_no_cancel(mocker):
    mocker.patch("rchitect.setup.ask_input", return_value="y")
    ret = reval("askYesNo('Yes/No/Cancel')")
    assert rcopy(ret) is True

    mocker.patch("rchitect.setup.ask_input", return_value="n")
    ret = reval("askYesNo('Yes/No/Cancel')")
    assert rcopy(ret) is False

    mocker.patch("rchitect.setup.ask_input", return_value="c")
    ret = reval("askYesNo('Yes/No/Cancel')")
    assert rcall("is.na", ret, _convert=True)
