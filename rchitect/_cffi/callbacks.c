#include <Python.h>
#include <stdio.h>

#include "callbacks.h"

#ifndef _WIN32
#include <unistd.h>  // for getpid
#endif

#ifndef _WIN32
static int main_id = -1;
#endif

int cb_interrupted;

// cffi releases GIL, so we need to ensure it. Mainly needed for loading reticulate.
void rchitect_run_Rmainloop(void) {
    PyGILState_STATE gstate = PyGILState_Ensure();
    run_Rmainloop();
    PyGILState_Release(gstate);
}

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

void cb_write_console_safe(const char* s, int bufline, int otype) {
    cb_write_console_capturable(s, bufline, otype);
}

void cb_busy_safe(int which) {
    cb_busy(which);
}

#else

void cb_write_console_safe(const char* s, int bufline, int otype) {
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

static void _process_events(void* n) {
    R_ProcessEvents();

#if defined(__APPLE__)
    void* what = R_checkActivity(0, 1);
    if (what != NULL) R_runHandlers(R_InputHandlers, what);
#elif defined(unix) || defined(__unix__) || defined(__unix)
    void* what = R_checkActivity(0, 1);
    R_runHandlers(R_InputHandlers, what);
#endif
}

void process_events(void) {
    R_ToplevelExec((void (*)(void*))_process_events, NULL);
}

#if defined(_WIN32)

void polled_events(void) {
    cb_polled_events();
}

int peek_event(void) {
    return GA_peekevent();
}

#else

void polled_events(void) {
    R_ToplevelExec((void (*)(void*))cb_polled_events_interruptible, NULL);
}

static void Call_R_checkActivity(void** what) {
    *what = R_checkActivity(0, 1);
}

int peek_event(void) {
    Rboolean ok;
    void* what;
    ok = R_ToplevelExec((void (*)(void*))&Call_R_checkActivity, &what);
    if (ok == FALSE) {
        return 0;
    }
    return what != NULL;
}

#endif
