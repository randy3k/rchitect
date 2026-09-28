#ifndef CALLBACKS_H__
#define CALLBACKS_H__

#include <stdlib.h>
#include <string.h>

#include "R.h"

// begin cdef

extern int cb_interrupted;

int cb_read_console_interruptible(const char *, unsigned char *, int, int);
void cb_polled_events_interruptible(void);
void cb_write_console_safe(const char *, int, int);
void cb_busy_safe(int);

void rchitect_run_Rmainloop(void);
void process_events(void);
void polled_events(void);
int peek_event(void);

// end cdef

// begin cb cdef

void cb_write_console_capturable(const char *, int, int);

void cb_suicide(const char *);
void cb_show_message(const char *);
int cb_read_console(const char *, unsigned char *, int, int);
void cb_write_console(const char *, int);
void cb_write_console_ex(const char *, int, int);
void cb_reset_console(void);
void cb_flush_console(void);
void cb_clearerr_console(void);
void cb_busy(int);
void cb_clean_up(int, int, int);
int cb_show_files(int, const char **, const char **, const char *, Rboolean, const char *);
int cb_choose_file(int, char *, int);
int cb_edit_file(const char *);
void cb_loadhistory(SEXP, SEXP, SEXP, SEXP);
void cb_savehistory(SEXP, SEXP, SEXP, SEXP);
void cb_addhistory(SEXP, SEXP, SEXP, SEXP);
int cb_edit_files(int, const char **, const char **, const char *);
SEXP cb_do_selectlist(SEXP, SEXP, SEXP, SEXP);
SEXP cb_do_dataentry(SEXP, SEXP, SEXP, SEXP);
SEXP cb_do_dataviewer(SEXP, SEXP, SEXP, SEXP);
void cb_process_events(void);
void cb_polled_events(void);
int cb_yes_no_cancel(const char *s);

// end cb cdef

#endif /* end of include guard: CALLBACKS_H__ */
