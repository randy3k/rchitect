from rchitect import rparse, reval, rcall, rlang, rprint, robject, rcopy
from rchitect.console import capture_console, read_stdout
from rchitect.interface import new_env, rclass, rsym

import pytest


def test_reval(gctorture):
    exp = rparse("x = 1L")
    assert "expression" in rclass(exp)
    assert "integer" in rclass(reval(exp))
    assert str(exp) == 'RObject{EXPRSXP}\nexpression(x = 1L)'
    call = rlang("seq", 1, 10, by=2)
    assert rcopy(reval(call)) == [1, 3, 5, 7, 9]


def test_rprint(gctorture):
    la = rlang(robject(rprint, asis=True, invisible=True), robject(1))
    assert rcall("capture.output", la, _convert=True) == "[1] 1"

    # Symbol and call objects must be printed as language objects, not evaluated
    with capture_console():
        rprint(rsym("undefined_symbol_xyz"))
        assert read_stdout().strip() == "undefined_symbol_xyz"

    with capture_console():
        rprint(rlang("stop", "should not be evaluated"))
        assert read_stdout().strip() == 'stop("should not be evaluated")'

    # Custom S3 print method should see `substitute(x)` as `x` and `envir$x` must not be clobbered
    env = new_env()
    reval("x <- 42L", envir=env)
    reval(
        'print.rprint_test_cls <- function(x, ...) cat(deparse(substitute(x)), x, sep = ":")',
        envir=env,
    )
    obj = reval('structure(99L, class = "rprint_test_cls")', envir=env)
    with capture_console():
        rprint(obj, envir=env)
        assert read_stdout().strip() == "x:99"
    assert rcopy(reval("x", envir=env)) == 42


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
    assert rcall(("base", ":::", "sum"), [1, 2, 3], _convert=True) == 6


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


def test_parse_text_complete(gctorture):
    from rchitect.interface import parse_text_complete, parse_text_incomplete

    assert parse_text_complete("1 + 1")
    assert not parse_text_incomplete("1 + 1")
    assert not parse_text_complete("1 + ")
    assert parse_text_incomplete("1 + ")
    assert parse_text_complete("1 + *")
    assert not parse_text_incomplete("1 + *")



