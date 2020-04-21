#include "process_events.h"

static void _process_events(void* n) {
    R_ProcessEvents();

#if defined(__APPLE__)
    void* what = R_checkActivity(0, 1);
    if (what != NULL)
       R_runHandlers(R_InputHandlers, what);
#elif defined(unix) || defined(__unix__) || defined(__unix)
    void* what = R_checkActivity(0, 1);
    R_runHandlers(R_InputHandlers, what);
#endif

}

void process_events() {
    R_ToplevelExec(_process_events, NULL);
}

#if defined(_WIN32)

int peek_event(void) {
    return GA_peekevent();
}

#else

int peek_event(void) {
    void* what = R_checkActivity(0, 1);
    return what != NULL;
}

#endif
