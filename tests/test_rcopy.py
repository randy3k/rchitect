# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rapi import rcopy, reval


def test_number():
    assert rcopy(reval("5")) == 5


def test_unicode():
    assert rcopy(reval("'α'")) == "α"
