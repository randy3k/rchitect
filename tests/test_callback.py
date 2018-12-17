# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import rcopy, rcall, robject


def test_lambda():
    rcopy(rcall(robject(lambda x: x + 3), 4)) == 7
