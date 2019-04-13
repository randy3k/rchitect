# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import rcopy, reval, rcall
from rchitect.interface import rstring
import string


def test_booleans():
    assert rcopy(reval("TRUE")) is True
    assert rcopy(reval("FALSE")) is False
    assert rcopy(list, reval("FALSE")) == [False]


def test_numbers():
    assert rcopy(reval("5")) == 5
    assert rcopy(list, reval("5")) == [5]
    assert rcopy(reval("2 + 1i")) == complex(2, 1)
    assert rcopy(reval("c(1, 3, 5)")) == [1.0, 3.0, 5.0]
    assert rcopy(reval("c(1 + 3i, 3 + 2i)")) == [complex(1, 3), complex(3, 2)]


def test_strings():
    assert rcopy(rstring("β")) == "β"
    assert rcopy(rstring("你")) == "你"
    assert rcopy(list, rstring("x")) == ["x"]
    assert rcopy(reval("LETTERS")) == list(string.ascii_uppercase)


def test_lists():
    d = rcopy(reval("list(a = 1, b = 'hello')"))
    assert d["a"] == 1 and d["b"] == "hello"
    d = rcopy(reval("list(x = list(1, 2))"))
    assert d["x"] == [1, 2]


def test_none():
    assert rcopy(reval("NULL")) is None


def test_raw():
    assert rcopy(reval("as.raw(charToRaw('hello'))")) == b"hello"


def test_functions():
    f = rcopy(reval("function(x) x^2"))
    assert f(3) == 9
    f2 = rcopy(reval("function(x) x^2"), _convert=False)
    assert rcopy(f2(3)) == 9
