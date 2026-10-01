#include <Python.h>
#include <string.h>

#include "robject.h"
#include "interface.h"
#include "callbacks.h"

// =============================================================================
// 1. Deferred SEXP Release & R Parse/Eval Helpers
// =============================================================================

static SEXP *deferred_release = NULL;
static size_t deferred_release_len = 0;
static size_t deferred_release_cap = 0;

static void flush_deferred_release(void) {
    if (deferred_release_len == 0 || R_GlobalEnv == NULL || !rchitect_is_main_thread()) {
        return;
    }
    for (size_t i = 0; i < deferred_release_len; i++) {
        R_ReleaseObject(deferred_release[i]);
    }
    deferred_release_len = 0;
}

int _libR_is_initialized(void) {
    return R_GlobalEnv != NULL;
}

typedef struct {
    SEXP text;
    int num;
    ParseStatus *status;
    SEXP source;
    SEXP val;
} ProtectedParseData;

static void protectedParse(void *d) {
    ProtectedParseData *data = (ProtectedParseData *)d;
    data->val = R_ParseVector(data->text, data->num, data->status, data->source);
}

static SEXP rchitect_ParseVector(SEXP text, int num, ParseStatus *status, SEXP source) {
    Rboolean ok;
    ProtectedParseData d;
    d.text = Rf_protect(text);
    d.num = num;
    d.status = status;
    d.source = Rf_protect(source);
    d.val = R_NilValue;
    ok = R_ToplevelExec(protectedParse, &d);
    if (ok == FALSE) {
        *status = PARSE_ERROR;
        d.val = R_NilValue;
    }
    Rf_unprotect(2);
    return d.val;
}

// =============================================================================
// 2. SEXP Preservation & Inspection
// =============================================================================

static const char *sexptype_to_str(unsigned int t) {
    switch (t) {
        case NILSXP: return "NILSXP";
        case SYMSXP: return "SYMSXP";
        case LISTSXP: return "LISTSXP";
        case CLOSXP: return "CLOSXP";
        case ENVSXP: return "ENVSXP";
        case PROMSXP: return "PROMSXP";
        case LANGSXP: return "LANGSXP";
        case SPECIALSXP: return "SPECIALSXP";
        case BUILTINSXP: return "BUILTINSXP";
        case CHARSXP: return "CHARSXP";
        case LGLSXP: return "LGLSXP";
        case INTSXP: return "INTSXP";
        case REALSXP: return "REALSXP";
        case CPLXSXP: return "CPLXSXP";
        case STRSXP: return "STRSXP";
        case DOTSXP: return "DOTSXP";
        case ANYSXP: return "ANYSXP";
        case VECSXP: return "VECSXP";
        case EXPRSXP: return "EXPRSXP";
        case BCODESXP: return "BCODESXP";
        case EXTPTRSXP: return "EXTPTRSXP";
        case WEAKREFSXP: return "WEAKREFSXP";
        case RAWSXP: return "RAWSXP";
        case S4SXP: return "S4SXP";
        case NEWSXP: return "NEWSXP";
        case FREESXP: return "FREESXP";
        case FUNSXP: return "FUNSXP";
        default: return "SEXP";
    }
}

static PyObject *py_c_preserve_sexp(PyObject *self, PyObject *args) {
    PyObject *ptr_obj;
    if (!PyArg_ParseTuple(args, "O", &ptr_obj)) return NULL;
    SEXP s = (SEXP)PyLong_AsVoidPtr(ptr_obj);
    if (s != NULL) {
        flush_deferred_release();
        R_PreserveObject(s);
    }
    Py_RETURN_NONE;
}

static PyObject *py_c_release_sexp(PyObject *self, PyObject *args) {
    PyObject *ptr_obj;
    if (!PyArg_ParseTuple(args, "O", &ptr_obj)) return NULL;
    SEXP s = (SEXP)PyLong_AsVoidPtr(ptr_obj);
    if (s != NULL && R_GlobalEnv != NULL) {
        if (rchitect_is_main_thread()) {
            flush_deferred_release();
            R_ReleaseObject(s);
        } else if (rchitect_is_main_process()) {
            if (deferred_release_len == deferred_release_cap) {
                size_t new_cap = deferred_release_cap == 0 ? 16 : deferred_release_cap * 2;
                SEXP *new_buf = (SEXP *)realloc(deferred_release, new_cap * sizeof(SEXP));
                if (new_buf != NULL) {
                    deferred_release = new_buf;
                    deferred_release_cap = new_cap;
                }
            }
            if (deferred_release_len < deferred_release_cap) {
                deferred_release[deferred_release_len++] = s;
            }
        }
    }
    Py_RETURN_NONE;
}

static PyObject *py_c_sexptype_name(PyObject *self, PyObject *args) {
    PyObject *ptr_obj;
    if (!PyArg_ParseTuple(args, "O", &ptr_obj)) return NULL;
    SEXP s = extract_sexp(ptr_obj);
    if (s == NULL) return NULL;
    return PyUnicode_FromString(sexptype_to_str(TYPEOF(s)));
}

// =============================================================================
// 3. Language Construction & Evaluation (rlang / rcall / reval / rparse)
// =============================================================================

static SEXP c_as_call(PyObject *f) {
    if (is_robject(f)) {
        return extract_sexp(f);
    }
    if (PyUnicode_Check(f)) {
        return c_install_py_str(f);
    }
    if (PyTuple_Check(f)) {
        Py_ssize_t n = PyTuple_Size(f);
        if (n == 2) {
            PyObject *pkg = PyTuple_GetItem(f, 0);
            PyObject *name = PyTuple_GetItem(f, 1);
            if (PyUnicode_Check(pkg) && PyUnicode_Check(name)) {
                SEXP pkg_sym = c_install_py_str(pkg);
                if (pkg_sym == NULL) return NULL;
                SEXP name_sym = c_install_py_str(name);
                if (name_sym == NULL) return NULL;
                return Rf_lang3(R_DoubleColonSymbol, pkg_sym, name_sym);
            }
        } else if (n == 3) {
            PyObject *pkg = PyTuple_GetItem(f, 0);
            PyObject *op = PyTuple_GetItem(f, 1);
            PyObject *name = PyTuple_GetItem(f, 2);
            if (PyUnicode_Check(pkg) && PyUnicode_Check(op) && PyUnicode_Check(name)) {
                SEXP op_sym = NULL;
                if (PyUnicode_CompareWithASCIIString(op, ":::") == 0) {
                    op_sym = R_TripleColonSymbol;
                } else if (PyUnicode_CompareWithASCIIString(op, "::") == 0) {
                    op_sym = R_DoubleColonSymbol;
                } else {
                    op_sym = c_install_py_str(op);
                }
                if (op_sym == NULL) return NULL;
                SEXP pkg_sym = c_install_py_str(pkg);
                if (pkg_sym == NULL) return NULL;
                SEXP name_sym = c_install_py_str(name);
                if (name_sym == NULL) return NULL;
                return Rf_lang3(op_sym, pkg_sym, name_sym);
            }
        }
    }
    PyErr_SetString(PyExc_TypeError, "unexpected function");
    return NULL;
}

static SEXP c_build_rlang(PyObject *f, PyObject *pos_args, PyObject *kw_args, int asis) {
    Py_ssize_t n_pos = PyTuple_Size(pos_args);
    Py_ssize_t n_kw = PyDict_Size(kw_args);
    if (n_kw < 0) return NULL;

    SEXP head_call = Rf_protect(c_as_call(f));
    if (head_call == NULL) {
        Rf_unprotect(1);
        return NULL;
    }

    SEXP t = Rf_protect(Rf_allocVector(LANGSXP, n_pos + n_kw + 1));
    SEXP s = t;
    SETCAR(s, head_call);

    for (Py_ssize_t i = 0; i < n_pos; i++) {
        PyObject *a = PyTuple_GetItem(pos_args, i);
        SEXP a_sexp = asis ? c_sexp_as_py_object_impl(a, 0, 0, 1, 0) : c_sexp_impl(NULL, a, 0, 0, 1, 0);
        if (a_sexp == NULL) {
            Rf_unprotect(2);
            return NULL;
        }
        s = CDR(s);
        SETCAR(s, a_sexp);
    }

    Py_ssize_t pos = 0;
    PyObject *k_obj, *v_obj;
    while (PyDict_Next(kw_args, &pos, &k_obj, &v_obj)) {
        SEXP v_sexp = asis ? c_sexp_as_py_object_impl(v_obj, 0, 0, 1, 0) : c_sexp_impl(NULL, v_obj, 0, 0, 1, 0);
        if (v_sexp == NULL) {
            Rf_unprotect(2);
            return NULL;
        }
        s = CDR(s);
        SETCAR(s, v_sexp);
        SEXP tag_sym = c_install_py_str(k_obj);
        if (tag_sym == NULL) {
            Rf_unprotect(2);
            return NULL;
        }
        SET_TAG(s, tag_sym);
    }

    Rf_unprotect(2);
    return t;
}

static PyObject *py_c_rlang(PyObject *self, PyObject *args) {
    PyObject *f;
    PyObject *pos_args;
    PyObject *kw_args;
    int asis = 0;
    if (!PyArg_ParseTuple(args, "OOO|p", &f, &pos_args, &kw_args, &asis)) return NULL;

    SEXP t = c_build_rlang(f, pos_args, kw_args, asis);
    if (t == NULL) return NULL;
    Rf_protect(t);
    PyObject *res = c_box_sexp(t);
    Rf_unprotect(1);
    return res;
}

static PyObject *py_c_rcall(PyObject *self, PyObject *args) {
    PyObject *f;
    PyObject *pos_args;
    PyObject *kw_args;
    PyObject *envir = Py_None;
    int asis = 0;
    int convert = 0;
    if (!PyArg_ParseTuple(args, "OOO|Opp", &f, &pos_args, &kw_args, &envir, &asis, &convert)) return NULL;

    flush_deferred_release();

    SEXP env_s = R_GlobalEnv;
    if (envir != Py_None) {
        env_s = extract_sexp(envir);
        if (env_s == NULL) return NULL;
    }

    SEXP t = c_build_rlang(f, pos_args, kw_args, asis);
    if (t == NULL) return NULL;
    Rf_protect(t);

    int status = 0;
    SEXP val;
    Py_BEGIN_ALLOW_THREADS
    val = R_tryEval(t, env_s, &status);
    Py_END_ALLOW_THREADS
    flush_deferred_release();
    if (status != 0) {
        Rf_unprotect(1);
        return Py_BuildValue("(Oi)", Py_None, status);
    }

    Rf_protect(val);
    PyObject *ret = convert ? c_rcopy_impl(val, Py_None, 0, 1) : c_box_sexp(val);
    Rf_unprotect(2);
    if (ret == NULL) return NULL;
    return Py_BuildValue("(Ni)", ret, 0);
}

static PyObject *py_c_reval(PyObject *self, PyObject *args) {
    PyObject *s_obj;
    if (!PyArg_ParseTuple(args, "O", &s_obj)) return NULL;

    flush_deferred_release();

    SEXP expr_s = extract_sexp(s_obj);
    if (expr_s == NULL) return NULL;
    Rf_protect(expr_s);

    SEXP val = R_NilValue;
    int status = 0;
    if (TYPEOF(expr_s) == EXPRSXP) {
        R_xlen_t n = Rf_xlength(expr_s);
        for (R_xlen_t i = 0; i < n; i++) {
            SEXP elt = VECTOR_ELT(expr_s, i);
            Py_BEGIN_ALLOW_THREADS
            val = R_tryEval(elt, R_GlobalEnv, &status);
            Py_END_ALLOW_THREADS
            flush_deferred_release();
            if (status != 0) {
                Rf_unprotect(1);
                return Py_BuildValue("(Oi)", Py_None, status);
            }
        }
    } else {
        Py_BEGIN_ALLOW_THREADS
        val = R_tryEval(expr_s, R_GlobalEnv, &status);
        Py_END_ALLOW_THREADS
        flush_deferred_release();
        if (status != 0) {
            Rf_unprotect(1);
            return Py_BuildValue("(Oi)", Py_None, status);
        }
    }

    Rf_protect(val);
    PyObject *ret = c_box_sexp(val);
    Rf_unprotect(2);
    if (ret == NULL) return NULL;
    return Py_BuildValue("(Ni)", ret, 0);
}

static PyObject *py_c_parse_text(PyObject *self, PyObject *args) {
    const char *buf;
    if (!PyArg_ParseTuple(args, "y", &buf)) return NULL;

    ParseStatus status = PARSE_NULL;
    SEXP str_s = Rf_protect(Rf_mkString(buf));
    SEXP val = rchitect_ParseVector(str_s, -1, &status, R_NilValue);
    if (status != PARSE_OK) {
        Rf_unprotect(1);
        return Py_BuildValue("(Oi)", Py_None, (int)status);
    }
    Rf_protect(val);
    PyObject *ret = c_box_sexp(val);
    Rf_unprotect(2);
    if (ret == NULL) return NULL;
    return Py_BuildValue("(Ni)", ret, (int)status);
}

static PyObject *py_c_parse_text_complete(PyObject *self, PyObject *args) {
    const char *buf;
    if (!PyArg_ParseTuple(args, "y", &buf)) return NULL;

    ParseStatus status = PARSE_NULL;
    SEXP str_s = Rf_protect(Rf_mkString(buf));
    rchitect_ParseVector(str_s, -1, &status, R_NilValue);
    Rf_unprotect(1);
    return PyBool_FromLong(status != PARSE_INCOMPLETE);
}

// =============================================================================
// 4. Attributes, Classes, Environments & Symbols
// =============================================================================

static PyObject *py_c_rclass(PyObject *self, PyObject *args) {
    PyObject *obj;
    int single_string = 0;
    if (!PyArg_ParseTuple(args, "O|p", &obj, &single_string)) return NULL;
    SEXP s = extract_sexp(obj);
    if (s == NULL) return NULL;
    SEXP cls = Rf_protect(R_data_class(s, single_string ? TRUE : FALSE));
    PyObject *res = c_rcopy_impl(
        cls,
        single_string ? (PyObject *)&PyUnicode_Type : (PyObject *)&PyList_Type,
        0,
        1
    );
    Rf_unprotect(1);
    return res;
}

static PyObject *py_c_setclass(PyObject *self, PyObject *args) {
    PyObject *obj;
    PyObject *classes;
    if (!PyArg_ParseTuple(args, "OO", &obj, &classes)) return NULL;
    SEXP s = extract_sexp(obj);
    if (s == NULL) return NULL;
    SEXP cls_sexp = Rf_protect(c_sexp_impl("character", classes, 0, 0, 1, 0));
    if (cls_sexp == NULL) {
        Rf_unprotect(1);
        return NULL;
    }
    Rf_setAttrib(s, R_ClassSymbol, cls_sexp);
    Rf_unprotect(1);
    Py_RETURN_NONE;
}

static PyObject *py_c_getattrib(PyObject *self, PyObject *args) {
    PyObject *obj;
    PyObject *key;
    if (!PyArg_ParseTuple(args, "OO", &obj, &key)) return NULL;
    SEXP s = extract_sexp(obj);
    if (s == NULL) return NULL;
    SEXP k_sexp = PyUnicode_Check(key) ? c_install_py_str(key) : extract_sexp(key);
    if (k_sexp == NULL) return NULL;
    SEXP attr = Rf_protect(Rf_getAttrib(s, k_sexp));
    PyObject *res = c_box_sexp(attr);
    Rf_unprotect(1);
    return res;
}

static PyObject *py_c_setattrib(PyObject *self, PyObject *args) {
    PyObject *obj;
    PyObject *key;
    PyObject *val;
    if (!PyArg_ParseTuple(args, "OOO", &obj, &key, &val)) return NULL;
    SEXP s = extract_sexp(obj);
    if (s == NULL) return NULL;
    SEXP k_sexp = PyUnicode_Check(key) ? c_install_py_str(key) : extract_sexp(key);
    if (k_sexp == NULL) return NULL;
    SEXP v_sexp = Rf_protect(c_sexp_impl(NULL, val, 0, 0, 1, 0));
    if (v_sexp == NULL) {
        Rf_unprotect(1);
        return NULL;
    }
    Rf_setAttrib(s, k_sexp, v_sexp);
    Rf_unprotect(1);
    Py_RETURN_NONE;
}

static PyObject *py_c_rnames(PyObject *self, PyObject *args) {
    PyObject *obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) return NULL;
    SEXP s = extract_sexp(obj);
    if (s == NULL) return NULL;
    SEXP names = Rf_protect(Rf_getAttrib(s, R_NamesSymbol));
    if (Rf_isNull(names)) {
        Rf_unprotect(1);
        return PyList_New(0);
    }
    PyObject *res = c_rcopy_str_list(names);
    Rf_unprotect(1);
    return res;
}

static PyObject *py_c_new_env(PyObject *self, PyObject *args) {
    PyObject *parent_obj = Py_None;
    if (!PyArg_ParseTuple(args, "|O", &parent_obj)) return NULL;
    SEXP parent = R_GlobalEnv;
    if (parent_obj != Py_None && PyObject_IsTrue(parent_obj)) {
        parent = extract_sexp(parent_obj);
        if (parent == NULL) return NULL;
    }
    SEXP env = Rf_protect(Rf_NewEnvironment(R_NilValue, R_NilValue, parent));
    PyObject *res = c_box_sexp(env);
    Rf_unprotect(1);
    return res;
}

static PyObject *py_c_rsym(PyObject *self, PyObject *args) {
    PyObject *s_obj;
    PyObject *t_obj = Py_None;
    if (!PyArg_ParseTuple(args, "O|O", &s_obj, &t_obj)) return NULL;
    SEXP res_sexp;
    if (t_obj != Py_None && PyObject_IsTrue(t_obj)) {
        SEXP pkg = c_install_py_str(s_obj);
        if (pkg == NULL) return NULL;
        SEXP sym = c_install_py_str(t_obj);
        if (sym == NULL) return NULL;
        res_sexp = Rf_protect(Rf_lang3(R_DoubleColonSymbol, pkg, sym));
    } else {
        res_sexp = c_install_py_str(s_obj);
        if (res_sexp == NULL) return NULL;
        Rf_protect(res_sexp);
    }
    PyObject *res = c_box_sexp(res_sexp);
    Rf_unprotect(1);
    return res;
}

static PyObject *py_c_getoption(PyObject *self, PyObject *args) {
    PyObject *key_obj;
    if (!PyArg_ParseTuple(args, "O", &key_obj)) return NULL;
    SEXP sym = c_install_py_str(key_obj);
    if (sym == NULL) return NULL;
    SEXP val = Rf_protect(Rf_GetOption1(sym));
    PyObject *res = c_box_sexp(val);
    Rf_unprotect(1);
    return res;
}

static PyObject *py_c_roption(PyObject *self, PyObject *args) {
    PyObject *key_obj;
    if (!PyArg_ParseTuple(args, "O", &key_obj)) return NULL;
    SEXP sym = c_install_py_str(key_obj);
    if (sym == NULL) return NULL;
    SEXP val = Rf_protect(Rf_GetOption1(sym));
    PyObject *res = c_rcopy_impl(val, Py_None, 0, 1);
    Rf_unprotect(1);
    return res;
}

// =============================================================================
// 5. CPython Method Table Registration
// =============================================================================

static PyMethodDef rchitect_interface_methods[] = {
    {"_c_preserve_sexp", py_c_preserve_sexp, METH_VARARGS, NULL},
    {"_c_release_sexp", py_c_release_sexp, METH_VARARGS, NULL},
    {"_c_sexptype_name", py_c_sexptype_name, METH_VARARGS, NULL},
    {"_c_parse_text", py_c_parse_text, METH_VARARGS, NULL},
    {"_c_parse_text_complete", py_c_parse_text_complete, METH_VARARGS, NULL},
    {"_c_rlang", py_c_rlang, METH_VARARGS, NULL},
    {"_c_rcall", py_c_rcall, METH_VARARGS, NULL},
    {"_c_reval", py_c_reval, METH_VARARGS, NULL},
    {"_c_rclass", py_c_rclass, METH_VARARGS, NULL},
    {"_c_setclass", py_c_setclass, METH_VARARGS, NULL},
    {"_c_getattrib", py_c_getattrib, METH_VARARGS, NULL},
    {"_c_setattrib", py_c_setattrib, METH_VARARGS, NULL},
    {"_c_rnames", py_c_rnames, METH_VARARGS, NULL},
    {"_c_new_env", py_c_new_env, METH_VARARGS, NULL},
    {"_c_rsym", py_c_rsym, METH_VARARGS, NULL},
    {"_c_getoption", py_c_getoption, METH_VARARGS, NULL},
    {"_c_roption", py_c_roption, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}
};

int _rchitect_register_interface_methods(void *mod_ptr) {
    return PyModule_AddFunctions((PyObject *)mod_ptr, rchitect_interface_methods);
}
