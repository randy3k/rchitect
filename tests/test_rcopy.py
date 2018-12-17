# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import rcopy, reval, rstring


def test_number():
    assert rcopy(reval("5")) == 5


def test_unicode():
    assert rcopy(rstring("β")) == "β"
    assert rcopy(rstring("你")) == "你"
