#ifndef CALLBACKS_H__
#define CALLBACKS_H__

#include <stdlib.h>
#include <string.h>

#include "R.h"

// begin cdef

extern int cb_interrupted;

int cb_read_console_safe(const char *, unsigned char *, int, int);
void cb_polled_events_safe(void);
void cb_write_console_ex_safe(const char *, int, int);
void cb_busy_safe(int);

int rchitect_is_main_process(void);
int rchitect_is_main_thread(void);
void rchitect_record_main_thread(void);
void rchitect_run_Rmainloop(void);
void process_events(void);
void polled_events(void);
int peek_event(void);

// end cdef

// begin cb cdef

void cb_show_message(const char *);
int cb_read_console(const char *, unsigned char *, int, int);
void cb_write_console_ex(const char *, int, int);
void cb_reset_console(void);
void cb_busy(int);
void cb_clean_up(int, int, int);
void cb_polled_events(void);
int cb_yes_no_cancel(const char *s);

// end cb cdef

#endif /* end of include guard: CALLBACKS_H__ */
