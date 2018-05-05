from __future__ import unicode_literals
from ctypes import c_char, c_char_p, c_double, c_int, c_ubyte, c_void_p, c_size_t
from ctypes import POINTER, CFUNCTYPE
from collections import namedtuple

from . import types, internals, interface
from .types import SEXP, SEXPTYPE, Rcomplex, R_len_t, R_xlen_t
from .utils import cglobal


Signature = namedtuple("Signature", ["cname", "restype", "argtypes"])

_globals = {}
_signatures = {}


def noop(*args):
    raise RuntimeError("rapi not yet ready")


def notavaiable(*args):
    raise NotImplementedError("method not avaiable")


def _make_closure(name, sign):
    _f = [noop]

    def setter(g):
        _f[0] = g

    def f(*args):
        return _f[0](*args)

    f.__name__ = str(name)
    f.__qualname__ = str(name)
    f.__module__ = str('rapi.internals')
    return f, setter


def _set_internals_attr(name, f):
    if hasattr(internals, name):
        print("warning: {} exists".format(name))
    else:
        setattr(internals, name, f)


def _register(name, restype, argtypes, cname=None):
    if not cname:
        cname = name
    sign = Signature(cname, restype, argtypes)
    f, setter = _make_closure(name, sign)
    _set_internals_attr(name, f)
    _signatures[name] = (sign, setter)


def _register_global(name):
    s = SEXP()
    setattr(internals, name, s)
    _globals[name] = s


# TODO: use pycparser to parse Rinternals.h

# CHAR
_register("CHAR", c_char_p, [SEXP], cname="R_CHAR")


# Various tests with macro versions in the second USE_RINTERNALS section
_register("Rf_isNull", c_int, [SEXP])
_register("Rf_isSymbol", c_int, [SEXP])
_register("Rf_isLogical", c_int, [SEXP])
_register("Rf_isReal", c_int, [SEXP])
_register("Rf_isComplex", c_int, [SEXP])
_register("Rf_isExpression", c_int, [SEXP])
_register("Rf_isEnvironment", c_int, [SEXP])
_register("Rf_isString", c_int, [SEXP])
_register("Rf_isObject", c_int, [SEXP])


# General Cons Cell Attributes
_register("ATTRIB", SEXP, [SEXP])
_register("OBJECT", c_int, [SEXP])
_register("MARK", c_int, [SEXP])
_register("TYPEOF", c_int, [SEXP])
_register("NAMED", c_int, [SEXP])
_register("REFCNT", c_int, [SEXP])
_register("TRACKREFS", c_int, [SEXP])
_register("SET_OBJECT", None, [SEXP, c_int])
_register("SET_TYPEOF", None, [SEXP, c_int])
_register("SET_NAMED", None, [SEXP, c_int])
_register("SET_ATTRIB", None, [SEXP, c_int])
_register("DUPLICATE_ATTRIB", None, [SEXP, SEXP])
_register("SHALLOW_DUPLICATE_ATTRIB", None, [SEXP, SEXP])
_register("ENSURE_NAMEDMAX", None, [SEXP])
_register("ENSURE_NAMED", None, [SEXP])
_register("SETTER_CLEAR_NAMED", None, [SEXP])
_register("RAISE_NAMED", None, [SEXP, c_int])


# S4 object testing
_register("IS_S4_OBJECT", c_int, [SEXP])
_register("SET_S4_OBJECT", None, [SEXP])
_register("UNSET_S4_OBJECT", None, [SEXP])


# JIT optimization support
_register("NOJIT", c_int, [SEXP])
_register("MAYBEJIT", c_int, [SEXP])
_register("SET_NOJIT", None, [SEXP])
_register("SET_MAYBEJIT", None, [SEXP])
_register("UNSET_MAYBEJIT", None, [SEXP])


# Growable vector support
_register("IS_GROWABLE", c_int, [SEXP])
_register("SET_GROWABLE_BIT", None, [SEXP])


# Vector Access Functions
_register("LENGTH", c_int, [SEXP])
_register("XLENGTH", R_xlen_t, [SEXP])
_register("TRUELENGTH", R_xlen_t, [SEXP])
_register("SETLENGTH", None, [SEXP, R_xlen_t])
_register("SET_TRUELENGTH", None, [SEXP, R_xlen_t])
_register("IS_LONG_VEC", c_int, [SEXP])
_register("LEVELS", c_int, [SEXP])
_register("SETLEVELS", c_int, [SEXP, c_int])

_register("LOGICAL", POINTER(c_int), [SEXP])
_register("INTEGER", POINTER(c_int), [SEXP])
_register("RAW", POINTER(c_ubyte), [SEXP])
_register("REAL", POINTER(c_double), [SEXP])
_register("COMPLEX", POINTER(Rcomplex), [SEXP])
_register("STRING_ELT", SEXP, [SEXP, R_xlen_t])
_register("VECTOR_ELT", SEXP, [SEXP, R_xlen_t])
_register("SET_STRING_ELT", None, [SEXP, R_xlen_t, SEXP])
_register("SET_VECTOR_ELT", None, [SEXP, R_xlen_t, SEXP])


# TODO: ALTREP support


# List Access Functions
_register("CONS", SEXP, [SEXP], cname="Rf_cons")
_register("LCONS", SEXP, [SEXP], cname="Rf_lcons")
for f in ["TAG", "CAR", "CDR", "CAAR", "CDAR", "CADR", "CDDR", "CDDDR", "CADDR",
          "CADDDR", "CAD4R"]:
    _register(f, SEXP, [SEXP])

_register("MISSING", c_int, [SEXP])
_register("SET_MISSING", None, [SEXP, c_int])
_register("SET_TAG", None, [SEXP, SEXP])
for f in ["SETCAR", "SETCDR", "SETCADR", "SETCADDR", "SETCADDDR", "SETCAD4R", "CONS_NR"]:
    _register(f, SEXP, [SEXP, SEXP])


# Closure Access Functions
for f in ["FORMALS", "BODY", "CLOENV"]:
    _register(f, SEXP, [SEXP])
for f in ["RDEBUG", "RSTEP", "RTRACE"]:
    _register(f, c_int, [SEXP])
for f in ["SET_RDEBUG", "SET_RSTEP", "SET_RTRACE"]:
    _register(f, None, [SEXP, c_int])
for f in ["SET_FORMALS", "SET_BODY", "SET_CLOENV"]:
    _register(f, None, [SEXP, SEXP])


# Symbol Access Functions

_register("PRINTNAME", SEXP, [SEXP])
_register("SYMVALUE", SEXP, [SEXP])
_register("INTERNAL", SEXP, [SEXP])
_register("DDVAL", c_int, [SEXP])
_register("SET_DDVAL", None, [SEXP, c_int])
_register("SET_PRINTNAME", SEXP, [SEXP, SEXP])
_register("SET_SYMVALUE", SEXP, [SEXP, SEXP])
_register("SET_INTERNAL", SEXP, [SEXP, SEXP])


# Environment Access Functions

_register("FRAME", SEXP, [SEXP])
_register("ENCLOS", SEXP, [SEXP])
_register("HASHTAB", SEXP, [SEXP])
_register("ENVFLAGS", c_int, [SEXP])
_register("SET_ENVFLAGS", None, [SEXP, c_int])
_register("SET_FRAME", None, [SEXP, SEXP])
_register("SET_ENCLOS", None, [SEXP, SEXP])
_register("SET_HASHTAB", None, [SEXP, SEXP])


# Promise Access Functions

_register("PRCODE", SEXP, [SEXP])
_register("PRENV", SEXP, [SEXP])
_register("PRVALUE", SEXP, [SEXP])
_register("PRSEEN", c_int, [SEXP])
_register("SET_PRSEEN", None, [SEXP, c_int])
_register("SET_PRENV", None, [SEXP, SEXP])
_register("SET_PRVALUE", None, [SEXP, SEXP])
_register("SET_PRCODE", None, [SEXP, SEXP])


# Hashing Functions

# _register("HASHASH", c_int, [SEXP])
# _register("HASHVALUE", c_int, [SEXP])
# _register("SET_HASHASH", None, [SEXP, c_int])
# _register("SET_HASHVALUE", None, [SEXP, c_int])


# Pointer Protection and Unprotection

_register("PROTECT", SEXP, [SEXP], cname="Rf_protect")
_register("UNPROTECT", None, [SEXP], cname="Rf_unprotect")
_register("UNPROTECT_PTR", None, [SEXP], cname="Rf_unprotect_ptr")
_register("PROTECT_WITH_INDEX", SEXP, [SEXP, POINTER(c_int)], cname="R_ProtectWithIndex")
_register("REPROTECT", SEXP, [SEXP, c_int], cname="R_Reprotect")


# Evaluation Environment

_register_global("R_GlobalEnv")
_register_global("R_EmptyEnv")
_register_global("R_BaseEnv")
_register_global("R_BaseNamespace")
_register_global("R_NamespaceRegistry")
_register_global("R_Srcref")

# Special Values

_register_global("R_NilValue")
_register_global("R_UnboundValue")
_register_global("R_MissingArg")
_register_global("R_InBCInterpreter")
_register_global("R_CurrentExpression")


# Symbol Table Shortcuts

_register_global("R_AsCharacterSymbol")
_register_global("R_baseSymbol")
_register_global("R_BaseSymbol")
_register_global("R_BraceSymbol")
_register_global("R_Bracket2Symbol")
_register_global("R_BracketSymbol")
_register_global("R_ClassSymbol")
_register_global("R_DeviceSymbol")
_register_global("R_DimNamesSymbol")
_register_global("R_DimSymbol")
_register_global("R_DollarSymbol")
_register_global("R_DotsSymbol")
_register_global("R_DoubleColonSymbol")
_register_global("R_DropSymbol")
_register_global("R_LastvalueSymbol")
_register_global("R_LevelsSymbol")
_register_global("R_ModeSymbol")
_register_global("R_NaRmSymbol")
_register_global("R_NameSymbol")
_register_global("R_NamesSymbol")
_register_global("R_NamespaceEnvSymbol")
_register_global("R_PackageSymbol")
_register_global("R_PreviousSymbol")
_register_global("R_QuoteSymbol")
_register_global("R_RowNamesSymbol")
_register_global("R_SeedsSymbol")
_register_global("R_SortListSymbol")
_register_global("R_SourceSymbol")
_register_global("R_SpecSymbol")
_register_global("R_TripleColonSymbol")
_register_global("R_TspSymbol")

_register_global("R_dot_defined")
_register_global("R_dot_Method")
_register_global("R_dot_packageName")
_register_global("R_dot_target")
_register_global("R_dot_Generic")

# Missing Values

_register_global("R_NaString")
_register_global("R_BlankString")
_register_global("R_BlankScalarString")


# srcref related functions

_register("R_GetCurrentSrcref", SEXP, [c_int])
_register("R_GetSrcFilename", SEXP, [SEXP])


# Type Coercions of all kinds

_register("Rf_asChar", SEXP, [SEXP])
_register("Rf_coerceVector", SEXP, [SEXP])
_register("Rf_PairToVectorList", SEXP, [SEXP])
_register("Rf_VectorToPairList", SEXP, [SEXP])
_register("Rf_asCharacterFactor", SEXP, [SEXP])
_register("Rf_asLogical", c_int, [SEXP])
_register("Rf_asInteger", c_int, [SEXP])
_register("Rf_asReal", c_double, [SEXP])
_register("Rf_asComplex", Rcomplex, [SEXP])


# Other Internally Used Functions

_register("Rf_acopy_string", c_char_p, [c_char_p],)
_register("Rf_addMissingVarsToNewEnv", SEXP, [SEXP, SEXP])
_register("Rf_alloc3DArray", SEXP, [SEXPTYPE, c_int, c_int, c_int])
_register("Rf_allocArray", SEXP, [SEXPTYPE, SEXP])
_register("Rf_allocFormalsList2", SEXP, [SEXP, SEXP])
_register("Rf_allocFormalsList3", SEXP, [SEXP, SEXP, SEXP])
_register("Rf_allocFormalsList4", SEXP, [SEXP, SEXP, SEXP, SEXP])
_register("Rf_allocFormalsList5", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP])
_register("Rf_allocFormalsList6", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP, SEXP])
_register("Rf_allocList", SEXP, [c_int])
_register("Rf_allocMatrix", SEXP, [SEXPTYPE, c_int, c_int])
_register("Rf_allocS4Object", SEXP, [])
_register("Rf_allocSExp", SEXP, [SEXPTYPE])
_register("Rf_allocVector", SEXP, [SEXPTYPE, R_xlen_t])
_register("Rf_allocVector3", SEXP, [SEXPTYPE, R_xlen_t, c_void_p])
_register("Rf_any_duplicated", R_xlen_t, [SEXP, c_int])
_register("Rf_any_duplicated3", R_xlen_t, [SEXP, SEXP, c_int])
_register("Rf_applyClosure", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP])
_register("Rf_arraySubscript", SEXP, [c_int, SEXP, SEXP, CFUNCTYPE(SEXP, SEXP, SEXP), CFUNCTYPE(SEXP, SEXP, c_int)])
_register("Rf_classgets", SEXP, [SEXP, SEXP])
_register("Rf_fixSubset3Args", SEXP, [SEXP, SEXP, SEXP, POINTER(SEXP)])
_register("Rf_copyMatrix", None, [SEXP, SEXP, c_int])
_register("Rf_copyListMatrix", None, [SEXP, SEXP, c_int])
_register("Rf_copyMostAttrib", None, [SEXP, SEXP])
_register("Rf_copyVector", None, [SEXP, SEXP])
_register("Rf_countContexts", c_int, [c_int, c_int])
_register("Rf_CreateTag", SEXP, [SEXP])
_register("Rf_defineVar", None, [SEXP, SEXP, SEXP])
_register("Rf_dimgets", SEXP, [SEXP, SEXP])
_register("Rf_dimnamesgets", SEXP, [SEXP, SEXP])
_register("Rf_DropDims", SEXP, [SEXP])
_register("Rf_duplicate", SEXP, [SEXP])
_register("Rf_shallow_duplicate", SEXP, [SEXP])
_register("Rf_lazy_duplicate", SEXP, [SEXP])
_register("Rf_duplicated", SEXP, [SEXP, c_int])
_register("R_envHasNoSpecialSymbols", c_int, [SEXP])
_register("Rf_eval", SEXP, [SEXP, SEXP])
_register("Rf_ExtractSubset", SEXP, [SEXP, SEXP, SEXP])
_register("Rf_findFun", SEXP, [SEXP, SEXP])
_register("Rf_findFun3", SEXP, [SEXP, SEXP, SEXP])
_register("Rf_findFunctionForBody", None, [SEXP])
_register("Rf_findVar", SEXP, [SEXP, SEXP])
_register("Rf_findVarInFrame", SEXP, [SEXP, SEXP])
_register("Rf_findVarInFrame3", SEXP, [SEXP, SEXP, c_int])
_register("Rf_getAttrib", SEXP, [SEXP, SEXP])
_register("Rf_GetArrayDimnames", SEXP, [SEXP])
_register("Rf_GetColNames", SEXP, [SEXP])
_register("Rf_GetMatrixDimnames", None, [SEXP, POINTER(SEXP), POINTER(SEXP), POINTER(c_char_p), POINTER(c_char_p)])
_register("Rf_GetOption1", SEXP, [SEXP])
_register("Rf_GetOptionDigits", c_int, [])
_register("Rf_GetOptionWidth", c_int, [])
_register("Rf_GetRowNames", SEXP, [SEXP])
_register("Rf_gsetVar", None, [SEXP, SEXP, SEXP])
_register("Rf_install", SEXP, [c_char_p])
_register("Rf_installChar", SEXP, [SEXP])
_register("Rf_installNoTrChar", SEXP, [SEXP])
_register("Rf_installDDVAL", SEXP, [c_int])
_register("Rf_installS3Signature", SEXP, [c_char_p, c_char_p])
_register("Rf_isFree", c_int, [SEXP])
_register("Rf_isOrdered", c_int, [SEXP])
_register("Rf_isUnmodifiedSpecSym", c_int, [SEXP, SEXP])
_register("Rf_isUnordered", c_int, [SEXP])
_register("Rf_isUnsorted", c_int, [SEXP])
_register("Rf_lengthgets", SEXP, [SEXP, R_len_t])
_register("Rf_xlengthgets", SEXP, [SEXP, R_xlen_t])
_register("R_lsInternal", SEXP, [SEXP, c_int])
_register("R_lsInternal3", SEXP, [SEXP, c_int, c_int])
_register("Rf_match", SEXP, [SEXP, SEXP, c_int])
_register("Rf_matchE", SEXP, [SEXP, SEXP, c_int, SEXP])
_register("Rf_namesgets", SEXP, [SEXP, SEXP])
_register("Rf_mkChar", SEXP, [c_char_p])
_register("Rf_mkCharLen", SEXP, [c_char_p, c_int])
_register("Rf_NonNullStringMatch", c_int, [SEXP, SEXP])
_register("Rf_ncols", c_int, [SEXP])
_register("Rf_nrows", c_int, [SEXP])
_register("Rf_nthcdr", SEXP, [SEXP, c_int])

# ../main/character.c

_register("R_nchar", c_int, [SEXP, c_int, c_int, c_int, c_char_p])

_register("Rf_pmatch", c_int, [SEXP, SEXP, c_int])
_register("Rf_psmatch", c_int, [c_char_p, c_char_p, c_int])
_register("R_ParseEvalString", SEXP, [c_char_p, SEXP])
_register("Rf_PrintValue", None, [SEXP])
_register("Rf_protect", SEXP, [SEXP])
_register("Rf_readS3VarsFromFrame", None, [SEXP, POINTER(SEXP), POINTER(SEXP), POINTER(SEXP), POINTER(SEXP), POINTER(SEXP), POINTER(SEXP)])
_register("Rf_setAttrib", SEXP, [SEXP, SEXP, SEXP])
_register("Rf_setSVector", None, [POINTER(SEXP), c_int, SEXP])
_register("Rf_setVar", SEXP, [SEXP, SEXP, SEXP])
_register("Rf_stringSuffix", SEXP, [SEXP, c_int])
_register("Rf_str2type", SEXPTYPE, [c_char_p])
_register("Rf_StringBlank", c_int, [SEXP])
_register("Rf_substitute", SEXP, [SEXP, SEXP])
_register("Rf_topenv", SEXP, [SEXP, SEXP])
_register("Rf_translateChar", c_char_p, [SEXP])
_register("Rf_translateChar0", c_char_p, [SEXP])
_register("Rf_translateCharUTF8", c_char_p, [SEXP])
_register("Rf_type2char", c_char_p, [SEXPTYPE])
_register("Rf_type2rstr", SEXP, [SEXPTYPE])
_register("Rf_type2str", SEXP, [SEXPTYPE])
_register("Rf_type2str_nowarn", SEXP, [SEXPTYPE])
_register("Rf_unprotect", None, [SEXP])
_register("Rf_unprotect_ptr", None, [SEXP])


# _register("R_signal_protect_error", None, [None], cname="R_signal_protect_error")
# _register("R_signal_unprotect_error", None, [None], cname="R_signal_unprotect_error")
# _register("R_signal_reprotect_error", None, [c_int], cname="R_signal_reprotect_error")

_register("R_ProtectWithIndex", SEXP, [SEXP, POINTER(c_int)])
_register("R_Reprotect", SEXP, [SEXP, c_int])

_register("R_tryEval", SEXP, [SEXP, SEXP, POINTER(c_int)])
_register("R_tryEvalSilent", SEXP, [SEXP, SEXP, POINTER(c_int)])
_register("R_curErrorBuf", c_char_p, [])

_register("Rf_isS4", c_int, [SEXP])
_register("Rf_asS4", SEXP, [SEXP, c_int, c_int])
_register("Rf_S3Class", SEXP, [SEXP])
_register("Rf_isBasicClass", c_int, [c_char_p])

_register("R_cycle_detected", c_int, [SEXP, SEXP])

_register("Rf_getCharCE", c_int, [SEXP])
_register("Rf_mkCharCE", SEXP, [c_char_p, c_int, c_int])
_register("Rf_reEnc", c_char_p, [c_char_p, c_int, c_int, c_int])

_register("R_forceAndCall", SEXP, [SEXP, c_int, SEXP])


# External pointer interface

_register("R_MakeExternalPtr", SEXP, [c_void_p, SEXP, SEXP])
_register("R_ExternalPtrAddr", c_void_p, [SEXP])
_register("R_ExternalPtrTag", SEXP, [SEXP])
_register("R_ExternalPtrProtected", SEXP, [SEXP])
_register("R_ClearExternalPtr", None, [SEXP])
_register("R_SetExternalPtrAddr", None, [SEXP, c_void_p])
_register("R_SetExternalPtrTag", None, [SEXP, SEXP])
_register("R_SetExternalPtrProtected", None, [SEXP, SEXP])
_register("R_MakeExternalPtrFn", SEXP, [c_void_p, SEXP, SEXP])
_register("R_ExternalPtrAddrFn", c_void_p, [SEXP])


# Finalization interface

_register("R_RegisterFinalizer", None, [SEXP, SEXP])
_register("R_RegisterCFinalizer", None, [SEXP, CFUNCTYPE(None, SEXP)])
_register("R_RegisterFinalizerEx", None, [SEXP, SEXP, c_int])
_register("R_RegisterCFinalizerEx", None, [SEXP, CFUNCTYPE(None, SEXP), c_int])
_register("R_RunPendingFinalizers", None, [])

# Weak reference interface


# Protected evaluation

_register("R_ToplevelExec", c_int, [CFUNCTYPE(None, c_void_p), c_void_p])
_register("R_ExecWithCleanup", SEXP, [CFUNCTYPE(SEXP, c_void_p), c_void_p, CFUNCTYPE(None, c_void_p), c_void_p])
_register("R_tryCatch", SEXP, [CFUNCTYPE(SEXP, c_void_p), c_void_p, SEXP, CFUNCTYPE(SEXP, c_void_p), c_void_p, CFUNCTYPE(None, c_void_p), c_void_p])
_register("R_tryCatchError", SEXP, [CFUNCTYPE(SEXP, c_void_p), c_void_p, CFUNCTYPE(SEXP, c_void_p), c_void_p])
_register("R_MakeUnwindCont", SEXP, [])
_register("R_ContinueUnwind", None, [SEXP])
_register("R_UnwindProtect", SEXP, [CFUNCTYPE(SEXP, c_void_p), c_void_p, CFUNCTYPE(None, c_void_p, c_int), c_void_p, SEXP])


# Environment and Binding Features

_register("R_RestoreHashCount", None, [SEXP])
_register("R_IsPackageEnv", c_int, [SEXP])
_register("R_PackageEnvName", SEXP, [SEXP])
_register("R_FindPackageEnv", SEXP, [SEXP])
_register("R_IsNamespaceEnv", c_int, [SEXP])
_register("R_NamespaceEnvSpec", SEXP, [SEXP])
_register("R_FindNamespace", SEXP, [SEXP])
_register("R_LockEnvironment", None, [SEXP, c_int])
_register("R_EnvironmentIsLocked", c_int, [SEXP])
_register("R_LockBinding", None, [SEXP, SEXP])
_register("R_unLockBinding", None, [SEXP, SEXP])
_register("R_MakeActiveBinding", None, [SEXP, SEXP, SEXP])
_register("R_BindingIsLocked", c_int, [SEXP, SEXP])
_register("R_BindingIsActive", c_int, [SEXP, SEXP])
_register("R_HasFancyBindings", c_int, [SEXP])


# ../main/errors.c


# slot management (in attrib.c)

_register("R_do_slot", SEXP, [SEXP, SEXP])
_register("R_do_slot_assign", SEXP, [SEXP, SEXP, SEXP])
_register("R_has_slot", c_int, [SEXP, SEXP])

# S3-S4 class (inheritance) (in attrib.c)

_register("R_S4_extends", SEXP, [SEXP, SEXP])

# class definition, new objects (objects.c)

_register("R_do_MAKE_CLASS", SEXP, [c_char_p])
_register("R_getClassDef", SEXP, [c_char_p])
_register("R_getClassDef_R", SEXP, [SEXP])
_register("R_has_methods_attached", c_int, [])
_register("R_isVirtualClass", c_int, [SEXP, SEXP])
_register("R_extends", c_int, [SEXP, SEXP, SEXP])
_register("R_do_new_object", SEXP, [SEXP])

# supporting  a C-level version of  is(., .)

_register("R_check_class_and_super", c_int, [SEXP, c_char_p, SEXP])
_register("R_check_class_etc", c_int, [SEXP, c_char_p])


# preserve objects across GCs

_register("R_PreserveObject", None, [SEXP])
_register("R_ReleaseObject", None, [SEXP])


# Shutdown actions

_register("R_dot_Last", None, [])
_register("R_RunExitFinalizers", None, [])


# Replacements for popen and system

_register("R_system", c_int, [c_char_p])


# R_compute_identical

_register("R_compute_identical", c_int, [SEXP, SEXP])

#  body(x) without "srcref" etc

_register("R_body_no_src", SEXP, [SEXP])

# C version of R's  indx <- order(..., na.last, decreasing)
_register("R_orderVector", None, [c_int, c_int, SEXP, c_int, c_int])
# C version of R's  indx <- order(x, na.last, decreasing)
_register("R_orderVector1", None, [c_int, c_int, SEXP, c_int, c_int])

# inlinable functions


_register("Rf_conformable", c_int, [SEXP, SEXP])
_register("Rf_elt", SEXP, [SEXP, c_int])
_register("Rf_inherits", c_int, [SEXP, c_char_p])
_register("Rf_isArray", c_int, [SEXP])
_register("Rf_isFactor", c_int, [SEXP])
_register("Rf_isFrame", c_int, [SEXP])
_register("Rf_isFunction", c_int, [SEXP])
_register("Rf_isInteger", c_int, [SEXP])
_register("Rf_isLanguage", c_int, [SEXP])
_register("Rf_isList", c_int, [SEXP])
_register("Rf_isMatrix", c_int, [SEXP])
_register("Rf_isNewList", c_int, [SEXP])
_register("Rf_isNumeric", c_int, [SEXP])
_register("Rf_isNumber", c_int, [SEXP])
_register("Rf_isPairList", c_int, [SEXP])
_register("Rf_isPrimitive", c_int, [SEXP])
_register("Rf_isTs", c_int, [SEXP])
_register("Rf_isUserBinop", c_int, [SEXP])
_register("Rf_isValidString", c_int, [SEXP])
_register("Rf_isValidStringF", c_int, [SEXP])
_register("Rf_isVector", c_int, [SEXP])
_register("Rf_isVectorAtomic", c_int, [SEXP])
_register("Rf_isVectorList", c_int, [SEXP])
_register("Rf_isVectorizable", c_int, [SEXP])
_register("Rf_lang1", SEXP, [SEXP])
_register("Rf_lang2", SEXP, [SEXP, SEXP])
_register("Rf_lang3", SEXP, [SEXP, SEXP, SEXP])
_register("Rf_lang4", SEXP, [SEXP, SEXP, SEXP, SEXP])
_register("Rf_lang5", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP])
_register("Rf_lang6", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP, SEXP])
_register("Rf_lastElt", SEXP, [SEXP])
_register("Rf_lcons", SEXP, [SEXP, SEXP])
_register("Rf_length", SEXP, [SEXP])
_register("Rf_list1", SEXP, [SEXP])
_register("Rf_list2", SEXP, [SEXP, SEXP])
_register("Rf_list3", SEXP, [SEXP, SEXP, SEXP])
_register("Rf_list4", SEXP, [SEXP, SEXP, SEXP, SEXP])
_register("Rf_list5", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP])
_register("Rf_list6", SEXP, [SEXP, SEXP, SEXP, SEXP, SEXP, SEXP])
_register("Rf_listAppend", SEXP, [SEXP, SEXP])
_register("Rf_mkNamed", SEXP, [SEXPTYPE, c_char_p])
_register("Rf_mkString", SEXP, [c_char_p])
_register("Rf_nlevels", c_int, [SEXP])
_register("Rf_stringPositionTr", c_int, [SEXP, c_char_p])
_register("Rf_ScalarComplex", SEXP, [Rcomplex])
_register("Rf_ScalarInteger", SEXP, [c_int])
_register("Rf_ScalarLogical", SEXP, [c_int])
_register("Rf_ScalarRaw", SEXP, [c_ubyte])
_register("Rf_ScalarReal", SEXP, [c_double])
_register("Rf_ScalarString", SEXP, [SEXP])
_register("Rf_xlength", R_xlen_t, [SEXP])
_register("LENGTH_EX", c_int, [SEXP, c_char_p, c_int])
_register("XLENGTH_EX", R_xlen_t, [SEXP])
_register("R_FixupRHS", SEXP, [SEXP, SEXP])


# Arith.h

_register_global("R_NaN")
_register_global("R_PosInf")
_register_global("R_NegInf")
_register_global("R_NaReal")
_register_global("R_NaInt")
_register("R_IsNA", c_int, [c_double])
_register("R_IsNaN", c_int, [c_double])
_register("R_finite", c_int, [c_double])


# Print.h

_register("Rf_formatRaw", None, [POINTER(c_ubyte), R_xlen_t, POINTER(c_int)])
_register("Rf_formatString", None, [POINTER(SEXP), R_xlen_t, POINTER(c_int), c_int])
_register("Rf_EncodeElement", c_char_p, [SEXP, c_int, c_int, c_char])
_register("Rf_EncodeElement0", c_char_p, [SEXP, c_int, c_int, c_char_p])
_register("Rf_EncodeEnvironment", SEXP, [SEXP])
_register("Rf_printArray", None, [SEXP, SEXP, c_int, c_int, SEXP])
_register("Rf_printMatrix", None, [SEXP, c_int, SEXP, c_int, c_int, SEXP, SEXP, c_char_p, c_char_p])
_register("Rf_printNamedVector", None, [SEXP, SEXP, c_int, c_char_p])
_register("Rf_printVector", None, [SEXP, c_int, c_int])


# Parse.h

_register("R_ParseVector", SEXP, [SEXP, c_int, POINTER(c_int), SEXP])

# Memory.h

_register("R_gc", None, [])
_register("R_gc_running", c_int, [])
_register("R_alloc", c_void_p, [c_size_t, c_int])
_register("R_allocLD", c_void_p, [c_size_t])


# Error.h


_register("Rf_error", None, None)
_register("Rf_warning", None, None)


def bootstrap(libR, rversion, verbose=True):
    for name, (sign, setter) in _signatures.items():
        try:
            f = getattr(libR, sign.cname)
            f.restype = sign.restype
            if sign.argtypes is not None:
                f.argtypes = sign.argtypes
            setter(f)
        except Exception:
            setter(notavaiable)
            if verbose:
                print("warning: cannot import {}".format(name))

    for name, var in _globals.items():
        var.value = cglobal(name, libR, c_void_p).value

    types.internals = internals
    types.interface = interface
