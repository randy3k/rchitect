#ifndef LIBR_H__
#define LIBR_H__

#include "R.h"
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
int _libR_is_initialized(void);
int _libR_load_symbols(void);
int _libR_load_constants(void);
void _libR_set_callback(char* name, void* cb);

int cb_read_console_interruptible(const char *, unsigned char *, int, int);
extern int cb_read_console_interrupted;


void _libR_setup_xptr_callback();
SEXP _libR_xptr_callback(SEXP, SEXP, SEXP, SEXP);
extern int xptr_callback_error_occured;
extern char xptr_callback_error_message[100];

// end cdef

// begin cb cdef

void cb_suicide(const char *);
void cb_show_message(const char *);
int  cb_read_console(const char *, unsigned char *, int, int);
void cb_write_console(const char *, int);
void cb_write_console_ex(const char *, int, int);
void cb_reset_console(void);
void cb_flush_console(void);
void cb_clearerr_console(void);
void cb_busy(int);
void cb_clean_up(int, int, int);
int  cb_show_files(int, const char **, const char **,
                   const char *, Rboolean, const char *);
int  cb_choose_file(int, char *, int);
int  cb_edit_file(const char *);
void cb_loadhistory(SEXP, SEXP, SEXP, SEXP);
void cb_savehistory(SEXP, SEXP, SEXP, SEXP);
void cb_addhistory(SEXP, SEXP, SEXP, SEXP);
int  cb_edit_files(int, const char **, const char **, const char *);
SEXP cb_do_selectlist(SEXP, SEXP, SEXP, SEXP);
SEXP cb_do_dataentry(SEXP, SEXP, SEXP, SEXP);
SEXP cb_do_dataviewer(SEXP, SEXP, SEXP, SEXP);
void cb_process_events();
void cb_polled_events();
int  cb_yes_no_cancel(const char *s);

SEXP xptr_callback(SEXP, SEXP, SEXP, SEXP);

// end cb cdef

#endif /* end of include guard: LIBR_H__ */
