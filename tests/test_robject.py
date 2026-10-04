from collections import OrderedDict
import os
import sys
import threading
import pytest
from rchitect import rcall, rcopy, reval, robject
from rchitect.interface import rclass, rdouble, rint, rstring


def test_booleans(gctorture):
    assert rcall("identical", robject([True, False]), reval("c(TRUE, FALSE)"), _convert=True)


def test_numbers(gctorture):
    assert rcall("identical", robject(1), rint(1), _convert=True)
    assert rcall("identical", robject(1.0), rdouble(1), _convert=True)
    assert not rcall("identical", robject(1), rdouble(1), _convert=True)
    assert not rcall("identical", robject(1.0), rint(1), _convert=True)

    assert rcall("identical", robject(complex(1, 2)), reval("1 + 2i"), _convert=True)

    assert rcall("identical", robject([1, 2]), reval("c(1L, 2L)"), _convert=True)
    assert rcall("identical", robject([1.0, 2.0]), reval("c(1, 2)"), _convert=True)
    assert rcall(
        "identical",
        robject([complex(1, 2), complex(2, 1)]),
        reval("c(1 + 2i, 2 + 1i)"),
        _convert=True,
    )

    with pytest.raises(TypeError):
        robject("complex", ["invalid"])

    # 64-bit integer overflow raises OverflowError, while NA_integer_ (-2147483648) round-trips
    with pytest.raises(OverflowError):
        robject(2**40)
    with pytest.raises(OverflowError):
        robject(-(2**40))
    with pytest.raises(OverflowError):
        robject("integer", [2**40])
    na_int = rcopy(reval("NA_integer_"))
    assert rcall("is.na", robject(na_int), _convert=True) is True
    assert rcall("is.na", robject("integer", [na_int]), _convert=True) is True

    class BadBool:
        def __bool__(self):
            raise RuntimeError("bad bool")

    with pytest.raises(RuntimeError, match="bad bool"):
        robject("logical", [BadBool()])


def test_strings(gctorture):
    assert rcall("identical", robject("abc"), rstring("abc"), _convert=True)
    assert rcall("identical", robject("β"), rstring("β"), _convert=True)
    assert rcall("identical", robject("你"), rstring("你"), _convert=True)
    assert rcall("identical", robject(["a", "b"]), reval("c('a', 'b')"), _convert=True)

    with pytest.raises(ValueError, match="embedded nul"):
        robject("a\x00b")
    with pytest.raises(ValueError, match="embedded nul"):
        rstring("\x00")


def test_raw(gctorture):
    assert rcall("rawToChar", robject("raw", b"hello"), _convert=True) == "hello"
    assert rcopy(robject("raw", b"\x01\x00\x02")) == b"\x01\x00\x02"


def test_none(gctorture):
    assert rcall("identical", robject(None), reval("NULL"), _convert=True)


def test_dicts(gctorture):
    d = OrderedDict([("a", 2), ("b", "hello")])
    assert rcall("identical", robject(d), reval("list(a = 2L, b = 'hello')"), _convert=True)
    d2 = {"a": 2, "b": "hello"}
    assert rcall("identical", robject(d2), reval("list(a = 2L, b = 'hello')"), _convert=True)


def test_functions(gctorture):
    def f(x):
        return x + 3

    fun = robject(f)
    assert "PyCallable" in rclass(fun)
    assert rcopy(fun) == f
    assert rcopy(rcall(fun, 4)) == f(4)
    assert rcopy(rcall(fun, x=4)) == f(4)

    fun = robject(lambda x: x + 3, convert=False)
    assert "PyCallable" in rclass(fun)
    ret = rcall(fun, 4)
    assert "PyObject" in rclass(ret)
    assert rcopy(ret) == f(4)

    makef = robject(lambda: f, convert=False)
    ret = rcall(makef)
    assert "PyCallable" in rclass(ret)
    assert rcopy(ret) == f

    msg = "error message " * 30

    def fail():
        raise ValueError(msg)

    err_fun = robject(fail)
    captured = rcopy(
        rcall(
            "tryCatch",
            rcall("as.call", [err_fun]),
            error=reval("function(e) conditionMessage(e)"),
        )
    )
    assert "ValueError" in captured and msg in captured

    def fail_empty():
        raise AssertionError()

    err_empty_fun = robject(fail_empty)
    captured_empty = rcopy(
        rcall(
            "tryCatch",
            rcall("as.call", [err_empty_fun]),
            error=reval("function(e) conditionMessage(e)"),
        )
    )
    assert captured_empty == "AssertionError"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="fork not supported on Windows")
def test_fork_xptr_finalizer():
    parent_pid = os.getpid()
    r_fd, w_fd = os.pipe()
    os.set_blocking(r_fd, False)

    def read_pids():
        try:
            data = os.read(r_fd, 4096)
        except BlockingIOError:
            return []
        return [int(x) for x in data.decode("ascii").splitlines() if x]

    class TrackedResource(object):
        def __del__(self):
            try:
                os.write(w_fd, "{}\n".format(os.getpid()).encode("ascii"))
            except OSError:
                pass

    stop_bg = threading.Event()

    def bg_gil_worker():
        while not stop_bg.is_set():
            _ = sum(range(100))

    bg = threading.Thread(target=bg_gil_worker)
    bg.start()
    try:
        rcall(("base", "assign"), "tracked_res", robject("PyObject", TrackedResource()))
        res = rcopy(
            reval(
                "parallel::mclapply(1:2, function(i) {"
                "  rm(tracked_res, envir = .GlobalEnv);"
                "  gc();"
                "  i"
                "}, mc.cores = 2)"
            )
        )
        assert res == [1, 2]
        assert read_pids() == []

        reval("rm(tracked_res, envir = .GlobalEnv); gc()")
        assert read_pids() == [parent_pid]
    finally:
        stop_bg.set()
        bg.join(timeout=1.0)
        os.close(r_fd)
        os.close(w_fd)
