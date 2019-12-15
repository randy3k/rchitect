from __future__ import unicode_literals

from rchitect.interface import rcall, reval, rcopy, rstring, rint
from six import text_type


def assign_line_buffer(buf):
    rcall(reval("utils:::.assignLinebuffer"), rstring(buf))
    rcall(reval("utils:::.assignEnd"), rint(len(buf)))
    token = rcopy(text_type, rcall(reval("utils:::.guessTokenFromLine")))
    return token


def complete_token(timeout=0):
    try:
        if timeout:
            rcall(("base", "setTimeLimit"), timeout)
        reval("utils:::.completeToken()")
        if timeout:
            rcall(("base", "setTimeLimit"))
    except Exception:
        if timeout:
            rcall(("base", "setTimeLimit"))
            rcall(("base", "assign"), "comps", None, env=reval("utils:::.CompletionEnv"))


def retrieve_completions():
    completions = rcopy(list, rcall(reval("utils:::.retrieveCompletions")))
    if not completions:
        return []
    else:
        return completions
