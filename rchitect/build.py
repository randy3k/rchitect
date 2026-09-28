import os
import re
import sys
from cffi import FFI

ffibuilder = FFI()

cdef_pattern = re.compile(r"// begin cdef(.*?)// end cdef", re.S)
win_cdef_pattern = re.compile(r"// begin win cdef(.*?)// end win cdef", re.S)
unix_cdef_pattern = re.compile(r"// begin unix cdef(.*?)// end unix cdef", re.S)
cb_cdef_pattern = re.compile(r"// begin cb cdef(.*?)// end cb cdef", re.S)

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def _clean_cdef(text):
    return (
        text.replace("RAPI_EXTERN", "extern")
        .replace("RAPI_FUNC", "extern")
        .replace("RGRAPHAPP_FUNC", "extern")
    )


for header_file in ["R.h", "libR.h", "gil.h", "parse.h", "process_events.h"]:
    with open(os.path.join(BASEDIR, "_cffi", header_file), "r") as f:
        content = f.read()
        m = cdef_pattern.search(content)
        ffibuilder.cdef(_clean_cdef(m.group(1)))
        if header_file == "R.h":
            if sys.platform.startswith("win"):
                pm = win_cdef_pattern.search(content)
            else:
                pm = unix_cdef_pattern.search(content)
            if pm:
                ffibuilder.cdef(_clean_cdef(pm.group(1)))

with open(os.path.join(BASEDIR, "_cffi", "libR.h"), "r") as f:
    m = cb_cdef_pattern.search(f.read())
    ffibuilder.cdef(
        """
        extern "Python+C" {{
            {}
        }}
    """.format(
            m.group(1)
        )
    )

if sys.platform.startswith("win"):
    libraries = ["R", "Rgraphapp"]
    extra_compile_args = []
    extra_link_args = []
elif sys.platform == "darwin":
    libraries = []
    extra_compile_args = ["-fvisibility=hidden"]
    extra_link_args = ["-Wl,-undefined,dynamic_lookup"]
else:
    libraries = ["R"]
    extra_compile_args = ["-fvisibility=hidden"]
    extra_link_args = []

ffibuilder.set_source(
    "rchitect._cffi_lib",
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
    libraries=libraries,
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
