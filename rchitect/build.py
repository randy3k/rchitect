import os
import re
import sys
from cffi import FFI

ffibuilder = FFI()

# cwd = os.path.dirname(os.path.realpath(__file__))
cdef_pattern = re.compile("// begin cdef([^$]*)// end cdef")
cb_cdef_pattern = re.compile("// begin cb cdef([^$]*)// end cb cdef")

BASEDIR = os.path.abspath(os.path.dirname(__file__))


for header_file in ["R.h", "libR.h", "gil.h", "parse.h", "process_events.h"]:
    with open(os.path.join(BASEDIR, "_cffi", header_file), "r") as f:
        m = cdef_pattern.search(f.read(), re.M)
        ffibuilder.cdef(m.group(1).replace("RAPI_EXTERN", "extern"))

if sys.platform.startswith("win"):
    ffibuilder.cdef(
        """
        extern char *(*get_R_HOME)(void);
        extern char *(*getRUser)(void);
        extern int* UserBreak_t;
        extern int* CharacterMode_t;
        extern int* EmitEmbeddedUTF8_t;
        extern int (*GA_peekevent)(void);
        extern int (*GA_initapp)(int, char **);
    """
    )
else:
    ffibuilder.cdef(
        """
        extern void* R_InputHandlers;
        extern void (**R_PolledEvents_t)(void);
        extern void* (*R_checkActivity)(int usec, int ignore_stdin);
        extern void (*R_runHandlers)(void* handlers, void* mask);
        extern int* R_interrupts_pending_t;
    """
    )

with open(os.path.join(BASEDIR, "_cffi", "libR.h"), "r") as f:
    m = cb_cdef_pattern.search(f.read(), re.M)
    ffibuilder.cdef(
        """
        extern "Python+C" {{
            {}
        }}
    """.format(
            m.group(1)
        )
    )

ffibuilder.set_source(
    "rchitect._cffi",
    """
    # include "gil.h"
    # include "libR.h"
    # include "parse.h"
    # include "process_events.h"
    """,
    include_dirs=[os.path.join(BASEDIR, "_cffi")],
    sources=[
        os.path.join("rchitect", "_cffi", f)
        for f in ["libR.c", "gil.c", "parse.c", "process_events.c"]
    ],
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
