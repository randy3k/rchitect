import os
import re
import sys
from cffi import FFI
ffibuilder = FFI()

# Rembedded.h
ffibuilder.cdef("""
int (*Rf_initialize_R)(int ac, char **av);
void (*setup_Rmainloop)();
void (*run_Rmainloop)();
""")

cwd = os.path.dirname(os.path.realpath(__file__))
cdef_pattern = re.compile("// begin cdef([^$]*)// end cdef")
cb_cdef_pattern = re.compile("// begin cb cdef([^$]*)// end cb cdef")

char* get_dl_error_message();

for header_file in ["R.h", "libR.h", "parse.h"]:
    with open(os.path.join(cwd, header_file), "r") as f:
        m = cdef_pattern.search(f.read(), re.M)
        ffibuilder.cdef(m.group(1).replace("RAPI_EXTERN", ""))

if sys.platform.startswith("win"):
    ffibuilder.cdef("""
        char *(*get_R_HOME)(void);
        char *(*getRUser)(void);
        int* UserBreak_t;
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
    "rapi._libR",
    """
    # include "libR.h"
    """,
    include_dirs=['src'],
    sources=['src/libR.c', 'src/parse.c'])

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
