import os
import re
import sys
from cffi import FFI
ffibuilder = FFI()

cwd = os.path.dirname(os.path.realpath(__file__))
cdef_pattern = re.compile("// begin cdef([^$]*)// end cdef")
cb_cdef_pattern = re.compile("// begin cb cdef([^$]*)// end cb cdef")


for header_file in ["R.h", "libR.h", "gli.h", "parse.h", "process_events.h"]:
    with open(os.path.join(cwd, header_file), "r") as f:
        m = cdef_pattern.search(f.read(), re.M)
        ffibuilder.cdef(m.group(1).replace("RAPI_EXTERN", ""))

if sys.platform.startswith("win"):
    ffibuilder.cdef("""
        char *(*get_R_HOME)(void);
        char *(*getRUser)(void);
        int* UserBreak_t;
        int* CharacterMode_t;
    """)
else:
    ffibuilder.cdef("""
        void* (*R_InputHandlers);
        void* (*R_checkActivity)(int usec, int ignore_stdin);
        void (*R_runHandlers)(void* handlers, void* mask);
        int* R_interrupts_pending_t;
    """)

with open(os.path.join(cwd, "libR.h"), "r") as f:
    m = cb_cdef_pattern.search(f.read(), re.M)
    ffibuilder.cdef("""
        extern "Python+C" {{
            {}
        }}
    """.format(m.group(1)))

ffibuilder.set_source(
    "rchitect._cffi",
    """
    # include "gli.h"
    # include "libR.h"
    # include "parse.h"
    # include "process_events.h"
    """,
    include_dirs=['rchitect/src'],
    sources=[
        'rchitect/src/libR.c',
        'rchitect/src/gli.c',
        'rchitect/src/parse.c',
        'rchitect/src/process_events.c'
    ])

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
