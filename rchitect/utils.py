import os
import re
import subprocess
import sys
import platform
import ctypes
import locale
from shutil import which

from packaging.version import parse as parse_version

if sys.platform.startswith("win"):
    from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER


def is_arm():
    return platform.machine().lower() == "arm64"


def is_64bit():
    return sys.maxsize > 2**32


def read_registry_from_local_machine(key, valueex):
    return QueryValueEx(OpenKey(HKEY_LOCAL_MACHINE, key), valueex)


def read_registry_from_current_user(key, valueex):
    return QueryValueEx(OpenKey(HKEY_CURRENT_USER, key), valueex)


def read_registry(key, valueex):
    try:
        return read_registry_from_current_user(key, valueex)
    except Exception:
        return read_registry_from_local_machine(key, valueex)


def read_r_install_path_from_registry():
    try:
        return read_registry("Software\\WOW6432Node\\R-Core\\R", "InstallPath")[0]
    except Exception:
        pass
    try:
        return read_registry("Software\\R-Core\\R", "InstallPath")[0]
    except Exception:
        pass
    return None


DECODE_ERROR_HANDLER = "backslashreplace"



def get_rhome_from_binary(rbinary):
    if sys.platform.startswith("win"):
        if rbinary and not rbinary.endswith(".exe"):
            rbinary = rbinary + ".exe"

    if not which(rbinary):
        return None
    try:
        env = {k: v for k, v in os.environ.items() if k != "R_HOME"}
        return subprocess.check_output([rbinary, "RHOME"], env=env).decode("utf-8").strip()
    except Exception:
        pass
    return None


def get_rhome():
    rhome = None

    if "R_BINARY" in os.environ:
        rbinary = os.environ["R_BINARY"]
        rhome = get_rhome_from_binary(rbinary)
        if not rhome:
            raise RuntimeError(
                "R binary ({}) does not exist.".format(rbinary)
            )
        os.environ["R_HOME"] = rhome
        return rhome

    if "R_HOME" in os.environ:
        rhome = os.environ["R_HOME"]
        if not os.path.isdir(rhome):
            raise RuntimeError("R_HOME ({}) does not exist.".format(rhome))
        return rhome

    rhome = get_rhome_from_binary("R")

    if not rhome:
        if sys.platform.startswith("win"):
            rhome = read_r_install_path_from_registry()        

    if rhome:
        os.environ["R_HOME"] = rhome
    else:
        raise RuntimeError("Cannot determine R HOME.")

    return rhome


def get_libr_path(rhome, ensure_path=False):
    # TODO: better support R_ARCH
    if sys.platform.startswith("win"):
        if is_arm():
            libr_path = os.path.join(rhome, "bin", "R.dll")
        elif is_64bit():
            libr_path = os.path.join(rhome, "bin", "x64", "R.dll")
        else:
            libr_path = os.path.join(rhome, "bin", "i386", "R.dll")
    elif sys.platform == "darwin":
        libr_path = os.path.join(rhome, "lib", "libR.dylib")
    else:
        libr_path = os.path.join(rhome, "lib", "libR.so")
    
    if not os.path.exists(libr_path):
        raise RuntimeError("R share library ({}) does not exist.".format(libr_path))
    
    # microsoft python doesn't load DLL's from PATH
    # we will need to open the DLL's directly in _libR_load    
    if sys.platform.startswith("win"):
        if ensure_path:
            ensure_path_for_dll(libr_path)

    return libr_path


def ensure_path_for_dll(libr_path):
    libr_dir = os.path.dirname(libr_path)
    try:
        # make sure Rblas.dll can be reachable
        msvcrt = ctypes.cdll.msvcrt
        msvcrt._wgetenv.restype = ctypes.c_wchar_p
        path = msvcrt._wgetenv(ctypes.c_wchar_p("PATH"))
        if libr_dir not in path:
            path = libr_dir + ";" + path
            msvcrt._wputenv(ctypes.c_wchar_p("PATH={}".format(path)))
    except Exception as e:
        print(e)
        pass


_libr_preloaded = False
_dll_dir_cookies = []


def preload_libr():
    global _libr_preloaded
    if _libr_preloaded:
        return

    rhome = get_rhome()
    libr_path = get_libr_path(rhome, ensure_path=True)
    libr_dir = os.path.dirname(libr_path)

    if sys.platform.startswith("win"):
        if hasattr(os, "add_dll_directory"):
            try:
                _dll_dir_cookies.append(os.add_dll_directory(libr_dir))
            except Exception:
                pass
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.LoadLibraryExW.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
        ]
        kernel32.LoadLibraryExW.restype = ctypes.c_void_p
        for dll_name in [
            "R.dll",
            "Rgraphapp.dll",
            "Rblas.dll",
            "Riconv.dll",
            "Rlapack.dll",
        ]:
            dll_path = os.path.join(libr_dir, dll_name)
            # LOAD_LIBRARY_SEARCH_DEFAULT_DIRS | LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR
            handle = kernel32.LoadLibraryExW(dll_path, None, 0x00001100)
            if not handle:
                handle = kernel32.LoadLibraryExW(dll_path, None, 0)
            if not handle:
                err = ctypes.get_last_error()
                raise Exception(
                    "Cannot load shared library {}: {}".format(
                        dll_path, ctypes.FormatError(err).strip()
                    )
                )
    else:
        if sys.platform != "darwin":
            rblas_path = os.path.join(libr_dir, "libRblas.so")
            if os.path.exists(rblas_path):
                try:
                    ctypes.CDLL(rblas_path, mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    pass
        try:
            ctypes.CDLL(libr_path, mode=ctypes.RTLD_GLOBAL)
        except OSError as e:
            raise Exception("Cannot load shared library: {}".format(e))

    _libr_preloaded = True


def rversion(rhome=None):
    if not rhome:
        rhome = get_rhome()
    try:
        output = (
            subprocess.check_output(
                [
                    os.path.join(rhome, "bin", "R"),
                    "--no-echo",
                    "-e",
                    "cat(as.character(getRversion()))",
                ],
                stderr=subprocess.STDOUT,
            )
            .decode("utf-8")
            .strip()
        )
        version = parse_version(output)
    except Exception:
        version = parse_version("1000.0.0")
    return version


UTFPATTERN = re.compile(b"\x02\xff\xfe(.*?)\x03\xff\xfe", re.S)


def rconsole2str(buf):
    ret = ""
    m = UTFPATTERN.search(buf)
    while m:
        a, b = m.span()
        ret += system2utf8(buf[:a]) + m.group(1).decode("utf-8", "backslashreplace")
        buf = buf[b:]
        m = UTFPATTERN.search(buf)
    ret += system2utf8(buf)
    return ret


if sys.platform == "win32":
    """
    The following only works after setlocale in C and
    R will initialize it for us. To mimic the behaviour, consider
    ```
    ctypes.cdll.msvcrt.setlocale(0, ctypes.c_char_p("chinese-traditional"))
    ```
    """

    mbtowc = ctypes.cdll.msvcrt.mbtowc
    mbtowc.argtypes = [
        ctypes.POINTER(ctypes.c_wchar),
        ctypes.POINTER(ctypes.c_char),
        ctypes.c_size_t,
    ]
    mbtowc.restype = ctypes.c_int

    wctomb = ctypes.cdll.msvcrt.wctomb
    wctomb.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_wchar]
    wctomb.restype = ctypes.c_int

    def system2utf8(buf):
        loc = locale.getlocale()
        if loc[1] == "UTF-8" or loc[1] == "utf8" or loc[1] == "65001":
            return buf.decode("utf-8", DECODE_ERROR_HANDLER)

        wcbuf = ctypes.create_unicode_buffer(1)
        text = ""
        while buf:
            n = mbtowc(wcbuf, buf, len(buf))
            if n <= 0:
                break
            text += wcbuf[0]
            buf = buf[n:]
        return text

    def utf8tosystem(text):
        loc = locale.getlocale()
        if loc[1] == "UTF-8" or loc[1] == "utf8" or loc[1] == "65001":
            return text.encode("utf-8", "backslashreplace")

        s = ctypes.create_string_buffer(10)
        buf = b""
        for c in text:
            try:
                n = wctomb(s, c)
            except Exception:
                n = -1

            if n > 0:
                buf += s[:n]
            else:
                buf += "\\u{{{}}}".format(hex(ord(c))[2:]).encode("ascii")
        return buf

else:

    def system2utf8(buf):
        return buf.decode("utf-8", DECODE_ERROR_HANDLER)

    def utf8tosystem(text):
        return text.encode("utf-8", "backslashreplace")


def get_utf8_host():
    if not sys.platform.startswith("win"):
        return None
    host = os.path.join(os.path.dirname(os.path.abspath(__file__)), "utf8_host.exe")
    if os.path.isfile(host):
        return host
    return None


def should_use_utf8_host(rhome=None):
    if not sys.platform.startswith("win"):
        return False
    if os.environ.get("RCHITECT_UTF8_HOST_DISABLED", "0") == "1":
        return False
    if os.environ.get("_RCHITECT_UTF8_HOST_ACTIVE", "0") == "1":
        return False
    try:
        if ctypes.windll.kernel32.GetACP() == 65001:
            return False
    except Exception:
        return False
    if not get_utf8_host():
        return False
    if rversion(rhome) < parse_version("4.2.0"):
        return False
    return True


def _assign_job_kill_on_close(proc_handle):
    try:
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateJobObjectW.argtypes = [ ctypes.c_void_p, wintypes.LPCWSTR ]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [ wintypes.HANDLE, wintypes.HANDLE ]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE (0x2000) | JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK (0x1000)
        info.BasicLimitInformation.LimitFlags = 0x2000 | 0x1000
        # JobObjectExtendedLimitInformation = 9
        if not kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            return None
        kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(proc_handle))
        return job
    except Exception:
        return None


def exec_utf8_host(args=None):
    host = get_utf8_host()
    if not host:
        return
    if args is None:
        args = sys.argv[1:]

    buf = ctypes.create_unicode_buffer(32768)
    ctypes.windll.kernel32.GetModuleFileNameW(ctypes.c_void_p(sys.dllhandle), buf, 32768)
    dll_path = buf.value
    base_exe = getattr(sys, "_base_executable", sys.executable)

    env = os.environ.copy()
    env["_RCHITECT_UTF8_HOST_ACTIVE"] = "1"
    env["_RCHITECT_PYTHON_DLL"] = dll_path
    env["_RCHITECT_BASE_EXE"] = base_exe
    if os.path.normcase(sys.executable) != os.path.normcase(base_exe):
        env["__PYVENV_LAUNCHER__"] = sys.executable

    ctypes.windll.kernel32.SetConsoleCtrlHandler(None, True)
    p = subprocess.Popen([host] + list(args), env=env)
    _job = _assign_job_kill_on_close(int(p._handle))  # noqa: F841
    sys.exit(p.wait())

