import sys
import subprocess
import pytest
from rchitect.utils import get_utf8_host, should_use_utf8_host


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only")
def test_utf8_host():
    host = get_utf8_host()
    assert host is not None
    assert should_use_utf8_host() is True

    inner_script = (
        "import sys, ctypes\n"
        "from rchitect import init, reval, rcopy, rcall, robject\n"
        "assert ctypes.windll.kernel32.GetACP() == 65001\n"
        "assert sys.executable == EXPECTED_EXE\n"
        "assert sys._base_executable == EXPECTED_BASE_EXE\n"
        "assert sys.prefix == EXPECTED_PREFIX\n"
        "init()\n"
        "s = '中文測試 αβγ'\n"
        "assert rcopy(reval(repr(s))) == s\n"
        "msg = '錯誤訊息 ' * 30\n"
        "err_fun = robject(lambda: (_ for _ in ()).throw(ValueError(msg)))\n"
        "captured = rcopy(rcall('tryCatch', rcall('as.call', [err_fun]), error=reval('function(e) conditionMessage(e)')))\n"
        "assert msg in captured\n"
        "print('UTF8_HOST_OK')\n"
    )
    code = (
        "import sys, rchitect.utils as u\n"
        f"script = {inner_script!r}\n"
        "script = script.replace('EXPECTED_EXE', repr(sys.executable))\n"
        "script = script.replace('EXPECTED_BASE_EXE', repr(sys._base_executable))\n"
        "script = script.replace('EXPECTED_PREFIX', repr(sys.prefix))\n"
        "u.exec_utf8_host(['-c', script])\n"
    )
    out = subprocess.check_output([sys.executable, "-c", code]).decode("utf-8").strip()
    assert out.endswith("UTF8_HOST_OK")
