# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rapi import rcopy, rcall, RObject


def test_lambda():
    rcopy(rcall(RObject(lambda x: x + 3), 4)) == 7
