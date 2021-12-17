import pytest
from rchitect import rcall



@pytest.fixture(scope='function')
def gctorture():
    rcall("gctorture", True)
    yield
    rcall("gctorture", False)
