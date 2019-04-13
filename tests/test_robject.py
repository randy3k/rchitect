# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import rcopy, rcall, reval, robject
from rchitect.interface import rclass, rstring, rint, rdouble


def test_numbers():
    assert rcall("identical", robject(1), rint(1), _convert=True)
    assert rcall("identical", robject(1.0), rdouble(1), _convert=True)
    assert not rcall("identical", robject(1), rdouble(1), _convert=True)
    assert not rcall("identical", robject(1.0), rint(1), _convert=True)

    assert rcall("identical", robject(complex(1, 2)), reval("1 + 2i"), _convert=True)

    assert rcall("identical", robject([1, 2]), reval("c(1L, 2L)"), _convert=True)
    assert rcall("identical", robject([1.0, 2.0]), reval("c(1, 2)"), _convert=True)


def test_strings():
    assert rcall("identical", robject("abc"), rstring("abc"), _convert=True)
    assert rcall("identical", robject("β"), rstring("β"), _convert=True)
    assert rcall("identical", robject("你"), rstring("你"), _convert=True)
    assert rcall("identical", robject(['a', 'b']), reval("c('a', 'b')"), _convert=True)


def test_lambda():
    def f(x):
        return x + 3

    fun = robject(f)
    assert "PyCallable" in rclass(fun)
    assert rcopy(rcall(fun, 4)) == f(4)

    fun = robject(lambda x: x + 3, convert=False)
    assert "PyCallable" in rclass(fun)
    ret = rcall(fun, 4)
    assert "PyObject" in rclass(ret)
    assert rcopy(ret) == f(4)
