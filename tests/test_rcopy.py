# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rapi import rtopy, reval


def test_number():
    assert rtopy(reval("5")) == 5


def test_unicode():
    assert rtopy(reval("'α'")) == "α"
