import pytest
from rchitect import rparse, reval, rcall, rlang, rprint, robject, rcopy
from rchitect.console import capture_console, read_stdout
from rchitect.interface import (
    getattrib,
    new_env,
    parse_text_complete,
    parse_text_incomplete,
    rclass,
    rsym,
    setattrib,
)


def test_rparse_and_reval(gctorture):
    exp = rparse("x = 1L")
    assert "expression" in rclass(exp)
    assert "integer" in rclass(reval(exp))
    assert str(exp) == "RObject{EXPRSXP}\nexpression(x = 1L)"
    call = rlang("seq", 1, 10, by=2)
    assert rcopy(reval(call)) == [1, 3, 5, 7, 9]


def test_rparse_and_reval_errors(gctorture):
    with pytest.raises(RuntimeError) as excinfo:
        rparse("x =")
    assert str(excinfo.value).startswith("Error")

    with pytest.raises(RuntimeError) as excinfo:
        rparse(r"'\g'")
    assert "an unrecognized escape in character string" in str(excinfo.value)

    with pytest.raises(RuntimeError) as excinfo:
        reval("1 + 'A'")
    assert "non-numeric argument to binary operator" in str(excinfo.value)

    with pytest.raises(RuntimeError) as excinfo:
        rcall("sum", ["a", "b"])
    assert "invalid 'type' (character) of argument" in str(excinfo.value)


def test_parse_text_complete(gctorture):
    assert parse_text_complete("1 + 1")
    assert not parse_text_incomplete("1 + 1")
    assert not parse_text_complete("1 + ")
    assert parse_text_incomplete("1 + ")
    assert parse_text_complete("1 + *")
    assert not parse_text_incomplete("1 + *")


def test_rcall(gctorture):
    assert rcall(("base", "sum"), [1, 2, 3], _convert=True) == 6
    assert rcall(("base", "::", "sum"), [1, 2, 3], _convert=True) == 6
    assert rcall(("base", ":::", "sum"), [1, 2, 3], _convert=True) == 6


def test_rprint(gctorture):
    la = rlang(robject(rprint, asis=True, invisible=True), robject(1))
    assert rcall("capture.output", la, _convert=True) == "[1] 1"

    # Symbol and call objects must be printed as language objects, not evaluated
    with capture_console(flushable=False):
        rprint(rsym("undefined_symbol_xyz"))
        assert read_stdout().strip() == "undefined_symbol_xyz"

    with capture_console(flushable=False):
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
    with capture_console(flushable=False):
        rprint(obj, envir=env)
        assert read_stdout().strip() == "x:99"
    assert rcopy(reval("x", envir=env)) == 42

    # RObject.__repr__ must not raise on R_MissingArg or failing S3 print methods
    missing_arg = reval("formals(function(x) x)$x")
    assert repr(missing_arg) == "RObject{SYMSXP}"

    reval('print.rprint_fail_cls <- function(x, ...) { cat("partial\\n"); stop("boom") }')
    fail_obj = reval('structure(1L, class = "rprint_fail_cls")')
    assert repr(fail_obj) == "RObject{INTSXP}"
    reval("rm(print.rprint_fail_cls, envir = .GlobalEnv)")

    with pytest.raises(TypeError, match="expect SEXP or RObject"):
        rprint(1)
    with pytest.raises(TypeError, match="expect SEXP or RObject"):
        reval(1)
    with pytest.raises(TypeError, match="expect SEXP or RObject"):
        rcopy(1)
    with pytest.raises(TypeError, match="expect SEXP or RObject"):
        rclass(1)


def test_symbol_and_env_validation(gctorture):
    for bad_sym in ["", "\x00", "a\x00b"]:
        with pytest.raises(ValueError):
            rsym(bad_sym)
        with pytest.raises(ValueError):
            rsym("base", bad_sym)
        with pytest.raises(ValueError):
            getattrib(robject(1), bad_sym)
        with pytest.raises(ValueError):
            setattrib(robject(1), bad_sym, 1)

    with pytest.raises(TypeError, match="expect environment"):
        new_env(robject(1))
    with pytest.raises(TypeError, match="expect environment"):
        rcall("ls", _envir=robject(1))

    # emptyenv() is a valid ENVSXP parent
    env = new_env(reval("emptyenv()"))
    assert "environment" in rclass(env)
