#include <Python.h>
#include <stdio.h>

#include "callbacks.h"

// =============================================================================
// 1. Main Process & Main Thread Tracking
// =============================================================================

#ifdef _WIN32
#include <windows.h>
static DWORD main_thread_id = 0;

int rchitect_is_main_process(void) {
    return 1;
}

int rchitect_is_main_thread(void) {
    if (main_thread_id == 0) {
        main_thread_id = GetCurrentThreadId();
    }
    return GetCurrentThreadId() == main_thread_id;
}
#else
#include <pthread.h>
#include <unistd.h>  // for getpid
static pid_t main_id = -1;
static pthread_t main_thread;

int rchitect_is_main_process(void) {
    if (main_id == -1) {
        main_id = getpid();
        main_thread = pthread_self();
    }
    return getpid() == main_id;
}

int rchitect_is_main_thread(void) {
    return rchitect_is_main_process() && pthread_equal(pthread_self(), main_thread);
}
#endif

void rchitect_record_main_thread(void) {
#ifdef _WIN32
    main_thread_id = GetCurrentThreadId();
#else
    main_id = getpid();
    main_thread = pthread_self();
#endif
}

// =============================================================================
// 2. R Main Loop & Safe Console Callbacks
// =============================================================================

int cb_interrupted;

void rchitect_run_Rmainloop(void) {
    rchitect_record_main_thread();
    run_Rmainloop();
}

// we need to wrap cb_read_console to make it KeyboardInterrupt aware
int cb_read_console_safe(const char* p, unsigned char* buf, int buflen, int add_history) {
    // flush buffered stdio
    fflush(NULL);
#ifndef _WIN32
    if (!rchitect_is_main_thread()) abort();
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

void cb_polled_events_safe(void) {
    if (!rchitect_is_main_thread()) return;
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

void cb_write_console_ex_safe(const char* s, int bufline, int otype) {
    cb_write_console_ex(s, bufline, otype);
}

#else

void cb_write_console_ex_safe(const char* s, int bufline, int otype) {
    // only capture the main process (worker threads are queued in console.py)
    int is_main = rchitect_is_main_thread();
    if (is_main || rchitect_is_main_process()) {
        if (is_main) {
            // flush buffered stdio
            fflush(NULL);
        }
        cb_write_console_ex(s, bufline, otype);
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

#endif

void cb_busy_safe(int which) {
    if (!rchitect_is_main_thread()) return;
    cb_busy(which);
}

// =============================================================================
// 3. Event Processing & Polling
// =============================================================================

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
    cb_polled_events_safe();
}

int peek_event(void) {
    return GA_peekevent();
}

#else

void polled_events(void) {
    R_ToplevelExec((void (*)(void*))cb_polled_events_safe, NULL);
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
