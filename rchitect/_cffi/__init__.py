from rchitect.utils import ensure_libr

ensure_libr()

from rchitect._cffi_lib import ffi, lib  # noqa: E402

__all__ = ["ffi", "lib"]
