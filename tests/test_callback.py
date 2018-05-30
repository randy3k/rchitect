# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rapi import rtopy, rcall, pytor


def test_lambda():
    rtopy(rcall(pytor(lambda x: x + 3), 4)) == 7
