import os
import shutil
import sys
from setuptools import setup
from setuptools.command.build_ext import build_ext as _build_ext


class build_ext(_build_ext):
    def run(self):
        self._extra_outputs = []
        super().run()
        if sys.platform.startswith("win"):
            self.build_utf8_host()

    def get_outputs(self):
        outputs = super().get_outputs()
        return outputs + getattr(self, "_extra_outputs", [])

    def build_utf8_host(self):
        from setuptools._distutils.ccompiler import new_compiler

        compiler = getattr(self, "compiler", None)
        if compiler is None:
            compiler = new_compiler(compiler=self.compiler)
            compiler.initialize()
        elif hasattr(compiler, "initialized") and not compiler.initialized:
            compiler.initialize()

        sources = [
            os.path.join("rchitect", "_cffi", "utf8_host.c"),
            os.path.join("rchitect", "_cffi", "utf8_host.rc"),
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
            "utf8_host",
            output_dir=out_dir,
            extra_postargs=["/MANIFEST:NO", "/STACK:0x4000000"],
        )
        built_exe = os.path.join(out_dir, "utf8_host.exe")
        self._extra_outputs.append(built_exe)
        if self.inplace:
            shutil.copy2(built_exe, os.path.join("rchitect", "utf8_host.exe"))


setup(
    cffi_modules=["rchitect/build.py:ffibuilder"],
    cmdclass={"build_ext": build_ext},
)
