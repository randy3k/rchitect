from __future__ import unicode_literals
import sys
from ctypes import c_char, c_char_p, c_double, c_int, c_uint, c_void_p, c_size_t
from ctypes import POINTER, CFUNCTYPE, Structure
from collections import namedtuple

from .types import SEXP, Rcomplex, R_len_t, R_xlen_t
# from .utils import rversion


Signature = namedtuple("Signature", ["cname", "restype", "argtypes"])

_function_registry = {}
_sexp_registry = {}
_constant_registry = {}


def noop(*args):
    raise RuntimeError("rchitect not yet ready")


def _make_closure(name, sign):
    _f = [noop]

    def setter(g):
        _f[0] = g

    def f(*args):
        return _f[0](*args)

    f.__name__ = str(name)
    f.__qualname__ = str(name)
    f.__module__ = str('rchitect.internals')
    return f, setter


def _assign(name, f):
    if hasattr(globals(), name):
        print("warning: {} exists".format(name))
    else:
        globals()[name] = f


def _register_function(name, restype, argtypes, cname=None):
    if not cname:
        cname = name
    sign = Signature(cname, restype, argtypes)
    f, setter = _make_closure(name, sign)
    _assign(name, f)
    _function_registry[name] = (sign, setter)


def _register_sexp(name):
    s = SEXP()
    _assign(name, s)
    _sexp_registry[name] = (s, SEXP)


class Constant(object):
    @property
    def value(self):
        return self.const.value

    @value.setter
    def value(self, v):
        self.const.value = v

    def set_constant(self, c):
        self.const = c


def _register_constant(name, vtype):
    c = Constant()
    _assign(name, c)
    _constant_registry[name] = (c, vtype)


# TODO: use pycparser to parse Rinternals.h

# mimic R.internals.h

# CHAR
_register_function("CHAR", c_char_p, [SEXP], cname="R_CHAR")


# Various tests with macro versions in the second USE_RINTERNALS section
_register_function("Rf_isNull", c_int, [SEXP])
_register_function("Rf_isSymbol", c_int, [SEXP])
_register_function("Rf_isLogical", c_int, [SEXP])
_register_function("Rf_isReal", c_int, [SEXP])
_register_function("Rf_isComplex", c_int, [SEXP])
_register_function("Rf_isExpression", c_int, [SEXP])
_register_function("Rf_isEnvironment", c_int, [SEXP])
_register_function("Rf_isString", c_int, [SEXP])
_register_function("Rf_isObject", c_int, [SEXP])


# General Cons Cell Attributes
_register_function("ATTRIB", SEXP, [SEXP])
_register_function("OBJECT", c_int, [SEXP])
_register_function("MARK", c_int, [SEXP])
_register_function("TYPEOF", c_int, [SEXP])
_register_function("NAMED", c_int, [SEXP])
_register_function("REFCNT", c_int, [SEXP])
# _register_function("TRACKREFS", c_int, [SEXP])
_register_function("SET_OBJECT", None, [SEXP, c_int])
_register_function("SET_TYPEOF", None, [SEXP, c_int])
_register_function("SET_NAMED", None, [SEXP, c_int])
_register_function("SET_ATTRIB", None, [SEXP, c_int])
_register_function("DUPLICATE_ATTRIB", None, [SEXP, SEXP])
_register_function("SHALLOW_DUPLICATE_ATTRIB", None, [SEXP, SEXP])
# _register_function("ENSURE_NAMEDMAX", None, [SEXP])
# _register_function("ENSURE_NAMED", None, [SEXP])
# _register_function("SETTER_CLEAR_NAMED", None, [SEXP])
# _register_function("RAISE_NAMED", None, [SEXP, c_int])


# S4 object testing
_register_function("IS_S4_OBJECT", c_int, [SEXP])
_register_function("SET_S4_OBJECT", None, [SEXP])
_register_function("UNSET_S4_OBJECT", None, [SEXP])


# JIT optimization support
_register_function("NOJIT", c_int, [SEXP])
_register_function("MAYBEJIT", c_int, [SEXP])
_register_function("SET_NOJIT", None, [SEXP])
_register_function("SET_MAYBEJIT", None, [SEXP])
_register_function("UNSET_MAYBEJIT", None, [SEXP])


# Growable vector support
_register_function("IS_GROWABLE", c_int, [SEXP])
_register_function("SET_GROWABLE_BIT", None, [SEXP])


# Vector Access Functions
_register_function("LENGTH", c_int, [SEXP])
_register_function("XLENGTH", R_xlen_t, [SEXP])
_register_function("TRUELENGTH", R_xlen_t, [SEXP])
_register_function("SETLENGTH", None, [SEXP, R_xlen_t])
_register_function("SET_TRUELENGTH", None, [SEXP, R_xlen_t])
_register_function("IS_LONG_VEC", c_int, [SEXP])
_register_function("LEVELS", c_int, [SEXP])
_register_function("SETLEVELS", c_int, [SEXP, c_int])

_register_function("LOGICAL", POINTER(c_int), [SEXP])
_register_function("INTEGER", POINTER(c_int), [SEXP])
_register_function("RAW", POINTER(c_char), [SEXP])
_register_function("REAL", POINTER(c_double), [SEXP])
_register_function("COMPLEX", POINTER(Rcomplex), [SEXP])
_register_function("STRING_ELT", SEXP, [SEXP, R_xlen_t])
_register_function("VECTOR_ELT", SEXP, [SEXP, R_xlen_t])
_register_function("SET_STRING_ELT", None, [SEXP, R_xlen_t, SEXP])
_register_function("SET_VECTOR_ELT", None, [SEXP, R_xlen_t, SEXP])


# TODO: ALTREP support


# List Access Functions
_register_function("CONS", SEXP, [SEXP], cname="Rf_cons")
_register_function("LCONS", SEXP, [SEXP], cname="Rf_lcons")
for f in ["TAG", "CAR", "CDR", "CAAR", "CDAR", "CADR", "CDDR", "CDDDR", "CADDR",
          "CADDDR", "CAD4R"]:
    _register_function(f, SEXP, [SEXP])

_register_function("MISSING", c_int, [SEXP])
_register_function("SET_MISSING", None, [SEXP, c_int])
_register_function("SET_TAG", None, [SEXP, SEXP])
for f in ["SETCAR", "SETCDR", "SETCADR", "SETCADDR", "SETCADDDR", "SETCAD4R", "CONS_NR"]:
    _register_function(f, SEXP, [SEXP, SEXP])


# Closure Access Functions
for f in ["FORMALS", "BODY", "CLOENV"]:
    _register_function(f, SEXP, [SEXP])
for f in ["RDEBUG", "RSTEP", "RTRACE"]:
    _register_function(f, c_int, [SEXP])
for f in ["SET_RDEBUG", "SET_RSTEP", "SET_RTRACE"]:
    _register_function(f, None, [SEXP, c_int])
for f in ["SET_FORMALS", "SET_BODY", "SET_CLOENV"]:
    _register_function(f, None, [SEXP, SEXP])


# Symbol Access Functions

_register_function("PRINTNAME", SEXP, [SEXP])
_register_function("SYMVALUE", SEXP, [SEXP])
_register_function("INTERNAL", SEXP, [SEXP])
_register_function("DDVAL", c_int, [SEXP])
_register_function("SET_DDVAL", None, [SEXP, c_int])
_register_function("SET_PRINTNAME", SEXP, [SEXP, SEXP])
_register_function("SET_SYMVALUE", SEXP, [SEXP, SEXP])
_register_function("SET_INTERNAL", SEXP, [SEXP, SEXP])


# Environment Access Functions

_register_function("FRAME", SEXP, [SEXP])
_register_function("ENCLOS", SEXP, [SEXP])
_register_function("HASHTAB", SEXP, [SEXP])
_register_function("ENVFLAGS", c_int, [SEXP])
_register_function("SET_ENVFLAGS", None, [SEXP, c_int])
_register_function("SET_FRAME", None, [SEXP, SEXP])
_register_function("SET_ENCLOS", None, [SEXP, SEXP])
_register_function("SET_HASHTAB", None, [SEXP, SEXP])


# Promise Access Functions

_register_function("PRCODE", SEXP, [SEXP])
_register_function("PRENV", SEXP, [SEXP])
_register_function("PRVALUE", SEXP, [SEXP])
_register_function("PRSEEN", c_int, [SEXP])
_register_function("SET_PRSEEN", None, [SEXP, c_int])
_register_function("SET_PRENV", None, [SEXP, SEXP])
_register_function("SET_PRVALUE", None, [SEXP, SEXP])
_register_function("SET_PRCODE", None, [SEXP, SEXP])


# Hashing Functions

# _register_function("HASHASH", c_int, [SEXP])
# _register_function("HASHVALUE", c_int, [SEXP])
# _register_function("SET_HASHASH", None, [SEXP, c_int])
# _register_function("SET_HASHVALUE", None, [SEXP, c_int])


# Pointer Protection and Unprotection

_register_function("PROTECT", SEXP, [SEXP], cname="Rf_protect")
_register_function("UNPROTECT", None, [SEXP], cname="Rf_unprotect")
_register_function("UNPROTECT_PTR", None, [SEXP], cname="Rf_unprotect_ptr")
_register_function("PROTECT_WITH_INDEX", SEXP, [SEXP, POINTER(c_int)], cname="R_ProtectWithIndex")
_register_function("REPROTECT", SEXP, [SEXP, c_int], cname="R_Reprotect")


# Evaluation Environment

_register_sexp("R_GlobalEnv")
_register_sexp("R_EmptyEnv")
_register_sexp("R_BaseEnv")
_register_sexp("R_BaseNamespace")
_register_sexp("R_NamespaceRegistry")
_register_sexp("R_Srcref")

# Special Values

_register_sexp("R_NilValue")
_register_sexp("R_UnboundValue")
_register_sexp("R_MissingArg")
_register_sexp("R_InBCInterpreter")
_register_sexp("R_CurrentExpression")


# Symbol Table Shortcuts

_register_sexp("R_AsCharacterSymbol")
_register_sexp("R_baseSymbol")
_register_sexp("R_BaseSymbol")
_register_sexp("R_BraceSymbol")
_register_sexp("R_Bracket2Symbol")
_register_sexp("R_BracketSymbol")
_register_sexp("R_ClassSymbol")
_register_sexp("R_DeviceSymbol")
_register_sexp("R_DimNamesSymbol")
_register_sexp("R_DimSymbol")
_register_sexp("R_DollarSymbol")
_register_sexp("R_DotsSymbol")
_register_sexp("R_DoubleColonSymbol")
_register_sexp("R_DropSymbol")
_register_sexp("R_LastvalueSymbol")
_register_sexp("R_LevelsSymbol")
_register_sexp("R_ModeSymbol")
_register_sexp("R_NaRmSymbol")
_register_sexp("R_NameSymbol")
_register_sexp("R_NamesSymbol")
_register_sexp("R_NamespaceEnvSymbol")
_register_sexp("R_PackageSymbol")
_register_sexp("R_PreviousSymbol")
_register_sexp("R_QuoteSymbol")
_register_sexp("R_RowNamesSymbol")
_register_sexp("R_SeedsSymbol")
_register_sexp("R_SortListSymbol")
_register_sexp("R_SourceSymbol")
_register_sexp("R_SpecSymbol")
_register_sexp("R_TripleColonSymbol")
_register_sexp("R_TspSymbol")

_register_sexp("R_dot_defined")
_register_sexp("R_dot_Method")
_register_sexp("R_dot_packageName")
_register_sexp("R_dot_target")
_register_sexp("R_dot_Generic")

# Missing Values

_register_sexp("R_NaString")
_register_sexp("R_BlankString")
_register_sexp("R_BlankScalarString")


# srcref related functions

_register_function("R_GetCurrentSrcref", SEXP, [c_int])
_register_function("R_GetSrcFilename", SEXP, [SEXP])


# Type Coercions of all kinds

_register_function("Rf_asChar", SEXP, [SEXP])
_register_function("Rf_coerceVector", SEXP, [SEXP])
_register_function("Rf_PairToVectorList", SEXP, [SEXP])
_register_function("Rf_VectorToPairList", SEXP, [SEXP])
_register_function("Rf_asCharacterFactor", SEXP, [SEXP])
_register_function("Rf_asLogical", c_int, [SEXP])
_register_function("Rf_asInteger", c_int, [SEXP])
_register_function("Rf_asReal", c_double, [SEXP])
_register_function("Rf_asComplex", Rcomplex, [SEXP])


# Other Internally Used Functions

_register_function("Rf_acopy_string", c_char_p, [c_char_p],)
# _register_function("Rf_addMissingVarsToNewEnv", SEXP, [SEXP, SEXP])
_register_function("Rf_alloc3DArray", SEXP, [c_uint, c_int, c_int, c_int])
_register_function("Rf_allocArray", SEXP, [c_uint, SEXP])
_register_function("Rf_allocFormalsList2", SEXP, [SEXP, SEXP])
_register_function("Rf_allocFormalsList3", SEXP, [SEXP, SEXP, SEXP])
_register_function("Rf_allocFormalsList4", SEXP, [SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_allocFormalsList5", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_allocFormalsList6", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_allocList", SEXP, [c_int])
_register_function("Rf_allocMatrix", SEXP, [c_uint, c_int, c_int])
_register_function("Rf_allocS4Object", SEXP, [])
_register_function("Rf_allocSExp", SEXP, [c_uint])
_register_function("Rf_allocVector", SEXP, [c_uint, R_xlen_t])
_register_function("Rf_allocVector3", SEXP, [c_uint, R_xlen_t, c_void_p])
_register_function("Rf_any_duplicated", R_xlen_t, [SEXP, c_int])
_register_function("Rf_any_duplicated3", R_xlen_t, [SEXP, SEXP, c_int])
_register_function("Rf_applyClosure", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_arraySubscript", SEXP, [c_int, SEXP, SEXP, CFUNCTYPE(SEXP, SEXP, SEXP), CFUNCTYPE(SEXP, SEXP, c_int)])
_register_function("Rf_classgets", SEXP, [SEXP, SEXP])
# _register_function("Rf_fixSubset3Args", SEXP, [SEXP, SEXP, SEXP, POINTER(SEXP)])
_register_function("Rf_copyMatrix", None, [SEXP, SEXP, c_int])
_register_function("Rf_copyListMatrix", None, [SEXP, SEXP, c_int])
_register_function("Rf_copyMostAttrib", None, [SEXP, SEXP])
_register_function("Rf_copyVector", None, [SEXP, SEXP])
_register_function("Rf_countContexts", c_int, [c_int, c_int])
_register_function("Rf_CreateTag", SEXP, [SEXP])
_register_function("Rf_defineVar", None, [SEXP, SEXP, SEXP])
_register_function("Rf_dimgets", SEXP, [SEXP, SEXP])
_register_function("Rf_dimnamesgets", SEXP, [SEXP, SEXP])
_register_function("Rf_DropDims", SEXP, [SEXP])
_register_function("Rf_duplicate", SEXP, [SEXP])
_register_function("Rf_shallow_duplicate", SEXP, [SEXP])
_register_function("Rf_lazy_duplicate", SEXP, [SEXP])
_register_function("Rf_duplicated", SEXP, [SEXP, c_int])
_register_function("R_envHasNoSpecialSymbols", c_int, [SEXP])
_register_function("Rf_eval", SEXP, [SEXP, SEXP])
# _register_function("Rf_ExtractSubset", SEXP, [SEXP, SEXP, SEXP])
_register_function("Rf_findFun", SEXP, [SEXP, SEXP])
# _register_function("Rf_findFun3", SEXP, [SEXP, SEXP, SEXP])
# _register_function("Rf_findFunctionForBody", None, [SEXP])
_register_function("Rf_findVar", SEXP, [SEXP, SEXP])
_register_function("Rf_findVarInFrame", SEXP, [SEXP, SEXP])
_register_function("Rf_findVarInFrame3", SEXP, [SEXP, SEXP, c_int])
_register_function("Rf_getAttrib", SEXP, [SEXP, SEXP])
_register_function("Rf_GetArrayDimnames", SEXP, [SEXP])
_register_function("Rf_GetColNames", SEXP, [SEXP])
_register_function("Rf_GetMatrixDimnames", None, [SEXP, POINTER(SEXP), POINTER(SEXP), POINTER(c_char_p), POINTER(c_char_p)])
_register_function("Rf_GetOption1", SEXP, [SEXP])
_register_function("Rf_GetOptionDigits", c_int, [])
_register_function("Rf_GetOptionWidth", c_int, [])
_register_function("Rf_GetRowNames", SEXP, [SEXP])
_register_function("Rf_gsetVar", None, [SEXP, SEXP, SEXP])
_register_function("Rf_install", SEXP, [c_char_p])
_register_function("Rf_installChar", SEXP, [SEXP])
# _register_function("Rf_installNoTrChar", SEXP, [SEXP])
# _register_function("Rf_installDDVAL", SEXP, [c_int])
# _register_function("Rf_installS3Signature", SEXP, [c_char_p, c_char_p])
_register_function("Rf_isFree", c_int, [SEXP])
_register_function("Rf_isOrdered", c_int, [SEXP])
# _register_function("Rf_isUnmodifiedSpecSym", c_int, [SEXP, SEXP])
_register_function("Rf_isUnordered", c_int, [SEXP])
_register_function("Rf_isUnsorted", c_int, [SEXP])
_register_function("Rf_lengthgets", SEXP, [SEXP, R_len_t])
_register_function("Rf_xlengthgets", SEXP, [SEXP, R_xlen_t])
_register_function("R_lsInternal", SEXP, [SEXP, c_int])
_register_function("R_lsInternal3", SEXP, [SEXP, c_int, c_int])
_register_function("Rf_match", SEXP, [SEXP, SEXP, c_int])
_register_function("Rf_matchE", SEXP, [SEXP, SEXP, c_int, SEXP])
_register_function("Rf_namesgets", SEXP, [SEXP, SEXP])
_register_function("Rf_mkChar", SEXP, [c_char_p])
_register_function("Rf_mkCharLen", SEXP, [c_char_p, c_int])
_register_function("Rf_NonNullStringMatch", c_int, [SEXP, SEXP])
_register_function("Rf_ncols", c_int, [SEXP])
_register_function("Rf_nrows", c_int, [SEXP])
_register_function("Rf_nthcdr", SEXP, [SEXP, c_int])

# ../main/character.c

_register_function("R_nchar", c_int, [SEXP, c_int, c_int, c_int, c_char_p])

_register_function("Rf_pmatch", c_int, [SEXP, SEXP, c_int])
_register_function("Rf_psmatch", c_int, [c_char_p, c_char_p, c_int])
_register_function("R_ParseEvalString", SEXP, [c_char_p, SEXP])
_register_function("Rf_PrintValue", None, [SEXP])
_register_function("Rf_protect", SEXP, [SEXP])
# _register_function("Rf_readS3VarsFromFrame", None, [SEXP, POINTER(SEXP), POINTER(SEXP), POINTER(SEXP), POINTER(SEXP), POINTER(SEXP), POINTER(SEXP)])
_register_function("Rf_setAttrib", SEXP, [SEXP, SEXP, SEXP])
_register_function("Rf_setSVector", None, [POINTER(SEXP), c_int, SEXP])
_register_function("Rf_setVar", SEXP, [SEXP, SEXP, SEXP])
# _register_function("Rf_stringSuffix", SEXP, [SEXP, c_int])
_register_function("Rf_str2type", c_uint, [c_char_p])
_register_function("Rf_StringBlank", c_int, [SEXP])
_register_function("Rf_substitute", SEXP, [SEXP, SEXP])
_register_function("Rf_topenv", SEXP, [SEXP, SEXP])
_register_function("Rf_translateChar", c_char_p, [SEXP])
_register_function("Rf_translateChar0", c_char_p, [SEXP])
_register_function("Rf_translateCharUTF8", c_char_p, [SEXP])
_register_function("Rf_type2char", c_char_p, [c_uint])
_register_function("Rf_type2rstr", SEXP, [c_uint])
_register_function("Rf_type2str", SEXP, [c_uint])
_register_function("Rf_type2str_nowarn", SEXP, [c_uint])
_register_function("Rf_unprotect", None, [SEXP])
_register_function("Rf_unprotect_ptr", None, [SEXP])


# _register_function("R_signal_protect_error", None, [None], cname="R_signal_protect_error")
# _register_function("R_signal_unprotect_error", None, [None], cname="R_signal_unprotect_error")
# _register_function("R_signal_reprotect_error", None, [c_int], cname="R_signal_reprotect_error")

_register_function("R_ProtectWithIndex", SEXP, [SEXP, POINTER(c_int)])
_register_function("R_Reprotect", SEXP, [SEXP, c_int])

_register_function("R_tryEval", SEXP, [SEXP, SEXP, POINTER(c_int)])
_register_function("R_tryEvalSilent", SEXP, [SEXP, SEXP, POINTER(c_int)])
_register_function("R_curErrorBuf", c_char_p, [])

_register_function("Rf_isS4", c_int, [SEXP])
_register_function("Rf_asS4", SEXP, [SEXP, c_int, c_int])
_register_function("Rf_S3Class", SEXP, [SEXP])
_register_function("Rf_isBasicClass", c_int, [c_char_p])

_register_function("R_cycle_detected", c_int, [SEXP, SEXP])

_register_function("Rf_getCharCE", c_int, [SEXP])
_register_function("Rf_mkCharCE", SEXP, [c_char_p, c_int, c_int])
_register_function("Rf_mkCharLenCE", SEXP, [c_char_p, c_int, c_int])
_register_function("Rf_reEnc", c_char_p, [c_char_p, c_int, c_int, c_int])

_register_function("R_forceAndCall", SEXP, [SEXP, c_int, SEXP])


# External pointer interface

_register_function("R_MakeExternalPtr", SEXP, [c_void_p, SEXP, SEXP])
_register_function("R_ExternalPtrAddr", c_void_p, [SEXP])
_register_function("R_ExternalPtrTag", SEXP, [SEXP])
_register_function("R_ExternalPtrProtected", SEXP, [SEXP])
_register_function("R_ClearExternalPtr", None, [SEXP])
_register_function("R_SetExternalPtrAddr", None, [SEXP, c_void_p])
_register_function("R_SetExternalPtrTag", None, [SEXP, SEXP])
_register_function("R_SetExternalPtrProtected", None, [SEXP, SEXP])
_register_function("R_MakeExternalPtrFn", SEXP, [c_void_p, SEXP, SEXP])
_register_function("R_ExternalPtrAddrFn", c_void_p, [SEXP])


# Finalization interface

_register_function("R_RegisterFinalizer", None, [SEXP, SEXP])
_register_function("R_RegisterCFinalizer", None, [SEXP, CFUNCTYPE(None, SEXP)])
_register_function("R_RegisterFinalizerEx", None, [SEXP, SEXP, c_int])
_register_function("R_RegisterCFinalizerEx", None, [SEXP, CFUNCTYPE(None, SEXP), c_int])
_register_function("R_RunPendingFinalizers", None, [])

# Weak reference interface


# Protected evaluation

_register_function("R_ToplevelExec", c_int, [CFUNCTYPE(None, c_void_p), c_void_p])
_register_function("R_ExecWithCleanup", SEXP, [CFUNCTYPE(SEXP, c_void_p), c_void_p, CFUNCTYPE(None, c_void_p), c_void_p])
_register_function("R_tryCatch", SEXP, [CFUNCTYPE(SEXP, c_void_p), c_void_p, SEXP, CFUNCTYPE(SEXP, c_void_p), c_void_p, CFUNCTYPE(None, c_void_p), c_void_p])
_register_function("R_tryCatchError", SEXP, [CFUNCTYPE(SEXP, c_void_p), c_void_p, CFUNCTYPE(SEXP, c_void_p), c_void_p])
# _register_function("R_MakeUnwindCont", SEXP, [])
# _register_function("R_ContinueUnwind", None, [SEXP])
# _register_function("R_UnwindProtect", SEXP, [CFUNCTYPE(SEXP, c_void_p), c_void_p, CFUNCTYPE(None, c_void_p, c_int), c_void_p, SEXP])


# Environment and Binding Features

_register_function("R_RestoreHashCount", None, [SEXP])
_register_function("R_IsPackageEnv", c_int, [SEXP])
_register_function("R_PackageEnvName", SEXP, [SEXP])
_register_function("R_FindPackageEnv", SEXP, [SEXP])
_register_function("R_IsNamespaceEnv", c_int, [SEXP])
_register_function("R_NamespaceEnvSpec", SEXP, [SEXP])
_register_function("R_FindNamespace", SEXP, [SEXP])
_register_function("R_LockEnvironment", None, [SEXP, c_int])
_register_function("R_EnvironmentIsLocked", c_int, [SEXP])
_register_function("R_LockBinding", None, [SEXP, SEXP])
_register_function("R_unLockBinding", None, [SEXP, SEXP])
_register_function("R_MakeActiveBinding", None, [SEXP, SEXP, SEXP])
_register_function("R_BindingIsLocked", c_int, [SEXP, SEXP])
_register_function("R_BindingIsActive", c_int, [SEXP, SEXP])
_register_function("R_HasFancyBindings", c_int, [SEXP])


# ../main/errors.c


# slot management (in attrib.c)

_register_function("R_do_slot", SEXP, [SEXP, SEXP])
_register_function("R_do_slot_assign", SEXP, [SEXP, SEXP, SEXP])
_register_function("R_has_slot", c_int, [SEXP, SEXP])

# S3-S4 class (inheritance) (in attrib.c)

_register_function("R_S4_extends", SEXP, [SEXP, SEXP])

# class definition, new objects (objects.c)

_register_function("R_do_MAKE_CLASS", SEXP, [c_char_p])
_register_function("R_getClassDef", SEXP, [c_char_p])
_register_function("R_getClassDef_R", SEXP, [SEXP])
_register_function("R_has_methods_attached", c_int, [])
_register_function("R_isVirtualClass", c_int, [SEXP, SEXP])
_register_function("R_extends", c_int, [SEXP, SEXP, SEXP])
_register_function("R_do_new_object", SEXP, [SEXP])

# supporting  a C-level version of  is(., .)

_register_function("R_check_class_and_super", c_int, [SEXP, c_char_p, SEXP])
_register_function("R_check_class_etc", c_int, [SEXP, c_char_p])


# preserve objects across GCs

_register_function("R_PreserveObject", None, [SEXP])
_register_function("R_ReleaseObject", None, [SEXP])


# Shutdown actions

_register_function("R_dot_Last", None, [])
_register_function("R_RunExitFinalizers", None, [])


# Replacements for popen and system

_register_function("R_system", c_int, [c_char_p])


# R_compute_identical

_register_function("R_compute_identical", c_int, [SEXP, SEXP])

#  body(x) without "srcref" etc

_register_function("R_body_no_src", SEXP, [SEXP])

# C version of R's  indx <- order(..., na.last, decreasing)
_register_function("R_orderVector", None, [c_int, c_int, SEXP, c_int, c_int])
# C version of R's  indx <- order(x, na.last, decreasing)
_register_function("R_orderVector1", None, [c_int, c_int, SEXP, c_int, c_int])

# inlinable functions


_register_function("Rf_conformable", c_int, [SEXP, SEXP])
_register_function("Rf_elt", SEXP, [SEXP, c_int])
_register_function("Rf_inherits", c_int, [SEXP, c_char_p])
_register_function("Rf_isArray", c_int, [SEXP])
_register_function("Rf_isFactor", c_int, [SEXP])
_register_function("Rf_isFrame", c_int, [SEXP])
_register_function("Rf_isFunction", c_int, [SEXP])
_register_function("Rf_isInteger", c_int, [SEXP])
_register_function("Rf_isLanguage", c_int, [SEXP])
_register_function("Rf_isList", c_int, [SEXP])
_register_function("Rf_isMatrix", c_int, [SEXP])
_register_function("Rf_isNewList", c_int, [SEXP])
_register_function("Rf_isNumeric", c_int, [SEXP])
_register_function("Rf_isNumber", c_int, [SEXP])
_register_function("Rf_isPairList", c_int, [SEXP])
_register_function("Rf_isPrimitive", c_int, [SEXP])
_register_function("Rf_isTs", c_int, [SEXP])
_register_function("Rf_isUserBinop", c_int, [SEXP])
_register_function("Rf_isValidString", c_int, [SEXP])
_register_function("Rf_isValidStringF", c_int, [SEXP])
_register_function("Rf_isVector", c_int, [SEXP])
_register_function("Rf_isVectorAtomic", c_int, [SEXP])
_register_function("Rf_isVectorList", c_int, [SEXP])
_register_function("Rf_isVectorizable", c_int, [SEXP])
_register_function("Rf_lang1", SEXP, [SEXP])
_register_function("Rf_lang2", SEXP, [SEXP, SEXP])
_register_function("Rf_lang3", SEXP, [SEXP, SEXP, SEXP])
_register_function("Rf_lang4", SEXP, [SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_lang5", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_lang6", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_lastElt", SEXP, [SEXP])
_register_function("Rf_lcons", SEXP, [SEXP, SEXP])
_register_function("Rf_length", SEXP, [SEXP])
_register_function("Rf_list1", SEXP, [SEXP])
_register_function("Rf_list2", SEXP, [SEXP, SEXP])
_register_function("Rf_list3", SEXP, [SEXP, SEXP, SEXP])
_register_function("Rf_list4", SEXP, [SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_list5", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_list6", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP, SEXP])
_register_function("Rf_listAppend", SEXP, [SEXP, SEXP])
_register_function("Rf_mkNamed", SEXP, [c_uint, c_char_p])
_register_function("Rf_mkString", SEXP, [c_char_p])
_register_function("Rf_nlevels", c_int, [SEXP])
_register_function("Rf_stringPositionTr", c_int, [SEXP, c_char_p])
_register_function("Rf_ScalarComplex", SEXP, [Rcomplex])
_register_function("Rf_ScalarInteger", SEXP, [c_int])
_register_function("Rf_ScalarLogical", SEXP, [c_int])
_register_function("Rf_ScalarRaw", SEXP, [c_char])
_register_function("Rf_ScalarReal", SEXP, [c_double])
_register_function("Rf_ScalarString", SEXP, [SEXP])
_register_function("Rf_xlength", R_xlen_t, [SEXP])
# _register_function("LENGTH_EX", c_int, [SEXP, c_char_p, c_int])
# _register_function("XLENGTH_EX", R_xlen_t, [SEXP])
_register_function("R_FixupRHS", SEXP, [SEXP, SEXP])


# Arith.h

_register_sexp("R_NaN")
_register_sexp("R_PosInf")
_register_sexp("R_NegInf")
_register_sexp("R_NaReal")
_register_sexp("R_NaInt")
_register_function("R_IsNA", c_int, [c_double])
_register_function("R_IsNaN", c_int, [c_double])
_register_function("R_finite", c_int, [c_double])


# Print.h

# _register_function("Rf_formatRaw", None, [c_char_p, R_xlen_t, POINTER(c_int)])
# _register_function("Rf_formatString", None, [POINTER(SEXP), R_xlen_t, POINTER(c_int), c_int])
# _register_function("Rf_EncodeElement", c_char_p, [SEXP, c_int, c_int, c_char])
# _register_function("Rf_EncodeElement0", c_char_p, [SEXP, c_int, c_int, c_char_p])
# _register_function("Rf_EncodeEnvironment", SEXP, [SEXP])
# _register_function("Rf_printArray", None, [SEXP, SEXP, c_int, c_int, SEXP])
# _register_function("Rf_printMatrix", None, [SEXP, c_int, SEXP, c_int, c_int, SEXP, SEXP, c_char_p, c_char_p])
# _register_function("Rf_printNamedVector", None, [SEXP, SEXP, c_int, c_char_p])
# _register_function("Rf_printVector", None, [SEXP, c_int, c_int])


# Parse.h

_register_function("R_ParseVector", SEXP, [SEXP, c_int, POINTER(c_int), SEXP])

# Memory.h

_register_function("R_gc", None, [])
_register_function("R_gc_running", c_int, [])
_register_function("R_alloc", c_void_p, [c_size_t, c_int])
_register_function("R_allocLD", c_void_p, [c_size_t])


# Error.h

_register_function("Rf_error", None, None)
_register_function("Rf_warning", None, None)


# Defn.h

_register_function("R_data_class", SEXP, [SEXP, c_int])

_register_sexp("R_InputHandlers")
_register_function("R_ProcessEvents", None, [])
_register_function("R_checkActivity", c_void_p, [c_int, c_int])
_register_function("R_runHandlers", None, [c_void_p, c_void_p])

_register_function("R_CheckUserInterrupt", None, [])


if sys.platform == "win32":
    _register_constant("UserBreak", c_int)
else:
    _register_constant("R_interrupts_pending", c_int)


# Rdynload.h


class R_CallMethodDef(Structure):
    _fields_ = [
        ("name", c_char_p),
        ("fun", c_void_p),
        ("numArgs", c_int)
    ]


_register_function("R_getDllInfo", c_void_p, [c_char_p])
_register_function("R_getEmbeddingDllInfo", c_void_p, [])
_register_function("R_registerRoutines", c_int, [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p])


_register_constant("R_Visible", c_int)
