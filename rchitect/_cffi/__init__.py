import os
import sys
from rchitect.utils import ensure_libr

ensure_libr()

if sys.platform.startswith("linux"):
    _old_dlopen_flags = sys.getdlopenflags()
    sys.setdlopenflags(_old_dlopen_flags | os.RTLD_GLOBAL)
    try:
        from rchitect._cffi_lib import ffi, lib  # noqa: E402
    finally:
        sys.setdlopenflags(_old_dlopen_flags)
else:
    from rchitect._cffi_lib import ffi, lib  # noqa: E402

__all__ = ["ffi", "lib"]
