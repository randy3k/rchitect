#define LIBR
#include "R.h"
#include "libR.h"

static void* libR_t;

static char last_loaded_symbol[100] = "";

char* get_last_loaded_symbol() {
    return last_loaded_symbol;
}

static char dl_error_message[1024] = "";

char* get_dl_error_message() {
#ifdef _WIN32
    LPVOID lpMsgBuf;
    DWORD dw = GetLastError();

    DWORD length = ::FormatMessage(
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

int load_libR(const char* libpath) {
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


int load_symbols() {
    LOAD_SYMBOL(Rf_initialize_R);
    LOAD_SYMBOL(setup_Rmainloop);
    LOAD_SYMBOL(run_Rmainloop);

    return true;
}
