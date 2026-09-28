from rchitect.utils import preload_libr

preload_libr()

from rchitect._cffi_lib import ffi, lib  # noqa: E402

__all__ = ["ffi", "lib"]
