from rchitect.interface import rcall, reval, rcopy


_completion_fns = None

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
            reval("utils:::.assignLinebuffer"),
            reval("utils:::.assignEnd"),
            reval("utils:::.guessTokenFromLine"),
            reval(_COMPLETE_TOKEN_CODE),
            reval("utils:::.retrieveCompletions"),
        )
    return _completion_fns


def assign_line_buffer(buf):
    assign_buf, assign_end, guess_token, _, _ = _get_completion_fns()
    rcall(assign_buf, buf)
    rcall(assign_end, len(buf))
    token = rcopy(str, rcall(guess_token))
    return token


def complete_token(timeout=0):
    _, _, _, complete_fn, _ = _get_completion_fns()
    rcall(complete_fn, timeout)


def retrieve_completions():
    _, _, _, _, retrieve_fn = _get_completion_fns()
    completions = rcopy(list, rcall(retrieve_fn))
    if not completions:
        return []
    else:
        return completions

