#include "gil.h"

#include <Python.h>

// cffi releases GIL, so we need to ensure it. Mainly needed for loading reticulate.

void rchitect_run_Rmainloop(void) {
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();
    run_Rmainloop();
    PyGILState_Release(gstate);
}

SEXP rchitect_tryEval(SEXP x, SEXP e, int* s) {
    PyGILState_STATE gstate;
    SEXP result;
    gstate = PyGILState_Ensure();
    result = R_tryEval(x, e, s);
    PyGILState_Release(gstate);
    return result;
}
