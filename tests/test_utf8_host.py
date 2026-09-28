import sys
import subprocess
import pytest
from rchitect.utils import get_utf8_host, should_use_utf8_host


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows only")
def test_utf8_host():
    host = get_utf8_host()
    assert host is not None
    assert should_use_utf8_host() is True

    code = (
        "import sys, ctypes, rchitect.utils as u; "
        "u.exec_utf8_host(['-c', "
        "'import sys, ctypes; "
        "assert ctypes.windll.kernel32.GetACP() == 65001; "
        "assert sys.executable == ' + repr(sys.executable) + '; "
        "assert sys._base_executable == ' + repr(sys._base_executable) + '; "
        "assert sys.prefix == ' + repr(sys.prefix) + '; "
        "print(\"UTF8_HOST_OK\")'])"
    )
    out = subprocess.check_output([sys.executable, "-c", code]).decode("utf-8").strip()
    assert out == "UTF8_HOST_OK"
