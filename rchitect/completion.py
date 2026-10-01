from rchitect.interface import rcall, reval, rcopy


_completion_fns = None

_ASSIGN_LINE_BUFFER_CODE = """
function(buf) {
    utils:::.assignLinebuffer(buf)
    utils:::.assignEnd(nchar(buf))
    utils:::.guessTokenFromLine()
}
"""

_COMPLETE_TOKEN_CODE = """
function(timeout = 0) {
    settimelimit <- timeout > 0
    tryCatch(
        {
            if (settimelimit) base::setTimeLimit(timeout)
            utils:::.completeToken()
            if (settimelimit) base::setTimeLimit()
        },
        error = function(e) {
            if (settimelimit) base::setTimeLimit()
            assign("comps", NULL, envir = utils:::.CompletionEnv)
        }
    )
}
"""


def _get_completion_fns():
    global _completion_fns
    if _completion_fns is None:
        _completion_fns = (
            reval(_ASSIGN_LINE_BUFFER_CODE),
            reval(_COMPLETE_TOKEN_CODE),
            reval("utils:::.retrieveCompletions"),
        )
    return _completion_fns


def assign_line_buffer(buf):
    assign_fn, _, _ = _get_completion_fns()
    return rcopy(str, rcall(assign_fn, buf))


def complete_token(timeout=0):
    _, complete_fn, _ = _get_completion_fns()
    rcall(complete_fn, timeout)


def retrieve_completions():
    _, _, retrieve_fn = _get_completion_fns()
    completions = rcopy(list, rcall(retrieve_fn))
    if not completions:
        return []
    else:
        return completions

