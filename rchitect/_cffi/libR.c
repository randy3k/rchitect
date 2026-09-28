#include "libR.h"

#include <stdio.h>

#include "R.h"

#ifndef _WIN32
#include <unistd.h>  // for getpid
#endif

int _libR_is_initialized(void) {
    return R_GlobalEnv != NULL;
}

int xptr_callback_error_occured;
char xptr_callback_error_message[4096];

SEXP _libR_xptr_callback(SEXP exptr, SEXP arglist, SEXP asis, SEXP convert) {
    SEXP result;
    xptr_callback_error_occured = 0;
    Rf_protect(exptr);
    Rf_protect(arglist);
    Rf_protect(asis);
    Rf_protect(convert);
    result = xptr_callback(exptr, arglist, asis, convert);
    Rf_unprotect(4);
    if (xptr_callback_error_occured == 1) {
        SEXP err_msg = Rf_protect(Rf_ScalarString(Rf_mkCharCE(xptr_callback_error_message, CE_UTF8)));
        SEXP stop_call = Rf_protect(Rf_lang2(Rf_install("stop"), err_msg));
        Rf_eval(stop_call, R_BaseEnv);
        Rf_unprotect(2);
    }
    return result;
}

static const R_CallMethodDef CallEntries[] = {{"_libR_xptr_callback", (DL_FUNC)&_libR_xptr_callback, 4},
                                              {NULL, NULL, 0}};

void _libR_setup_xptr_callback(void) {
    DllInfo* dll = R_getEmbeddingDllInfo();
    R_registerRoutines(dll, NULL, (void*)CallEntries, NULL, NULL);
}

#ifndef _WIN32
int main_id = -1;
#endif

int cb_interrupted;

// we need to wrap cb_read_console to make it KeyboardInterrupt aware
int cb_read_console_interruptible(const char* p, unsigned char* buf, int buflen, int add_history) {
    // flush buffered stdio
    fflush(NULL);
#ifndef _WIN32
    if (main_id == -1) main_id = getpid();
    if (getpid() != main_id) abort();
#endif
    int ret;
    cb_interrupted = 0;
    ret = cb_read_console(p, buf, buflen, add_history);
    if (cb_interrupted == 1) {
        cb_interrupted = 0;
#ifdef _WIN32
        UserBreak = 1;
#else
        R_interrupts_pending = 1;
#endif
        R_CheckUserInterrupt();
    }
    return ret;
}

void cb_polled_events_interruptible(void) {
#ifndef _WIN32
    if (main_id == -1) main_id = getpid();
    if (getpid() != main_id) return;
#endif
    cb_polled_events();
    if (cb_interrupted == 1) {
        cb_interrupted = 0;
#ifdef _WIN32
        UserBreak = 1;
#else
        R_interrupts_pending = 1;
#endif
        R_CheckUserInterrupt();
    }
}

#ifdef _WIN32

// actually we don't use it
void cb_write_console_safe(const char* s, int bufline, int otype) {
    cb_write_console_capturable(s, bufline, otype);
}

// actually we don't use it
void cb_busy_safe(int which) {
    cb_busy(which);
}

#else

void cb_write_console_safe(const char* s, int bufline, int otype) {
    // TODO: is it possible to capture the output of forks?

    if (main_id == -1) main_id = getpid();
    // only capture the main process
    if (getpid() == main_id) {
        // flush buffered stdio
        fflush(NULL);
        cb_write_console_capturable(s, bufline, otype);
    } else {
        if (otype == 0) {
            printf("%s", s);
            fflush(stdout);
        } else {
            fprintf(stderr, "%s", s);
            fflush(stderr);
        }
    }
}

void cb_busy_safe(int which) {
    if (main_id == -1) main_id = getpid();
    if (getpid() != main_id) return;
    cb_busy(which);
}

#endif
