#ifndef R_H__
#define R_H__

# include <stddef.h>

#ifndef LIBR
#define RAPI_EXTERN extern
#else
#define RAPI_EXTERN
#endif

// begin cdef
typedef unsigned char Rbyte;

typedef enum {Bytes, Chars, Width} nchar_type;

typedef int R_len_t;

// FIXME: when size of size_t <= 4
typedef ptrdiff_t R_xlen_t;

typedef unsigned int SEXPTYPE;

static const unsigned int NILSXP     =  0;
static const unsigned int SYMSXP     =  1;
static const unsigned int LISTSXP    =  2;
static const unsigned int CLOSXP     =  3;
static const unsigned int ENVSXP     =  4;
static const unsigned int PROMSXP    =  5;
static const unsigned int LANGSXP    =  6;
static const unsigned int SPECIALSXP =  7;
static const unsigned int BUILTINSXP =  8;
static const unsigned int CHARSXP    =  9;
static const unsigned int LGLSXP     = 10;
static const unsigned int INTSXP     = 13;
static const unsigned int REALSXP    = 14;
static const unsigned int CPLXSXP    = 15;
static const unsigned int STRSXP     = 16;
static const unsigned int DOTSXP     = 17;
static const unsigned int ANYSXP     = 18;
static const unsigned int VECSXP     = 19;
static const unsigned int EXPRSXP    = 20;
static const unsigned int BCODESXP   = 21;
static const unsigned int EXTPTRSXP  = 22;
static const unsigned int WEAKREFSXP = 23;
static const unsigned int RAWSXP     = 24;
static const unsigned int S4SXP      = 25;
static const unsigned int NEWSXP     = 30;
static const unsigned int FREESXP    = 31;
static const unsigned int FUNSXP     = 99;

typedef struct {
    double r;
    double i;
} Rcomplex;

typedef enum { FALSE = 0, TRUE } Rboolean;

struct sxpinfo_struct {
    SEXPTYPE type      :  5;
    unsigned int scalar:  1;
    unsigned int obj   :  1;
    unsigned int alt   :  1;
    unsigned int gp    : 16;
    unsigned int mark  :  1;
    unsigned int debug :  1;
    unsigned int trace :  1;
    unsigned int spare :  1;
    unsigned int gcgen :  1;
    unsigned int gccls :  3;
    unsigned int named : 16;
    unsigned int extra : 16;
};

struct vecsxp_struct {
    R_xlen_t    length;
    R_xlen_t    truelength;
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
RAPI_EXTERN const char* (*R_CHAR)(SEXP x);
RAPI_EXTERN Rboolean (*Rf_isNull)(SEXP s);
RAPI_EXTERN Rboolean (*Rf_isSymbol)(SEXP s);
RAPI_EXTERN Rboolean (*Rf_isLogical)(SEXP s);
RAPI_EXTERN Rboolean (*Rf_isReal)(SEXP s);
RAPI_EXTERN Rboolean (*Rf_isComplex)(SEXP s);
RAPI_EXTERN Rboolean (*Rf_isExpression)(SEXP s);
RAPI_EXTERN Rboolean (*Rf_isEnvironment)(SEXP s);
RAPI_EXTERN Rboolean (*Rf_isString)(SEXP s);
RAPI_EXTERN Rboolean (*Rf_isObject)(SEXP s);

RAPI_EXTERN int (*TYPEOF)(SEXP x);
RAPI_EXTERN int (*IS_S4_OBJECT)(SEXP x);

RAPI_EXTERN int  (*LENGTH)(SEXP x);
RAPI_EXTERN R_xlen_t (*XLENGTH)(SEXP x);
RAPI_EXTERN R_xlen_t  (*TRUELENGTH)(SEXP x);
RAPI_EXTERN void (*SETLENGTH)(SEXP x, R_xlen_t v);
RAPI_EXTERN void (*SET_TRUELENGTH)(SEXP x, R_xlen_t v);
RAPI_EXTERN int  (*IS_LONG_VEC)(SEXP x);
RAPI_EXTERN int  (*LEVELS)(SEXP x);
RAPI_EXTERN int  (*SETLEVELS)(SEXP x, int v);

// Vector Access Functions
RAPI_EXTERN int *(*LOGICAL)(SEXP x);
RAPI_EXTERN int  *(*INTEGER)(SEXP x);
RAPI_EXTERN Rbyte *(*RAW)(SEXP x);
RAPI_EXTERN double *(*REAL)(SEXP x);
RAPI_EXTERN Rcomplex *(*COMPLEX)(SEXP x);
RAPI_EXTERN SEXP (*STRING_ELT)(SEXP x, R_xlen_t i);
RAPI_EXTERN SEXP (*VECTOR_ELT)(SEXP x, R_xlen_t i);
RAPI_EXTERN void (*SET_STRING_ELT)(SEXP x, R_xlen_t i, SEXP v);
RAPI_EXTERN SEXP (*SET_VECTOR_ELT)(SEXP x, R_xlen_t i, SEXP v);

// List Access
RAPI_EXTERN SEXP (*Rf_cons)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_lcons)(SEXP, SEXP);
RAPI_EXTERN SEXP (*TAG)(SEXP e);
RAPI_EXTERN SEXP (*CAR)(SEXP e);
RAPI_EXTERN SEXP (*CDR)(SEXP e);
RAPI_EXTERN SEXP (*CAAR)(SEXP e);
RAPI_EXTERN SEXP (*CDAR)(SEXP e);
RAPI_EXTERN SEXP (*CADR)(SEXP e);
RAPI_EXTERN SEXP (*CDDR)(SEXP e);
RAPI_EXTERN SEXP (*CDDDR)(SEXP e);
RAPI_EXTERN SEXP (*CADDR)(SEXP e);
RAPI_EXTERN SEXP (*CADDDR)(SEXP e);
RAPI_EXTERN SEXP (*CAD4R)(SEXP e);
RAPI_EXTERN int  (*MISSING)(SEXP x);
RAPI_EXTERN void (*SET_MISSING)(SEXP x, int v);
RAPI_EXTERN void (*SET_TAG)(SEXP x, SEXP y);
RAPI_EXTERN SEXP (*SETCAR)(SEXP x, SEXP y);
RAPI_EXTERN SEXP (*SETCDR)(SEXP x, SEXP y);
RAPI_EXTERN SEXP (*SETCADR)(SEXP x, SEXP y);
RAPI_EXTERN SEXP (*SETCADDR)(SEXP x, SEXP y);
RAPI_EXTERN SEXP (*SETCADDDR)(SEXP x, SEXP y);
RAPI_EXTERN SEXP (*SETCAD4R)(SEXP e, SEXP y);
RAPI_EXTERN SEXP (*CONS_NR)(SEXP a, SEXP b);

RAPI_EXTERN SEXP (*PRINTNAME)(SEXP x);

RAPI_EXTERN SEXP (*Rf_protect)(SEXP);
RAPI_EXTERN void (*Rf_unprotect)(int);

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

RAPI_EXTERN SEXP (*Rf_asChar)(SEXP);
RAPI_EXTERN SEXP (*Rf_coerceVector)(SEXP, SEXPTYPE);
RAPI_EXTERN SEXP (*Rf_PairToVectorList)(SEXP x);
RAPI_EXTERN SEXP (*Rf_VectorToPairList)(SEXP x);
RAPI_EXTERN SEXP (*Rf_asCharacterFactor)(SEXP x);
RAPI_EXTERN int (*Rf_asLogical)(SEXP x);
RAPI_EXTERN int (*Rf_asLogical2)(SEXP x, int checking, SEXP call, SEXP rho);
RAPI_EXTERN int (*Rf_asInteger)(SEXP x);
RAPI_EXTERN double (*Rf_asReal)(SEXP x);
RAPI_EXTERN Rcomplex (*Rf_asComplex)(SEXP x);

RAPI_EXTERN char * (*Rf_acopy_string)(const char *);
RAPI_EXTERN void (*Rf_addMissingVarsToNewEnv)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_alloc3DArray)(SEXPTYPE, int, int, int);
RAPI_EXTERN SEXP (*Rf_allocArray)(SEXPTYPE, SEXP);
RAPI_EXTERN SEXP (*Rf_allocFormalsList2)(SEXP sym1, SEXP sym2);
RAPI_EXTERN SEXP (*Rf_allocFormalsList3)(SEXP sym1, SEXP sym2, SEXP sym3);
RAPI_EXTERN SEXP (*Rf_allocFormalsList4)(SEXP sym1, SEXP sym2, SEXP sym3, SEXP sym4);
RAPI_EXTERN SEXP (*Rf_allocFormalsList5)(SEXP sym1, SEXP sym2, SEXP sym3, SEXP sym4, SEXP sym5);
RAPI_EXTERN SEXP (*Rf_allocFormalsList6)(SEXP sym1, SEXP sym2, SEXP sym3, SEXP sym4, SEXP sym5, SEXP sym6);
RAPI_EXTERN SEXP (*Rf_allocMatrix)(SEXPTYPE, int, int);
RAPI_EXTERN SEXP (*Rf_allocList)(int);
RAPI_EXTERN SEXP (*Rf_allocS4Object)(void);
RAPI_EXTERN SEXP (*Rf_allocSExp)(SEXPTYPE);
RAPI_EXTERN SEXP (*Rf_allocVector3)(SEXPTYPE, R_xlen_t, void*);
RAPI_EXTERN R_xlen_t (*Rf_any_duplicated)(SEXP x, Rboolean from_last);
RAPI_EXTERN R_xlen_t (*Rf_any_duplicated3)(SEXP x, SEXP incomp, Rboolean from_last);
RAPI_EXTERN SEXP (*Rf_applyClosure)(SEXP, SEXP, SEXP, SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_arraySubscript)(int, SEXP, SEXP, SEXP (*)(SEXP,SEXP), SEXP (*)(SEXP, int), SEXP);
RAPI_EXTERN SEXP (*Rf_classgets)(SEXP, SEXP);
RAPI_EXTERN void (*Rf_copyMatrix)(SEXP, SEXP, Rboolean);
RAPI_EXTERN void (*Rf_copyListMatrix)(SEXP, SEXP, Rboolean);
RAPI_EXTERN void (*Rf_copyMostAttrib)(SEXP, SEXP);
RAPI_EXTERN void (*Rf_copyVector)(SEXP, SEXP);
RAPI_EXTERN int (*Rf_countContexts)(int, int);
RAPI_EXTERN SEXP (*Rf_CreateTag)(SEXP);
RAPI_EXTERN void (*Rf_defineVar)(SEXP, SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_dimgets)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_dimnamesgets)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_DropDims)(SEXP);
RAPI_EXTERN SEXP (*Rf_duplicate)(SEXP);
RAPI_EXTERN SEXP (*Rf_shallow_duplicate)(SEXP);
// RAPI_EXTERN SEXP (*R_duplicate_attr)(SEXP);
// RAPI_EXTERN SEXP (*R_shallow_duplicate_attr)(SEXP);
RAPI_EXTERN SEXP (*Rf_lazy_duplicate)(SEXP);

RAPI_EXTERN SEXP (*Rf_duplicated)(SEXP, Rboolean);
RAPI_EXTERN Rboolean (*R_envHasNoSpecialSymbols)(SEXP);
RAPI_EXTERN SEXP (*Rf_eval)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_findFun)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_findVar)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_findVarInFrame)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_findVarInFrame3)(SEXP, SEXP, Rboolean);
RAPI_EXTERN SEXP (*Rf_getAttrib)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_GetArrayDimnames)(SEXP);
RAPI_EXTERN SEXP (*Rf_GetColNames)(SEXP);
RAPI_EXTERN void (*Rf_GetMatrixDimnames)(SEXP, SEXP*, SEXP*, const char**, const char**);
RAPI_EXTERN SEXP (*Rf_GetOption1)(SEXP);
RAPI_EXTERN int (*Rf_GetOptionDigits)(void);
RAPI_EXTERN int (*Rf_GetOptionWidth)(void);
RAPI_EXTERN SEXP (*Rf_GetRowNames)(SEXP);
RAPI_EXTERN void (*Rf_gsetVar)(SEXP, SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_install)(const char *);
RAPI_EXTERN SEXP (*Rf_installChar)(SEXP);
RAPI_EXTERN Rboolean (*Rf_isFree)(SEXP);
RAPI_EXTERN Rboolean (*Rf_isOrdered)(SEXP);
RAPI_EXTERN Rboolean (*Rf_isUnordered)(SEXP);
RAPI_EXTERN Rboolean (*Rf_isUnsorted)(SEXP, Rboolean);
RAPI_EXTERN SEXP (*Rf_lengthgets)(SEXP, R_len_t);
RAPI_EXTERN SEXP (*Rf_xlengthgets)(SEXP, R_xlen_t);
RAPI_EXTERN SEXP (*R_lsInternal)(SEXP, Rboolean);
RAPI_EXTERN SEXP (*R_lsInternal3)(SEXP, Rboolean, Rboolean);
RAPI_EXTERN SEXP (*Rf_match)(SEXP, SEXP, int);
RAPI_EXTERN SEXP (*Rf_matchE)(SEXP, SEXP, int, SEXP);
RAPI_EXTERN SEXP (*Rf_namesgets)(SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_mkChar)(const char *);
RAPI_EXTERN SEXP (*Rf_mkCharLen)(const char *, int);
RAPI_EXTERN Rboolean (*Rf_NonNullStringMatch)(SEXP, SEXP);
RAPI_EXTERN int (*Rf_ncols)(SEXP);
RAPI_EXTERN int (*Rf_nrows)(SEXP);
RAPI_EXTERN SEXP (*Rf_nthcdr)(SEXP, int);

RAPI_EXTERN int (*R_nchar)(SEXP string, nchar_type type_, Rboolean allowNA, Rboolean keepNA, const char* msg_name);
RAPI_EXTERN Rboolean (*Rf_pmatch)(SEXP, SEXP, Rboolean);
RAPI_EXTERN Rboolean (*Rf_psmatch)(const char *, const char *, Rboolean);
RAPI_EXTERN SEXP (*R_ParseEvalString)(const char *, SEXP);
RAPI_EXTERN void (*Rf_PrintValue)(SEXP);
// RAPI_EXTERN void (*Rf_printwhere)(void);
RAPI_EXTERN void (*Rf_readS3VarsFromFrame)(SEXP, SEXP*, SEXP*, SEXP*, SEXP*, SEXP*, SEXP*);
RAPI_EXTERN SEXP (*Rf_setAttrib)(SEXP, SEXP, SEXP);
RAPI_EXTERN void (*Rf_setSVector)(SEXP*, int, SEXP);
RAPI_EXTERN void (*Rf_setVar)(SEXP, SEXP, SEXP);
RAPI_EXTERN SEXP (*Rf_stringSuffix)(SEXP, int);
RAPI_EXTERN SEXPTYPE (*Rf_str2type)(const char *);
RAPI_EXTERN Rboolean (*Rf_StringBlank)(SEXP);
RAPI_EXTERN SEXP (*Rf_substitute)(SEXP,SEXP);
RAPI_EXTERN SEXP (*Rf_topenv)(SEXP, SEXP);
RAPI_EXTERN const char * (*Rf_translateChar)(SEXP);
RAPI_EXTERN const char * (*Rf_translateChar0)(SEXP);
RAPI_EXTERN const char * (*Rf_translateCharUTF8)(SEXP);
RAPI_EXTERN const char * (*Rf_type2char)(SEXPTYPE);
RAPI_EXTERN SEXP (*Rf_type2rstr)(SEXPTYPE);
RAPI_EXTERN SEXP (*Rf_type2str)(SEXPTYPE);
RAPI_EXTERN SEXP (*Rf_type2str_nowarn)(SEXPTYPE);

// Rembedded.h
RAPI_EXTERN int (*Rf_initialize_R)(int ac, char **av);
RAPI_EXTERN void (*setup_Rmainloop)(void);
RAPI_EXTERN void (*run_Rmainloop)(void);


#endif /* end of include guard: R_H__ */
