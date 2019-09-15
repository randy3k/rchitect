# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import rparse, reval, rcall, rlang, rprint, robject
from rchitect.interface import rclass

import pytest
import sys


def test_reval():
    exp = rparse("x = 1L")
    assert "expression" in rclass(exp)
    assert "integer" in rclass(reval(exp))
    assert str(exp) == 'RObject{EXPRSXP}\nexpression(x = 1L)'


def test_rprint():
    la = rlang(robject(rprint, asis=True), robject(1))
    assert rcall("capture.output", la, _convert=True) == ['[1] 1', 'NULL']


def test_rparse_error():
    with pytest.raises(Exception) as excinfo:
        rparse("x =")
    assert str(excinfo.value).startswith("Error")


def test_reval_error():
    with pytest.raises(Exception) as excinfo:
        try:
            original_stderr = sys.stderr
            sys.stderr = None
            reval("1 + 'A'")
        finally:
            sys.stderr = original_stderr
    assert str(excinfo.value).startswith("Error")


def test_rcall_error():
    with pytest.raises(Exception) as excinfo:
        try:
            original_stderr = sys.stderr
            sys.stderr = None
            rcall("sum", [1, "A"])
        finally:
            sys.stderr = original_stderr
    assert str(excinfo.value).startswith("Error")
