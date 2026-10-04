import os
import re
import shutil
import sys
from setuptools import setup
from setuptools.command.build_ext import build_ext as _build_ext


def parse_r_h_symbols():
    r_h_path = os.path.join("rchitect", "_cffi", "R.h")
    with open(r_h_path, "r") as f:
        content = f.read()

    cdef_m = re.search(r"// begin cdef(.*?)// end cdef", content, re.S)
    if sys.platform.startswith("win"):
        plat_m = re.search(r"// begin win cdef(.*?)// end win cdef", content, re.S)
    else:
        plat_m = re.search(r"// begin unix cdef(.*?)// end unix cdef", content, re.S)

    sections = (cdef_m.group(1) if cdef_m else "") + "\n" + (plat_m.group(1) if plat_m else "")

    r_funcs = []
    r_data = []
    rgraphapp_funcs = []

    for line in sections.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("RAPI_FUNC "):
            m = re.match(r"^RAPI_FUNC\s+.*?\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
            if m:
                r_funcs.append(m.group(1))
        elif line.startswith("RGRAPHAPP_FUNC "):
            m = re.match(r"^RGRAPHAPP_FUNC\s+.*?\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
            if m:
                rgraphapp_funcs.append(m.group(1))
        elif line.startswith("RAPI_EXTERN "):
            m = re.search(r"\(\s*\*\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", line)
            if not m:
                m = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*;$", line)
            if m:
                r_data.append(m.group(1))

    return r_funcs, r_data, rgraphapp_funcs


class build_ext(_build_ext):
    def run(self):
        self._extra_outputs = []
        if sys.platform.startswith("win"):
            self.build_win_import_libs()
        else:
            self.build_unix_stub_libs()
        super().run()
        if sys.platform.startswith("win"):
            self.build_host()

    def get_outputs(self):
        outputs = super().get_outputs()
        return outputs + getattr(self, "_extra_outputs", [])

    def _get_initialized_compiler(self):
        from setuptools._distutils.ccompiler import new_compiler
        from setuptools._distutils.sysconfig import customize_compiler

        compiler = getattr(self, "compiler", None)
        if compiler is None or isinstance(compiler, str):
            compiler = new_compiler(compiler=compiler)
            customize_compiler(compiler)
        if hasattr(compiler, "initialize") and not getattr(compiler, "initialized", False):
            compiler.initialize()
        return compiler

    def _add_temp_library_dir(self, lib_dir):
        abs_dir = os.path.abspath(lib_dir)
        if self.library_dirs is None:
            self.library_dirs = []
        if abs_dir not in self.library_dirs:
            self.library_dirs.append(abs_dir)
        for ext in getattr(self, "extensions", []):
            if abs_dir not in ext.library_dirs:
                ext.library_dirs.append(abs_dir)

    def build_win_import_libs(self):
        os.makedirs(self.build_temp, exist_ok=True)
        r_funcs, r_data, rgraphapp_funcs = parse_r_h_symbols()
        compiler = self._get_initialized_compiler()

        r_def = os.path.join(self.build_temp, "R.def")
        with open(r_def, "w") as f:
            f.write("LIBRARY R\nEXPORTS\n")
            for sym in r_funcs:
                f.write("    {}\n".format(sym))
            for sym in r_data:
                f.write("    {} DATA\n".format(sym))

        rga_def = os.path.join(self.build_temp, "Rgraphapp.def")
        with open(rga_def, "w") as f:
            f.write("LIBRARY Rgraphapp\nEXPORTS\n")
            for sym in rgraphapp_funcs:
                f.write("    {}\n".format(sym))

        import sysconfig

        plat = (getattr(self, "plat_name", None) or sysconfig.get_platform()).lower()
        if "arm64" in plat:
            machine = "/MACHINE:ARM64"
        else:
            machine = "/MACHINE:X64"

        r_lib = os.path.join(self.build_temp, "R.lib")
        rga_lib = os.path.join(self.build_temp, "Rgraphapp.lib")
        lib_exe = getattr(compiler, "lib", "lib.exe")
        compiler.spawn([lib_exe, "/nologo", machine, "/def:" + r_def, "/out:" + r_lib])
        compiler.spawn([lib_exe, "/nologo", machine, "/def:" + rga_def, "/out:" + rga_lib])
        self._add_temp_library_dir(self.build_temp)

    def build_unix_stub_libs(self):
        os.makedirs(self.build_temp, exist_ok=True)
        r_funcs, r_data, _ = parse_r_h_symbols()
        compiler = self._get_initialized_compiler()

        stub_r_c = os.path.join(self.build_temp, "stub_r.c")
        with open(stub_r_c, "w") as f:
            for sym in r_funcs:
                f.write("void {}(void) {{}}\n".format(sym))
            for sym in r_data:
                f.write("void *{} = 0;\n".format(sym))

        stub_rblas_c = os.path.join(self.build_temp, "stub_rblas.c")
        with open(stub_rblas_c, "w") as f:
            f.write("void dgemm_(void) {}\n")

        stub_rlapack_c = os.path.join(self.build_temp, "stub_rlapack.c")
        with open(stub_rlapack_c, "w") as f:
            f.write("void dgesv_(void) {}\n")

        objs = compiler.compile(
            [stub_r_c, stub_rblas_c, stub_rlapack_c],
            output_dir=self.build_temp,
        )

        if sys.platform == "darwin":
            linker = [arg for arg in compiler.linker_so if arg != "-bundle"] + ["-dynamiclib"]
            for obj, libname in zip(objs, ("libR.dylib", "libRblas.dylib", "libRlapack.dylib")):
                out_lib = os.path.join(self.build_temp, libname)
                compiler.spawn(
                    linker + [obj, "-Wl,-install_name,@rpath/" + libname, "-o", out_lib]
                )
        else:
            for obj, libname in zip(objs, ("libR.so", "libRblas.so", "libRlapack.so")):
                out_lib = os.path.join(self.build_temp, libname)
                compiler.link_shared_object(
                    [obj],
                    out_lib,
                    extra_postargs=["-Wl,-soname," + libname],
                )

        self._add_temp_library_dir(self.build_temp)

    def build_host(self):
        compiler = self._get_initialized_compiler()
        sources = [
            os.path.join("rchitect", "_cffi", "host.c"),
            os.path.join("rchitect", "_cffi", "host.rc"),
        ]
        objs = compiler.compile(
            sources,
            output_dir=self.build_temp,
            include_dirs=[os.path.join("rchitect", "_cffi")],
        )
        out_dir = os.path.join(self.build_lib, "rchitect")
        os.makedirs(out_dir, exist_ok=True)
        compiler.link_executable(
            objs,
            "host",
            output_dir=out_dir,
            libraries=["advapi32"],
            extra_postargs=["/MANIFEST:NO", "/STACK:0x4000000"],
        )
        built_exe = os.path.join(out_dir, "host.exe")
        self._extra_outputs.append(built_exe)
        if self.inplace:
            shutil.copy2(built_exe, os.path.join("rchitect", "host.exe"))


setup(
    cffi_modules=["rchitect/build.py:ffibuilder"],
    cmdclass={"build_ext": build_ext},
)
