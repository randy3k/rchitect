from __future__ import unicode_literals

from rchitect.interface import rcall, reval, rcopy, rstring, rint
from six import text_type


def assign_line_buffer(buf):
    rcall(reval("utils:::.assignLinebuffer"), rstring(buf))
    rcall(reval("utils:::.assignEnd"), rint(len(buf)))
    token = rcopy(text_type, rcall(reval("utils:::.guessTokenFromLine")))
    return token


CompleteCode = """
tryCatch(
    {{
        if ({settimelimit}) base::setTimeLimit({timeout})
        utils:::.completeToken()
        if ({settimelimit}) base::setTimeLimit()
    }},
    error = function(e) {{
        if ({settimelimit}) base::setTimeLimit()
        assign("comps", NULL, env = utils:::.CompletionEnv)
    }}
)
"""


def complete_token(timeout=0):
    try:
        reval(
            CompleteCode.format(
                settimelimit="TRUE" if timeout > 0 else "FALSE",
                timeout=str(timeout)),
            envir=rcall("new.env")
        )
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
