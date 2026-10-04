import os
import shutil
import subprocess
import sys
import pytest
from packaging.version import parse as parse_version
import rchitect.utils as u
from rchitect.utils import (
    ensure_path_for_dll,
    get_host,
    get_libr_path,
    get_rhome,
    get_rhome_from_binary,
    should_use_host,
)


def test_get_rhome_and_r_binary(monkeypatch, tmp_path):
    expected_rhome = get_rhome()
    rbinary = os.path.join(expected_rhome, "bin", "R")
    monkeypatch.setenv("R_BINARY", rbinary)
    monkeypatch.delenv("R_HOME", raising=False)
    assert get_rhome() == expected_rhome
    assert os.environ.get("R_HOME") == expected_rhome

    monkeypatch.setenv("R_HOME", "/nonexistent/rhome")
    assert get_rhome() == expected_rhome
    assert os.environ.get("R_HOME") == expected_rhome

    # Tilde expansion in get_rhome_from_binary
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert get_rhome_from_binary("~/nonexistent_R_bin") is None

    # ensure_path_for_dll compares normalized os.pathsep entries rather than substring match
    target_dir = os.path.join(str(tmp_path), "R", "bin")
    superstring_dir = target_dir + "_extra"
    monkeypatch.setenv("PATH", superstring_dir)
    ensure_path_for_dll(os.path.join(target_dir, "R.dll"))
    assert os.environ["PATH"].split(os.pathsep) == [target_dir, superstring_dir]
    # Second call is a no-op
    ensure_path_for_dll(os.path.join(target_dir, "R.dll"))
    assert os.environ["PATH"].split(os.pathsep) == [target_dir, superstring_dir]


def test_r_version_check(monkeypatch):
    monkeypatch.setattr(u, "rversion", lambda rhome=None: parse_version("4.1.3"))
    with pytest.raises(RuntimeError, match="R >= 4.2.0 is required"):
        u.ensure_libr()


def test_windows_arm64_detection_and_libr_path(monkeypatch, tmp_path):
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
        "if sys.platform == 'darwin':\n"
        "    blas = rcopy(reval('extSoftVersion()[\"BLAS\"]'))\n"
        "    rblas = os.path.join(os.environ['R_HOME'], 'lib', 'libRblas.dylib')\n"
        "    if os.path.isfile(rblas):\n"
        "        assert os.path.realpath(blas) == os.path.realpath(rblas)\n"
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


def test_macos_homebrew_r_without_librblas(tmp_path):
    if sys.platform != "darwin":
        return

    rhome = u.get_rhome()
    libr_path = u.get_libr_path(rhome)
    orig_rblas = os.path.join(rhome, "lib", "libRblas.dylib")
    if not os.path.isfile(orig_rblas):
        return

    otool_out = subprocess.check_output(["otool", "-L", libr_path]).decode("utf-8")
    old_blas_load = None
    for line in otool_out.splitlines()[1:]:
        dep = line.strip().split(" (", 1)[0]
        if dep.endswith("libRblas.dylib"):
            old_blas_load = dep
            break
    if not old_blas_load:
        return

    fake_rhome = tmp_path / "homebrew_r"
    fake_lib = fake_rhome / "lib"
    fake_lib.mkdir(parents=True)
    for entry in os.listdir(rhome):
        if entry != "lib":
            os.symlink(os.path.join(rhome, entry), str(fake_rhome / entry))

    real_lib_dir = os.path.join(rhome, "lib")
    for entry in os.listdir(real_lib_dir):
        if entry == "libR.dylib" or entry.startswith("libRblas"):
            continue
        os.symlink(os.path.join(real_lib_dir, entry), str(fake_lib / entry))

    ext_blas_dir = tmp_path / "openblas" / "lib"
    ext_blas_dir.mkdir(parents=True)
    fake_openblas = ext_blas_dir / "libopenblas_fake.dylib"
    shutil.copy2(os.path.realpath(orig_rblas), str(fake_openblas))
    subprocess.check_call(["install_name_tool", "-id", str(fake_openblas), str(fake_openblas)])
    subprocess.check_call(["codesign", "-f", "-s", "-", str(fake_openblas)])

    fake_libr = fake_lib / "libR.dylib"
    shutil.copy2(os.path.realpath(libr_path), str(fake_libr))
    subprocess.check_call(
        ["install_name_tool", "-change", old_blas_load, str(fake_openblas), str(fake_libr)]
    )
    subprocess.check_call(["codesign", "-f", "-s", "-", str(fake_libr)])

    assert not (fake_lib / "libRblas.dylib").exists()
    detected = u._get_macos_blas_path(str(fake_libr))
    assert detected is not None
    assert os.path.realpath(detected) == os.path.realpath(str(fake_openblas))

    inner_script = (
        "import os\n"
        "from rchitect import init, reval, rcopy\n"
        "init()\n"
        "blas = rcopy(reval('extSoftVersion()[\"BLAS\"]'))\n"
        f"assert os.path.realpath(blas) == os.path.realpath({str(fake_openblas)!r})\n"
        "print('HOMEBREW_BLAS_OK')\n"
    )
    code = (
        "import rchitect.utils as u\n"
        f"u.exec_host(['-c', {inner_script!r}])\n"
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in (
            "R_BINARY",
            "_RCHITECT_R_BINARY",
            "_RCHITECT_R_HOME",
            "_RCHITECT_HOST_ACTIVE",
            "_RCHITECT_LIBR_LOADED",
            "_RCHITECT_PRELOAD_LIBS",
            "DYLD_INSERT_LIBRARIES",
            "LD_PRELOAD",
        )
    }
    env["R_HOME"] = str(fake_rhome)
    out = (
        subprocess.check_output([sys.executable, "-c", code], env=env)
        .decode("utf-8")
        .strip()
    )
    assert out.endswith("HOMEBREW_BLAS_OK")
