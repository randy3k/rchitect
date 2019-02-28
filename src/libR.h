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

char* get_last_loaded_symbol();

char* get_dl_error_message();

int load_libR(const char* libpath);

int load_symbols();

#endif /* end of include guard: LIBR_H__ */
