# include "parse.h"

typedef struct {
    SEXP text;
    int num;
    ParseStatus* status;
    SEXP source;
    SEXP val;
} ProtectedParseData;

static void protectedParse(void *d) {
    ProtectedParseData *data = (ProtectedParseData *)d;
    data->val = _R_ParseVector(data->text, data->num, data->status, data->source);
}

SEXP R_ParseVector(SEXP text, int num, ParseStatus* status, SEXP source) {
    Rboolean ok;
    ProtectedParseData d;
    d.text = Rf_protect(text);
    d.num = num;
    d.status = status;
    d.source = Rf_protect(source);
    ok = R_ToplevelExec(protectedParse, &d);
    if (ok == FALSE) {
        *status = PARSE_ERROR;
    }
    Rf_unprotect(2);
    return d.val;
}
