#include <Python.h>
#include <string.h>

#include "robject.h"

#ifndef PyList_SET_ITEM
#define PyList_SET_ITEM(op, i, v) ((void)PyList_SetItem((op), (i), (v)))
#endif
#ifndef PyTuple_SET_ITEM
#define PyTuple_SET_ITEM(op, i, v) ((void)PyTuple_SetItem((op), (i), (v)))
#endif

// =============================================================================
// 1. Embedded Python Object & R Function Extraction Helpers
// =============================================================================

static PyObject *c_extract_pyobj_from_env_or_clos(SEXP s) {
    if (TYPEOF(s) == EXTPTRSXP) {
        return c_from_xptr(s);
    }
    if (TYPEOF(s) == CLOSXP) {
        SEXP py_obj_attr = Rf_getAttrib(s, Rf_install("py_object"));
        if (py_obj_attr != R_NilValue && TYPEOF(py_obj_attr) == EXTPTRSXP) {
            return c_from_xptr(py_obj_attr);
        }
    }
    SEXP get_sym = Rf_install("get");
    SEXP pyobj_str = Rf_protect(Rf_mkString("pyobj"));
    SEXP call = Rf_protect(Rf_lang3(get_sym, pyobj_str, s));
    int status = 0;
    SEXP x = Rf_protect(R_tryEval(call, R_BaseEnv, &status));
    if (status != 0 || TYPEOF(x) != EXTPTRSXP) {
        Rf_unprotect(3);
        PyErr_SetString(PyExc_RuntimeError, "Failed to extract pyobj from R object");
        return NULL;
    }
    PyObject *res = c_from_xptr(x);
    Rf_unprotect(3);
    return res;
}

static PyObject *c_wrap_r_function(SEXP s, int asis, int convert) {
    PyObject *robj = c_box_sexp(s);
    if (robj == NULL) return NULL;
    PyObject *py_asis = PyBool_FromLong(asis);
    PyObject *py_convert = PyBool_FromLong(convert);
    PyObject *res = PyObject_CallFunctionObjArgs(g_WrapRFunction, robj, py_asis, py_convert, NULL);
    Py_DECREF(robj);
    Py_DECREF(py_asis);
    Py_DECREF(py_convert);
    return res;
}

// =============================================================================
// 2. R Vector & List Conversion Helpers
// =============================================================================

static PyObject *c_rcopy_int_list(SEXP s) {
    R_xlen_t n = Rf_xlength(s);
    int *p = INTEGER(s);
    PyObject *lst = PyList_New((Py_ssize_t)n);
    if (lst == NULL) return NULL;
    for (R_xlen_t i = 0; i < n; i++) {
        PyObject *item = PyLong_FromLong(p[i]);
        if (item == NULL) {
            Py_DECREF(lst);
            return NULL;
        }
        PyList_SET_ITEM(lst, (Py_ssize_t)i, item);
    }
    return lst;
}

static PyObject *c_rcopy_lgl_list(SEXP s) {
    R_xlen_t n = Rf_xlength(s);
    int *p = LOGICAL(s);
    PyObject *lst = PyList_New((Py_ssize_t)n);
    if (lst == NULL) return NULL;
    for (R_xlen_t i = 0; i < n; i++) {
        PyObject *item = PyBool_FromLong(p[i]);
        PyList_SET_ITEM(lst, (Py_ssize_t)i, item);
    }
    return lst;
}

static PyObject *c_rcopy_real_list(SEXP s) {
    R_xlen_t n = Rf_xlength(s);
    double *p = REAL(s);
    PyObject *lst = PyList_New((Py_ssize_t)n);
    if (lst == NULL) return NULL;
    for (R_xlen_t i = 0; i < n; i++) {
        PyObject *item = PyFloat_FromDouble(p[i]);
        if (item == NULL) {
            Py_DECREF(lst);
            return NULL;
        }
        PyList_SET_ITEM(lst, (Py_ssize_t)i, item);
    }
    return lst;
}

static PyObject *c_rcopy_cplx_list(SEXP s) {
    R_xlen_t n = Rf_xlength(s);
    Rcomplex *p = COMPLEX(s);
    PyObject *lst = PyList_New((Py_ssize_t)n);
    if (lst == NULL) return NULL;
    for (R_xlen_t i = 0; i < n; i++) {
        PyObject *item = PyComplex_FromDoubles(p[i].r, p[i].i);
        if (item == NULL) {
            Py_DECREF(lst);
            return NULL;
        }
        PyList_SET_ITEM(lst, (Py_ssize_t)i, item);
    }
    return lst;
}

PyObject *c_rcopy_str_list(SEXP s) {
    R_xlen_t n = Rf_xlength(s);
    PyObject *lst = PyList_New((Py_ssize_t)n);
    if (lst == NULL) return NULL;
    const void *vmax = vmaxget();
    for (R_xlen_t i = 0; i < n; i++) {
        const char *utf8 = Rf_translateCharUTF8(STRING_ELT(s, i));
        PyObject *item = PyUnicode_FromString(utf8);
        vmaxset(vmax);
        if (item == NULL) {
            Py_DECREF(lst);
            return NULL;
        }
        PyList_SET_ITEM(lst, (Py_ssize_t)i, item);
    }
    return lst;
}

static PyObject *c_rcopy_vec_list(SEXP s, int asis, int convert) {
    R_xlen_t n = Rf_xlength(s);
    PyObject *lst = PyList_New((Py_ssize_t)n);
    if (lst == NULL) return NULL;
    for (R_xlen_t i = 0; i < n; i++) {
        PyObject *item = c_rcopy_impl(VECTOR_ELT(s, i), Py_None, asis, convert);
        if (item == NULL) {
            Py_DECREF(lst);
            return NULL;
        }
        PyList_SET_ITEM(lst, (Py_ssize_t)i, item);
    }
    return lst;
}

static PyObject *c_rcopy_vec_tuple(SEXP s, int asis, int convert) {
    R_xlen_t n = Rf_xlength(s);
    PyObject *tup = PyTuple_New((Py_ssize_t)n);
    if (tup == NULL) return NULL;
    for (R_xlen_t i = 0; i < n; i++) {
        PyObject *item = c_rcopy_impl(VECTOR_ELT(s, i), Py_None, asis, convert);
        if (item == NULL) {
            Py_DECREF(tup);
            return NULL;
        }
        PyTuple_SET_ITEM(tup, (Py_ssize_t)i, item);
    }
    return tup;
}

static PyObject *c_rcopy_vec_dict(SEXP s, SEXP names, int use_ordered_dict, int asis, int convert) {
    R_xlen_t n = Rf_xlength(s);
    PyObject *d;
    if (use_ordered_dict && g_OrderedDict_Type != NULL) {
        d = PyObject_CallNoArgs(g_OrderedDict_Type);
    } else {
        d = PyDict_New();
    }
    if (d == NULL) return NULL;
    if (Rf_isNull(names)) return d;

    const void *vmax = vmaxget();
    for (R_xlen_t i = 0; i < n; i++) {
        const char *k_str = Rf_translateCharUTF8(STRING_ELT(names, i));
        PyObject *k = PyUnicode_FromString(k_str);
        vmaxset(vmax);
        if (k == NULL) {
            Py_DECREF(d);
            return NULL;
        }
        PyObject *v = c_rcopy_impl(VECTOR_ELT(s, i), Py_None, asis, convert);
        if (v == NULL) {
            Py_DECREF(k);
            Py_DECREF(d);
            return NULL;
        }
        if (PyObject_SetItem(d, k, v) < 0) {
            Py_DECREF(k);
            Py_DECREF(v);
            Py_DECREF(d);
            return NULL;
        }
        Py_DECREF(k);
        Py_DECREF(v);
    }
    return d;
}

// =============================================================================
// 3. R -> Python Dispatch (c_rcopy_impl & py_c_rcopy)
// =============================================================================

static PyObject *c_rcopy_default_by_sexptype(SEXP s, int asis, int convert) {
    unsigned int t = TYPEOF(s);
    switch (t) {
        case NILSXP:
            Py_RETURN_NONE;
        case INTSXP:
            if (Rf_xlength(s) == 1) return PyLong_FromLong(INTEGER(s)[0]);
            return c_rcopy_int_list(s);
        case LGLSXP:
            if (Rf_xlength(s) == 1) return PyBool_FromLong(LOGICAL(s)[0]);
            return c_rcopy_lgl_list(s);
        case REALSXP:
            if (Rf_xlength(s) == 1) return PyFloat_FromDouble(REAL(s)[0]);
            return c_rcopy_real_list(s);
        case CPLXSXP:
            if (Rf_xlength(s) == 1) {
                Rcomplex z = COMPLEX(s)[0];
                return PyComplex_FromDoubles(z.r, z.i);
            }
            return c_rcopy_cplx_list(s);
        case RAWSXP:
            return PyBytes_FromStringAndSize((const char *)RAW(s), (Py_ssize_t)Rf_xlength(s));
        case STRSXP:
            if (Rf_xlength(s) == 1) {
                const void *vmax = vmaxget();
                PyObject *res = PyUnicode_FromString(Rf_translateCharUTF8(STRING_ELT(s, 0)));
                vmaxset(vmax);
                return res;
            }
            return c_rcopy_str_list(s);
        case VECSXP: {
            SEXP names = Rf_protect(Rf_getAttrib(s, R_NamesSymbol));
            PyObject *res;
            if (Rf_isNull(names)) {
                res = c_rcopy_vec_list(s, asis, convert);
            } else {
                res = c_rcopy_vec_dict(s, names, 1, asis, convert);
            }
            Rf_unprotect(1);
            return res;
        }
        case CLOSXP:
        case BUILTINSXP:
            return c_wrap_r_function(s, asis, convert);
        default:
            return c_box_sexp(s);
    }
}

PyObject *c_rcopy_impl(SEXP s, PyObject *target_type, int asis, int convert) {
    if (target_type == NULL || target_type == Py_None) {
        if (Rf_isObject(s)) {
            unsigned int st = TYPEOF(s);
            SEXP classes = Rf_protect(R_data_class(s, FALSE));
            R_xlen_t ncls = Rf_xlength(classes);
            const void *vmax = vmaxget();
            for (R_xlen_t i = 0; i < ncls; i++) {
                const char *cls = Rf_translateCharUTF8(STRING_ELT(classes, i));
                if (strcmp(cls, "PyObject") == 0 && st == EXTPTRSXP) {
                    vmaxset(vmax);
                    Rf_unprotect(1);
                    return c_from_xptr(s);
                }
                if ((strcmp(cls, "PyCallable") == 0 || strcmp(cls, "python.builtin.function") == 0) &&
                    st == CLOSXP) {
                    vmaxset(vmax);
                    Rf_unprotect(1);
                    return c_extract_pyobj_from_env_or_clos(s);
                }
                if (strcmp(cls, "python.builtin.object") == 0 && (st == ENVSXP || st == CLOSXP)) {
                    vmaxset(vmax);
                    Rf_unprotect(1);
                    return c_extract_pyobj_from_env_or_clos(s);
                }
            }
            vmaxset(vmax);
            Rf_unprotect(1);
        }
        return c_rcopy_default_by_sexptype(s, asis, convert);
    }

    unsigned int st = TYPEOF(s);
    if (target_type == g_RObject_Type) {
        return c_box_sexp(s);
    }
    if (target_type == (PyObject *)&PyBaseObject_Type) {
        if (st == EXTPTRSXP) return c_from_xptr(s);
        if (st == ENVSXP || st == CLOSXP) return c_extract_pyobj_from_env_or_clos(s);
    }
    if (target_type == (PyObject *)Py_TYPE(Py_None) && st == NILSXP) {
        Py_RETURN_NONE;
    }
    if (target_type == (PyObject *)&PyList_Type) {
        switch (st) {
            case NILSXP: return PyList_New(0);
            case INTSXP: return c_rcopy_int_list(s);
            case LGLSXP: return c_rcopy_lgl_list(s);
            case REALSXP: return c_rcopy_real_list(s);
            case CPLXSXP: return c_rcopy_cplx_list(s);
            case STRSXP: return c_rcopy_str_list(s);
            case VECSXP: return c_rcopy_vec_list(s, asis, convert);
            default: break;
        }
    }
    if (target_type == (PyObject *)&PyTuple_Type && st == VECSXP) {
        return c_rcopy_vec_tuple(s, asis, convert);
    }
    if (target_type == (PyObject *)&PyDict_Type && st == VECSXP) {
        SEXP names = Rf_protect(Rf_getAttrib(s, R_NamesSymbol));
        PyObject *res = c_rcopy_vec_dict(s, names, 0, asis, convert);
        Rf_unprotect(1);
        return res;
    }
    if (target_type == g_OrderedDict_Type && st == VECSXP) {
        SEXP names = Rf_protect(Rf_getAttrib(s, R_NamesSymbol));
        PyObject *res = c_rcopy_vec_dict(s, names, 1, asis, convert);
        Rf_unprotect(1);
        return res;
    }
    if (target_type == (PyObject *)&PyLong_Type && st == INTSXP) {
        return PyLong_FromLong(INTEGER(s)[0]);
    }
    if (target_type == (PyObject *)&PyBool_Type && st == LGLSXP) {
        return PyBool_FromLong(LOGICAL(s)[0]);
    }
    if (target_type == (PyObject *)&PyFloat_Type && st == REALSXP) {
        return PyFloat_FromDouble(REAL(s)[0]);
    }
    if (target_type == (PyObject *)&PyComplex_Type && st == CPLXSXP) {
        Rcomplex z = COMPLEX(s)[0];
        return PyComplex_FromDoubles(z.r, z.i);
    }
    if (target_type == (PyObject *)&PyBytes_Type && st == RAWSXP) {
        return PyBytes_FromStringAndSize((const char *)RAW(s), (Py_ssize_t)Rf_xlength(s));
    }
    if (target_type == (PyObject *)&PyUnicode_Type && st == STRSXP) {
        const void *vmax = vmaxget();
        PyObject *res = PyUnicode_FromString(Rf_translateCharUTF8(STRING_ELT(s, 0)));
        vmaxset(vmax);
        return res;
    }
    if (target_type == g_Function_Type && (st == CLOSXP || st == BUILTINSXP)) {
        return c_wrap_r_function(s, asis, convert);
    }
    if (PyType_Check(target_type) && PyType_IsSubtype((PyTypeObject *)target_type, &PyBaseObject_Type)) {
        if (target_type == (PyObject *)&PyBaseObject_Type) {
            return c_box_sexp(s);
        }
    }

    PyErr_SetString(PyExc_NotImplementedError, "Dispatch not found for rcopy signature");
    return NULL;
}

PyObject *py_c_rcopy(PyObject *self, PyObject *args) {
    PyObject *target_type;
    PyObject *obj;
    int asis = 0;
    int convert = 1;
    if (!PyArg_ParseTuple(args, "OO|pp", &target_type, &obj, &asis, &convert)) return NULL;
    SEXP s = extract_sexp(obj);
    if (s == NULL) return NULL;
    Rf_protect(s);
    PyObject *res = c_rcopy_impl(s, target_type, asis, convert);
    Rf_unprotect(1);
    return res;
}
