# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import reval, rcopy, rcall, robject
import string


def test_rcopy_reticulate_object():
    reval("library(reticulate)")
    py_object = reval("r_to_py(LETTERS)")
    assert rcopy(py_object) == list(string.ascii_uppercase)


class Foo():
    pass


def test_r_to_py_rchitect_object():
    reval("library(reticulate)")
    foo = Foo()
    x = rcall("r_to_py", robject(foo))
    assert "python.builtin.object" in rcopy(rcall("class", x))
