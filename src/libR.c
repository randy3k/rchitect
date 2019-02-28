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
    *ppSymbol = NULL;

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
if (!load_symbol(#name, (void**) &name)) \
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

    LOAD_SYMBOL(Rf_initialize_R);
    LOAD_SYMBOL(setup_Rmainloop);
    LOAD_SYMBOL(run_Rmainloop);

    return true;
}
