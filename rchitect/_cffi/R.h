#ifndef R_H__
#define R_H__

#include <stddef.h>

#ifdef _WIN32
#define RAPI_EXTERN __declspec(dllimport) extern
#else
#define RAPI_EXTERN extern
#endif
#define RAPI_FUNC extern
#define RGRAPHAPP_FUNC extern

// begin cdef
typedef unsigned char Rbyte;

typedef enum { Bytes, Chars, Width } nchar_type;
typedef void *(*DL_FUNC)();

typedef int R_len_t;

// FIXME: when size of size_t <= 4
typedef ptrdiff_t R_xlen_t;

typedef unsigned int SEXPTYPE;

static const unsigned int NILSXP = 0;
static const unsigned int SYMSXP = 1;
static const unsigned int LISTSXP = 2;
static const unsigned int CLOSXP = 3;
static const unsigned int ENVSXP = 4;
static const unsigned int PROMSXP = 5;
static const unsigned int LANGSXP = 6;
static const unsigned int SPECIALSXP = 7;
static const unsigned int BUILTINSXP = 8;
static const unsigned int CHARSXP = 9;
static const unsigned int LGLSXP = 10;
static const unsigned int INTSXP = 13;
static const unsigned int REALSXP = 14;
static const unsigned int CPLXSXP = 15;
static const unsigned int STRSXP = 16;
static const unsigned int DOTSXP = 17;
static const unsigned int ANYSXP = 18;
static const unsigned int VECSXP = 19;
static const unsigned int EXPRSXP = 20;
static const unsigned int BCODESXP = 21;
static const unsigned int EXTPTRSXP = 22;
static const unsigned int WEAKREFSXP = 23;
static const unsigned int RAWSXP = 24;
static const unsigned int S4SXP = 25;
static const unsigned int NEWSXP = 30;
static const unsigned int FREESXP = 31;
static const unsigned int FUNSXP = 99;

typedef struct {
    double r;
    double i;
} Rcomplex;

typedef enum { FALSE = 0, TRUE } Rboolean;

struct sxpinfo_struct {
    SEXPTYPE type : 5;
    unsigned int scalar : 1;
    unsigned int obj : 1;
    unsigned int alt : 1;
    unsigned int gp : 16;
    unsigned int mark : 1;
    unsigned int debug : 1;
    unsigned int trace : 1;
    unsigned int spare : 1;
    unsigned int gcgen : 1;
    unsigned int gccls : 3;
    unsigned int named : 16;
    unsigned int extra : 16;
};

struct vecsxp_struct {
    R_xlen_t length;
    R_xlen_t truelength;
};

struct primsxp_struct {
    int offset;
};

struct symsxp_struct {
    struct SEXPREC *pname;
    struct SEXPREC *value;
    struct SEXPREC *internal;
};

struct listsxp_struct {
    struct SEXPREC *carval;
    struct SEXPREC *cdrval;
    struct SEXPREC *tagval;
};

struct envsxp_struct {
    struct SEXPREC *frame;
    struct SEXPREC *enclos;
    struct SEXPREC *hashtab;
};

struct closxp_struct {
    struct SEXPREC *formals;
    struct SEXPREC *body;
    struct SEXPREC *env;
};

struct promsxp_struct {
    struct SEXPREC *value;
    struct SEXPREC *expr;
    struct SEXPREC *env;
};

typedef struct SEXPREC {
    struct sxpinfo_struct sxpinfo;
    struct SEXPREC *attrib;
    struct SEXPREC *gengc_next_node, *gengc_prev_node;
    union {
        struct primsxp_struct primsxp;
        struct symsxp_struct symsxp;
        struct listsxp_struct listsxp;
        struct envsxp_struct envsxp;
        struct closxp_struct closxp;
        struct promsxp_struct promsxp;
    } u;
} SEXPREC;

typedef struct SEXPREC *SEXP;

// Rinternals.h
RAPI_FUNC const char *R_CHAR(SEXP x);
RAPI_FUNC Rboolean Rf_isNull(SEXP s);
RAPI_FUNC Rboolean Rf_isSymbol(SEXP s);
RAPI_FUNC Rboolean Rf_isLogical(SEXP s);
RAPI_FUNC Rboolean Rf_isReal(SEXP s);
RAPI_FUNC Rboolean Rf_isComplex(SEXP s);
RAPI_FUNC Rboolean Rf_isExpression(SEXP s);
RAPI_FUNC Rboolean Rf_isEnvironment(SEXP s);
RAPI_FUNC Rboolean Rf_isString(SEXP s);
RAPI_FUNC Rboolean Rf_isObject(SEXP s);

RAPI_FUNC int TYPEOF(SEXP x);

RAPI_FUNC int LENGTH(SEXP x);
RAPI_FUNC R_xlen_t XLENGTH(SEXP x);
RAPI_FUNC int IS_LONG_VEC(SEXP x);

// Vector Access Functions
RAPI_FUNC int *LOGICAL(SEXP x);
RAPI_FUNC int *INTEGER(SEXP x);
RAPI_FUNC Rbyte *RAW(SEXP x);
RAPI_FUNC double *REAL(SEXP x);
RAPI_FUNC Rcomplex *COMPLEX(SEXP x);
RAPI_FUNC SEXP STRING_ELT(SEXP x, R_xlen_t i);
RAPI_FUNC SEXP VECTOR_ELT(SEXP x, R_xlen_t i);
RAPI_FUNC void SET_STRING_ELT(SEXP x, R_xlen_t i, SEXP v);
RAPI_FUNC SEXP SET_VECTOR_ELT(SEXP x, R_xlen_t i, SEXP v);

// List Access
RAPI_FUNC SEXP Rf_cons(SEXP, SEXP);
RAPI_FUNC SEXP Rf_lcons(SEXP, SEXP);
RAPI_FUNC SEXP TAG(SEXP e);
RAPI_FUNC SEXP CAR(SEXP e);
RAPI_FUNC SEXP CDR(SEXP e);
RAPI_FUNC SEXP CAAR(SEXP e);
RAPI_FUNC SEXP CDAR(SEXP e);
RAPI_FUNC SEXP CADR(SEXP e);
RAPI_FUNC SEXP CDDR(SEXP e);
RAPI_FUNC SEXP CDDDR(SEXP e);
RAPI_FUNC SEXP CADDR(SEXP e);
RAPI_FUNC SEXP CADDDR(SEXP e);
RAPI_FUNC SEXP CAD4R(SEXP e);
RAPI_FUNC void SET_TAG(SEXP x, SEXP y);
RAPI_FUNC SEXP SETCAR(SEXP x, SEXP y);
RAPI_FUNC SEXP SETCDR(SEXP x, SEXP y);
RAPI_FUNC SEXP SETCADR(SEXP x, SEXP y);
RAPI_FUNC SEXP SETCADDR(SEXP x, SEXP y);
RAPI_FUNC SEXP SETCADDDR(SEXP x, SEXP y);
RAPI_FUNC SEXP SETCAD4R(SEXP e, SEXP y);

RAPI_FUNC SEXP PRINTNAME(SEXP x);

RAPI_FUNC SEXP Rf_protect(SEXP);
RAPI_FUNC void Rf_unprotect(int);

RAPI_EXTERN SEXP R_GlobalEnv;
RAPI_EXTERN SEXP R_EmptyEnv;
RAPI_EXTERN SEXP R_BaseEnv;
RAPI_EXTERN SEXP R_BaseNamespace;
RAPI_EXTERN SEXP R_NamespaceRegistry;
RAPI_EXTERN SEXP R_Srcref;
RAPI_EXTERN SEXP R_NilValue;
RAPI_EXTERN SEXP R_UnboundValue;
RAPI_EXTERN SEXP R_MissingArg;
RAPI_EXTERN SEXP R_InBCInterpreter;
RAPI_EXTERN SEXP R_CurrentExpression;
RAPI_EXTERN SEXP R_AsCharacterSymbol;
RAPI_EXTERN SEXP R_baseSymbol;
RAPI_EXTERN SEXP R_BaseSymbol;
RAPI_EXTERN SEXP R_BraceSymbol;
RAPI_EXTERN SEXP R_Bracket2Symbol;
RAPI_EXTERN SEXP R_BracketSymbol;
RAPI_EXTERN SEXP R_ClassSymbol;
RAPI_EXTERN SEXP R_DeviceSymbol;
RAPI_EXTERN SEXP R_DimNamesSymbol;
RAPI_EXTERN SEXP R_DimSymbol;
RAPI_EXTERN SEXP R_DollarSymbol;
RAPI_EXTERN SEXP R_DotsSymbol;
RAPI_EXTERN SEXP R_DoubleColonSymbol;
RAPI_EXTERN SEXP R_DropSymbol;
RAPI_EXTERN SEXP R_LastvalueSymbol;
RAPI_EXTERN SEXP R_LevelsSymbol;
RAPI_EXTERN SEXP R_ModeSymbol;
RAPI_EXTERN SEXP R_NaRmSymbol;
RAPI_EXTERN SEXP R_NameSymbol;
RAPI_EXTERN SEXP R_NamesSymbol;
RAPI_EXTERN SEXP R_NamespaceEnvSymbol;
RAPI_EXTERN SEXP R_PackageSymbol;
RAPI_EXTERN SEXP R_PreviousSymbol;
RAPI_EXTERN SEXP R_QuoteSymbol;
RAPI_EXTERN SEXP R_RowNamesSymbol;
RAPI_EXTERN SEXP R_SeedsSymbol;
RAPI_EXTERN SEXP R_SortListSymbol;
RAPI_EXTERN SEXP R_SourceSymbol;
RAPI_EXTERN SEXP R_SpecSymbol;
RAPI_EXTERN SEXP R_TripleColonSymbol;
RAPI_EXTERN SEXP R_TspSymbol;
RAPI_EXTERN SEXP R_dot_defined;
RAPI_EXTERN SEXP R_dot_Method;
RAPI_EXTERN SEXP R_dot_packageName;
RAPI_EXTERN SEXP R_dot_target;
RAPI_EXTERN SEXP R_dot_Generic;
RAPI_EXTERN SEXP R_NaString;
RAPI_EXTERN SEXP R_BlankString;
RAPI_EXTERN SEXP R_BlankScalarString;

RAPI_FUNC SEXP Rf_asChar(SEXP);
RAPI_FUNC SEXP Rf_coerceVector(SEXP, SEXPTYPE);
RAPI_FUNC SEXP Rf_PairToVectorList(SEXP x);
RAPI_FUNC SEXP Rf_VectorToPairList(SEXP x);
RAPI_FUNC SEXP Rf_asCharacterFactor(SEXP x);
RAPI_FUNC int Rf_asLogical(SEXP x);
RAPI_FUNC int Rf_asInteger(SEXP x);
RAPI_FUNC double Rf_asReal(SEXP x);
RAPI_FUNC Rcomplex Rf_asComplex(SEXP x);

RAPI_FUNC char *Rf_acopy_string(const char *);
RAPI_FUNC SEXP Rf_alloc3DArray(SEXPTYPE, int, int, int);
RAPI_FUNC SEXP Rf_allocArray(SEXPTYPE, SEXP);
RAPI_FUNC SEXP Rf_allocMatrix(SEXPTYPE, int, int);
RAPI_FUNC SEXP Rf_allocList(int);
RAPI_FUNC SEXP Rf_allocS4Object(void);
RAPI_FUNC SEXP Rf_allocSExp(SEXPTYPE);
RAPI_FUNC SEXP Rf_allocVector3(SEXPTYPE, R_xlen_t, void *);
RAPI_FUNC R_xlen_t Rf_any_duplicated(SEXP x, Rboolean from_last);
RAPI_FUNC R_xlen_t Rf_any_duplicated3(SEXP x, SEXP incomp, Rboolean from_last);
RAPI_FUNC SEXP Rf_classgets(SEXP, SEXP);
RAPI_FUNC void Rf_copyMatrix(SEXP, SEXP, Rboolean);
RAPI_FUNC void Rf_copyListMatrix(SEXP, SEXP, Rboolean);
RAPI_FUNC void Rf_copyMostAttrib(SEXP, SEXP);
RAPI_FUNC void Rf_copyVector(SEXP, SEXP);
RAPI_FUNC void Rf_defineVar(SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_dimgets(SEXP, SEXP);
RAPI_FUNC SEXP Rf_dimnamesgets(SEXP, SEXP);
RAPI_FUNC SEXP Rf_duplicate(SEXP);
RAPI_FUNC SEXP Rf_shallow_duplicate(SEXP);

RAPI_FUNC SEXP Rf_duplicated(SEXP, Rboolean);
RAPI_FUNC SEXP Rf_eval(SEXP, SEXP);
RAPI_FUNC SEXP Rf_findFun(SEXP, SEXP);
RAPI_FUNC SEXP Rf_findVar(SEXP, SEXP);
RAPI_FUNC SEXP Rf_findVarInFrame(SEXP, SEXP);
RAPI_FUNC SEXP Rf_findVarInFrame3(SEXP, SEXP, Rboolean);
RAPI_FUNC SEXP Rf_getAttrib(SEXP, SEXP);
RAPI_FUNC SEXP Rf_GetArrayDimnames(SEXP);
RAPI_FUNC SEXP Rf_GetColNames(SEXP);
RAPI_FUNC void Rf_GetMatrixDimnames(SEXP, SEXP *, SEXP *, const char **, const char **);
RAPI_FUNC SEXP Rf_GetOption1(SEXP);
RAPI_FUNC SEXP Rf_GetRowNames(SEXP);
RAPI_FUNC void Rf_gsetVar(SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_install(const char *);
RAPI_FUNC SEXP Rf_installChar(SEXP);
RAPI_FUNC Rboolean Rf_isOrdered(SEXP);
RAPI_FUNC Rboolean Rf_isUnordered(SEXP);
RAPI_FUNC Rboolean Rf_isUnsorted(SEXP, Rboolean);
RAPI_FUNC SEXP Rf_lengthgets(SEXP, R_len_t);
RAPI_FUNC SEXP Rf_xlengthgets(SEXP, R_xlen_t);
RAPI_FUNC SEXP R_lsInternal(SEXP, Rboolean);
RAPI_FUNC SEXP R_lsInternal3(SEXP, Rboolean, Rboolean);
RAPI_FUNC SEXP Rf_match(SEXP, SEXP, int);
RAPI_FUNC SEXP Rf_matchE(SEXP, SEXP, int, SEXP);
RAPI_FUNC SEXP Rf_namesgets(SEXP, SEXP);
RAPI_FUNC SEXP Rf_mkChar(const char *);
RAPI_FUNC SEXP Rf_mkCharLen(const char *, int);
RAPI_FUNC int Rf_ncols(SEXP);
RAPI_FUNC int Rf_nrows(SEXP);
RAPI_FUNC SEXP Rf_nthcdr(SEXP, int);

RAPI_FUNC Rboolean Rf_pmatch(SEXP, SEXP, Rboolean);
RAPI_FUNC Rboolean Rf_psmatch(const char *, const char *, Rboolean);
RAPI_FUNC SEXP R_ParseEvalString(const char *, SEXP);
RAPI_FUNC void Rf_PrintValue(SEXP);
RAPI_FUNC SEXP Rf_setAttrib(SEXP, SEXP, SEXP);
RAPI_FUNC void Rf_setVar(SEXP, SEXP, SEXP);
RAPI_FUNC SEXPTYPE Rf_str2type(const char *);
RAPI_FUNC Rboolean Rf_StringBlank(SEXP);
RAPI_FUNC SEXP Rf_substitute(SEXP, SEXP);
RAPI_FUNC SEXP Rf_topenv(SEXP, SEXP);
RAPI_FUNC const char *Rf_translateChar(SEXP);
RAPI_FUNC const char *Rf_translateCharUTF8(SEXP);
RAPI_FUNC const char *Rf_type2char(SEXPTYPE);
RAPI_FUNC SEXP Rf_type2rstr(SEXPTYPE);
RAPI_FUNC SEXP Rf_type2str(SEXPTYPE);
RAPI_FUNC SEXP Rf_type2str_nowarn(SEXPTYPE);

RAPI_FUNC SEXP R_tryEval(SEXP, SEXP, int *);
RAPI_FUNC SEXP R_tryEvalSilent(SEXP, SEXP, int *);
RAPI_FUNC const char *R_curErrorBuf(void);

RAPI_FUNC Rboolean Rf_isS4(SEXP);
RAPI_FUNC SEXP Rf_asS4(SEXP, Rboolean, int);

typedef enum { CE_NATIVE = 0, CE_UTF8 = 1, CE_LATIN1 = 2, CE_BYTES = 3, CE_SYMBOL = 5, CE_ANY = 99 } cetype_t;

RAPI_FUNC cetype_t Rf_getCharCE(SEXP);
RAPI_FUNC SEXP Rf_mkCharCE(const char *, cetype_t);
RAPI_FUNC SEXP Rf_mkCharLenCE(const char *, int, cetype_t);
RAPI_FUNC const char *Rf_reEnc(const char *x, cetype_t ce_in, cetype_t ce_out, int subst);

RAPI_FUNC SEXP R_MakeExternalPtr(void *p, SEXP tag, SEXP prot);
RAPI_FUNC void *R_ExternalPtrAddr(SEXP s);
RAPI_FUNC SEXP R_ExternalPtrTag(SEXP s);
RAPI_FUNC SEXP R_ExternalPtrProtected(SEXP s);
RAPI_FUNC void R_ClearExternalPtr(SEXP s);
RAPI_FUNC void R_SetExternalPtrAddr(SEXP s, void *p);
RAPI_FUNC void R_SetExternalPtrTag(SEXP s, SEXP tag);
RAPI_FUNC void R_SetExternalPtrProtected(SEXP s, SEXP p);
RAPI_FUNC SEXP R_MakeExternalPtrFn(DL_FUNC p, SEXP tag, SEXP prot);
RAPI_FUNC DL_FUNC R_ExternalPtrAddrFn(SEXP s);

typedef void (*R_CFinalizer_t)(SEXP);

RAPI_FUNC void R_RegisterFinalizer(SEXP s, SEXP fun);
RAPI_FUNC void R_RegisterCFinalizer(SEXP s, R_CFinalizer_t fun);
RAPI_FUNC void R_RegisterFinalizerEx(SEXP s, SEXP fun, Rboolean onexit);
RAPI_FUNC void R_RegisterCFinalizerEx(SEXP s, R_CFinalizer_t fun, Rboolean onexit);
RAPI_FUNC void R_RunPendingFinalizers(void);

RAPI_FUNC SEXP R_MakeWeakRef(SEXP key, SEXP val, SEXP fin, Rboolean onexit);
RAPI_FUNC SEXP R_MakeWeakRefC(SEXP key, SEXP val, R_CFinalizer_t fin, Rboolean onexit);
RAPI_FUNC SEXP R_WeakRefKey(SEXP w);
RAPI_FUNC SEXP R_WeakRefValue(SEXP w);
RAPI_FUNC void R_RunWeakRefFinalizer(SEXP w);

RAPI_FUNC SEXP R_PromiseExpr(SEXP);
RAPI_FUNC SEXP R_ClosureExpr(SEXP);
RAPI_FUNC SEXP R_BytecodeExpr(SEXP e);

RAPI_FUNC Rboolean R_ToplevelExec(void (*fun)(void *), void *data);
RAPI_FUNC SEXP R_tryCatch(SEXP (*)(void *), void *, SEXP, SEXP (*)(SEXP, void *), void *, void (*)(void *), void *);
RAPI_FUNC SEXP R_tryCatchError(SEXP (*)(void *), void *, SEXP (*)(SEXP, void *), void *);

RAPI_FUNC Rboolean R_IsPackageEnv(SEXP rho);
RAPI_FUNC SEXP R_PackageEnvName(SEXP rho);
RAPI_FUNC Rboolean R_IsNamespaceEnv(SEXP rho);
RAPI_FUNC SEXP R_NamespaceEnvSpec(SEXP rho);
RAPI_FUNC SEXP R_FindNamespace(SEXP info);
RAPI_FUNC void R_LockEnvironment(SEXP env, Rboolean bindings);
RAPI_FUNC Rboolean R_EnvironmentIsLocked(SEXP env);
RAPI_FUNC void R_LockBinding(SEXP sym, SEXP env);
RAPI_FUNC void R_unLockBinding(SEXP sym, SEXP env);
RAPI_FUNC void R_MakeActiveBinding(SEXP sym, SEXP fun, SEXP env);
RAPI_FUNC Rboolean R_BindingIsLocked(SEXP sym, SEXP env);
RAPI_FUNC Rboolean R_BindingIsActive(SEXP sym, SEXP env);

RAPI_FUNC void Rf_errorcall(SEXP, const char *, ...);
RAPI_FUNC void Rf_warningcall(SEXP, const char *, ...);

RAPI_FUNC SEXP R_do_slot(SEXP obj, SEXP name);
RAPI_FUNC SEXP R_do_slot_assign(SEXP obj, SEXP name, SEXP value);
RAPI_FUNC int R_has_slot(SEXP obj, SEXP name);

RAPI_FUNC void R_PreserveObject(SEXP);
RAPI_FUNC void R_ReleaseObject(SEXP);

RAPI_FUNC void R_dot_Last(void);
RAPI_FUNC void R_RunExitFinalizers(void);

RAPI_FUNC Rboolean R_compute_identical(SEXP, SEXP, int);

RAPI_FUNC SEXP Rf_allocVector(SEXPTYPE, R_xlen_t);
RAPI_FUNC SEXP Rf_elt(SEXP, int);
RAPI_FUNC Rboolean Rf_inherits(SEXP, const char *);
RAPI_FUNC Rboolean Rf_isArray(SEXP);
RAPI_FUNC Rboolean Rf_isFactor(SEXP);
RAPI_FUNC Rboolean Rf_isFrame(SEXP);
RAPI_FUNC Rboolean Rf_isFunction(SEXP);
RAPI_FUNC Rboolean Rf_isInteger(SEXP);
RAPI_FUNC Rboolean Rf_isLanguage(SEXP);
RAPI_FUNC Rboolean Rf_isList(SEXP);
RAPI_FUNC Rboolean Rf_isMatrix(SEXP);
RAPI_FUNC Rboolean Rf_isNewList(SEXP);
RAPI_FUNC Rboolean Rf_isNumber(SEXP);
RAPI_FUNC Rboolean Rf_isNumeric(SEXP);
RAPI_FUNC Rboolean Rf_isPairList(SEXP);
RAPI_FUNC Rboolean Rf_isPrimitive(SEXP);
RAPI_FUNC Rboolean Rf_isTs(SEXP);
RAPI_FUNC Rboolean Rf_isVector(SEXP);
RAPI_FUNC Rboolean Rf_isVectorAtomic(SEXP);
RAPI_FUNC Rboolean Rf_isVectorList(SEXP);
RAPI_FUNC Rboolean Rf_isVectorizable(SEXP);
RAPI_FUNC SEXP Rf_lang1(SEXP);
RAPI_FUNC SEXP Rf_lang2(SEXP, SEXP);
RAPI_FUNC SEXP Rf_lang3(SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_lang4(SEXP, SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_lang5(SEXP, SEXP, SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_lang6(SEXP, SEXP, SEXP, SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_lastElt(SEXP);
RAPI_FUNC R_len_t Rf_length(SEXP);
RAPI_FUNC SEXP Rf_list1(SEXP);
RAPI_FUNC SEXP Rf_list2(SEXP, SEXP);
RAPI_FUNC SEXP Rf_list3(SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_list4(SEXP, SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_list5(SEXP, SEXP, SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_list6(SEXP, SEXP, SEXP, SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_listAppend(SEXP, SEXP);
RAPI_FUNC SEXP Rf_mkNamed(SEXPTYPE, const char **);
RAPI_FUNC SEXP Rf_mkString(const char *);
RAPI_FUNC int Rf_nlevels(SEXP);
RAPI_FUNC SEXP Rf_ScalarComplex(Rcomplex);
RAPI_FUNC SEXP Rf_ScalarInteger(int);
RAPI_FUNC SEXP Rf_ScalarLogical(int);
RAPI_FUNC SEXP Rf_ScalarRaw(Rbyte);
RAPI_FUNC SEXP Rf_ScalarReal(double);
RAPI_FUNC SEXP Rf_ScalarString(SEXP);
RAPI_FUNC R_xlen_t Rf_xlength(SEXP);

// Arith.h
RAPI_FUNC int R_IsNA(double);
RAPI_FUNC int R_IsNaN(double);
RAPI_FUNC int R_finite(double);

// Parse.h
typedef enum { PARSE_NULL, PARSE_OK, PARSE_INCOMPLETE, PARSE_ERROR, PARSE_EOF } ParseStatus;

RAPI_FUNC SEXP R_ParseVector(SEXP, int, ParseStatus *, SEXP);

// Memory.h
RAPI_FUNC void *vmaxget(void);
RAPI_FUNC void vmaxset(const void *);

RAPI_FUNC void R_gc(void);

RAPI_FUNC char *R_alloc(size_t, int);
RAPI_FUNC long double *R_allocLD(size_t nelem);

// Error.h
RAPI_FUNC void Rf_error(const char *, ...);
RAPI_FUNC void Rf_warning(const char *, ...);
RAPI_FUNC void R_ShowMessage(const char *s);

// Defn.h
RAPI_FUNC void R_ProcessEvents(void);
RAPI_FUNC SEXP Rf_NewEnvironment(SEXP, SEXP, SEXP);
RAPI_FUNC SEXP R_data_class(SEXP, Rboolean);

// Utils.h
RAPI_FUNC void R_CheckUserInterrupt(void);

// RStartup.h
typedef struct {
    Rboolean R_Quiet;
    Rboolean R_Slave;
    Rboolean R_Interactive;
    Rboolean R_Verbose;
    Rboolean LoadSiteFile;
    Rboolean LoadInitFile;
    Rboolean DebugInitFile;
    int RestoreAction;
    int SaveAction;
    size_t vsize;
    size_t nsize;
    size_t max_vsize;
    size_t max_nsize;
    size_t ppsize;
    int NoRenviron;
    char *rhome;
    char *home;
    // we use _ReadConsole and _WriteConsole to avoid name collision
    int (*_ReadConsole)(const char *, unsigned char *, int, int);
    void (*_WriteConsole)(const char *, int);
    void (*CallBack)(void);
    void (*ShowMessage)(const char *);
    int (*YesNoCancel)(const char *);
    void (*Busy)(int);
    int CharacterMode;
    void (*WriteConsoleEx)(const char *, int, int);
} structRstart;
typedef structRstart *Rstart;

RAPI_FUNC void R_DefParams(Rstart);
RAPI_FUNC void R_SetParams(Rstart);
RAPI_FUNC void R_set_command_line_arguments(int argc, char **argv);

// Rinterface.h
RAPI_EXTERN int R_SignalHandlers;

// Rembedded.h
RAPI_FUNC int Rf_initialize_R(int ac, char **av);
RAPI_FUNC void setup_Rmainloop(void);
RAPI_FUNC void run_Rmainloop(void);

// Rdynload.h
typedef struct {
    const char *name;
    DL_FUNC fun;
    int numArgs;
} R_CallMethodDef;
typedef struct _DllInfo DllInfo;

typedef R_CallMethodDef R_ExternalMethodDef;
RAPI_FUNC DllInfo *R_getEmbeddingDllInfo(void);
RAPI_FUNC int R_registerRoutines(DllInfo *, void *, void *, void *, void *);

// end cdef

#ifdef _WIN32
// begin win cdef
RAPI_FUNC char *get_R_HOME(void);
RAPI_FUNC char *getRUser(void);
RAPI_EXTERN int UserBreak;
RAPI_EXTERN int CharacterMode;
RAPI_EXTERN int EmitEmbeddedUTF8;
RGRAPHAPP_FUNC int GA_peekevent(void);
RGRAPHAPP_FUNC int GA_initapp(int, char **);
// end win cdef
#else
// begin unix cdef
// eventloop.h
RAPI_EXTERN void *R_InputHandlers;
RAPI_EXTERN void (*R_PolledEvents)(void);

RAPI_FUNC void *R_checkActivity(int usec, int ignore_stdin);
RAPI_FUNC void R_runHandlers(void *handlers, void *mask);

RAPI_EXTERN int R_interrupts_pending;

// Rinterface.h callbacks
RAPI_EXTERN void *R_Outputfile;
RAPI_EXTERN void *R_Consolefile;
RAPI_EXTERN void (*ptr_R_Suicide)(const char *);
RAPI_EXTERN void (*ptr_R_ShowMessage)(const char *);
RAPI_EXTERN int (*ptr_R_ReadConsole)(const char *, unsigned char *, int, int);
RAPI_EXTERN void (*ptr_R_WriteConsole)(const char *, int);
RAPI_EXTERN void (*ptr_R_WriteConsoleEx)(const char *, int, int);
RAPI_EXTERN void (*ptr_R_ResetConsole)(void);
RAPI_EXTERN void (*ptr_R_FlushConsole)(void);
RAPI_EXTERN void (*ptr_R_ClearerrConsole)(void);
RAPI_EXTERN void (*ptr_R_Busy)(int);
RAPI_EXTERN void (*ptr_R_CleanUp)(int, int, int);
RAPI_EXTERN int (*ptr_R_ShowFiles)(int, const char **, const char **, const char *, Rboolean, const char *);
RAPI_EXTERN int (*ptr_R_ChooseFile)(int, char *, int);
RAPI_EXTERN int (*ptr_R_EditFile)(const char *);
RAPI_EXTERN void (*ptr_R_loadhistory)(SEXP, SEXP, SEXP, SEXP);
RAPI_EXTERN void (*ptr_R_savehistory)(SEXP, SEXP, SEXP, SEXP);
RAPI_EXTERN void (*ptr_R_addhistory)(SEXP, SEXP, SEXP, SEXP);
RAPI_EXTERN int (*ptr_R_EditFiles)(int, const char **, const char **, const char *);
RAPI_EXTERN SEXP (*ptr_do_selectlist)(SEXP, SEXP, SEXP, SEXP);
RAPI_EXTERN SEXP (*ptr_do_dataentry)(SEXP, SEXP, SEXP, SEXP);
RAPI_EXTERN SEXP (*ptr_do_dataviewer)(SEXP, SEXP, SEXP, SEXP);
RAPI_EXTERN void (*ptr_R_ProcessEvents)(void);
// end unix cdef
#endif

#endif /* end of include guard: R_H__ */
