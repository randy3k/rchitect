from rchitect import rcall, reval, rcopy
from rchitect.interface import rclass, new_env
import os


def test_py_tools():
    unattached_env = new_env()
    path_unattached = reval("""
        os <- getOption("rchitect.py_tools")$import("os")
        os$path$join("foo", "bar")
    """, envir=unattached_env)
    assert rcopy(path_unattached) == os.path.join("foo", "bar")
    assert "path" in rcopy(reval("utils:::.DollarNames(os, 'pa')", envir=unattached_env))

    env = new_env()
    reval("getOption('rchitect.py_tools')$attach()", envir=env)
    env_names = rcall("names", env, _convert=True)
    assert "import" in env_names
    assert "$.PyObject" not in env_names

    reval("os <- import('os')", envir=env)

    path = reval("""
        os$path$join("foo", "bar")
    """, envir=env)
    assert "character" in rclass(path)
    assert rcopy(path) == os.path.join("foo", "bar")

    path = reval("""
        py_call(os$path$join, "foo", "bar")
    """, envir=env)
    assert "PyObject" in rclass(path)
    assert rcopy(path) == os.path.join("foo", "bar")

    ret = reval("""
        bulitins <- import_builtins()
        len <- bulitins$len
        len(py_eval("[1, 2, 3]"))
    """, envir=env)
    assert rcopy(ret) == 3

    ret = reval("""
        pyo <- py_object("hello")
        py_copy(pyo)
    """, envir=env)
    assert rcopy(ret) == "hello"

    ret = reval("""
        x <- py_eval("[1, 2, 3]")
        x[2L]
    """, envir=env)
    assert rcopy(ret) == 3

    ret = reval("""
        x <- py_eval("[1, 2, 3]")
        x[2L] <- 4L
        x
    """, envir=env)
    assert rcopy(ret) == [1, 2, 4]
    assert not rcall("attributes", ret, _convert=True)['convert']

    ret = reval("""
        d <- dict(a = 1L, b = 2L)
        d['b']
    """, envir=env)
    assert rcopy(ret) == 2

    ret = reval("""
        Foo <- py_eval("type(str('Foo'), (object,), {'bar': lambda self: 42})")
        foo <- Foo()
        foo$x <- 1L
        foo
    """, envir=env)
    assert rcopy(ret).x == 1
    assert not rcall("attributes", ret, _convert=True)['convert']
    assert "bar" in rcopy(reval("utils:::.DollarNames(foo, 'ba')", envir=env))
    assert "append" in rcopy(reval("utils:::.DollarNames(py_eval('[1, 2]'), 'app')", envir=env))

    ret = reval("""
        rchitect <- import("rchitect")
        rchitect$xxxx <- 3L
        rchitect
    """, envir=env)
    assert rcopy(ret).xxxx == 3
    assert rcall("attributes", ret, _convert=True)['convert']

    assert rcopy(reval("py_unicode('hello')", envir=env)) == "hello"

    assert rcopy(reval("tuple('a', 3)", envir=env)) == ('a', 3)

    # Multi-index subscripting on PyObject (both [ and [<- and direct py_get_item/py_set_item)
    ret_multi = reval("""
        m <- dict()
        m[1L, 2L] <- 99L
        c(py_copy(m[1L, 2L]), py_copy(py_get_item(m, 1L, 2L)))
    """, envir=env)
    assert rcopy(ret_multi) == [99, 99]

    ret_multi_set = reval("""
        py_set_item(m, 3L, 4L, 77L)
        py_copy(m[3L, 4L])
    """, envir=env)
    assert rcopy(ret_multi_set) == 77

    # py_eval and py_call evaluate strings against __main__.__dict__
    import __main__
    import pytest

    __main__._test_py_tools_var = 123
    __main__._test_py_tools_fn = lambda a, b: a + b
    try:
        assert rcopy(reval("py_copy(py_eval('_test_py_tools_var'))", envir=env)) == 123
        assert rcopy(reval("py_copy(py_call('_test_py_tools_fn', 10L, 20L))", envir=env)) == 30
    finally:
        del __main__._test_py_tools_var
        del __main__._test_py_tools_fn

    with pytest.raises(RuntimeError, match="py_object expected 1 or 2 positional arguments"):
        reval("py_object()", envir=env)
