#ifndef INTERFACE_H__
#define INTERFACE_H__

#include "R.h"

// begin cdef

int _libR_is_initialized(void);

// end cdef

void c_preserve_sexp(SEXP s);
int _rchitect_register_interface_methods(void *mod_ptr);

#endif /* end of include guard: INTERFACE_H__ */
