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

// Rembedded.h
RAPI_EXTERN int (*Rf_initialize_R)(int ac, char **av);
RAPI_EXTERN void (*setup_Rmainloop)(void);
RAPI_EXTERN void (*run_Rmainloop)(void);


#endif /* end of include guard: R_H__ */
