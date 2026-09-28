#include <Python.h>
#include <string.h>

#include "robject.h"
#include "interface.h"

static PyObject *g_RObject_Type = NULL;
static PyObject *g_OrderedDict_Type = NULL;
static PyObject *g_Function_Type = NULL;
static PyObject *g_WrapRFunction = NULL;

int is_robject(PyObject *obj) {
    if (g_RObject_Type == NULL || obj == NULL) return 0;
    return PyObject_TypeCheck(obj, (PyTypeObject *)g_RObject_Type);
}

SEXP extract_sexp(PyObject *obj) {
    if (obj == NULL) {
        PyErr_SetString(PyExc_TypeError, "expect SEXP or RObject");
        return NULL;
    }
    if (PyLong_CheckExact(obj)) {
        return (SEXP)PyLong_AsVoidPtr(obj);
    }
    if (is_robject(obj) || PyObject_HasAttrString(obj, "_ptr")) {
        PyObject *ptr_obj = PyObject_GetAttrString(obj, "_ptr");
        if (ptr_obj == NULL) return NULL;
        SEXP s = (SEXP)PyLong_AsVoidPtr(ptr_obj);
        Py_DECREF(ptr_obj);
        return s;
    }
    PyErr_SetString(PyExc_TypeError, "expect SEXP or RObject");
    return NULL;
}

PyObject *c_box_sexp(SEXP s) {
    if (g_RObject_Type == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "RObject type not initialized");
        return NULL;
    }
    Rf_protect(s);
    PyObject *ptr_int = PyLong_FromVoidPtr((void *)s);
    if (ptr_int == NULL) {
        Rf_unprotect(1);
        return NULL;
    }
    PyObject *robj = PyObject_CallFunctionObjArgs(g_RObject_Type, ptr_int, NULL);
    Py_DECREF(ptr_int);
    Rf_unprotect(1);
    return robj;
}

static void c_xptr_finalizer(SEXP s) {
    void *addr = R_ExternalPtrAddr(s);
    if (addr != NULL) {
        R_ClearExternalPtr(s);
        if (Py_IsInitialized()) {
            PyGILState_STATE gstate = PyGILState_Ensure();
            Py_DECREF((PyObject *)addr);
            PyGILState_Release(gstate);
        }
    }
}

static SEXP c_new_xptr(PyObject *obj) {
    Py_INCREF(obj);
    SEXP s = Rf_protect(R_MakeExternalPtr((void *)obj, R_NilValue, R_NilValue));
    R_RegisterCFinalizerEx(s, c_xptr_finalizer, TRUE);
    Rf_unprotect(1);
    return s;
}

static PyObject *c_from_xptr(SEXP s) {
    void *addr = R_ExternalPtrAddr(s);
    if (addr == NULL) {
        Py_RETURN_NONE;
    }
    PyObject *obj = (PyObject *)addr;
    Py_INCREF(obj);
    return obj;
}

static SEXP c_mk_rchar_utf8(const char *buf, Py_ssize_t len) {
    int is_ascii = 1;
    for (Py_ssize_t i = 0; i < len; i++) {
        if ((unsigned char)buf[i] >= 128) {
            is_ascii = 0;
            break;
        }
    }
    return Rf_mkCharLenCE(buf, (int)len, is_ascii ? CE_NATIVE : CE_UTF8);
}

SEXP c_mk_rchar_from_py(PyObject *str_obj) {
    Py_ssize_t len = 0;
    const char *buf = PyUnicode_AsUTF8AndSize(str_obj, &len);
    if (buf == NULL) return NULL;
    return c_mk_rchar_utf8(buf, len);
}

SEXP c_install_py_str(PyObject *str_obj) {
    SEXP ch = Rf_protect(c_mk_rchar_from_py(str_obj));
    if (ch == NULL) {
        Rf_unprotect(1);
        return NULL;
    }
    SEXP sym = Rf_install(Rf_translateChar(ch));
    Rf_unprotect(1);
    return sym;
}

static int c_sexp_has_class(SEXP s, const char *target_cls) {
    if (!Rf_isObject(s)) return 0;
    SEXP classes = Rf_protect(R_data_class(s, FALSE));
    R_xlen_t n = Rf_xlength(classes);
    int found = 0;
    for (R_xlen_t i = 0; i < n; i++) {
        const char *c = Rf_translateCharUTF8(STRING_ELT(classes, i));
        if (strcmp(c, target_cls) == 0) {
            found = 1;
            break;
        }
    }
    Rf_unprotect(1);
    return found;
}

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
            SEXP names = Rf_getAttrib(s, R_NamesSymbol);
            if (Rf_isNull(names)) {
                return c_rcopy_vec_list(s, asis, convert);
            } else {
                return c_rcopy_vec_dict(s, names, 1, asis, convert);
            }
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
        SEXP names = Rf_getAttrib(s, R_NamesSymbol);
        return c_rcopy_vec_dict(s, names, 0, asis, convert);
    }
    if (target_type == g_OrderedDict_Type && st == VECSXP) {
        SEXP names = Rf_getAttrib(s, R_NamesSymbol);
        return c_rcopy_vec_dict(s, names, 1, asis, convert);
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

static SEXP c_sexp_function(PyObject *f, int asis, int convert, int invisible, int is_pycallable) {
    if (PyObject_HasAttrString(f, "__robject__")) {
        PyObject *robj = PyObject_GetAttrString(f, "__robject__");
        if (robj == NULL) return NULL;
        SEXP s = extract_sexp(robj);
        Py_DECREF(robj);
        return s;
    }

    SEXP env = Rf_protect(Rf_NewEnvironment(R_NilValue, R_NilValue, R_GlobalEnv));
    SEXP fp = Rf_protect(c_new_xptr(f));
    SEXP pyobj_cls = Rf_protect(Rf_mkString("PyObject"));
    Rf_setAttrib(fp, R_ClassSymbol, pyobj_cls);
    Rf_defineVar(Rf_install("pointer"), fp, env);

    SEXP dotlist = Rf_protect(Rf_lang2(Rf_install("list"), R_DotsSymbol));
    SEXP cb_name = Rf_protect(Rf_mkString("_libR_xptr_callback"));
    SEXP asis_s = Rf_protect(Rf_ScalarLogical(asis));
    SEXP conv_s = Rf_protect(Rf_ScalarLogical(convert));
    SEXP body = Rf_protect(
        Rf_lang6(Rf_install(".Call"), cb_name, Rf_install("pointer"), dotlist, asis_s, conv_s)
    );
    int nprot = 8;
    if (invisible) {
        body = Rf_protect(Rf_lang2(Rf_install("invisible"), body));
        nprot++;
    }

    SEXP dots_formals = Rf_protect(Rf_list1(R_MissingArg));
    SET_TAG(dots_formals, R_DotsSymbol);
    SEXP lang = Rf_protect(Rf_lang3(Rf_install("function"), dots_formals, body));
    nprot += 2;

    int status = 0;
    SEXP val = Rf_protect(R_tryEval(lang, env, &status));
    nprot++;
    Rf_setAttrib(val, Rf_install("py_object"), fp);

    if (is_pycallable) {
        SEXP cls = Rf_protect(Rf_allocVector(STRSXP, 2));
        SET_STRING_ELT(cls, 0, Rf_mkChar("PyCallable"));
        SET_STRING_ELT(cls, 1, Rf_mkChar("PyObject"));
        Rf_setAttrib(val, R_ClassSymbol, cls);
        Rf_unprotect(1);
    }

    Rf_unprotect(nprot);
    return val;
}

static SEXP c_sexp_pyobject(PyObject *obj, int convert) {
    if (is_robject(obj)) {
        SEXP existing = extract_sexp(obj);
        if (existing != NULL && c_sexp_has_class(existing, "PyObject")) {
            return existing;
        }
    }
    SEXP p = Rf_protect(c_new_xptr(obj));
    SEXP cls = Rf_protect(Rf_mkString("PyObject"));
    Rf_setAttrib(p, R_ClassSymbol, cls);
    SEXP conv_val = Rf_protect(Rf_ScalarLogical(convert));
    Rf_setAttrib(p, Rf_install("convert"), conv_val);
    Rf_unprotect(3);
    return p;
}

SEXP c_sexp_as_py_object_impl(PyObject *obj, int asis, int has_convert, int convert, int invisible) {
    if (is_robject(obj)) {
        return extract_sexp(obj);
    }
    if (PyCallable_Check(obj)) {
        return c_sexp_function(obj, asis, has_convert ? convert : 0, invisible, 1);
    }
    return c_sexp_pyobject(obj, has_convert ? convert : 1);
}

static SEXP c_sexp_list_with_rclass(
    const char *rclass,
    PyObject *seq,
    int asis,
    int has_convert,
    int convert,
    int invisible
) {
    if (strcmp(rclass, "logical") == 0) {
        Py_ssize_t n = PyList_Size(seq);
        SEXP x = Rf_protect(Rf_allocVector(LGLSXP, n));
        int *p = LOGICAL(x);
        for (Py_ssize_t i = 0; i < n; i++) {
            p[i] = PyObject_IsTrue(PyList_GetItem(seq, i));
        }
        Rf_unprotect(1);
        return x;
    }
    if (strcmp(rclass, "integer") == 0) {
        Py_ssize_t n = PyList_Size(seq);
        SEXP x = Rf_protect(Rf_allocVector(INTSXP, n));
        int *p = INTEGER(x);
        for (Py_ssize_t i = 0; i < n; i++) {
            long v = PyLong_AsLong(PyList_GetItem(seq, i));
            if (v == -1 && PyErr_Occurred()) {
                Rf_unprotect(1);
                return NULL;
            }
            p[i] = (int)v;
        }
        Rf_unprotect(1);
        return x;
    }
    if (strcmp(rclass, "numeric") == 0) {
        Py_ssize_t n = PyList_Size(seq);
        SEXP x = Rf_protect(Rf_allocVector(REALSXP, n));
        double *p = REAL(x);
        for (Py_ssize_t i = 0; i < n; i++) {
            double v = PyFloat_AsDouble(PyList_GetItem(seq, i));
            if (v == -1.0 && PyErr_Occurred()) {
                Rf_unprotect(1);
                return NULL;
            }
            p[i] = v;
        }
        Rf_unprotect(1);
        return x;
    }
    if (strcmp(rclass, "complex") == 0) {
        Py_ssize_t n = PyList_Size(seq);
        SEXP x = Rf_protect(Rf_allocVector(CPLXSXP, n));
        Rcomplex *p = COMPLEX(x);
        for (Py_ssize_t i = 0; i < n; i++) {
            PyObject *item = PyList_GetItem(seq, i);
            p[i].r = PyComplex_RealAsDouble(item);
            p[i].i = PyComplex_ImagAsDouble(item);
        }
        Rf_unprotect(1);
        return x;
    }
    if (strcmp(rclass, "character") == 0) {
        Py_ssize_t n = PyList_Size(seq);
        SEXP x = Rf_protect(Rf_allocVector(STRSXP, n));
        for (Py_ssize_t i = 0; i < n; i++) {
            SEXP ch = c_mk_rchar_from_py(PyList_GetItem(seq, i));
            if (ch == NULL) {
                Rf_unprotect(1);
                return NULL;
            }
            SET_STRING_ELT(x, i, ch);
        }
        Rf_unprotect(1);
        return x;
    }
    if (strcmp(rclass, "list") == 0) {
        if (PyList_Check(seq)) {
            Py_ssize_t n = PyList_Size(seq);
            SEXP x = Rf_protect(Rf_allocVector(VECSXP, n));
            for (Py_ssize_t i = 0; i < n; i++) {
                SEXP elt = c_sexp_impl(NULL, PyList_GetItem(seq, i), asis, has_convert, convert, invisible);
                if (elt == NULL) {
                    Rf_unprotect(1);
                    return NULL;
                }
                SET_VECTOR_ELT(x, i, elt);
            }
            Rf_unprotect(1);
            return x;
        }
        if (PyTuple_Check(seq)) {
            Py_ssize_t n = PyTuple_Size(seq);
            SEXP x = Rf_protect(Rf_allocVector(VECSXP, n));
            for (Py_ssize_t i = 0; i < n; i++) {
                SEXP elt = c_sexp_impl(NULL, PyTuple_GetItem(seq, i), asis, has_convert, convert, invisible);
                if (elt == NULL) {
                    Rf_unprotect(1);
                    return NULL;
                }
                SET_VECTOR_ELT(x, i, elt);
            }
            Rf_unprotect(1);
            return x;
        }
        if (PyDict_Check(seq)) {
            PyObject *items = PyMapping_Items(seq);
            if (items == NULL) return NULL;
            Py_ssize_t n = PyList_Size(items);
            SEXP v = Rf_protect(Rf_allocVector(VECSXP, n));
            SEXP k = Rf_protect(Rf_allocVector(STRSXP, n));
            for (Py_ssize_t i = 0; i < n; i++) {
                PyObject *pair = PyList_GetItem(items, i);
                PyObject *key_obj = PyTuple_GetItem(pair, 0);
                PyObject *val_obj = PyTuple_GetItem(pair, 1);
                SEXP ch = c_mk_rchar_from_py(key_obj);
                if (ch == NULL) {
                    Py_DECREF(items);
                    Rf_unprotect(2);
                    return NULL;
                }
                SET_STRING_ELT(k, i, ch);
                SEXP elt = c_sexp_impl(NULL, val_obj, asis, has_convert, convert, invisible);
                if (elt == NULL) {
                    Py_DECREF(items);
                    Rf_unprotect(2);
                    return NULL;
                }
                SET_VECTOR_ELT(v, i, elt);
            }
            Py_DECREF(items);
            Rf_setAttrib(v, R_NamesSymbol, k);
            Rf_unprotect(2);
            return v;
        }
    }
    PyErr_SetString(PyExc_NotImplementedError, "Unsupported list/dict conversion for RClass");
    return NULL;
}

static const char *infer_sexpclass(PyObject *obj) {
    if (PyBool_Check(obj)) return "logical";
    if (PyLong_CheckExact(obj)) return "integer";
    if (PyFloat_CheckExact(obj)) return "numeric";
    if (PyComplex_Check(obj)) return "complex";
    if (PyUnicode_CheckExact(obj)) return "character";
    if (PyBytes_CheckExact(obj)) return "raw";
    if (PyList_Check(obj)) {
        Py_ssize_t n = PyList_Size(obj);
        int all_bool = 1, all_int = 1, all_float = 1, all_complex = 1, all_str = 1;
        for (Py_ssize_t i = 0; i < n; i++) {
            PyObject *item = PyList_GetItem(obj, i);
            if (!PyBool_Check(item)) all_bool = 0;
            if (!PyLong_CheckExact(item)) all_int = 0;
            if (!PyFloat_CheckExact(item)) all_float = 0;
            if (!PyComplex_Check(item)) all_complex = 0;
            if (!PyUnicode_CheckExact(item)) all_str = 0;
            if (!all_bool && !all_int && !all_float && !all_complex && !all_str) {
                return "list";
            }
        }
        if (all_bool) return "logical";
        if (all_int) return "integer";
        if (all_float) return "numeric";
        if (all_complex) return "complex";
        if (all_str) return "character";
        return "list";
    }
    if (PyTuple_Check(obj) || PyDict_Check(obj)) {
        return "list";
    }
    if (PyCallable_Check(obj)) {
        if (PyObject_HasAttrString(obj, "__robject__")) {
            return "function";
        }
        return "PyCallable";
    }
    return "PyObject";
}

SEXP c_sexp_impl(
    const char *rclass,
    PyObject *obj,
    int asis,
    int has_convert,
    int convert,
    int invisible
) {
    if (rclass == NULL) {
        if (obj == Py_None) return R_NilValue;
        if (is_robject(obj)) return extract_sexp(obj);
        rclass = infer_sexpclass(obj);
    }

    if (strcmp(rclass, "NULL") == 0 && obj == Py_None) {
        return R_NilValue;
    }
    if (strcmp(rclass, "logical") == 0) {
        if (PyBool_Check(obj)) return Rf_ScalarLogical(obj == Py_True);
        if (PyList_Check(obj)) return c_sexp_list_with_rclass("logical", obj, asis, has_convert, convert, invisible);
    }
    if (strcmp(rclass, "integer") == 0) {
        if (PyLong_Check(obj)) {
            long v = PyLong_AsLong(obj);
            if (v == -1 && PyErr_Occurred()) return NULL;
            return Rf_ScalarInteger((int)v);
        }
        if (PyList_Check(obj)) return c_sexp_list_with_rclass("integer", obj, asis, has_convert, convert, invisible);
    }
    if (strcmp(rclass, "numeric") == 0) {
        if (PyFloat_Check(obj) || PyLong_Check(obj)) {
            double v = PyFloat_AsDouble(obj);
            if (v == -1.0 && PyErr_Occurred()) return NULL;
            return Rf_ScalarReal(v);
        }
        if (PyList_Check(obj)) return c_sexp_list_with_rclass("numeric", obj, asis, has_convert, convert, invisible);
    }
    if (strcmp(rclass, "complex") == 0) {
        if (PyComplex_Check(obj)) {
            Rcomplex c;
            c.r = PyComplex_RealAsDouble(obj);
            c.i = PyComplex_ImagAsDouble(obj);
            return Rf_ScalarComplex(c);
        }
        if (PyList_Check(obj)) return c_sexp_list_with_rclass("complex", obj, asis, has_convert, convert, invisible);
    }
    if (strcmp(rclass, "character") == 0) {
        if (PyUnicode_Check(obj)) {
            SEXP ch = Rf_protect(c_mk_rchar_from_py(obj));
            if (ch == NULL) {
                Rf_unprotect(1);
                return NULL;
            }
            SEXP res = Rf_ScalarString(ch);
            Rf_unprotect(1);
            return res;
        }
        if (PyList_Check(obj)) return c_sexp_list_with_rclass("character", obj, asis, has_convert, convert, invisible);
    }
    if (strcmp(rclass, "raw") == 0 && PyBytes_Check(obj)) {
        char *buf = NULL;
        Py_ssize_t n = 0;
        if (PyBytes_AsStringAndSize(obj, &buf, &n) < 0) return NULL;
        SEXP x = Rf_protect(Rf_allocVector(RAWSXP, n));
        if (n > 0) {
            memcpy(RAW(x), buf, (size_t)n);
        }
        Rf_unprotect(1);
        return x;
    }
    if (strcmp(rclass, "list") == 0) {
        return c_sexp_list_with_rclass("list", obj, asis, has_convert, convert, invisible);
    }
    if (strcmp(rclass, "function") == 0 && PyCallable_Check(obj)) {
        return c_sexp_function(obj, asis, has_convert ? convert : 1, invisible, 0);
    }
    if (strcmp(rclass, "PyCallable") == 0 && PyCallable_Check(obj)) {
        return c_sexp_function(obj, asis, has_convert ? convert : 0, invisible, 1);
    }
    if (strcmp(rclass, "PyObject") == 0) {
        return c_sexp_pyobject(obj, has_convert ? convert : 1);
    }

    PyErr_SetString(PyExc_TypeError, "Cannot convert Python object to requested R class");
    return NULL;
}

static SEXP _rchitect_xptr_callback(SEXP exptr, SEXP arglist, SEXP asis_s, SEXP convert_s) {
    PyGILState_STATE gstate = PyGILState_Ensure();
    int asis = Rf_asLogical(asis_s);
    int convert = Rf_asLogical(convert_s);
    PyObject *f = (PyObject *)R_ExternalPtrAddr(exptr);
    if (f == NULL) {
        PyGILState_Release(gstate);
        Rf_error("NULL Python callable in _libR_xptr_callback");
        return R_NilValue;
    }

    R_xlen_t n = Rf_xlength(arglist);
    SEXP names = Rf_getAttrib(arglist, R_NamesSymbol);
    int has_names = !Rf_isNull(names);

    PyObject *pos_list = PyList_New(0);
    PyObject *kwargs = PyDict_New();
    const void *vmax = vmaxget();
    for (R_xlen_t i = 0; i < n; i++) {
        SEXP elt = VECTOR_ELT(arglist, i);
        const char *k = has_names ? Rf_translateCharUTF8(STRING_ELT(names, i)) : "";
        vmaxset(vmax);
        PyObject *py_val;
        if (asis) {
            py_val = c_box_sexp(elt);
        } else {
            py_val = c_rcopy_impl(elt, Py_None, 0, 1);
        }
        if (py_val == NULL) {
            Py_DECREF(pos_list);
            Py_DECREF(kwargs);
            goto handle_error;
        }
        if (k != NULL && k[0] != '\0') {
            PyDict_SetItemString(kwargs, k, py_val);
            Py_DECREF(py_val);
        } else {
            PyList_Append(pos_list, py_val);
            Py_DECREF(py_val);
        }
    }

    PyObject *args = PyList_AsTuple(pos_list);
    Py_DECREF(pos_list);
    PyObject *ret = PyObject_Call(f, args, kwargs);
    Py_DECREF(args);
    Py_DECREF(kwargs);

    if (ret == NULL) {
        goto handle_error;
    }

    SEXP res_sexp;
    if (convert) {
        res_sexp = c_sexp_impl(NULL, ret, asis, 1, 1, 0);
    } else {
        res_sexp = c_sexp_as_py_object_impl(ret, asis, 1, 0, 0);
    }
    if (res_sexp != NULL) {
        Rf_protect(res_sexp);
    }
    Py_DECREF(ret);
    if (res_sexp != NULL) {
        Rf_unprotect(1);
    }
    if (res_sexp == NULL && PyErr_Occurred()) {
        goto handle_error;
    }
    PyGILState_Release(gstate);
    return res_sexp;

handle_error:
    {
        PyObject *ptype = NULL, *pvalue = NULL, *ptraceback = NULL;
        PyErr_Fetch(&ptype, &pvalue, &ptraceback);
        char err_buf[4096];
        err_buf[0] = '\0';
        if (pvalue != NULL) {
            PyObject *pstr = PyObject_Str(pvalue);
            if (pstr != NULL) {
                Py_ssize_t len = 0;
                const char *utf8 = PyUnicode_AsUTF8AndSize(pstr, &len);
                if (utf8 != NULL) {
                    size_t copy_len = (size_t)len < sizeof(err_buf) - 1 ? (size_t)len : sizeof(err_buf) - 1;
                    memcpy(err_buf, utf8, copy_len);
                    err_buf[copy_len] = '\0';
                }
                Py_DECREF(pstr);
            }
        }
        Py_XDECREF(ptype);
        Py_XDECREF(pvalue);
        Py_XDECREF(ptraceback);
        PyGILState_Release(gstate);

        SEXP err_ch = Rf_protect(Rf_mkCharCE(err_buf, CE_UTF8));
        SEXP err_msg = Rf_protect(Rf_ScalarString(err_ch));
        SEXP stop_call = Rf_protect(Rf_lang2(Rf_install("stop"), err_msg));
        Rf_eval(stop_call, R_BaseEnv);
        Rf_unprotect(3);
        return R_NilValue;
    }
}

static const R_CallMethodDef CallEntries[] = {
    {"_libR_xptr_callback", (DL_FUNC)&_rchitect_xptr_callback, 4},
    {NULL, NULL, 0}
};

void _libR_setup_xptr_callback(void) {
    DllInfo *dll = R_getEmbeddingDllInfo();
    R_registerRoutines(dll, NULL, (void *)CallEntries, NULL, NULL);
}

static PyObject *py_c_rcopy(PyObject *self, PyObject *args) {
    PyObject *target_type;
    PyObject *obj;
    int asis = 0;
    int convert = 1;
    if (!PyArg_ParseTuple(args, "OO|pp", &target_type, &obj, &asis, &convert)) return NULL;
    SEXP s = extract_sexp(obj);
    if (s == NULL) return NULL;
    return c_rcopy_impl(s, target_type, asis, convert);
}

static PyObject *py_c_sexp(PyObject *self, PyObject *args) {
    PyObject *rclass_obj;
    PyObject *obj;
    int asis = 0;
    int has_convert = 0;
    int convert = 1;
    int invisible = 0;
    if (!PyArg_ParseTuple(args, "OO|pppi", &rclass_obj, &obj, &asis, &has_convert, &convert, &invisible)) {
        return NULL;
    }
    const char *rclass = NULL;
    if (rclass_obj != Py_None) {
        rclass = PyUnicode_AsUTF8AndSize(rclass_obj, NULL);
        if (rclass == NULL) return NULL;
    }
    SEXP s = c_sexp_impl(rclass, obj, asis, has_convert, convert, invisible);
    if (s == NULL) return NULL;
    return c_box_sexp(s);
}

static PyObject *py_c_sexp_as_py_object(PyObject *self, PyObject *args) {
    PyObject *obj;
    int asis = 0;
    int has_convert = 0;
    int convert = 1;
    int invisible = 0;
    if (!PyArg_ParseTuple(args, "O|pppi", &obj, &asis, &has_convert, &convert, &invisible)) {
        return NULL;
    }
    SEXP s = c_sexp_as_py_object_impl(obj, asis, has_convert, convert, invisible);
    if (s == NULL) return NULL;
    return c_box_sexp(s);
}

static PyMethodDef rchitect_conv_methods[] = {
    {"_c_rcopy", py_c_rcopy, METH_VARARGS, NULL},
    {"_c_sexp", py_c_sexp, METH_VARARGS, NULL},
    {"_c_sexp_as_py_object", py_c_sexp_as_py_object, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}
};

int _rchitect_init_conv(
    void *mod_ptr,
    void *robject_type_ptr,
    void *ordered_dict_type_ptr,
    void *function_type_ptr,
    void *wrap_r_func_ptr
) {
    PyGILState_STATE gstate = PyGILState_Ensure();
    PyObject *mod = (PyObject *)mod_ptr;

    Py_XDECREF(g_RObject_Type);
    g_RObject_Type = (PyObject *)robject_type_ptr;
    Py_XINCREF(g_RObject_Type);

    Py_XDECREF(g_OrderedDict_Type);
    g_OrderedDict_Type = (PyObject *)ordered_dict_type_ptr;
    Py_XINCREF(g_OrderedDict_Type);

    Py_XDECREF(g_Function_Type);
    g_Function_Type = (PyObject *)function_type_ptr;
    Py_XINCREF(g_Function_Type);

    Py_XDECREF(g_WrapRFunction);
    g_WrapRFunction = (PyObject *)wrap_r_func_ptr;
    Py_XINCREF(g_WrapRFunction);

    int rc1 = PyModule_AddFunctions(mod, rchitect_conv_methods);
    int rc2 = _rchitect_register_interface_methods(mod_ptr);
    PyGILState_Release(gstate);
    return (rc1 == 0 && rc2 == 0) ? 1 : 0;
}
