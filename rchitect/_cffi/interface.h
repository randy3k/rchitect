#ifndef INTERFACE_H__
#define INTERFACE_H__

#include "R.h"

// begin cdef

int _libR_is_initialized(void);
SEXP rchitect_ParseVector(SEXP, int, ParseStatus *, SEXP);
SEXP rchitect_tryEval(SEXP, SEXP, int *);

// end cdef

int _rchitect_register_interface_methods(void *mod_ptr);

#endif /* end of include guard: INTERFACE_H__ */
