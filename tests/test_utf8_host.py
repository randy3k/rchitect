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
        "assert u._libr_loaded is True\n"
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
            "_RCHITECT_LIBR_LOADED",
            "_RCHITECT_PRELOAD_LIBS",
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
        if k
        not in (
            "_RCHITECT_HOST_ACTIVE",
            "_RCHITECT_LIBR_LOADED",
            "_RCHITECT_PRELOAD_LIBS",
        )
    }
    out = subprocess.check_output([sys.executable, "-c", script], env=env).decode("utf-8").strip()
    assert out.endswith("EXTERNAL_OK")


def test_stripped_preload_falls_back_to_load_libr():
    if sys.platform.startswith("win"):
        return

    script = (
        "import rchitect.utils as u\n"
        "assert u._host_active is True\n"
        "assert u._libr_loaded is False\n"
        "from rchitect import init, reval, rcopy\n"
        "assert u._libr_loaded is True\n"
        "init()\n"
        "assert rcopy(reval('1 + 1')) == 2\n"
        "print('FALLBACK_OK')\n"
    )
    env = os.environ.copy()
    env["_RCHITECT_HOST_ACTIVE"] = "1"
    env["_RCHITECT_LIBR_LOADED"] = "1"
    env.pop("DYLD_INSERT_LIBRARIES", None)
    env.pop("LD_PRELOAD", None)
    out = subprocess.check_output([sys.executable, "-c", script], env=env).decode("utf-8").strip()
    assert out.endswith("FALLBACK_OK")


def test_r_version_check(monkeypatch):
    import pytest
    import rchitect.utils as u
    from packaging.version import parse as parse_version

    monkeypatch.setattr(u, "rversion", lambda rhome=None: parse_version("4.1.3"))
    with pytest.raises(RuntimeError, match="R >= 4.2.0 is required"):
        u.ensure_libr()

