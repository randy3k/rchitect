from rchitect import rcall, reval, rcopy
from rchitect.interface import rclass, new_env
import os


def test_py_tools():
    env = new_env()
    reval("getOption('rchitect.py_tools')$attach()", envir=env)
    assert "import" in rcall("names", env, _convert=True)

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
        Foo <- py_eval("type(str('Foo'), (object,), {})")
        foo <- Foo()
        foo$x <- 1L
        foo
    """, envir=env)
    assert rcopy(ret).x == 1
    assert not rcall("attributes", ret, _convert=True)['convert']

    ret = reval("""
        rchitect <- import("rchitect")
        rchitect$xxxx <- 3L
        rchitect
    """, envir=env)
    assert rcopy(ret).xxxx == 3
    assert rcall("attributes", ret, _convert=True)['convert']

    assert rcopy(reval("py_unicode('hello')", envir=env)) == "hello"

    assert rcopy(reval("tuple('a', 3)", envir=env)) == ('a', 3)
