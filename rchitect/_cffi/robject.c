#include <Python.h>
#include <string.h>

#include "robject.h"
#include "interface.h"
#include "callbacks.h"

// =============================================================================
// 1. Type Cache, Boxing & External Pointer Helpers
// =============================================================================

PyObject *g_RObject_Type = NULL;
PyObject *g_OrderedDict_Type = NULL;
PyObject *g_Function_Type = NULL;
PyObject *g_WrapRFunction = NULL;
static PyObject *g_str_ptr = NULL;
static PyObject *g_str_s = NULL;

SEXP r_sym_py_object = NULL;
SEXP r_sym_get = NULL;
static SEXP r_sym_convert = NULL;
static SEXP r_sym_pointer = NULL;
static SEXP r_sym_list = NULL;
static SEXP r_sym_dot_call = NULL;
static SEXP r_sym_invisible = NULL;
static SEXP r_sym_function = NULL;
static SEXP r_sym_stop = NULL;

static void ensure_cached_symbols(void) {
    if (r_sym_py_object == NULL) {
        r_sym_py_object = Rf_install("py_object");
        r_sym_get = Rf_install("get");
        r_sym_convert = Rf_install("convert");
        r_sym_pointer = Rf_install("pointer");
        r_sym_list = Rf_install("list");
        r_sym_dot_call = Rf_install(".Call");
        r_sym_invisible = Rf_install("invisible");
        r_sym_function = Rf_install("function");
        r_sym_stop = Rf_install("stop");
    }
}

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
    PyObject *ptr_obj = g_str_ptr != NULL
        ? PyObject_GetAttr(obj, g_str_ptr)
        : PyObject_GetAttrString(obj, "_ptr");
    if (ptr_obj != NULL) {
        SEXP s = (SEXP)PyLong_AsVoidPtr(ptr_obj);
        Py_DECREF(ptr_obj);
        return s;
    }
    if (PyErr_ExceptionMatches(PyExc_AttributeError)) {
        PyErr_SetString(PyExc_TypeError, "expect SEXP or RObject");
    }
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
    PyObject *robj = PyType_GenericAlloc((PyTypeObject *)g_RObject_Type, 0);
    if (robj == NULL) {
        Py_DECREF(ptr_int);
        Rf_unprotect(1);
        return NULL;
    }
    if (PyObject_SetAttr(robj, g_str_ptr, ptr_int) < 0 ||
            PyObject_SetAttr(robj, g_str_s, Py_None) < 0) {
        Py_DECREF(ptr_int);
        Py_DECREF(robj);
        Rf_unprotect(1);
        return NULL;
    }
    Py_DECREF(ptr_int);
    c_preserve_sexp(s);
    Rf_unprotect(1);
    return robj;
}

static void c_xptr_finalizer(SEXP s) {
    void *addr = R_ExternalPtrAddr(s);
    if (addr != NULL) {
        R_ClearExternalPtr(s);
        if (Py_IsInitialized() && rchitect_is_main_thread()) {
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

PyObject *c_from_xptr(SEXP s) {
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
    if (PyUnicode_Check(str_obj) && PyUnicode_IS_ASCII(str_obj)) {
        return Rf_mkCharLenCE(buf, (int)len, CE_NATIVE);
    }
    return c_mk_rchar_utf8(buf, len);
}

SEXP c_install_py_str(PyObject *str_obj) {
    if (PyUnicode_Check(str_obj) && PyUnicode_IS_ASCII(str_obj)) {
        const char *buf = PyUnicode_AsUTF8(str_obj);
        if (buf == NULL) return NULL;
        return Rf_install(buf);
    }
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

// =============================================================================
// 2. Python -> R Conversion (robject / sexp)
// =============================================================================

static SEXP c_sexp_function(PyObject *f, int asis, int convert, int invisible, int is_pycallable) {
    if (PyObject_HasAttrString(f, "__robject__")) {
        PyObject *robj = PyObject_GetAttrString(f, "__robject__");
        if (robj == NULL) return NULL;
        SEXP s = extract_sexp(robj);
        Py_DECREF(robj);
        return s;
    }

    ensure_cached_symbols();
    SEXP env = Rf_protect(Rf_NewEnvironment(R_NilValue, R_NilValue, R_GlobalEnv));
    SEXP fp = Rf_protect(c_new_xptr(f));
    SEXP pyobj_cls = Rf_protect(Rf_mkString("PyObject"));
    Rf_setAttrib(fp, R_ClassSymbol, pyobj_cls);
    Rf_defineVar(r_sym_pointer, fp, env);

    SEXP dotlist = Rf_protect(Rf_lang2(r_sym_list, R_DotsSymbol));
    SEXP cb_name = Rf_protect(Rf_mkString("_libR_xptr_callback"));
    SEXP asis_s = Rf_protect(Rf_ScalarLogical(asis));
    SEXP conv_s = Rf_protect(Rf_ScalarLogical(convert));
    SEXP body = Rf_protect(
        Rf_lang6(r_sym_dot_call, cb_name, r_sym_pointer, dotlist, asis_s, conv_s)
    );
    int nprot = 8;
    if (invisible) {
        body = Rf_protect(Rf_lang2(r_sym_invisible, body));
        nprot++;
    }

    SEXP dots_formals = Rf_protect(Rf_list1(R_MissingArg));
    SET_TAG(dots_formals, R_DotsSymbol);
    SEXP lang = Rf_protect(Rf_lang3(r_sym_function, dots_formals, body));
    nprot += 2;

    int status = 0;
    SEXP val = Rf_protect(R_tryEval(lang, env, &status));
    nprot++;
    if (status != 0 || val == R_NilValue) {
        Rf_unprotect(nprot);
        PyErr_SetString(PyExc_RuntimeError, "Failed to create R function wrapper");
        return NULL;
    }
    Rf_setAttrib(val, r_sym_py_object, fp);

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
    ensure_cached_symbols();
    SEXP p = Rf_protect(c_new_xptr(obj));
    SEXP cls = Rf_protect(Rf_mkString("PyObject"));
    Rf_setAttrib(p, R_ClassSymbol, cls);
    SEXP conv_val = Rf_protect(Rf_ScalarLogical(convert));
    Rf_setAttrib(p, r_sym_convert, conv_val);
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
            double r = PyComplex_RealAsDouble(item);
            if (r == -1.0 && PyErr_Occurred()) {
                Rf_unprotect(1);
                return NULL;
            }
            double im = PyComplex_ImagAsDouble(item);
            if (im == -1.0 && PyErr_Occurred()) {
                Rf_unprotect(1);
                return NULL;
            }
            p[i].r = r;
            p[i].i = im;
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
        if (PyDict_CheckExact(seq)) {
            Py_ssize_t n = PyDict_Size(seq);
            SEXP v = Rf_protect(Rf_allocVector(VECSXP, n));
            SEXP k = Rf_protect(Rf_allocVector(STRSXP, n));
            Py_ssize_t pos = 0, i = 0;
            PyObject *key_obj, *val_obj;
            while (PyDict_Next(seq, &pos, &key_obj, &val_obj)) {
                SEXP ch = c_mk_rchar_from_py(key_obj);
                if (ch == NULL) {
                    Rf_unprotect(2);
                    return NULL;
                }
                SET_STRING_ELT(k, i, ch);
                SEXP elt = c_sexp_impl(NULL, val_obj, asis, has_convert, convert, invisible);
                if (elt == NULL) {
                    Rf_unprotect(2);
                    return NULL;
                }
                SET_VECTOR_ELT(v, i, elt);
                i++;
            }
            Rf_setAttrib(v, R_NamesSymbol, k);
            Rf_unprotect(2);
            return v;
        } else if (PyDict_Check(seq)) {
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
            if (c.r == -1.0 && PyErr_Occurred()) return NULL;
            c.i = PyComplex_ImagAsDouble(obj);
            if (c.i == -1.0 && PyErr_Occurred()) return NULL;
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

// =============================================================================
// 3. R Callable Trampoline (_libR_xptr_callback)
// =============================================================================

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
    SEXP names = Rf_protect(Rf_getAttrib(arglist, R_NamesSymbol));
    int has_names = !Rf_isNull(names);

    PyObject *pos_list = PyList_New(0);
    PyObject *kwargs = PyDict_New();
    const void *vmax = vmaxget();
    for (R_xlen_t i = 0; i < n; i++) {
        SEXP elt = VECTOR_ELT(arglist, i);
        const char *k = has_names ? Rf_translateCharUTF8(STRING_ELT(names, i)) : "";
        PyObject *py_val;
        if (asis) {
            py_val = c_box_sexp(elt);
        } else {
            py_val = c_rcopy_impl(elt, Py_None, 0, 1);
        }
        if (py_val == NULL) {
            vmaxset(vmax);
            Rf_unprotect(1);
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
        vmaxset(vmax);
    }
    Rf_unprotect(1);

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

        ensure_cached_symbols();
        SEXP err_ch = Rf_protect(Rf_mkCharCE(err_buf, CE_UTF8));
        SEXP err_msg = Rf_protect(Rf_ScalarString(err_ch));
        SEXP stop_call = Rf_protect(Rf_lang2(r_sym_stop, err_msg));
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
    ensure_cached_symbols();
    DllInfo *dll = R_getEmbeddingDllInfo();
    R_registerRoutines(dll, NULL, (void *)CallEntries, NULL, NULL);
}

// =============================================================================
// 4. CPython Method Table & Module Initialization
// =============================================================================

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

    if (g_str_ptr == NULL) {
        g_str_ptr = PyUnicode_InternFromString("_ptr");
    }
    if (g_str_s == NULL) {
        g_str_s = PyUnicode_InternFromString("_s");
    }

    int rc1 = PyModule_AddFunctions(mod, rchitect_conv_methods);
    int rc2 = _rchitect_register_interface_methods(mod_ptr);
    PyGILState_Release(gstate);
    return (rc1 == 0 && rc2 == 0 && g_str_ptr != NULL && g_str_s != NULL) ? 1 : 0;
}
