#define LIBR
#include "R.h"
#include "libR.h"

static void* libR_t;

static char last_loaded_symbol[100] = "";

char* _libR_last_loaded_symbol() {
    return last_loaded_symbol;
}

static char dl_error_message[1024] = "";

char* _libR_dl_error_message() {
#ifdef _WIN32
    LPVOID lpMsgBuf;
    DWORD dw = GetLastError();

    DWORD length = FormatMessage(
        FORMAT_MESSAGE_ALLOCATE_BUFFER |
        FORMAT_MESSAGE_FROM_SYSTEM |
        FORMAT_MESSAGE_IGNORE_INSERTS,
        NULL,
        dw,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPTSTR) &lpMsgBuf,
        0, NULL );

    if (length != 0) {
        strcpy(dl_error_message, lpMsgBuf);
        LocalFree(lpMsgBuf);
    } else {
        strcpy(dl_error_message, "(Unknown error)");
    }
#else
    char* msg = dlerror();
    if (msg != NULL)
        strcpy(dl_error_message, msg);
    else
        strcpy(dl_error_message, "(Unknown error)");
#endif
    return dl_error_message;
}

int _libR_load(const char* libpath) {
    libR_t = NULL;
#ifdef _WIN32
    libR_t = (void*)LoadLibraryEx(libpath, NULL, 0);
#else
    libR_t = dlopen(libpath, RTLD_NOW|RTLD_GLOBAL);
#endif
    if (libR_t == NULL) {
        return false;
    } else {
        return true;
    }
}

int load_symbol(const char* name, void** ppSymbol) {
    strcpy(last_loaded_symbol, name);
#ifdef _WIN32
    *ppSymbol = (void*) GetProcAddress((HINSTANCE) libR_t, name);
#else
    *ppSymbol = dlsym(libR_t, name);
#endif
    if (*ppSymbol == NULL) {
        return false;
    } else {
        return true;
    }
}

#define LOAD_SYMBOL_AS(name, as) \
if (!load_symbol(#name, (void**) &as)) \
    return false;

#define LOAD_SYMBOL(name) \
if (!load_symbol(#name, (void**) &name)) {\
    return false; \
}

int load_constant(const char* name, void** ppSymbol) {
    strcpy(last_loaded_symbol, name);
#ifdef _WIN32
    *ppSymbol = *((void**) GetProcAddress((HINSTANCE) libR_t, name));
#else
    *ppSymbol = *((void**) dlsym(libR_t, name));
#endif
    if (*ppSymbol == NULL) {
        return false;
    } else {
        return true;
    }
}

#define LOAD_CONSTANT_AS(name, as) \
if (!load_constant(#name, (void**) &as)) \
    return false;

#define LOAD_CONSTANT(name) \
if (!load_constant(#name, (void**) &name)) \
    return false;

int _libR_load_symbols() {

    LOAD_SYMBOL(R_CHAR);
    LOAD_SYMBOL(Rf_isNull);
    LOAD_SYMBOL(Rf_isSymbol);
    LOAD_SYMBOL(Rf_isLogical);
    LOAD_SYMBOL(Rf_isReal);
    LOAD_SYMBOL(Rf_isComplex);
    LOAD_SYMBOL(Rf_isExpression);
    LOAD_SYMBOL(Rf_isEnvironment);
    LOAD_SYMBOL(Rf_isString);
    LOAD_SYMBOL(Rf_isObject);

    LOAD_SYMBOL(TYPEOF);
    LOAD_SYMBOL(IS_S4_OBJECT);

    LOAD_SYMBOL(LENGTH);
    LOAD_SYMBOL(XLENGTH);
    LOAD_SYMBOL(TRUELENGTH);
    LOAD_SYMBOL(SETLENGTH);
    LOAD_SYMBOL(SET_TRUELENGTH);
    LOAD_SYMBOL(IS_LONG_VEC);
    LOAD_SYMBOL(LEVELS);
    LOAD_SYMBOL(SETLEVELS);

    LOAD_SYMBOL(LOGICAL);
    LOAD_SYMBOL(INTEGER);
    LOAD_SYMBOL(RAW);
    LOAD_SYMBOL(REAL);
    LOAD_SYMBOL(COMPLEX);
    LOAD_SYMBOL(STRING_ELT);
    LOAD_SYMBOL(VECTOR_ELT);
    LOAD_SYMBOL(SET_STRING_ELT);
    LOAD_SYMBOL(SET_VECTOR_ELT);

    LOAD_SYMBOL(Rf_cons);
    LOAD_SYMBOL(Rf_lcons);
    LOAD_SYMBOL(TAG);
    LOAD_SYMBOL(CAR);
    LOAD_SYMBOL(CDR);
    LOAD_SYMBOL(CAAR);
    LOAD_SYMBOL(CDAR);
    LOAD_SYMBOL(CADR);
    LOAD_SYMBOL(CDDR);
    LOAD_SYMBOL(CDDDR);
    LOAD_SYMBOL(CADDR);
    LOAD_SYMBOL(CADDDR);
    LOAD_SYMBOL(CAD4R);
    LOAD_SYMBOL(MISSING);
    LOAD_SYMBOL(SET_MISSING);
    LOAD_SYMBOL(SET_TAG);
    LOAD_SYMBOL(SETCAR);
    LOAD_SYMBOL(SETCDR);
    LOAD_SYMBOL(SETCADR);
    LOAD_SYMBOL(SETCADDR);
    LOAD_SYMBOL(SETCADDDR);
    LOAD_SYMBOL(SETCAD4R);
    LOAD_SYMBOL(CONS_NR);

    LOAD_SYMBOL(PRINTNAME);

    LOAD_SYMBOL(Rf_protect);
    LOAD_SYMBOL(Rf_unprotect);

    LOAD_SYMBOL(Rf_asChar);
    LOAD_SYMBOL(Rf_coerceVector);
    LOAD_SYMBOL(Rf_PairToVectorList);
    LOAD_SYMBOL(Rf_VectorToPairList);
    LOAD_SYMBOL(Rf_asCharacterFactor);
    LOAD_SYMBOL(Rf_asLogical);
    // LOAD_SYMBOL(Rf_asLogical2);
    LOAD_SYMBOL(Rf_asInteger);
    LOAD_SYMBOL(Rf_asReal);
    LOAD_SYMBOL(Rf_asComplex);

    LOAD_SYMBOL(Rf_acopy_string);
    LOAD_SYMBOL(Rf_addMissingVarsToNewEnv);
    LOAD_SYMBOL(Rf_alloc3DArray);
    LOAD_SYMBOL(Rf_allocArray);
    LOAD_SYMBOL(Rf_allocFormalsList2);
    LOAD_SYMBOL(Rf_allocFormalsList3);
    LOAD_SYMBOL(Rf_allocFormalsList4);
    LOAD_SYMBOL(Rf_allocFormalsList5);
    LOAD_SYMBOL(Rf_allocFormalsList6);
    LOAD_SYMBOL(Rf_allocMatrix);
    LOAD_SYMBOL(Rf_allocList);
    LOAD_SYMBOL(Rf_allocS4Object);
    LOAD_SYMBOL(Rf_allocSExp);
    LOAD_SYMBOL(Rf_allocVector3);
    LOAD_SYMBOL(Rf_any_duplicated);
    LOAD_SYMBOL(Rf_any_duplicated3);
    LOAD_SYMBOL(Rf_applyClosure);
    LOAD_SYMBOL(Rf_arraySubscript);
    LOAD_SYMBOL(Rf_classgets);
    LOAD_SYMBOL(Rf_copyMatrix);
    LOAD_SYMBOL(Rf_copyListMatrix);
    LOAD_SYMBOL(Rf_copyMostAttrib);
    LOAD_SYMBOL(Rf_copyVector);
    LOAD_SYMBOL(Rf_countContexts);
    LOAD_SYMBOL(Rf_CreateTag);
    LOAD_SYMBOL(Rf_defineVar);
    LOAD_SYMBOL(Rf_dimgets);
    LOAD_SYMBOL(Rf_dimnamesgets);
    LOAD_SYMBOL(Rf_DropDims);
    LOAD_SYMBOL(Rf_duplicate);
    LOAD_SYMBOL(Rf_shallow_duplicate);
    // LOAD_SYMBOL(R_duplicate_attr);
    // LOAD_SYMBOL(R_shallow_duplicate_attr);
    LOAD_SYMBOL(Rf_lazy_duplicate);

    LOAD_SYMBOL(Rf_duplicated);
    LOAD_SYMBOL(R_envHasNoSpecialSymbols);
    LOAD_SYMBOL(Rf_eval);
    LOAD_SYMBOL(Rf_findFun);
    LOAD_SYMBOL(Rf_findVar);
    LOAD_SYMBOL(Rf_findVarInFrame);
    LOAD_SYMBOL(Rf_findVarInFrame3);
    LOAD_SYMBOL(Rf_getAttrib);
    LOAD_SYMBOL(Rf_GetArrayDimnames);
    LOAD_SYMBOL(Rf_GetColNames);
    LOAD_SYMBOL(Rf_GetMatrixDimnames);
    LOAD_SYMBOL(Rf_GetOption1);
    LOAD_SYMBOL(Rf_GetOptionDigits);
    LOAD_SYMBOL(Rf_GetOptionWidth);
    LOAD_SYMBOL(Rf_GetRowNames);
    LOAD_SYMBOL(Rf_gsetVar);
    LOAD_SYMBOL(Rf_install);
    LOAD_SYMBOL(Rf_installChar);
    LOAD_SYMBOL(Rf_isFree);
    LOAD_SYMBOL(Rf_isOrdered);
    LOAD_SYMBOL(Rf_isUnordered);
    LOAD_SYMBOL(Rf_isUnsorted);
    LOAD_SYMBOL(Rf_lengthgets);
    LOAD_SYMBOL(Rf_xlengthgets);
    LOAD_SYMBOL(R_lsInternal);
    LOAD_SYMBOL(R_lsInternal3);
    LOAD_SYMBOL(Rf_match);
    LOAD_SYMBOL(Rf_matchE);
    LOAD_SYMBOL(Rf_namesgets);
    LOAD_SYMBOL(Rf_mkChar);
    LOAD_SYMBOL(Rf_mkCharLen);
    LOAD_SYMBOL(Rf_NonNullStringMatch);
    LOAD_SYMBOL(Rf_ncols);
    LOAD_SYMBOL(Rf_nrows);
    LOAD_SYMBOL(Rf_nthcdr);

    LOAD_SYMBOL(R_nchar);
    LOAD_SYMBOL(Rf_pmatch);
    LOAD_SYMBOL(Rf_psmatch);
    LOAD_SYMBOL(R_ParseEvalString);
    LOAD_SYMBOL(Rf_PrintValue);
    // LOAD_SYMBOL(Rf_printwhere);
    LOAD_SYMBOL(Rf_readS3VarsFromFrame);
    LOAD_SYMBOL(Rf_setAttrib);
    LOAD_SYMBOL(Rf_setSVector);
    LOAD_SYMBOL(Rf_setVar);
    LOAD_SYMBOL(Rf_stringSuffix);
    LOAD_SYMBOL(Rf_str2type);
    LOAD_SYMBOL(Rf_StringBlank);
    LOAD_SYMBOL(Rf_substitute);
    LOAD_SYMBOL(Rf_topenv);
    LOAD_SYMBOL(Rf_translateChar);
    LOAD_SYMBOL(Rf_translateChar0);
    LOAD_SYMBOL(Rf_translateCharUTF8);
    LOAD_SYMBOL(Rf_type2char);

    LOAD_SYMBOL(Rf_type2rstr);
    LOAD_SYMBOL(Rf_type2str);
    LOAD_SYMBOL(Rf_type2str_nowarn);


    LOAD_SYMBOL(Rf_initialize_R);
    LOAD_SYMBOL(setup_Rmainloop);
    LOAD_SYMBOL(run_Rmainloop);

    return true;
}

int _libR_load_constants() {

    LOAD_CONSTANT(R_GlobalEnv);
    LOAD_CONSTANT(R_EmptyEnv);
    LOAD_CONSTANT(R_BaseEnv);
    LOAD_CONSTANT(R_BaseNamespace);
    LOAD_CONSTANT(R_NamespaceRegistry);
    LOAD_CONSTANT(R_Srcref);
    LOAD_CONSTANT(R_NilValue);
    LOAD_CONSTANT(R_UnboundValue);
    LOAD_CONSTANT(R_MissingArg);
    LOAD_CONSTANT(R_InBCInterpreter);
    LOAD_CONSTANT(R_CurrentExpression);
    LOAD_CONSTANT(R_AsCharacterSymbol);
    LOAD_CONSTANT(R_baseSymbol);
    LOAD_CONSTANT(R_BaseSymbol);
    LOAD_CONSTANT(R_BraceSymbol);
    LOAD_CONSTANT(R_Bracket2Symbol);
    LOAD_CONSTANT(R_BracketSymbol);
    LOAD_CONSTANT(R_ClassSymbol);
    LOAD_CONSTANT(R_DeviceSymbol);
    LOAD_CONSTANT(R_DimNamesSymbol);
    LOAD_CONSTANT(R_DimSymbol);
    LOAD_CONSTANT(R_DollarSymbol);
    LOAD_CONSTANT(R_DotsSymbol);
    LOAD_CONSTANT(R_DoubleColonSymbol);
    LOAD_CONSTANT(R_DropSymbol);
    LOAD_CONSTANT(R_LastvalueSymbol);
    LOAD_CONSTANT(R_LevelsSymbol);
    LOAD_CONSTANT(R_ModeSymbol);
    LOAD_CONSTANT(R_NaRmSymbol);
    LOAD_CONSTANT(R_NameSymbol);
    LOAD_CONSTANT(R_NamesSymbol);
    LOAD_CONSTANT(R_NamespaceEnvSymbol);
    LOAD_CONSTANT(R_PackageSymbol);
    LOAD_CONSTANT(R_PreviousSymbol);
    LOAD_CONSTANT(R_QuoteSymbol);
    LOAD_CONSTANT(R_RowNamesSymbol);
    LOAD_CONSTANT(R_SeedsSymbol);
    LOAD_CONSTANT(R_SortListSymbol);
    LOAD_CONSTANT(R_SourceSymbol);
    LOAD_CONSTANT(R_SpecSymbol);
    LOAD_CONSTANT(R_TripleColonSymbol);
    LOAD_CONSTANT(R_TspSymbol);
    LOAD_CONSTANT(R_dot_defined);
    LOAD_CONSTANT(R_dot_Method);
    LOAD_CONSTANT(R_dot_packageName);
    LOAD_CONSTANT(R_dot_target);
    LOAD_CONSTANT(R_dot_Generic);
    LOAD_CONSTANT(R_NaString);
    LOAD_CONSTANT(R_BlankString);
    LOAD_CONSTANT(R_BlankScalarString);

    return true;
}
