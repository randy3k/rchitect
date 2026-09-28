from rchitect import rparse, reval, rcall, rlang, rprint, robject
from rchitect.interface import rclass

import pytest


def test_reval(gctorture):
    exp = rparse("x = 1L")
    assert "expression" in rclass(exp)
    assert "integer" in rclass(reval(exp))
    assert str(exp) == 'RObject{EXPRSXP}\nexpression(x = 1L)'


def test_rprint(gctorture):
    la = rlang(robject(rprint, asis=True, invisible=True), robject(1))
    assert rcall("capture.output", la, _convert=True) == "[1] 1"


def test_rparse_error(gctorture):
    with pytest.raises(Exception) as excinfo:
        rparse("x =")
        assert str(excinfo.value).startswith("Error")


def test_rparse_error2(gctorture):
    with pytest.raises(Exception) as excinfo:
        rparse("'\\g'")
        assert "an unrecognized escape in character string" in str(excinfo.value)


def test_reval_error(gctorture):
    with pytest.raises(Exception) as excinfo:
        reval("1 + 'A'")
        assert "non-numeric argument to binary operator" in str(excinfo.value)


def test_rcall_error(gctorture):
    with pytest.raises(Exception) as excinfo:
        rcall("sum", ["a", "b"])
        assert "invalid 'type' (character) of argument" in str(excinfo.value)


def test_rcall_tuple(gctorture):
    assert rcall(("base", "sum"), [1, 2, 3], _convert=True) == 6
    assert rcall(("base", "::", "sum"), [1, 2, 3], _convert=True) == 6
    assert isinstance(rcall(("utils", ":::", ".retrieveCompletions"), _convert=True), list)


def test_get_rhome_r_binary(monkeypatch):
    import os
    from rchitect.utils import get_rhome

    expected_rhome = get_rhome()
    rbinary = os.path.join(expected_rhome, "bin", "R")
    monkeypatch.setenv("R_BINARY", rbinary)
    monkeypatch.delenv("R_HOME", raising=False)
    assert get_rhome() == expected_rhome
    assert os.environ.get("R_HOME") == expected_rhome

    monkeypatch.setenv("R_HOME", "/nonexistent/rhome")
    assert get_rhome() == expected_rhome
    assert os.environ.get("R_HOME") == expected_rhome


