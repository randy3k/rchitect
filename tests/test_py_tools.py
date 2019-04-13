# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import rparse, rcall, rcopy
from rchitect.interface import rclass
import os


def test_py_tools():
    env = rcall("new.env")
    rcall("eval", rparse("getOption('rchitect_py_tools')$register()"), envir=env)
    assert "import" in rcall("names", env, _convert=True)

    rcall("eval", rparse("os = import('os')"), envir=env)

    path = rcall("eval", rparse("""
        os$path$join("foo", "bar")
    """), envir=env)
    assert "character" in rclass(path)
    assert rcopy(path) == os.path.join("foo", "bar")

    path = rcall("eval", rparse("""
        py_call(os$path$join, "foo", "bar")
    """), envir=env)
    assert "PyObject" in rclass(path)
    assert rcopy(path) == os.path.join("foo", "bar")
