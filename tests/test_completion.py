# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rchitect import completion


def test_completion(gctorture):
    completion.assign_line_buffer("lib")
    completion.complete_token()
    assert "library" in completion.retrieve_completions()
