from rchitect import rcopy, reval
from rchitect.interface import rstring
import string
from collections import OrderedDict


def test_booleans(gctorture):
    assert rcopy(reval("TRUE")) is True
    assert rcopy(reval("FALSE")) is False
    assert rcopy(list, reval("FALSE")) == [False]
    assert rcopy(reval("c(TRUE, FALSE)")) == [True, False]


def test_numbers(gctorture):
    assert rcopy(reval("5")) == 5
    assert rcopy(list, reval("5")) == [5]
    assert rcopy(reval("2 + 1i")) == complex(2, 1)
    assert rcopy(reval("c(1L, 3L, 5L)")) == [1, 3, 5]
    assert rcopy(reval("c(1, 3, 5)")) == [1.0, 3.0, 5.0]
    assert rcopy(reval("c(1 + 3i, 3 + 2i)")) == [complex(1, 3), complex(3, 2)]


def test_strings(gctorture):
    assert rcopy(rstring("β")) == "β"
    assert rcopy(rstring("你")) == "你"
    assert rcopy(list, rstring("x")) == ["x"]
    assert rcopy(reval("LETTERS")) == list(string.ascii_uppercase)


def test_lists(gctorture):
    d = rcopy(reval("list(a = 1, b = 'hello')"))
    assert isinstance(d, OrderedDict)
    assert d["a"] == 1 and d["b"] == "hello"
    d = rcopy(dict, reval("list(a = 1, b = 'hello')"))
    assert isinstance(d, dict)
    assert d["a"] == 1 and d["b"] == "hello"
    d = rcopy(reval("list(x = list(1, 2))"))
    assert d["x"] == [1, 2]
    assert rcopy(tuple, reval("list(1, 2)")) == (1, 2)


def test_none(gctorture):
    assert rcopy(reval("NULL")) is None


def test_raw(gctorture):
    assert rcopy(reval("as.raw(charToRaw('hello'))")) == b"hello"


def test_functions(gctorture):
    f = rcopy(reval("function(x) x^2"))
    assert f(3) == 9
    f2 = rcopy(reval("function(x) x^2"), convert=False)
    assert rcopy(f2(3)) == 9
    sumfun = rcopy(reval("sum"))
    assert sumfun([1, 2, 3]) == 6
