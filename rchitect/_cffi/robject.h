#ifndef ROBJECT_H__
#define ROBJECT_H__

#include "R.h"

// begin cdef

void _libR_setup_xptr_callback(void);

int _rchitect_init_conv(
    void *mod_ptr,
    void *robject_type_ptr,
    void *ordered_dict_type_ptr,
    void *function_type_ptr,
    void *wrap_r_func_ptr
);

// end cdef

#ifdef Py_PYTHON_H
int is_robject(PyObject *obj);
SEXP extract_sexp(PyObject *obj);
PyObject *c_box_sexp(SEXP s);
SEXP c_mk_rchar_from_py(PyObject *str_obj);
SEXP c_install_py_str(PyObject *str_obj);
PyObject *c_rcopy_str_list(SEXP s);
PyObject *c_rcopy_impl(SEXP s, PyObject *target_type, int asis, int convert);
SEXP c_sexp_impl(
    const char *rclass,
    PyObject *obj,
    int asis,
    int has_convert,
    int convert,
    int invisible
);
SEXP c_sexp_as_py_object_impl(PyObject *obj, int asis, int has_convert, int convert, int invisible);
#endif

#endif /* end of include guard: ROBJECT_H__ */
