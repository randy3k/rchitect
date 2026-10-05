import __main__
import os
import pytest
from rchitect import rcall, rcopy, reval
from rchitect.interface import new_env, rclass


@pytest.fixture
def py_tools_env():
    env = new_env()
    reval("getOption('rchitect.py_tools')$attach()", envir=env)
    return env


def test_import_and_attach(py_tools_env):
    unattached_env = new_env()
    path_unattached = reval(
        """
        os <- getOption("rchitect.py_tools")$import("os")
        os$path$join("foo", "bar")
    """,
        envir=unattached_env,
    )
    assert rcopy(path_unattached) == os.path.join("foo", "bar")
    assert "path" in rcopy(reval("utils:::.DollarNames(os, 'pa')", envir=unattached_env))

    env_names = rcall("names", py_tools_env, _convert=True)
    assert "import" in env_names
    assert "$.PyObject" not in env_names

    reval("os <- import('os')", envir=py_tools_env)
    path = reval('os$path$join("foo", "bar")', envir=py_tools_env)
    assert "character" in rclass(path)
    assert rcopy(path) == os.path.join("foo", "bar")


def test_call_and_eval(py_tools_env):
    reval("os <- import('os')", envir=py_tools_env)
    path = reval('py_call(os$path$join, "foo", "bar")', envir=py_tools_env)
    assert "PyObject" in rclass(path)
    assert rcopy(path) == os.path.join("foo", "bar")

    ret = reval(
        """
        builtins <- import_builtins()
        len <- builtins$len
        len(py_eval("[1, 2, 3]"))
    """,
        envir=py_tools_env,
    )
    assert rcopy(ret) == 3

    __main__._test_py_tools_var = 123
    __main__._test_py_tools_fn = lambda a, b: a + b
    try:
        assert rcopy(reval("py_copy(py_eval('_test_py_tools_var'))", envir=py_tools_env)) == 123
        assert (
            rcopy(reval("py_copy(py_call('_test_py_tools_fn', 10L, 20L))", envir=py_tools_env))
            == 30
        )
    finally:
        del __main__._test_py_tools_var
        del __main__._test_py_tools_fn


def test_indexing_and_attributes(py_tools_env):
    ret = reval(
        """
        x <- py_eval("[1, 2, 3]")
        x[2L]
    """,
        envir=py_tools_env,
    )
    assert rcopy(ret) == 3

    ret = reval(
        """
        x <- py_eval("[1, 2, 3]")
        x[2L] <- 4L
        x
    """,
        envir=py_tools_env,
    )
    assert rcopy(ret) == [1, 2, 4]
    assert not rcall("attributes", ret, _convert=True)["convert"]

    ret = reval(
        """
        d <- dict(a = 1L, b = 2L)
        d['b']
    """,
        envir=py_tools_env,
    )
    assert rcopy(ret) == 2

    ret_multi = reval(
        """
        m <- dict()
        m[1L, 2L] <- 99L
        c(py_copy(m[1L, 2L]), py_copy(py_get_item(m, 1L, 2L)))
    """,
        envir=py_tools_env,
    )
    assert rcopy(ret_multi) == [99, 99]

    ret_multi_set = reval(
        """
        py_set_item(m, 3L, 4L, 77L)
        py_copy(m[3L, 4L])
    """,
        envir=py_tools_env,
    )
    assert rcopy(ret_multi_set) == 77

    ret = reval(
        """
        rchitect <- import("rchitect")
        rchitect$xxxx <- 3L
        rchitect
    """,
        envir=py_tools_env,
    )
    assert rcopy(ret).xxxx == 3
    assert rcall("attributes", ret, _convert=True)["convert"]


def test_dollar_names_and_completion(py_tools_env):
    ret = reval(
        """
        Foo <- py_eval("type(str('Foo'), (object,), {'bar': lambda self: 42})")
        foo <- Foo()
        foo$x <- 1L
        foo
    """,
        envir=py_tools_env,
    )
    assert rcopy(ret).x == 1
    assert not rcall("attributes", ret, _convert=True)["convert"]
    assert "bar" in rcopy(reval("utils:::.DollarNames(foo, 'ba')", envir=py_tools_env))
    assert "append" in rcopy(
        reval("utils:::.DollarNames(py_eval('[1, 2]'), 'app')", envir=py_tools_env)
    )


def test_type_helpers_and_errors(py_tools_env):
    ret = reval(
        """
        pyo <- py_object("hello")
        py_copy(pyo)
    """,
        envir=py_tools_env,
    )
    assert rcopy(ret) == "hello"
    assert rcopy(reval("py_unicode('hello')", envir=py_tools_env)) == "hello"
    assert rcopy(reval("tuple('a', 3)", envir=py_tools_env)) == ("a", 3)

    with pytest.raises(RuntimeError, match="py_object expected 1 or 2 positional arguments"):
        reval("py_object()", envir=py_tools_env)
