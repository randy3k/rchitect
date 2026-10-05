import ctypes
import os
import platform
import re

import subprocess
import sys
from shutil import which

from packaging.version import parse as parse_version

if sys.platform.startswith("win"):
    from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER


# =============================================================================
# 1. R Discovery & Version
# =============================================================================


def is_arm():
    if sys.platform.startswith("win"):
        return "(arm64)" in sys.version.lower()
    return platform.machine().lower() in ("arm64", "aarch64")


def read_registry_from_local_machine(key, valueex):
    with OpenKey(HKEY_LOCAL_MACHINE, key) as k:
        return QueryValueEx(k, valueex)


def read_registry_from_current_user(key, valueex):
    with OpenKey(HKEY_CURRENT_USER, key) as k:
        return QueryValueEx(k, valueex)


def read_registry(key, valueex):
    try:
        return read_registry_from_current_user(key, valueex)
    except Exception:
        return read_registry_from_local_machine(key, valueex)


def read_r_install_path_from_registry():
    keys = (
        "Software\\R-Core\\R",
        "Software\\WOW6432Node\\R-Core\\R",
    )
    fallback = None
    for key in keys:
        for reader in (read_registry_from_current_user, read_registry_from_local_machine):
            try:
                path = reader(key, "InstallPath")[0]
            except Exception:
                continue
            if path and os.path.isdir(path):
                if fallback is None:
                    fallback = path
                dll_rel = (
                    os.path.join("bin", "R.dll")
                    if is_arm()
                    else os.path.join("bin", "x64", "R.dll")
                )
                if os.path.isfile(os.path.join(path, dll_rel)):
                    return path
    return fallback


def get_rhome_from_binary(rbinary):
    if rbinary:
        rbinary = os.path.expanduser(rbinary)
    if sys.platform.startswith("win"):
        if rbinary and not rbinary.lower().endswith((".exe", ".bat", ".cmd")):
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

    if os.environ.get("R_BINARY"):
        rbinary = os.environ["R_BINARY"]
        cached_rhome = os.environ.get("R_HOME")
        if (
            cached_rhome
            and os.environ.get("_RCHITECT_R_BINARY") == rbinary
            and os.environ.get("_RCHITECT_R_HOME") == cached_rhome
            and os.path.isdir(cached_rhome)
        ):
            return cached_rhome
        rhome = get_rhome_from_binary(rbinary)
        if not rhome:
            raise RuntimeError("R binary ({}) does not exist.".format(rbinary))
        os.environ["R_HOME"] = rhome
        os.environ["_RCHITECT_R_BINARY"] = rbinary
        os.environ["_RCHITECT_R_HOME"] = rhome
        return rhome

    if os.environ.get("R_HOME"):
        rhome = os.environ["R_HOME"]
        if not os.path.isdir(rhome):
            raise RuntimeError("R_HOME ({}) does not exist.".format(rhome))
        return rhome

    rhome = get_rhome_from_binary("R")

    if not rhome and sys.platform.startswith("win"):
        rhome = read_r_install_path_from_registry()

    if rhome:
        os.environ["R_HOME"] = rhome
    else:
        raise RuntimeError("Cannot determine R HOME.")

    return rhome


_R_VERSION_MAJOR_RE = re.compile(r'^#define\s+R_MAJOR\s+"([^"]+)"', re.M)
_R_VERSION_MINOR_RE = re.compile(r'^#define\s+R_MINOR\s+"([^"]+)"', re.M)
_R_DESC_VERSION_RE = re.compile(r"^Version:\s*(\S+)", re.M)
_rversion_cache = {}


def rversion(rhome=None):
    if not rhome:
        rhome = get_rhome()
    if rhome in _rversion_cache:
        return _rversion_cache[rhome]
    rversion_h = os.path.join(rhome, "include", "Rversion.h")
    if os.path.isfile(rversion_h):
        try:
            with open(rversion_h, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            m_major = _R_VERSION_MAJOR_RE.search(content)
            m_minor = _R_VERSION_MINOR_RE.search(content)
            if m_major and m_minor:
                version = parse_version("{}.{}".format(m_major.group(1), m_minor.group(1)))
                _rversion_cache[rhome] = version
                return version
        except Exception:
            pass
    base_desc = os.path.join(rhome, "library", "base", "DESCRIPTION")
    if os.path.isfile(base_desc):
        try:
            with open(base_desc, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            m_ver = _R_DESC_VERSION_RE.search(content)
            if m_ver:
                version = parse_version(m_ver.group(1))
                _rversion_cache[rhome] = version
                return version
        except Exception:
            pass
    try:
        output = (
            subprocess.check_output(
                [
                    os.path.join(rhome, "bin", "R"),
                    "--no-echo",
                    "--vanilla",
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
    _rversion_cache[rhome] = version
    return version


def ensure_path_for_dll(libr_path):
    libr_dir = os.path.dirname(libr_path)
    env_path = os.environ.get("PATH", "")
    norm_dir = os.path.normcase(os.path.normpath(libr_dir))
    path_entries = [
        os.path.normcase(os.path.normpath(p))
        for p in env_path.split(os.pathsep)
        if p
    ]
    if norm_dir not in path_entries:
        os.environ["PATH"] = (
            libr_dir + os.pathsep + env_path if env_path else libr_dir
        )


def get_libr_path(rhome, ensure_path=False):
    # TODO: better support R_ARCH
    if sys.platform.startswith("win"):
        if is_arm():
            libr_path = os.path.join(rhome, "bin", "R.dll")
        else:
            libr_path = os.path.join(rhome, "bin", "x64", "R.dll")
    elif sys.platform == "darwin":
        libr_path = os.path.join(rhome, "lib", "libR.dylib")
    else:
        libr_path = os.path.join(rhome, "lib", "libR.so")

    if not os.path.exists(libr_path):
        if sys.platform.startswith("win"):
            other_path = (
                os.path.join(rhome, "bin", "x64", "R.dll")
                if is_arm()
                else os.path.join(rhome, "bin", "R.dll")
            )
            if os.path.exists(other_path):
                raise RuntimeError(
                    "R ({}) and Python ({}) architectures do not match.".format(
                        "x64" if is_arm() else "ARM64",
                        "ARM64" if is_arm() else "x64",
                    )
                )
        raise RuntimeError("R share library ({}) does not exist.".format(libr_path))

    if sys.platform.startswith("win") and ensure_path:
        ensure_path_for_dll(libr_path)

    return libr_path


# =============================================================================
# 2. Shared Library Loading & Preload State
# =============================================================================

_libr_loaded = False
_external_libr = False
_host_active = False
_dll_dir_cookies = []


def _is_libr_in_process():
    try:
        if sys.platform.startswith("win"):
            kernel32 = ctypes.windll.kernel32
            kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
            kernel32.GetModuleHandleW.restype = ctypes.c_void_p
            return bool(kernel32.GetModuleHandleW("R.dll"))
        else:
            return hasattr(ctypes.CDLL(None), "R_GlobalEnv")
    except Exception:
        return False


def reset_preload_env():
    global _libr_loaded, _external_libr, _host_active
    if not _host_active and not _libr_loaded:
        if (
            "_RCHITECT_HOST_ACTIVE" not in os.environ
            and "_RCHITECT_LIBR_LOADED" not in os.environ
            and _is_libr_in_process()
        ):
            _external_libr = True
            _libr_loaded = True

    if os.environ.pop("_RCHITECT_HOST_ACTIVE", None) == "1":
        _host_active = True
    if os.environ.pop("_RCHITECT_LIBR_LOADED", None) == "1":
        if sys.platform.startswith("win"):
            _libr_loaded = True
        else:
            _libr_loaded = _is_libr_in_process()

    preload_libs = os.environ.pop("_RCHITECT_PRELOAD_LIBS", None)
    if not preload_libs:
        return

    var = "DYLD_INSERT_LIBRARIES" if sys.platform == "darwin" else "LD_PRELOAD"
    if var not in os.environ:
        return

    injected = set(preload_libs.split(":"))
    libs = [lib for lib in os.environ[var].split(":") if lib and lib not in injected]
    if libs:
        os.environ[var] = ":".join(libs)
    else:
        del os.environ[var]


def setup_r_dll_dir(rhome=None):
    if not rhome:
        rhome = get_rhome()
    libr_path = get_libr_path(rhome, ensure_path=True)
    libr_dir = os.path.dirname(libr_path)
    try:
        _dll_dir_cookies.append(os.add_dll_directory(libr_dir))
    except Exception:
        pass


class _LinkMap(ctypes.Structure):
    # Matches the prefix of `struct link_map` from `<link.h>` on Linux/glibc.
    # On Linux, the `void *` handle returned by `dlopen()` (`CDLL._handle`) is
    # a `struct link_map *`.
    _fields_ = [
        ("l_addr", ctypes.c_void_p),
        ("l_name", ctypes.c_void_p),
    ]


# Keep string buffers alive for the lifetime of the process since `l_name`
# stores a raw `char *` pointer read by the dynamic linker.
_soname_bufs = []


def _register_linux_soname(handle, soname):
    """Register a short SONAME on an already-loaded `ctypes.CDLL` handle on Linux.

    R on Linux builds `libR.so`, `libRblas.so`, and `libRlapack.so` without a
    `DT_SONAME` ELF header entry, while R's base package shared libraries
    (e.g., `utils.so`, `methods.so`, `stats.so`, `grDevices.so`, `lapack.so`)
    declare `DT_NEEDED` for the bare filename `"libR.so"` (or `"libRlapack.so"`
    / `"libRblas.so"`) without an `RPATH`.

    When `ctypes.CDLL(full_path, mode=ctypes.RTLD_GLOBAL)` loads `libR.so` by
    absolute path in a process started without `LD_LIBRARY_PATH` containing
    `$R_HOME/lib`, glibc only records the full path in `link_map->l_name`.
    Subsequent `dlopen()` calls from R for `utils.so` then fail to find
    `"libR.so"` because glibc's `_dl_name_match_p(name, map)` only sees the
    full path in `map->l_name` and has no `DT_SONAME` in `map->l_libname`.

    Pointing `link_map->l_name` to a pinned buffer containing the bare SONAME
    (e.g., `"libR.so"`) makes `_dl_name_match_p` match the in-memory library
    immediately without requiring `LD_LIBRARY_PATH` or process re-exec.
    """
    if not sys.platform.startswith("linux") or not getattr(handle, "_handle", None):
        return
    try:
        buf = ctypes.create_string_buffer(soname.encode("utf-8"))
        _soname_bufs.append(buf)
        _LinkMap.from_address(handle._handle).l_name = ctypes.addressof(buf)
    except Exception:
        pass


def load_libr(rhome=None):
    if not rhome:
        rhome = get_rhome()
    libr_path = get_libr_path(rhome)
    libr_dir = os.path.dirname(libr_path)
    if sys.platform != "darwin":
        rblas_path = os.path.join(libr_dir, "libRblas.so")
        if os.path.exists(rblas_path):
            try:
                h_blas = ctypes.CDLL(rblas_path, mode=ctypes.RTLD_GLOBAL)
                _register_linux_soname(h_blas, "libRblas.so")
            except OSError:
                pass
    try:
        h_r = ctypes.CDLL(libr_path, mode=ctypes.RTLD_GLOBAL)
        _register_linux_soname(h_r, "libR.so")
    except OSError as e:
        raise Exception("Cannot load shared library: {}".format(e))
    if sys.platform != "darwin":
        rlapack_path = os.path.join(libr_dir, "libRlapack.so")
        if os.path.exists(rlapack_path):
            try:
                h_lapack = ctypes.CDLL(rlapack_path, mode=ctypes.RTLD_GLOBAL)
                _register_linux_soname(h_lapack, "libRlapack.so")
            except OSError:
                pass


def ensure_libr():
    global _libr_loaded
    reset_preload_env()
    rhome = get_rhome()
    if rversion(rhome) < parse_version("4.2.0"):
        raise RuntimeError("R >= 4.2.0 is required")
    if _libr_loaded:
        return
    if sys.platform.startswith("win"):
        setup_r_dll_dir(rhome)
    else:
        load_libr(rhome)
    _libr_loaded = True


# =============================================================================
# 3. Host Launcher & Process Re-Exec
# =============================================================================


def get_host():
    if not sys.platform.startswith("win"):
        return None
    host = os.path.join(os.path.dirname(os.path.abspath(__file__)), "host.exe")
    if os.path.isfile(host):
        return host
    return None


def should_use_host():
    reset_preload_env()
    if _host_active or _external_libr:
        return False
    if os.environ.get("RCHITECT_HOST_DISABLED", "0") == "1":
        return False
    if sys.platform.startswith("win") and not get_host():
        return False
    return True


def _get_macos_blas_path(libr_path):
    """Resolve the actual BLAS dylib path used by `libR.dylib` on macOS.

    When preloading `libR.dylib` via `DYLD_INSERT_LIBRARIES`, its BLAS library
    must also be preloaded ahead of `libR.dylib` so BLAS symbols (e.g. `dgemm_`)
    are available in the flat namespace and when `$R_HOME/lib` is not in the
    default dyld search path.

    Different macOS R distributions link BLAS in different ways:
    - CRAN R links `@rpath/libRblas.dylib` in `$R_HOME/lib` (which may symlink
      to `libRblas.0.dylib` or Apple's Accelerate `libRblas.vecLib.dylib`).
    - Homebrew R links external OpenBLAS (`libopenblas.dylib`) directly and does
      not ship `$R_HOME/lib/libRblas.dylib` at all.

    Rather than manually parsing Mach-O load commands, we open `libR.dylib`
    with `dlopen(..., RTLD_LAZY | RTLD_LOCAL)`, look up `dgemm_` via `dlsym`,
    and query `dladdr` (`Dl_info.dli_fname`) so `dyld` itself reports the exact
    file path of the library providing BLAS symbols.
    """
    class _Dl_info(ctypes.Structure):
        _fields_ = [
            ("dli_fname", ctypes.c_char_p),
            ("dli_fbase", ctypes.c_void_p),
            ("dli_sname", ctypes.c_char_p),
            ("dli_saddr", ctypes.c_void_p),
        ]

    lib_dir = os.path.dirname(libr_path)
    open_path = os.path.realpath(libr_path)
    try:
        libc = ctypes.CDLL(None)
        libc.dlopen.argtypes = [ctypes.c_char_p, ctypes.c_int]
        libc.dlopen.restype = ctypes.c_void_p
        libc.dlsym.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        libc.dlsym.restype = ctypes.c_void_p
        libc.dladdr.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Dl_info)]
        libc.dladdr.restype = ctypes.c_int
        libc.dlclose.argtypes = [ctypes.c_void_p]
        libc.dlclose.restype = ctypes.c_int

        # RTLD_LAZY (0x1) | RTLD_LOCAL (0x4)
        handle = libc.dlopen(open_path.encode("utf-8"), 0x1 | 0x4)
        if handle:
            try:
                addr = libc.dlsym(handle, b"dgemm_")
                info = _Dl_info()
                if addr and libc.dladdr(addr, ctypes.byref(info)) and info.dli_fname:
                    blas_path = info.dli_fname.decode("utf-8", "ignore")
                    if blas_path:
                        return blas_path
            finally:
                libc.dlclose(handle)
    except Exception:
        pass
    fallback = os.path.join(lib_dir, "libRblas.dylib")
    if os.path.isfile(fallback):
        return fallback
    return None


def _setup_unix_preload_env(rhome, env):
    lib_path = os.path.join(rhome, "lib")
    ldpaths = os.path.join(rhome, "etc", "ldpaths")
    ldpaths_out = ""

    if os.path.isfile(ldpaths):
        try:
            sub_env = env.copy()
            sub_env["_RCHITECT_TMP_LDPATHS"] = ldpaths
            ldpaths_out = (
                subprocess.check_output(
                    [
                        "/bin/sh",
                        "-c",
                        '. "$_RCHITECT_TMP_LDPATHS" >/dev/null 2>&1; printf "%s" "$R_LD_LIBRARY_PATH"',
                    ],
                    env=sub_env,
                )
                .decode("utf-8", "ignore")
                .strip()
            )
        except Exception:
            pass
    else:
        ldpaths_out = env.get("R_LD_LIBRARY_PATH", "")

    if not ldpaths_out:
        r_ld_library_path = lib_path
    elif lib_path not in ldpaths_out.split(":"):
        r_ld_library_path = "{}:{}".format(lib_path, ldpaths_out)
    else:
        r_ld_library_path = ldpaths_out
    env["R_LD_LIBRARY_PATH"] = r_ld_library_path

    ld_var = "DYLD_FALLBACK_LIBRARY_PATH" if sys.platform == "darwin" else "LD_LIBRARY_PATH"
    existing_ld = env.get(ld_var, "")
    env[ld_var] = (
        "{}:{}".format(r_ld_library_path, existing_ld) if existing_ld else r_ld_library_path
    )

    if sys.platform == "darwin":
        libr_path = os.path.join(lib_path, "libR.dylib")
        if os.path.isfile(libr_path):
            open_path = os.path.realpath(libr_path)
            blas_path = _get_macos_blas_path(libr_path)
            if blas_path and blas_path != libr_path and blas_path != open_path:
                preload_libs = "{}:{}".format(blas_path, libr_path)
            else:
                preload_libs = libr_path
            existing_insert = env.get("DYLD_INSERT_LIBRARIES", "")
            env["DYLD_INSERT_LIBRARIES"] = (
                "{}:{}".format(existing_insert, preload_libs) if existing_insert else preload_libs
            )
            env["_RCHITECT_PRELOAD_LIBS"] = preload_libs
            env["_RCHITECT_LIBR_LOADED"] = "1"
    else:
        libr_path = os.path.join(lib_path, "libR.so")
        rblas_path = os.path.join(lib_path, "libRblas.so")
        if os.path.isfile(libr_path):
            if os.path.isfile(rblas_path):
                preload_libs = "{}:{}".format(rblas_path, libr_path)
            else:
                preload_libs = libr_path
            existing_preload = env.get("LD_PRELOAD", "")
            env["LD_PRELOAD"] = (
                "{}:{}".format(existing_preload, preload_libs) if existing_preload else preload_libs
            )
            env["_RCHITECT_PRELOAD_LIBS"] = preload_libs
            env["_RCHITECT_LIBR_LOADED"] = "1"


def _assign_job_kill_on_close(proc_handle):
    try:
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
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


def exec_host(args=None):
    if args is None:
        args = sys.argv[1:]
    args = list(args)

    if sys.platform.startswith("win"):
        host = get_host()
        if not host:
            return
        env = os.environ.copy()
        env["_RCHITECT_HOST_ACTIVE"] = "1"

        buf = ctypes.create_unicode_buffer(32768)
        ctypes.windll.kernel32.GetModuleFileNameW(ctypes.c_void_p(sys.dllhandle), buf, 32768)
        dll_path = buf.value
        base_exe = getattr(sys, "_base_executable", sys.executable)

        env["_RCHITECT_PYTHON_DLL"] = dll_path
        env["_RCHITECT_BASE_EXE"] = base_exe
        if os.path.normcase(sys.executable) != os.path.normcase(base_exe):
            env["__PYVENV_LAUNCHER__"] = sys.executable

        ctypes.windll.kernel32.SetConsoleCtrlHandler(None, True)
        p = subprocess.Popen([host] + args, env=env)
        _job = _assign_job_kill_on_close(int(p._handle))  # noqa: F841
        sys.exit(p.wait())
    else:
        for i, arg in enumerate(args):
            if arg.startswith("--r-binary=") and arg[11:]:
                os.environ["R_BINARY"] = arg[11:]
            elif arg == "--r-binary" and i + 1 < len(args) and args[i + 1]:
                os.environ["R_BINARY"] = args[i + 1]

        rhome = None
        try:
            rhome = get_rhome()
        except Exception:
            pass

        env = os.environ.copy()
        env["_RCHITECT_HOST_ACTIVE"] = "1"
        if rhome and os.path.isdir(rhome):
            _setup_unix_preload_env(rhome, env)

        os.execve(sys.executable, [sys.executable] + args, env)


def maybe_reexec(args=None, module=None):
    if not should_use_host():
        return
    if args is None:
        reexec_args = ["-P"] if sys.version_info >= (3, 11) else []
        if module:
            reexec_args += ["-m", module] + sys.argv[1:]
        else:
            reexec_args += sys.argv
    else:
        reexec_args = list(args)
    exec_host(reexec_args)

