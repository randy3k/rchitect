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

typedef void *(*DL_FUNC)();

typedef int R_len_t;

// FIXME: when size of size_t <= 4
typedef ptrdiff_t R_xlen_t;

typedef unsigned int SEXPTYPE;

enum {
    NILSXP = 0,
    SYMSXP = 1,
    LISTSXP = 2,
    CLOSXP = 3,
    ENVSXP = 4,
    PROMSXP = 5,
    LANGSXP = 6,
    SPECIALSXP = 7,
    BUILTINSXP = 8,
    CHARSXP = 9,
    LGLSXP = 10,
    INTSXP = 13,
    REALSXP = 14,
    CPLXSXP = 15,
    STRSXP = 16,
    DOTSXP = 17,
    ANYSXP = 18,
    VECSXP = 19,
    EXPRSXP = 20,
    BCODESXP = 21,
    EXTPTRSXP = 22,
    WEAKREFSXP = 23,
    RAWSXP = 24,
    S4SXP = 25,
    NEWSXP = 30,
    FREESXP = 31,
    FUNSXP = 99
};

typedef struct {
    double r;
    double i;
} Rcomplex;

typedef enum { FALSE = 0, TRUE } Rboolean;

typedef struct SEXPREC *SEXP;

// Rinternals.h
RAPI_FUNC Rboolean Rf_isNull(SEXP s);
RAPI_FUNC Rboolean Rf_isObject(SEXP s);

RAPI_FUNC int TYPEOF(SEXP x);

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
RAPI_FUNC SEXP CDR(SEXP e);
RAPI_FUNC void SET_TAG(SEXP x, SEXP y);
RAPI_FUNC SEXP SETCAR(SEXP x, SEXP y);

RAPI_FUNC SEXP Rf_protect(SEXP);
RAPI_FUNC void Rf_unprotect(int);

RAPI_EXTERN SEXP R_GlobalEnv;
RAPI_EXTERN SEXP R_BaseEnv;
RAPI_EXTERN SEXP R_NilValue;
RAPI_EXTERN SEXP R_MissingArg;
RAPI_EXTERN SEXP R_ClassSymbol;
RAPI_EXTERN SEXP R_DotsSymbol;
RAPI_EXTERN SEXP R_DoubleColonSymbol;
RAPI_EXTERN SEXP R_NamesSymbol;
RAPI_EXTERN SEXP R_TripleColonSymbol;

RAPI_FUNC int Rf_asLogical(SEXP x);

RAPI_FUNC void Rf_defineVar(SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_eval(SEXP, SEXP);
RAPI_FUNC SEXP Rf_getAttrib(SEXP, SEXP);
RAPI_FUNC SEXP Rf_GetOption1(SEXP);
RAPI_FUNC SEXP Rf_install(const char *);
RAPI_FUNC SEXP Rf_mkChar(const char *);
RAPI_FUNC SEXP Rf_setAttrib(SEXP, SEXP, SEXP);
RAPI_FUNC const char *Rf_translateChar(SEXP);
RAPI_FUNC const char *Rf_translateCharUTF8(SEXP);

RAPI_FUNC SEXP R_tryEval(SEXP, SEXP, int *);

typedef enum { CE_NATIVE = 0, CE_UTF8 = 1, CE_LATIN1 = 2, CE_BYTES = 3, CE_SYMBOL = 5, CE_ANY = 99 } cetype_t;

RAPI_FUNC SEXP Rf_mkCharCE(const char *, cetype_t);
RAPI_FUNC SEXP Rf_mkCharLenCE(const char *, int, cetype_t);

RAPI_FUNC SEXP R_MakeExternalPtr(void *p, SEXP tag, SEXP prot);
RAPI_FUNC void *R_ExternalPtrAddr(SEXP s);
RAPI_FUNC void R_ClearExternalPtr(SEXP s);

typedef void (*R_CFinalizer_t)(SEXP);

RAPI_FUNC void R_RegisterCFinalizerEx(SEXP s, R_CFinalizer_t fun, Rboolean onexit);

RAPI_FUNC Rboolean R_ToplevelExec(void (*fun)(void *), void *data);

RAPI_FUNC void R_PreserveObject(SEXP);
RAPI_FUNC void R_ReleaseObject(SEXP);

RAPI_FUNC SEXP Rf_allocVector(SEXPTYPE, R_xlen_t);
RAPI_FUNC SEXP Rf_lang2(SEXP, SEXP);
RAPI_FUNC SEXP Rf_lang3(SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_lang6(SEXP, SEXP, SEXP, SEXP, SEXP, SEXP);
RAPI_FUNC SEXP Rf_list1(SEXP);
RAPI_FUNC SEXP Rf_mkString(const char *);
RAPI_FUNC SEXP Rf_ScalarComplex(Rcomplex);
RAPI_FUNC SEXP Rf_ScalarInteger(int);
RAPI_FUNC SEXP Rf_ScalarLogical(int);
RAPI_FUNC SEXP Rf_ScalarReal(double);
RAPI_FUNC SEXP Rf_ScalarString(SEXP);
RAPI_FUNC R_xlen_t Rf_xlength(SEXP);

// Parse.h
typedef enum { PARSE_NULL, PARSE_OK, PARSE_INCOMPLETE, PARSE_ERROR, PARSE_EOF } ParseStatus;

RAPI_FUNC SEXP R_ParseVector(SEXP, int, ParseStatus *, SEXP);

// Memory.h
RAPI_FUNC void *vmaxget(void);
RAPI_FUNC void vmaxset(const void *);

// Error.h
RAPI_FUNC void Rf_error(const char *, ...);

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
    int EmitEmbeddedUTF8;
    void (*CleanUp)(int, int, int);
    void (*ClearerrConsole)(void);
    void (*FlushConsole)(void);
    void (*ResetConsole)(void);
    void (*Suicide)(const char *);
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
RAPI_EXTERN void (*ptr_R_ShowMessage)(const char *);
RAPI_EXTERN int (*ptr_R_ReadConsole)(const char *, unsigned char *, int, int);
RAPI_EXTERN void (*ptr_R_WriteConsole)(const char *, int);
RAPI_EXTERN void (*ptr_R_WriteConsoleEx)(const char *, int, int);
RAPI_EXTERN void (*ptr_R_ResetConsole)(void);
RAPI_EXTERN void (*ptr_R_Busy)(int);
RAPI_EXTERN void (*ptr_R_CleanUp)(int, int, int);
// end unix cdef
#endif

#endif /* end of include guard: R_H__ */
