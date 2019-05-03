#include "process_events.h"


void process_events() {
// TODO: use R_ToplevelExec

#if defined(__APPLE__) || defined(_WIN32)
    R_ProcessEvents();
#endif

#if defined(__APPLE__)
    void* what = R_checkActivity(0, 1);
    if (what != NULL)
       R_runHandlers(R_InputHandlers, what);
#elif defined(unix) || defined(__unix__) || defined(__unix)
    void* what = R_checkActivity(0, 1);
    R_runHandlers(R_InputHandlers, what);
#endif

}
