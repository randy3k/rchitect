#ifndef GIL_H__
#define GIL_H__

# include "R.h"

// begin cdef

void run_Rmainloop(void);

SEXP R_tryEval(SEXP, SEXP, int *);

// end cdef

#endif /* end of include guard: GIL_H__ */
