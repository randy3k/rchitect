from __future__ import unicode_literals

from rchitect import rparse, reval
from rchitect.interface import rclass

import pytest


def test_reval():
    exp = rparse("x = 1L")
    assert "expression" in rclass(exp)
    assert "integer" in rclass(reval(exp))
    assert str(exp) == 'RObject{EXPRSXP}\nexpression(x = 1L)'


def test_rparse_error():
    with pytest.raises(Exception) as excinfo:
        rparse("x =")
    assert str(excinfo.value) == "parse error"


def test_reval_error():
    with pytest.raises(Exception) as excinfo:
        reval("1 + 'A'")
    assert str(excinfo.value) == "eval error"
