#include <Python.h>
#include "gli.h"

// cffi releases GLI look, so we need to ensure it. Mainly needed for loading reticulate.

void run_Rmainloop(void) {
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();
    _run_Rmainloop();
    PyGILState_Release(gstate);
}

SEXP R_tryEval(SEXP x, SEXP e, int* s) {
    PyGILState_STATE gstate;
    SEXP result;
    gstate = PyGILState_Ensure();
    result = _R_tryEval(x, e, s);
    PyGILState_Release(gstate);
    return result;
}
