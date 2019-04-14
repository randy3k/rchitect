# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import reval, rcopy


def test_input(mocker):
    mocker.patch("rchitect.setup.ask_input", return_value="hello")
    ret = reval("readline('> ')")
    assert rcopy(ret) == "hello"


def test_long_input(mocker):
    s = "a" * 5000
    mocker.patch("rchitect.setup.ask_input", return_value=s)
    ret = reval("readline('> ')")
    assert rcopy(ret) == s
