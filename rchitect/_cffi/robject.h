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
extern PyObject *g_RObject_Type;
extern PyObject *g_OrderedDict_Type;
extern PyObject *g_Function_Type;
extern PyObject *g_WrapRFunction;

extern SEXP r_sym_py_object;
extern SEXP r_sym_get;

int is_robject(PyObject *obj);
SEXP extract_sexp(PyObject *obj);
PyObject *c_box_sexp(SEXP s);
PyObject *c_from_xptr(SEXP s);
SEXP c_mk_rchar_from_py(PyObject *str_obj);
SEXP c_install_py_str(PyObject *str_obj);
int c_sexp_has_class(SEXP s, const char *target_cls);
PyObject *c_rcopy_str_list(SEXP s);
PyObject *c_rcopy_impl(SEXP s, PyObject *target_type, int asis, int convert);
PyObject *py_c_rcopy(PyObject *self, PyObject *args);
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
