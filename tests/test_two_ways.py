# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rchitect import rcopy, reval, robject
from rchitect.interface import unbox


def test_rfunction(gctorture):
    f = reval("function() {}")
    assert unbox(robject(rcopy(f))) == unbox(f)


def test_pyfunction(gctorture):
    def f():
        pass

    assert rcopy(robject(f)) == f
