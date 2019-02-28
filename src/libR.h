#ifndef LIBR_H__
#define LIBR_H__

#include <stdlib.h>
#include <string.h>

#ifndef _WIN32
#include <dlfcn.h>
#else
#define WIN32_LEAN_AND_MEAN 1
#include <windows.h>
#endif

// begin cdef

char* _libR_last_loaded_symbol(void);

char* _libR_dl_error_message(void);

int _libR_load(const char* libpath);

int _libR_load_symbols(void);

#endif /* end of include guard: LIBR_H__ */
