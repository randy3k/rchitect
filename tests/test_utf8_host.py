import os
import shutil
import sys
import subprocess
from rchitect.utils import get_host, should_use_host


def test_host():
    if sys.platform.startswith("win"):
        assert get_host() is not None
    assert should_use_host() is True

    inner_script = (
        "import os, sys, ctypes\n"
        "import rchitect.utils as u\n"
        "assert u.should_use_host() is False\n"
        "assert 'R_HOME' in os.environ and os.path.isdir(os.environ['R_HOME'])\n"
        "if sys.platform.startswith('win'):\n"
        "    assert ctypes.windll.kernel32.GetACP() == 65001\n"
        "else:\n"
        "    assert 'R_LD_LIBRARY_PATH' in os.environ\n"
        "    ld_var = 'DYLD_FALLBACK_LIBRARY_PATH' if sys.platform == 'darwin' else 'LD_LIBRARY_PATH'\n"
        "    assert ld_var in os.environ\n"
        "    preload_var = 'DYLD_INSERT_LIBRARIES' if sys.platform == 'darwin' else 'LD_PRELOAD'\n"
        "    assert preload_var not in os.environ\n"
        "assert sys.executable == EXPECTED_EXE\n"
        "assert sys._base_executable == EXPECTED_BASE_EXE\n"
        "assert sys.prefix == EXPECTED_PREFIX\n"
        "from rchitect import init, reval, rcopy, rcall, robject\n"
        "assert u._libr_loaded is True\n"
        "init()\n"
        "s = '中文測試 αβγ'\n"
        "assert rcopy(reval(repr(s))) == s\n"
        "msg = '錯誤訊息 ' * 30\n"
        "err_fun = robject(lambda: (_ for _ in ()).throw(ValueError(msg)))\n"
        "captured = rcopy(rcall('tryCatch', rcall('as.call', [err_fun]), error=reval('function(e) conditionMessage(e)')))\n"
        "assert msg in captured\n"
        "print('HOST_OK')\n"
    )
    code = (
        "import sys, rchitect.utils as u\n"
        f"script = {inner_script!r}\n"
        "script = script.replace('EXPECTED_EXE', repr(sys.executable))\n"
        "script = script.replace('EXPECTED_BASE_EXE', repr(sys._base_executable))\n"
        "script = script.replace('EXPECTED_PREFIX', repr(sys.prefix))\n"
        "u.exec_host(['-c', script])\n"
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in (
            "_RCHITECT_HOST_ACTIVE",
            "_RCHITECT_LIBR_LOADED",
            "_RCHITECT_PRELOAD_LIBS",
            "DYLD_INSERT_LIBRARIES",
            "LD_PRELOAD",
        )
    }
    out = subprocess.check_output([sys.executable, "-c", code], env=env).decode("utf-8").strip()
    assert out.endswith("HOST_OK")


def test_host_r_binary_arg(tmp_path):
    r_bin = shutil.which("R")
    if not r_bin:
        return

    inner_script = (
        "import os\n"
        "import rchitect.utils as u\n"
        "u.maybe_reexec()\n"
        "assert os.environ.get('R_BINARY') == EXPECTED_RBIN\n"
        "assert os.environ.get('_RCHITECT_R_BINARY') == EXPECTED_RBIN\n"
        "assert os.path.isdir(os.environ.get('R_HOME', ''))\n"
        "assert os.environ.get('_RCHITECT_R_HOME') == os.environ.get('R_HOME')\n"
        "print('RBIN_OK')\n"
    )
    script_file = tmp_path / "run_rbin.py"
    script_file.write_text(inner_script.replace("EXPECTED_RBIN", repr(r_bin)), encoding="utf-8")
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in (
            "R_HOME",
            "R_BINARY",
            "_RCHITECT_R_BINARY",
            "_RCHITECT_R_HOME",
            "_RCHITECT_HOST_ACTIVE",
        )
    }
    out = (
        subprocess.check_output(
            [sys.executable, str(script_file), f"--r-binary={r_bin}"],
            env=env,
        )
        .decode("utf-8")
        .strip()
    )
    assert out.endswith("RBIN_OK")


def test_external_libr_skips_host():
    from rchitect.utils import get_rhome, get_libr_path

    libr_path = get_libr_path(get_rhome())
    script = (
        "import ctypes, os, sys\n"
        f"libr_path = {libr_path!r}\n"
        "if sys.platform.startswith('win'):\n"
        "    os.add_dll_directory(os.path.dirname(libr_path))\n"
        "    ctypes.WinDLL(libr_path)\n"
        "else:\n"
        "    ctypes.CDLL(libr_path, mode=ctypes.RTLD_GLOBAL)\n"
        "import rchitect.utils as u\n"
        "assert u._external_libr is True\n"
        "assert u.should_use_host() is False\n"
        "print('EXTERNAL_OK')\n"
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k != "_RCHITECT_HOST_ACTIVE"
    }
    out = subprocess.check_output([sys.executable, "-c", script], env=env).decode("utf-8").strip()
    assert out.endswith("EXTERNAL_OK")


def test_unix_r_lib_symlink():
    if sys.platform.startswith("win"):
        return

    script = (
        "import os\n"
        "import rchitect.utils as u\n"
        "assert u._libr_loaded is False\n"
        "from rchitect import init, reval, rcopy\n"
        "assert u._libr_loaded is True\n"
        "r_lib_link = os.path.join(os.path.dirname(os.path.abspath(u.__file__)), '_r_lib')\n"
        "assert os.path.islink(r_lib_link)\n"
        "assert os.readlink(r_lib_link) == os.path.dirname(u.get_libr_path(u.get_rhome()))\n"
        "init()\n"
        "assert rcopy(reval('1 + 1')) == 2\n"
        "print('SYMLINK_OK')\n"
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("LD_LIBRARY_PATH", "DYLD_FALLBACK_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES", "LD_PRELOAD")
    }
    out = subprocess.check_output([sys.executable, "-c", script], env=env).decode("utf-8").strip()
    assert out.endswith("SYMLINK_OK")


def test_r_version_check(monkeypatch):
    import pytest
    import rchitect.utils as u
    from packaging.version import parse as parse_version

    monkeypatch.setattr(u, "rversion", lambda rhome=None: parse_version("4.1.3"))
    with pytest.raises(RuntimeError, match="R >= 4.2.0 is required"):
        u.ensure_libr()


def test_windows_arm64_detection_and_libr_path(monkeypatch, tmp_path):
    import pytest
    import rchitect.utils as u

    monkeypatch.setattr(u.sys, "platform", "win32")
    monkeypatch.setattr(u.platform, "machine", lambda: "ARM64")

    # x64 Python running under emulation on Windows 11 ARM64 (#40)
    monkeypatch.setattr(
        u.sys,
        "version",
        "3.13.0 (tags/v3.13.0:60403a5, Oct  7 2024, 09:38:07) [MSC v.1941 64 bit (AMD64)]",
    )
    assert u.is_arm() is False

    rhome_x64 = tmp_path / "R-x64"
    (rhome_x64 / "bin" / "x64").mkdir(parents=True)
    dll_x64 = rhome_x64 / "bin" / "x64" / "R.dll"
    dll_x64.write_bytes(b"")
    assert u.get_libr_path(str(rhome_x64)) == str(dll_x64)

    # Native ARM64 Python on Windows 11 ARM64
    monkeypatch.setattr(
        u.sys,
        "version",
        "3.13.0 (tags/v3.13.0:60403a5, Oct  7 2024, 09:53:29) [MSC v.1941 64 bit (ARM64)]",
    )
    assert u.is_arm() is True

    rhome_arm = tmp_path / "R-arm64"
    (rhome_arm / "bin").mkdir(parents=True)
    dll_arm = rhome_arm / "bin" / "R.dll"
    dll_arm.write_bytes(b"")
    assert u.get_libr_path(str(rhome_arm)) == str(dll_arm)

    # Architecture mismatch: ARM64 Python with x64 R
    with pytest.raises(RuntimeError, match=r"R \(x64\) and Python \(ARM64\) architectures do not match"):
        u.get_libr_path(str(rhome_x64))

    # Architecture mismatch: x64 Python with ARM64 R
    monkeypatch.setattr(
        u.sys,
        "version",
        "3.13.0 (tags/v3.13.0:60403a5, Oct  7 2024, 09:38:07) [MSC v.1941 64 bit (AMD64)]",
    )
    with pytest.raises(RuntimeError, match=r"R \(ARM64\) and Python \(x64\) architectures do not match"):
        u.get_libr_path(str(rhome_arm))

    # Registry lookup prefers R installation matching Python architecture
    reg_entries = {
        "Software\\R-Core\\R": (str(rhome_arm), 1),
        "Software\\WOW6432Node\\R-Core\\R": (str(rhome_x64), 1),
    }
    monkeypatch.setattr(u, "read_registry_from_current_user", lambda k, v: (_ for _ in ()).throw(OSError()))
    monkeypatch.setattr(u, "read_registry_from_local_machine", lambda k, v: reg_entries[k])

    assert u.read_r_install_path_from_registry() == str(rhome_x64)

    monkeypatch.setattr(
        u.sys,
        "version",
        "3.13.0 (tags/v3.13.0:60403a5, Oct  7 2024, 09:53:29) [MSC v.1941 64 bit (ARM64)]",
    )
    assert u.read_r_install_path_from_registry() == str(rhome_arm)


