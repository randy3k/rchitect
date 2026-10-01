from rchitect import reticulate, reval, rcopy, rcall, robject
import string
import pytest
import sys


@pytest.mark.skipif(sys.version_info.major <= 2, reason="new version reticulate doesn't work in py2")
def test_rcopy_reticulate_object():
    reval("library(reticulate)")
    py_object = reval("r_to_py(LETTERS)")
    assert rcopy(py_object) == list(string.ascii_uppercase)


class Foo():
    pass


@pytest.mark.skipif(sys.version_info.major <= 2, reason="new version reticulate doesn't work in py2")
def test_r_to_py_rchitect_object():
    reval("library(reticulate)")
    foo = Foo()
    x = rcall("r_to_py", robject(foo))
    assert "python.builtin.object" in rcopy(rcall("class", x))
    assert rcopy(x) is foo


def test_py_to_r_rchitect_object():
    reval("library(reticulate)")
    r_vec = reval("1:5")
    py_wrapped = rcall("r_to_py", robject("PyObject", r_vec))
    assert rcopy(rcall("py_to_r", py_wrapped)) == [1, 2, 3, 4, 5]
    del py_wrapped
    del r_vec
    rcall("gc")


def test_reticulate_helpers():
    reval("library(reticulate)")
    assert reticulate.is_installed() is True
    assert reticulate.is_loaded() is True
    called = []
    reticulate.on_load(lambda: called.append(True))
    assert called == [True]
    assert reticulate.py_repl_active() is False
