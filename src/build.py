from cffi import FFI
ffibuilder = FFI()

# Rembedded.h
ffibuilder.cdef("""
int (*Rf_initialize_R)(int ac, char **av);
void (*setup_Rmainloop)();
void (*run_Rmainloop)();
""")

# libR.h
ffibuilder.cdef("""
char* get_last_loaded_symbol();

char* get_dl_error_message();

for header_file in ["R.h", "libR.h"]:
    with open(os.path.join(cwd, header_file), "r") as f:
        m = cdef_pattern.search(f.read(), re.M)
        if m:
            ffibuilder.cdef(m.group(1).replace("RAPI_EXTERN", ""))


HEADER = """
# include "R.h"
# include "libR.h"
"""

ffibuilder.set_source(
    "rapi._libR",
    HEADER,
    include_dirs=['src'],
    sources=['src/libR.c'])

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
